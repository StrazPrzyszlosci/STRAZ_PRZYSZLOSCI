"""Build explicit, bounded worker inputs from public source and typed runtime metadata."""
from __future__ import annotations
import hashlib
import ast
import json
import re
import subprocess
import tarfile
import io
from dataclasses import asdict
from pathlib import Path


class InputUnavailable(ValueError):
    pass


def safe_relative(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise InputUnavailable('unsafe_input_path')
    if any(part in {'.git', '.env', 'providers.json'} for part in path.parts):
        raise InputUnavailable('private_input_path')
    return path


def public_runtime(path, name):
    if not path.exists():
        raise InputUnavailable('missing_runtime:' + name)
    rows = [json.loads(s) for s in path.read_text().splitlines() if s.strip()] if path.suffix == '.jsonl' else json.loads(path.read_text())
    if not rows:
        raise InputUnavailable('empty_runtime:' + name)
    if name == 'decisions.jsonl':
        allowed = {'id', 'question_type', 'deferred', 'chosen', 'final', 'confidence', 'probabilities', 'options', 'scores', 'engine'}
    elif name == 'labels.jsonl':
        allowed = {'decision_id', 'accepted', 'source'}
    else:
        raise InputUnavailable('runtime_not_exportable:' + name)
    return [{k: v for k, v in row.items() if k in allowed} for row in rows]


def prepare_inputs(task, repo_root, state_dir, feedback=None):
    root, state = Path(repo_root), Path(state_dir)
    files, runtime = {}, {}
    try:
        tracked = set(subprocess.check_output(['git', '-C', str(root), 'ls-files'], text=True).splitlines())
    except subprocess.CalledProcessError:
        tracked = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    refs = list(task.input_refs)
    if task.source.startswith('handoff:'):
        refs.insert(0, 'docs/' + task.source.split(':', 1)[1])
    for value in dict.fromkeys(refs):
        relative = safe_relative(value)
        path = root / relative
        if str(relative) not in tracked or path.is_symlink() or not path.is_file():
            raise InputUnavailable('missing_public_source:' + str(relative))
        text = path.read_text()
        if len(text.encode()) > 120000:
            raise InputUnavailable('source_too_large:' + str(relative))
        files[str(relative)] = text
    for name in task.runtime_refs:
        path = state / safe_relative(name)
        if path.is_symlink() or not path.resolve().is_relative_to(state.resolve()):
            raise InputUnavailable('unsafe_runtime_source:' + name)
        runtime[name] = public_runtime(path, name)
    if task.kind == 'patch' and (not task.allowed_paths or not task.acceptance_ref):
        raise InputUnavailable('patch_requires_scope_and_acceptance')
    acceptance = None
    if task.acceptance_ref:
        relative = safe_relative(task.acceptance_ref)
        if str(relative) not in tracked or not (root / relative).is_file():
            raise InputUnavailable('missing_acceptance:' + str(relative))
        acceptance = (root / relative).read_text()
    excerpts = {}
    for name, symbols in task.focus_symbols.items():
        if name not in files:
            raise InputUnavailable('missing_focus_source:' + name)
        lines = files[name].splitlines()
        selected = [node for node in ast.walk(ast.parse(files[name])) if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in symbols]
        if len(selected) < len(symbols):
            raise InputUnavailable('missing_focus_symbol:' + name)
        excerpts[name] = '\n\n'.join('\n'.join(lines[node.lineno - 1:node.end_lineno]) for node in selected)
    manifest = {'task_id': task.task_id, 'title': task.title, 'context': task.context,
                'constraints': task.constraints, 'kind': task.kind, 'allowed_paths': task.allowed_paths,
                'input_files': files, 'runtime_metadata': runtime, 'acceptance': acceptance,
                'previous_feedback': feedback or {}, 'source_excerpts': excerpts, 'expected_outputs': ['output/PROPOSAL.md'] + (['output/changes.patch'] if task.kind == 'patch' else [])}
    # Feedback is context for the next attempt, not a new version of the inputs.
    version = {k: v for k, v in manifest.items() if k != 'previous_feedback'}
    manifest['input_hash'] = hashlib.sha256(json.dumps(version, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return manifest


def task_prompt(manifest):
    snippets = []
    for name, text in manifest['input_files'].items():
        # Exact files are mounted too; inline only the relevant starting context.
        snippets.append(f'### /repo/{name}\n' + manifest.get('source_excerpts', {}).get(name, text[:16000]))
    return '\n'.join([
        '# Zadanie ewolucji repo — wykonaj konkretny wynik',
        json.dumps({k: manifest[k] for k in ['task_id', 'title', 'context', 'constraints', 'kind', 'allowed_paths', 'expected_outputs']}, ensure_ascii=False),
        'Repo jest dostępne tylko do odczytu pod /repo. Pełny manifest: /input/task.json.',
        'Nie szukaj plików po całym repo. Poniżej masz konkretne ścieżki i ich kontekst.',
        'Zapisz wynik w /work/output/PROPOSAL.md. Dla zadania patch zapisz również /work/output/changes.patch jako poprawny unified diff względem /repo.',
        'Patch może zmieniać wyłącznie allowed_paths. Nie kopiuj całego repo. Nie instaluj pakietów i nie używaj sieci poza skonfigurowanym API.',
        'Testy uruchomi kontroler w izolowanej kopii. Zapoznaj się z acceptance w /input/task.json. Wynik stdout nie zastępuje plików.',
        'Runtime metadata: ' + json.dumps(manifest['runtime_metadata'], ensure_ascii=False),
        'Aktualny sprzęt hosta (nie zmienia wersji zadania): ' + json.dumps(manifest.get('hardware_context', {}), ensure_ascii=False),
        'Niezależny warunek odbioru:\n' + (manifest.get('acceptance') or 'Nie dotyczy kodu; wymagany konkretny opis w PROPOSAL.md.'),
        'Poprzednia próba i uwagi do poprawy: ' + json.dumps(manifest['previous_feedback'], ensure_ascii=False),
        *snippets,
    ])


def repository_snapshot(repo_root, state_dir):
    import fcntl
    import shutil
    import uuid
    root = Path(repo_root)
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    parent = Path(state_dir) / 'repo_snapshots'
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / commit
    with (parent / 'snapshot.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not target.exists():
            temp = parent / ('.' + uuid.uuid4().hex)
            temp.mkdir()
            try:
                data = subprocess.check_output(['git', '-C', str(root), 'archive', commit])
                with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                    archive.extractall(temp, filter='data')
                temp.rename(target)
            finally:
                if temp.exists():
                    shutil.rmtree(temp)
    return target, commit
