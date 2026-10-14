"""Launch the bundled Study MCP using an operator-owned local connection file."""
import json
import os
from pathlib import Path
import sys


def connection_path():
    explicit = os.environ.get('OPENSCI_CONNECTION_FILE')
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            raise ValueError('Connection path must be absolute')
        return path
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA')
        if not base:
            raise ValueError('Local application directory unavailable')
        return Path(base) / 'OpenSci' / 'connection.json'
    return Path.home() / '.config' / 'opensci' / 'connection.json'


def main():
    try:
        if sys.version_info < (3, 10):
            raise ValueError('Python 3.10 or newer required')
        path = connection_path()
        if path.stat().st_size > 16384:
            raise ValueError('Oversized connection file')
        cfg = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(cfg, dict) or set(cfg) != {'schema_version', 'coordinator_root', 'policy'}:
            raise ValueError('Invalid connection fields')
        if type(cfg['schema_version']) is not int or cfg['schema_version'] != 1:
            raise ValueError('Unsupported connection format')
        root, policy = Path(cfg['coordinator_root']), Path(cfg['policy'])
        if not root.is_absolute() or not root.is_dir() or not policy.is_absolute() or not policy.is_file():
            raise ValueError('Missing absolute coordinator or policy path')
        server = Path(__file__).resolve().with_name('hub_mcp.py')
    except (OSError, ValueError, TypeError, KeyError):
        # Do not echo paths, configuration contents or raw exceptions to the host.
        print('OpenSci Study setup is required. Configure the local connection file and a protected policy; see docs/PLUGINS.md.', file=sys.stderr)
        return 2
    # Only this bundled entrypoint is executable; the config supplies data paths.
    os.execv(sys.executable, [sys.executable, '-E', '-s', '-B', str(server),
                            '--coordinator-root', str(root), '--policy', str(policy)])
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
