"""Package an existing Hermes install for a secret-free, offline sandbox. Never installs packages."""
import argparse
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
from pathlib import Path


def prepare(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    version = destination / commit
    if (version / 'READY.json').exists():
        return version
    version.mkdir(parents=True, exist_ok=True)
    archive = subprocess.check_output(['git', '-C', str(source), 'archive', commit])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        members = [m for m in tar.getmembers() if '.env' not in Path(m.name).parts and not m.name.endswith(('.pem', '.key'))]
        tar.extractall(version / 'source', members=members, filter='data')
    packages = source / '.venv/lib/python3.12/site-packages'
    if not (packages / 'openai').exists():
        raise RuntimeError('an existing CPython 3.12 Hermes venv is required')
    shutil.copytree(packages, version / 'deps', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pth'), symlinks=False)
    (version / 'venv/bin').mkdir(parents=True, exist_ok=True)
    (version / 'venv/lib/python3.12').mkdir(parents=True, exist_ok=True)
    (version / 'venv/pyvenv.cfg').write_text('home = /usr/bin\ninclude-system-site-packages = false\nversion = 3.12\n')
    for path, target in [(version / 'venv/bin/python3', '/usr/bin/python3'),
                         (version / 'venv/lib/python3.12/site-packages', '/runtime/deps')]:
        if not path.is_symlink():
            path.symlink_to(target)
    (version / 'bin').mkdir(exist_ok=True)
    (version / 'entry.py').write_text('''import os,sys
from pathlib import Path
sys.path[:0]=["/runtime/source","/runtime/deps"]
os.environ["HERMES_HOME"]="/work/home"
os.environ["TERMINAL_ENV"]="local"
Path("/work/home").mkdir(exist_ok=True)
# This is the ephemeral, fixed-model proxy token, never a provider credential.
# Hermes' custom-provider child does not consistently read OPENAI_API_KEY.
if "--oneshot" in sys.argv and "--api-key" not in sys.argv and os.environ.get("OPENAI_API_KEY"):
    sys.argv.extend(["--api-key",os.environ["OPENAI_API_KEY"]])
from hermes_cli.main import main
main()
''')
    (version / 'bin/hermes').write_text('#!/bin/sh\nexec /runtime/venv/bin/python3 /runtime/entry.py "$@"\n')
    (version / 'bin/hermes').chmod(0o755)
    (version / 'READY.json').write_text(json.dumps({'source_commit': commit, 'python': '3.12',
         'source_archive_sha256': hashlib.sha256(archive).hexdigest(), 'dependency_source': 'existing venv; no .pth hooks',
         'host_configuration_copied': False}, indent=2))
    return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.source, args.destination))
