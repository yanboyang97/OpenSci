"""Build distributable archives from an explicitly reviewed file inventory."""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tools' / 'release_files.json'
FORBIDDEN = re.compile(r'(?i)(?:^|/)(?:tests?|__pycache__|node_modules|secrets|runs|backups|archives|audit|\.venv)(?:/|$)|\.local\.|\.(?:pyc|log|pid|lnk|key|pem|pfx|p12|dpapi|db|sqlite|sqlite3|zip|tar|gz)$|(?:^|/)\.env(?:\.|$)')
SECRET = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{24,}|AKIA[A-Z0-9]{16})\b')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_inventory():
    obj = json.loads(MANIFEST.read_text(encoding='utf-8'))
    names = obj['files']
    if obj.get('schema_version') != 1 or not isinstance(names, list) or names != sorted(set(names)):
        raise ValueError('Release inventory must be a sorted unique file list')
    for name in names:
        p = PurePosixPath(name)
        if not name.isascii() or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or FORBIDDEN.search(name):
            raise ValueError('Forbidden release path: '+name)
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('Missing or unsafe release file: '+name)
        if SECRET.search(path.read_bytes()):
            raise ValueError('Potential credential material in: '+name)
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts}
    if actual != set(names):
        raise ValueError('Unlisted or missing files; review the inventory before packaging: '+', '.join(sorted(actual ^ set(names))))
    if 'SHA256SUMS.txt' not in names or 'tools/release_files.json' not in names:
        raise ValueError('Release must include its inventory and hash manifest')
    return names


def expected_hashes(names):
    return ''.join(sha((ROOT/name).read_bytes())+'  '+name+'\n' for name in names if name != 'SHA256SUMS.txt')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-hashes', action='store_true', help='Refresh hashes after reviewing source changes and the explicit inventory')
    parser.add_argument('--check', action='store_true', help='Check only; do not build archives')
    parser.add_argument('--output', type=Path, help='New or existing output directory outside the source tree')
    args = parser.parse_args()
    names = read_inventory()
    hashes = expected_hashes(names)
    target = ROOT / 'SHA256SUMS.txt'
    if args.refresh_hashes:
        target.write_text(hashes, encoding='utf-8', newline='\n')
    elif target.read_text(encoding='utf-8') != hashes:
        raise ValueError('Release hashes are stale; review the changes before refreshing')
    if args.check:
        print('Checked '+str(len(names))+' release files; no archives written.')
        return
    if args.output is None:
        parser.error('--output is required unless --check is used')
    output = args.output.resolve()
    if output == ROOT or output.is_relative_to(ROOT):
        raise ValueError('Keep release archives outside source')
    tree = ast.parse((ROOT/'scripts/common.py').read_text(encoding='utf-8'))
    version = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in n.targets))
    output.mkdir(parents=True, exist_ok=True)
    products = [('OpenSci-'+version, 'OpenSci-'+version+'/'), ('OpenSci-Study-Plugin-'+version, ''), ('OpenSci-MCP-'+version, '')]
    paths = [output/(name+'.zip') for name, _ in products]
    if any(p.exists() for p in paths) or (output/'SHA256SUMS.txt').exists():
        raise ValueError('Output files already exist; choose a new release directory')
    for (name, prefix), path in zip(products, paths):
        with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for relative in names:
                item = zipfile.ZipInfo(prefix+relative, date_time=(2026, 10, 14, 0, 0, 0))
                item.compress_type = zipfile.ZIP_DEFLATED
                item.external_attr = 0o100644 << 16
                z.writestr(item, (ROOT/relative).read_bytes())
    (output/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in paths), encoding='utf-8')
    print('Created runtime, plugin and MCP archives in '+str(output))


if __name__ == '__main__':
    main()
