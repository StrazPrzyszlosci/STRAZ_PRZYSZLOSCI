"""Check worktree claims and reserve tasks under one shared Git lock."""
import argparse
import fcntl
import fnmatch
import json
import re
import subprocess
from datetime import date
from pathlib import Path


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def collect(root, all_worktrees=False):
    roots = [Path(root)]
    if all_worktrees:
        roots = [Path(line[9:]) for line in git(root, 'worktree', 'list', '--porcelain').splitlines() if line.startswith('worktree ')]
    claims = {}
    superseded = set()
    for tree in roots:
        for path in (tree / 'docs/AGENT_CLAIMS').glob('*.md'):
            text = path.read_text()
            # An operator's transfer remains authoritative after the new
            # owner finishes; closing a claim must not resurrect old owners.
            if 'Decyzja operatora' in text:
                line = re.search(r'^- Supersedes claims: (.*)', text, re.M)
                if line:
                    superseded.update(re.findall(r'T\d+-[\w-]+\.md', line[1]))
            match = re.search(r'^- Status:\s*(\w+)', text, re.M)
            if not match or match[1] != 'in_progress':
                continue
            task = re.match(r'T\d+', path.name)
            if not task:
                continue
            scope = re.search(r'<!-- claim-scope (.*?) -->', text)
            claims[path.name] = {'task': task[0], 'path': str(path),
                                 'writes': json.loads(scope[1])['writes'] if scope else []}
    return {name: claim for name, claim in claims.items() if name not in superseded}


def overlap(first, second):
    return first == second or fnmatch.fnmatch(first, second) or fnmatch.fnmatch(second, first)


def conflicts(claims):
    found = []
    entries = list(claims.items())
    for i, (name, item) in enumerate(entries):
        for other_name, other in entries[i + 1:]:
            if item['task'] == other['task'] or any(overlap(a, b) for a in item['writes'] for b in other['writes']):
                found.append([name, other_name])
    return found


def reserve(root, task, owner, writes):
    if not re.fullmatch(r'T\d+', task) or not re.fullmatch(r'[a-zA-Z0-9_-]+', owner):
        raise ValueError('invalid task or owner')
    common = Path(git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    with (common / 'agent-claims.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        claims = collect(root, True)
        candidate = f'{task}-{owner}.md'
        claims[candidate] = {'task': task, 'path': candidate, 'writes': writes}
        if conflicts(claims):
            raise ValueError('claim collision: ' + json.dumps(conflicts(claims)))
        path = Path(root) / 'docs/AGENT_CLAIMS' / candidate
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as file:
            file.write(f'# CLAIM {task} — {owner}\n- Zadanie: {task}\n- Status: in_progress\n- Start: {date.today()}\n'
                       f'- Branch/worktree: {git(root, "branch", "--show-current")} / {Path(root).resolve()}\n'
                       '- Dotknięte pliki: ' + ', '.join(writes) + '\n'
                       '<!-- claim-scope ' + json.dumps({'writes': writes}) + ' -->\n')
        return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'reserve'])
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--all-worktrees', action='store_true')
    parser.add_argument('--task')
    parser.add_argument('--owner')
    parser.add_argument('--writes', nargs='+', default=[])
    args = parser.parse_args()
    if args.action == 'reserve':
        print(reserve(args.root, args.task or '', args.owner or '', args.writes))
        return 0
    claims = collect(args.root, args.all_worktrees)
    found = conflicts(claims)
    print(json.dumps({'active_claims': len(claims), 'conflicts': found}, ensure_ascii=False))
    return 1 if found else 0


if __name__ == '__main__':
    raise SystemExit(main())
