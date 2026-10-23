"""Independent validation of a quarantined patch against an immutable source snapshot."""
import ast
import fnmatch
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from selfopt_chain.sandbox import Sandbox


def validate_patch(output, snapshot, manifest, destination):
    output, snapshot, destination = Path(output), Path(snapshot), Path(destination)
    patch = output / 'changes.patch'
    proposal = output / 'PROPOSAL.md'
    report = {'ok': False, 'method': 'independent_patch_validation', 'checks': {}, 'changed_paths': []}
    if not patch.is_file() or patch.is_symlink() or not proposal.is_file() or not proposal.read_text().strip():
        return {**report, 'error': 'missing_patch_or_proposal'}
    try:
        stat = subprocess.run(['git', 'apply', '--numstat', '-z', str(patch.resolve())], cwd=snapshot,
                              capture_output=True, check=True).stdout.decode()
        paths = [row.split('\t', 2)[-1] for row in stat.split('\0') if row]
        forbidden = {'.git', '.env', 'AGENTS.md', 'charter.json'}
        if not paths or any(Path(p).is_absolute() or '..' in Path(p).parts or any(x in forbidden for x in Path(p).parts)
                            or not any(fnmatch.fnmatch(p, allowed) for allowed in manifest['allowed_paths']) for p in paths):
            return {**report, 'error': 'patch_outside_scope', 'changed_paths': paths}
        destination.mkdir(parents=True, exist_ok=True)
        candidate = destination / 'candidate'
        shutil.copytree(snapshot, candidate)
        subprocess.run(['git', 'apply', '--check', str(patch.resolve())], cwd=candidate, capture_output=True, check=True)
        subprocess.run(['git', 'apply', str(patch.resolve())], cwd=candidate, capture_output=True, check=True)
        for path in paths:
            file = candidate / path
            if file.is_symlink() or not file.resolve().is_relative_to(candidate.resolve()):
                return {**report, 'error': 'unsafe_candidate_path'}
            if file.suffix == '.py' and file.exists():
                ast.parse(file.read_text())
        report['checks']['patch_applies_and_syntax'] = True
        report['changed_paths'] = paths
        acceptance = destination / 'acceptance'
        acceptance.mkdir()
        (acceptance / 'check.py').write_text(manifest['acceptance'])
        # The acceptance program is supplied by the controller, never the producer.
        for name, tree in [('baseline', snapshot), ('candidate', candidate)]:
            result = subprocess.run(Sandbox(tree).command(['/usr/bin/python3', '/acceptance/check.py'],
                                    mounts=[(acceptance, '/acceptance')]), capture_output=True, text=True, timeout=90)
            (destination / (name + '_acceptance.log')).write_text(result.stdout + result.stderr)
            report['checks'][name + '_acceptance_returncode'] = result.returncode
        if report['checks']['baseline_acceptance_returncode'] == 0:
            return {**report, 'error': 'no_demonstrated_improvement'}
        if report['checks']['candidate_acceptance_returncode'] != 0:
            return {**report, 'error': 'acceptance_failed', 'feedback': (destination / 'candidate_acceptance.log').read_text()[-6000:]}
        result = Sandbox(candidate).run(['/usr/bin/python3', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'], timeout=150)
        (destination / 'full_python.log').write_text(result.stdout + result.stderr)
        report['checks']['full_python_returncode'] = result.returncode
        if result.returncode:
            return {**report, 'error': 'regression_failed', 'feedback': (destination / 'full_python.log').read_text()[-6000:]}
        report.update(ok=True, patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
                      candidate_dir=str(candidate), demonstrated_improvement='baseline acceptance fails; candidate acceptance and full regression pass')
    except (OSError, ValueError, SyntaxError, subprocess.SubprocessError) as error:
        report['error'] = type(error).__name__
    return report
