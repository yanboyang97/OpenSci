"""Read-only, stdlib workspace observation; also sent verbatim over SSH/WSL.

No authentication probes, package installations or experiment submission.
Origin is hashed to avoid exposing embedded credentials in repository URLs.
"""
import getpass
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def observe(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Workspace must be a directory')

    def git(*args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                                timeout=10, check=True)
        return result.stdout.decode('utf-8').strip()

    if Path(git('rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('Workspace must be the repository root')
    commit = git('rev-parse', 'HEAD')
    dirty = bool(git('status', '--porcelain', '--untracked-files=normal'))
    try:
        origin = git('remote', 'get-url', 'origin')
    except subprocess.CalledProcessError:
        origin = ''
    return {'schema_version': 1, 'workspace': str(root), 'account': getpass.getuser(),
            'host': platform.node(), 'os': platform.system().lower(),
            'commit': commit, 'dirty': dirty,
            'origin_sha256': hashlib.sha256(origin.encode()).hexdigest() if origin else None,
            'python': platform.python_version(),
            'tools': {name: shutil.which(name) is not None for name in ('git', 'codex', 'claude', 'gcloud')},
            'tests': 'not_checked', 'authentication': 'not_checked',
            'model_services': 'not_checked', 'unattended': 'not_checked'}


if __name__ == '__main__':
    try:
        print(json.dumps(observe(sys.argv[1]), ensure_ascii=True))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        # Commands may contain repository credentials: never print command/stderr.
        print(json.dumps({'error': type(exc).__name__, 'available': False}))
        raise SystemExit(2)
