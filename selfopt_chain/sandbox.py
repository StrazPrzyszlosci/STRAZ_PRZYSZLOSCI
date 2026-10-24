"""Filesystem and network boundary for local validation of untrusted artifacts."""
from pathlib import Path
import shutil
import subprocess


class Sandbox:
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()

    def command(self, argv, mounts=None, environment=None):
        binary = shutil.which('bwrap')
        if not binary:
            raise RuntimeError('bubblewrap_required')
        args = [binary, '--unshare-all', '--die-with-parent', '--new-session',
                '--clearenv', '--setenv', 'PATH', '/usr/bin:/bin',
                '--setenv', 'HOME', '/work/home', '--proc', '/proc', '--dev', '/dev',
                '--tmpfs', '/tmp']
        for path in ['/usr', '/bin', '/sbin', '/lib', '/lib64']:
            if Path(path).exists():
                args += ['--ro-bind', path, path]
        for source, target in (mounts or []):
            args += ['--ro-bind', str(source), target]
        for key, value in (environment or {}).items():
            args += ['--setenv', key, str(value)]
        args += ['--bind', str(self.workspace), '/work', '--chdir', '/work', '--', *argv]
        return args

    def run(self, argv, timeout=30):
        return subprocess.run(self.command(argv), capture_output=True, text=True, timeout=timeout)
