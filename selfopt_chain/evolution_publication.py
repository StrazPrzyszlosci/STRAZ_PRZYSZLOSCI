"""Idempotent publication requests. Producer never receives GitHub credentials or main access."""
import hashlib
import os
import uuid
import json
import re
import subprocess
from pathlib import Path


def atomic_write(path, data):
    temp = path.with_name('.' + uuid.uuid4().hex + '.tmp')
    with temp.open('w') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def request_publication(state_dir, receipt_path, repository):
    state, receipt_path = Path(state_dir).resolve(), Path(receipt_path).resolve()
    if not receipt_path.is_relative_to(state / 'evolution_queue') or receipt_path.name != 'evolution_receipt.json':
        raise ValueError('receipt_outside_controller_queue')
    receipt = json.loads(receipt_path.read_text())
    if not all(receipt.get(k) is True for k in ['gate_ok', 'execution_ok', 'security_ok', 'validation_ok', 'review_ok']):
        raise ValueError('candidate_not_ready')
    validation = receipt.get('validation') or {}
    archive = Path(receipt.get('archive_path', '')).resolve()
    if not archive.is_relative_to(state / 'candidate_archive'):
        raise ValueError('archive_outside_controller')
    patch = archive / 'changes.patch'
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()
    if validation.get('patch_sha256') != digest:
        raise ValueError('patch_changed_after_validation')
    worker = json.loads((receipt_path.parent / 'hermes_receipt.json').read_text())
    base = worker.get('source_commit', '')
    if not re.fullmatch('[a-f0-9]{40}', base) or not re.fullmatch(r'[\w.-]+/[\w.-]+', repository):
        raise ValueError('invalid_base_or_repository')
    folder = state / 'publication_requests'
    folder.mkdir(exist_ok=True)
    path = folder / (digest + '.json')
    if path.exists():
        return path
    request = {'status': 'awaiting_publisher', 'repository': repository, 'base_commit': base,
               'branch': 'codex/evolution-' + digest[:16], 'patch': str(patch), 'patch_sha256': digest,
               'receipt': str(receipt_path), 'title': receipt['title'], 'draft': True,
               'auto_merge': False, 'no_direct_push': True,
               'body': 'Automatycznie wytworzony kandydat: ' + receipt['title'] + '\n\n'
                       'Niezależny odbiór: baseline fail, candidate pass, pełna regresja pass. '
                       'Review modelu: pass. Wymagane review człowieka przed merge.\n\n'
                       'Patch SHA256: ' + digest + '\nBaseline: ' + base}
    atomic_write(path, request)
    return path


def stage_branch(request_path, repo_root):
    path, root = Path(request_path), Path(repo_root)
    request = json.loads(path.read_text())
    if not re.fullmatch(r'codex/evolution-[a-f0-9]{16}', request.get('branch', '')) or request.get('auto_merge') is not False or request.get('draft') is not True:
        raise ValueError('publication_policy_violation')
    if request.get('published_url'):
        return request
    patch = Path(request['patch'])
    if hashlib.sha256(patch.read_bytes()).hexdigest() != request['patch_sha256']:
        raise ValueError('patch_changed')
    def git(*args, cwd=root):
        return subprocess.check_output(['git', '-C', str(cwd), *args], text=True).strip()
    if request.get('prepared_commit'):
        if git('rev-parse', request['branch']) != request['prepared_commit']:
            raise ValueError('publication_branch_changed')
        return request
    workspace = path.parent.parent / 'publication_worktrees' / request['branch'].split('/')[-1]
    workspace.parent.mkdir(exist_ok=True)
    git('worktree', 'add', '-b', request['branch'], str(workspace), request['base_commit'])
    git('apply', '--check', str(patch), cwd=workspace)
    git('apply', str(patch), cwd=workspace)
    git('add', '-A', cwd=workspace)
    git('commit', '-m', 'evolution: ' + request['title'], cwd=workspace)
    request.update(status='prepared', prepared_commit=git('rev-parse', 'HEAD', cwd=workspace), workspace=str(workspace))
    atomic_write(path, request)
    return request


def record_published(request_path, url):
    path = Path(request_path)
    request = json.loads(path.read_text())
    if not re.fullmatch('https://github.com/' + re.escape(request['repository']) + r'/pull/\d+', url):
        raise ValueError('invalid_pull_request_url')
    if request.get('published_url') not in [None, url]:
        raise ValueError('already_published')
    request.update(status='published', published_url=url)
    atomic_write(path, request)
