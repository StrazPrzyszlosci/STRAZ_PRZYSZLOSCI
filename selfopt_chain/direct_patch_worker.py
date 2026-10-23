"""A bounded patch producer for complete task contracts; all code still goes through sandbox validation."""
import difflib
import fnmatch
import json
import os
import uuid
from pathlib import Path
from selfopt_chain.evolution_inputs import repository_snapshot, safe_relative
from selfopt_chain.evolution_validation import validate_patch
from selfopt_chain.hermes_worker import SecurityGate
from selfopt_chain.omniroute import OmniRouteEngine
from selfopt_chain.quota import BudgetedEngine


class DirectPatchWorker:
    executor_name = 'direct_patch'

    def __init__(self, models, ledger, repo_root, state_dir, should_stop=None):
        self.models, self.ledger = models, ledger
        self.repo_root, self.state_dir = Path(repo_root), Path(state_dir)
        self.should_stop = should_stop or (lambda: False)
        self.engine = BudgetedEngine(OmniRouteEngine(models), models, ledger, self.should_stop)

    @staticmethod
    def enabled():
        return os.environ.get('SELFOPT_NETWORK') == '1'

    def run_isolated(self, query, *, model_alias=None, input_bundle=None):
        run_id = uuid.uuid4().hex[:12]
        output = self.state_dir / 'direct_quarantine' / run_id
        output.mkdir(parents=True)
        receipt = {'run_id': run_id, 'quarantine_dir': str(output), 'executed': False, 'exit_code': None,
                   'security_gate': {'ok': False}, 'validation': {'ok': False}, 'released_from_quarantine': False,
                   'producer': self.executor_name}
        try:
            max_tokens = int(os.environ.get('SELFOPT_CODE_MAX_TOKENS', '8192'))
        except ValueError:
            receipt['error'] = 'invalid_output_budget'
            return receipt
        if not 1024 <= max_tokens <= 16384:
            receipt['error'] = 'invalid_output_budget'
            return receipt
        receipt['max_output_tokens'] = max_tokens
        bundle = input_bundle or {}
        if bundle.get('kind') != 'patch':
            receipt['error'] = 'direct_producer_requires_patch_contract'
            return receipt
        snapshot, commit = repository_snapshot(self.repo_root, self.state_dir)
        receipt['source_commit'] = commit
        focused_sources = {name: bundle.get('source_excerpts', {}).get(name, text[:16000]) for name, text in bundle['input_files'].items()}
        contract = {key: bundle.get(key) for key in ['task_id','title','context','constraints','allowed_paths','acceptance','previous_feedback']}
        contract['sources'] = focused_sources
        instruction = '\n'.join([
            'Przygotuj minimalną poprawkę kodu. Nie masz narzędzi; wszystkie wejścia i warunki masz poniżej.',
            'Odpowiedz WYŁĄCZNIE JSON: {"proposal": "opis markdown", "edits": [{"path":"plik", "old":"dokładny unikalny istniejący fragment", "new":"nowy fragment"}], "new_files": [{"path":"nowy test", "content":"kod"}]}',
            'W edits zachowaj dokładne wcięcia i znaki nowej linii. old musi występować raz. Nie zmieniaj nic poza allowed_paths.',
            'Nie zwracaj unified diff ani poleceń shell. Kontroler zbuduje patch i uruchomi niezależne testy.',
            json.dumps(contract, ensure_ascii=False),
        ])
        requested = model_alias
        used, attempts = set(), {}
        receipt['attempt_results'] = []
        for _ in range(2):
            result = self.engine.complete({'kind': 'code_draft', 'privacy': 'public', 'task_id': bundle['task_id'], 'max_tokens': max_tokens}, requested, instruction)
            receipt['attempt_results'].append({key: result.get(key) for key in
                ['requested_model_id', 'ok', 'error_class', 'latency_ms', 'response_diagnostic']})
            if result.get('attempt_recorded'):
                mid = result['requested_model_id']
                attempts[mid] = attempts.get(mid, 0) + 1
                used.add(mid)
            if result.get('ok') or result.get('error_class') not in {'connection_error','http_error','bad_response'}:
                break
            from selfopt_chain.router import route_task
            alternatives = [m for m in self.models if m['model_id'] not in used]
            decision = route_task({'kind':'code_draft','privacy':'public','requires':['text','code']}, alternatives, self.ledger)
            requested = (decision.get('chosen') or {}).get('model_id')
            if not requested:
                break
        receipt['executed'] = True
        receipt['model_id'] = result.get('model_id')
        receipt['api_calls'] = attempts
        if not result.get('ok'):
            receipt.update(exit_code=1, error=result.get('error_class'))
            return receipt
        raw = result.get('output', '')
        (output / 'response.json').write_text(json.dumps({'model_id': result.get('model_id'), 'output': raw}, ensure_ascii=False))
        try:
            start, end = raw.find('{'), raw.rfind('}')
            response = json.loads(raw[start:end + 1])
            changed, originals = {}, {}
            edits, new_files = response.get('edits', []), response.get('new_files', [])
            if not isinstance(edits, list) or not isinstance(new_files, list) or len(edits) + len(new_files) > 12:
                raise ValueError('invalid_edit_list')
            def scoped(value):
                name = str(safe_relative(value))
                if not any(fnmatch.fnmatch(name, pattern) for pattern in bundle['allowed_paths']):
                    raise ValueError('edit_outside_scope:' + name)
                return name
            for edit in edits:
                name = scoped(edit['path'])
                source = snapshot / name
                if not source.is_file() or source.is_symlink():
                    raise ValueError('source_missing:' + name)
                original = source.read_text()
                if name in bundle['input_files'] and bundle['input_files'][name] != original:
                    raise ValueError('source_snapshot_changed')
                originals.setdefault(name, original)
                current = changed.get(name, original)
                old, new = edit['old'], edit['new']
                if not isinstance(old, str) or not isinstance(new, str) or not old or current.count(old) != 1:
                    raise ValueError('old_fragment_not_unique_or_exact:' + name)
                changed[name] = current.replace(old, new, 1)
            for new_file in new_files:
                name = scoped(new_file['path'])
                if (snapshot / name).exists() or name in changed:
                    raise ValueError('new_file_already_exists:' + name)
                originals[name], changed[name] = '', new_file['content']
            if not changed or not isinstance(response.get('proposal'), str) or not response['proposal'].strip():
                raise ValueError('empty_production')
            patch = ''.join(''.join(difflib.unified_diff(originals[name].splitlines(True), content.splitlines(True),
                            fromfile='a/' + name if originals[name] else '/dev/null', tofile='b/' + name)) for name, content in changed.items())
            (output / 'changes.patch').write_text(patch)
            (output / 'PROPOSAL.md').write_text(response['proposal'])
            gate = SecurityGate().inspect_code(patch + '\n' + response['proposal'])
            receipt['security_gate'] = gate
            receipt['exit_code'] = 0
            if gate['ok']:
                receipt['validation'] = validate_patch(output, snapshot, bundle, self.state_dir / 'validations' / run_id)
            if not receipt['validation'].get('ok'):
                receipt['error'] = receipt['validation'].get('error', 'unsafe_production')
        except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
            receipt.update(exit_code=1, error=str(error))
        return receipt
