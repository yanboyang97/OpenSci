"""Verify the delivered bytes, not publisher identity. Stdlib; no writes/network."""
import hashlib
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--installed", action="store_true", help="Verify listed runtime bytes; permit and report additional local deployment files")
args = parser.parse_args()
from pathlib import Path, PurePosixPath

root=Path(__file__).resolve().parent
seen=set()
for line in (root/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    expected, relative=line.split('  ',1)
    parts=PurePosixPath(relative)
    if parts.is_absolute() or '..' in parts.parts or '\\' in relative or ':' in relative or relative in seen:
        raise SystemExit('Invalid manifest path')
    seen.add(relative)
    path=root.joinpath(*parts.parts)
    if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
        raise SystemExit('Missing or unsafe file: '+relative)
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    if h.hexdigest()!=expected:
        raise SystemExit('CHECKSUM MISMATCH: '+relative)
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
extra=actual-seen-{'SHA256SUMS.txt'}
if extra and not args.installed:
    raise SystemExit('Unlisted files found (verify before local setup): '+', '.join(sorted(extra)))
print(('Verified listed runtime files; '+str(len(extra))+' additional local files are outside this manifest. ' if args.installed else 'Verified exact delivery file set. ')+str(len(seen))+' listed hashes checked; not publisher identity.')
