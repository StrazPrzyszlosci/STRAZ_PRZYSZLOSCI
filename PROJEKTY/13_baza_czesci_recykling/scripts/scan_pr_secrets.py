#!/usr/bin/env python3
"""Pre-PR secret scan for Project 13.

Scans staged or specified files for potential secret patterns.
Run before opening a PR to catch accidental secret commits.

Usage:
  python3 scan_pr_secrets.py                  # scan all tracked files
  python3 scan_pr_secrets.py --staged          # scan only git-staged files
  python3 scan_pr_secrets.py --diff HEAD~1    # scan files changed since HEAD~1
  python3 scan_pr_secrets.py --diff main      # scan files changed vs branch main

Exit code: 0 = clean, 1 = potential secrets found, 2 = error.
"""

import argparse
import os
import re
import subprocess
import sys

PATTERNS = [
    (r'(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}', 'GitHub PAT / token'),
    (r'AIzaSy[A-Za-z0-9_\-]{30,}', 'Google API key (YouTube/Gemini)'),
    (r'ya29\.[A-Za-z0-9_\-]{30,}', 'Google OAuth access token'),
    (r'sk-[A-Za-z0-9]{20,}', 'OpenAI / Anthropic API key'),
    (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', 'Private key'),
    (r'(password|passwd|secret|token|api_key|apikey|access_key|secret_key)\s*[:=]\s*["\'][A-Za-z0-9_\-]{8,}["\']', 'Hardcoded credential value'),
]

EXCLUDE_PATHS = {
    '.env.example',
    'PROJEKTY/13_baza_czesci_recykling/.env.example',
    'scan_pr_secrets.py',
}

EXCLUDE_EXTENSIONS = {
    '.jsonl',
    '.csv',
    '.sql',
}

EXCLUDE_DIRS = {
    'tests',
    'test',
    '__pycache__',
}

compiled = [(re.compile(p), label) for p, label in PATTERNS]


def get_files(mode, diff_ref):
    if mode == 'staged':
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True, text=True
        )
    elif mode == 'diff' and diff_ref:
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--diff-filter=ACM', diff_ref],
            capture_output=True, text=True
        )
    else:
        result = subprocess.run(
            ['git', 'ls-files'],
            capture_output=True, text=True
        )
    if result.returncode != 0:
        print(f'git error: {result.stderr.strip()}', file=sys.stderr)
        sys.exit(2)
    return [f for f in result.stdout.strip().splitlines() if f]


def should_skip(filepath):
    basename = os.path.basename(filepath)
    if filepath in EXCLUDE_PATHS or basename in EXCLUDE_PATHS:
        return True
    _, ext = os.path.splitext(filepath)
    if ext.lower() in EXCLUDE_EXTENSIONS:
        return True
    parts = filepath.replace('\\', '/').split('/')
    for d in parts:
        if d.lower() in EXCLUDE_DIRS:
            return True
    return False


def scan_file(filepath):
    findings = []
    try:
        with open(filepath, 'r', errors='replace') as f:
            for lineno, line in enumerate(f, 1):
                for regex, label in compiled:
                    if regex.search(line):
                        findings.append((lineno, label, line.rstrip()[:200]))
                        break
    except (OSError, IOError):
        pass
    return findings


def main():
    parser = argparse.ArgumentParser(description='Pre-PR secret scan for Project 13')
    parser.add_argument('--staged', action='store_true', help='Scan only git-staged files')
    parser.add_argument('--diff', metavar='REF', help='Scan files changed since REF (e.g. HEAD~1, main)')
    args = parser.parse_args()

    mode = 'staged' if args.staged else ('diff' if args.diff else 'all')
    files = get_files(mode, args.diff)

    if not files:
        print('No files to scan.')
        sys.exit(0)

    total_findings = 0
    for filepath in files:
        if should_skip(filepath):
            continue
        findings = scan_file(filepath)
        for lineno, label, line in findings:
            print(f'  {filepath}:{lineno}  [{label}]  {line}')
            total_findings += 1

    if total_findings > 0:
        print(f'\nFound {total_findings} potential secret(s). Do not commit these values.')
        print('Move secrets to .env (local), Kaggle Secrets, or GitHub Secrets instead.')
        sys.exit(1)
    else:
        print(f'Scanned {len(files)} file(s). No potential secrets detected.')
        sys.exit(0)


if __name__ == '__main__':
    main()
