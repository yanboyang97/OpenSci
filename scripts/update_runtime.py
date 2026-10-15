"""Opt-in runtime updates and private full-folder backups. Python standard library only."""
import argparse
import ast
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
import zipfile

REPOSITORY = 'https://api.github.com/repos/yanboyang97/OpenSci'
MAX_FILES = 100000
MAX_BYTES = 20 * 1024**3
FORBIDDEN = re.compile(r'(?i)(?:^|/)(?:secrets|data|runs|backups|archives|connection|connections|\.git|\.venv|__pycache__)(?:/|$)|\.local\.|\.(?:dpapi|key|pem|pfx|p12|log|pid|db|sqlite|sqlite3)$|(?:^|/)\.env(?:\.|$)')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Unsafe relative filename')
    parts = PurePosixPath(name).parts
    if PurePosixPath(name).is_absolute() or name != '/'.join(parts):
        raise ValueError('Unsafe relative filename')
    for part in parts:
        if part in ('.', '..') or part.endswith((' ', '.')) or any(ord(c) < 32 for c in part):
            raise ValueError('Unsafe relative filename')
        if re.fullmatch(r'(?i)(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part):
            raise ValueError('Reserved filename')
    return name


def ordinary(path):
    path = Path(path)
    # Reject links/junctions on every existing ancestor, including the root itself.
    for item in [path] + list(path.parents):
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Links and junctions require a separate reviewed backup/update')
    return path


def private_directory(path):
    path = ordinary(Path(path).absolute())
    path.mkdir(mode=0o700)  # Must be new; never change ACLs on an existing user directory.
    if os.name == 'nt':
        result = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'], capture_output=True, check=True)
        sid = next(csv.reader(io.StringIO(result.stdout.decode(errors='replace').strip())))[1]
        subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r',
                        '*'+sid+':(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return path


def atomic(path, data):
    path = ordinary(Path(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.opensci-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        if path.exists():
            # ReplaceFile preserves the destination's Windows ACL.
            if os.name == 'nt':
                import ctypes
                replace = ctypes.windll.kernel32.ReplaceFileW
                if not replace(str(path), name, None, 0, None, None):
                    raise OSError('Could not replace runtime file; original retained')
            else:
                os.chmod(name, stat.S_IMODE(path.stat().st_mode))
                os.replace(name, path)
        else:
            os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save(path, value):
    atomic(path, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def inventory(root):
    root = ordinary(Path(root).absolute())
    if not root.is_dir():
        raise ValueError('Backup source directory does not exist')
    result = {}
    total = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            ordinary(Path(base)/name)
        for name in files:
            p = Path(base)/name
            relative = safe_name(p.relative_to(root).as_posix())
            if relative == '.opensci-update.lock':
                continue
            if not p.is_file():
                raise ValueError('Non-regular backup input')
            total += p.stat().st_size
            if len(result) >= MAX_FILES or total > MAX_BYTES:
                raise ValueError('Backup exceeds supported size; use a verified external backup')
            result[relative] = {'sha256': file_sha(p), 'size': p.stat().st_size}
    return result


def roots_for(runtime, coordinator, extras):
    roots = {'runtime': str(ordinary(Path(runtime).absolute()))}
    for label, path in [('coordinator', coordinator)] + [('extra-'+str(i+1), p) for i, p in enumerate(extras)]:
        if path:
            value = ordinary(Path(path).absolute())
            if not value.is_dir():
                raise ValueError('Selected backup folder is missing')
            if any(value == Path(r) or value.is_relative_to(Path(r)) for r in roots.values()):
                continue
            if any(Path(r).is_relative_to(value) for r in roots.values()):
                raise ValueError('Choose non-overlapping backup roots')
            roots[label] = str(value)
    return roots


def backup(roots, output):
    output = Path(output).absolute()
    if any(output.is_relative_to(Path(root)) for root in roots.values()):
        raise ValueError('Backup destination must be outside every selected source folder')
    folder = private_directory(output)
    before = {label: inventory(root) for label, root in roots.items()}
    total = sum(item['size'] for files in before.values() for item in files.values())
    if total > MAX_BYTES or sum(map(len, before.values())) > MAX_FILES:
        raise ValueError('Combined backup exceeds the supported limit')
    if shutil.disk_usage(folder).free < total + 64 * 1024**2:
        raise ValueError('Insufficient free space for backup')
    manifest = {'schema_version': 1, 'type': 'opensci-full-folder-backup', 'roots': roots, 'files': before,
                'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'excluded': ['Running processes, OS services/registry, external folders not explicitly selected',
                             'Credential-store portability and filesystem ACLs are not guaranteed']}
    archive = folder/'backup.zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for label, files in before.items():
            # Preserve empty directories too; never follow links.
            z.writestr(label+'/', b'')
            for base, dirs, _ in os.walk(roots[label]):
                for name in dirs:
                    z.writestr(label+'/'+(Path(base)/name).relative_to(roots[label]).as_posix()+'/', b'')
            for name, entry in files.items():
                p = Path(roots[label])/name
                if file_sha(p) != entry['sha256']:
                    raise ValueError('A source changed during backup; stop writers and retry in a new folder')
                z.write(p, label+'/'+name)
        z.writestr('backup-manifest.json', json.dumps(manifest, ensure_ascii=False).encode('utf-8'))
    if before != {label: inventory(root) for label, root in roots.items()}:
        raise ValueError('Source changed during backup; this backup is not accepted')
    digest = file_sha(archive)
    verify_backup(archive, digest)
    save(folder/'receipt.json', {'archive': str(archive), 'sha256': digest, 'roots': roots,
                                 'verified': True, 'encrypted': False})
    return {'archive': str(archive), 'sha256': digest, 'roots': roots, 'verified': True, 'encrypted': False}


def zip_entries(z):
    entries = {}
    folded = set()
    total = 0
    for item in z.infolist():
        name = safe_name(item.filename.rstrip('/'))
        if name.casefold() in folded or stat.S_ISLNK(item.external_attr >> 16):
            raise ValueError('Duplicate, case-colliding or linked ZIP entry')
        folded.add(name.casefold())
        total += item.file_size
        if len(folded) > MAX_FILES or total > MAX_BYTES:
            raise ValueError('ZIP exceeds supported limits')
        entries[name] = item
    return entries


def verify_backup(archive, expected):
    if not re.fullmatch('[0-9a-f]{64}', expected) or file_sha(archive) != expected:
        raise ValueError('Backup checksum does not match the trusted receipt')
    with zipfile.ZipFile(archive) as z:
        entries = zip_entries(z)
        if entries['backup-manifest.json'].file_size > 32 * 1024**2:
            raise ValueError('Oversized backup manifest')
        obj = json.loads(z.read('backup-manifest.json'))
        if obj.get('type') != 'opensci-full-folder-backup' or obj.get('schema_version') != 1:
            raise ValueError('Not an OpenSci full-folder backup')
        expected_files = {'backup-manifest.json'}
        for label, files in obj['files'].items():
            safe_name(label)
            for relative, row in files.items():
                name = safe_name(label+'/'+safe_name(relative))
                expected_files.add(name)
                if entries[name].file_size != row['size']:
                    raise ValueError('Backup size mismatch')
                with z.open(name) as handle:
                    h = hashlib.sha256()
                    for block in iter(lambda: handle.read(1024*1024), b''):
                        h.update(block)
                if h.hexdigest() != row['sha256']:
                    raise ValueError('Backup content mismatch')
        if {n for n, e in entries.items() if not e.is_dir()} != expected_files:
            raise ValueError('Unexpected backup content')
    return obj


def restore_backup(archive, expected, destination):
    verify_backup(archive, expected)
    destination = private_directory(destination)
    with zipfile.ZipFile(archive) as z:
        for name, entry in zip_entries(z).items():
            if name == 'backup-manifest.json':
                continue
            p = destination/name
            if entry.is_dir():
                p.mkdir(parents=True, exist_ok=True)
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                with z.open(entry) as src, p.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
    return {'restored_to': str(destination), 'services_started': False}


def product_name(name):
    safe_name(name)
    if not name.isascii() or FORBIDDEN.search(name):
        raise ValueError('Release contains a protected local-data path')
    if name.startswith('coordination/') and not name.startswith(('coordination/templates/', 'coordination/packets/')) and name != 'coordination/requests/.gitkeep':
        raise ValueError('Release contains Study records')
    if name.startswith('config/') and '.example' not in name:
        raise ValueError('Release contains non-example configuration')
    if name.startswith('manuscript/') and name != 'manuscript/README.md':
        raise ValueError('Release contains a manuscript')
    if name.startswith('tools/claude-launcher/') and name.endswith('.psd1') and '/providers/' not in name and '.example.' not in name:
        raise ValueError('Release contains machine configuration')


def version(raw):
    tree = ast.parse(raw.decode('utf-8'))
    value = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in n.targets))
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError('Only stable numeric versions are supported')
    return value


def hashes(raw):
    result = {}
    folded = set()
    for line in raw.decode('utf-8').splitlines():
        digest, name = line.split('  ', 1)
        product_name(name)
        if name.casefold() in folded or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Invalid runtime manifest')
        folded.add(name.casefold())
        result[name] = digest
    return result


def package_contents(package, expected):
    if not re.fullmatch('[0-9a-f]{64}', expected) or file_sha(package) != expected:
        raise ValueError('Package checksum mismatch')
    with zipfile.ZipFile(package) as z:
        entries = zip_entries(z)
        tops = {name.split('/')[0] for name in entries}
        if len(tops) != 1 or not re.fullmatch(r'OpenSci-\d+\.\d+\.\d+', next(iter(tops))):
            raise ValueError('Select the full OpenSci runtime ZIP, not a plugin/source archive')
        prefix = next(iter(tops))+'/'
        contents = {n[len(prefix):]: z.read(e) for n, e in entries.items() if not e.is_dir()}
    for name in contents:
        product_name(name)
    listed = hashes(contents['SHA256SUMS.txt'])
    if set(contents) != set(listed) | {'SHA256SUMS.txt'}:
        raise ValueError('Package manifest does not cover its exact contents')
    if any(sha(contents[n]) != digest for n, digest in listed.items()):
        raise ValueError('Package file checksum mismatch')
    files = json.loads(contents['tools/release_files.json'])
    if files.get('schema_version') != 1 or set(files['files']) != set(contents) or len(files['files']) != len(contents):
        raise ValueError('Package inventory mismatch')
    ver = version(contents['scripts/common.py'])
    if prefix != 'OpenSci-'+ver+'/':
        raise ValueError('Package version mismatch')
    return contents, ver


def plan(package, expected, runtime, coordinator, work, extras):
    runtime = ordinary(Path(runtime).absolute())
    payload, new_version = package_contents(package, expected)
    old_version = version((runtime/'scripts/common.py').read_bytes())
    if tuple(map(int, new_version.split('.'))) <= tuple(map(int, old_version.split('.'))):
        raise ValueError('Update requires a newer version; use recovery for a failed update')
    old = hashes((runtime/'SHA256SUMS.txt').read_bytes())
    old['SHA256SUMS.txt'] = file_sha(runtime/'SHA256SUMS.txt')
    changes = []
    for name, data in payload.items():
        p = ordinary(runtime/name)
        current = file_sha(p) if p.is_file() else None
        if p.exists() and not p.is_file():
            raise ValueError('File/directory conflict: '+name)
        if current == sha(data):
            continue
        if name in old and current != old[name]:
            raise ValueError('Locally modified or missing software file: '+name)
        if name not in old and p.exists():
            raise ValueError('New software path conflicts with an existing user file: '+name)
        changes.append({'path': name, 'before': current, 'after': sha(data)})
    # Protect all existing managed files, even those not changed by this release.
    for name, digest in old.items():
        if not ordinary(runtime/name).is_file() or file_sha(runtime/name) != digest:
            raise ValueError('Installed software differs from its manifest: '+name)
    roots = roots_for(runtime, coordinator, extras)
    work = Path(work).absolute()
    if any(work.is_relative_to(Path(root)) for root in roots.values()):
        raise ValueError('Update work directory must be outside all backed-up roots')
    private_directory(work)
    stage = work/'payload'
    stage.mkdir()
    for name, data in payload.items():
        atomic(stage/name, data)
    result = {'schema_version': 1, 'runtime': str(runtime), 'from_version': old_version,
              'to_version': new_version, 'package_sha256': expected, 'backup_roots': roots,
              'changes': sorted(changes, key=lambda r: (r['path'] == 'SHA256SUMS.txt', r['path'])),
              'installed_manifest': old['SHA256SUMS.txt'], 'retained_retired_files': sorted(set(old)-set(payload))}
    save(work/'plan.json', result)
    return {'plan': str(work/'plan.json'), 'from_version': old_version, 'to_version': new_version,
            'software_files_to_change': len(changes), 'user_files_to_delete': 0}


@contextlib.contextmanager
def update_lock(runtime):
    path = ordinary(Path(runtime)/'.opensci-update.lock')
    with path.open('a+b') as handle:
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)
    # Retain an inert lock file: unlinking creates a concurrent-open race on POSIX.


def check_rows(runtime, rows, allowed):
    for row in rows:
        product_name(row['path'])
        p = ordinary(Path(runtime)/row['path'])
        actual = file_sha(p) if p.is_file() else None
        if p.exists() and not p.is_file() or actual not in [row[k] for k in allowed]:
            raise ValueError('Concurrent change or recovery conflict: '+row['path'])


def verify_installed(runtime):
    for name, digest in hashes((Path(runtime)/'SHA256SUMS.txt').read_bytes()).items():
        path = ordinary(Path(runtime)/name)
        if not path.is_file() or file_sha(path) != digest:
            raise ValueError('Installed software changed: '+name)


def apply(plan_path):
    plan_path = ordinary(Path(plan_path).absolute())
    obj = json.loads(plan_path.read_text(encoding='utf-8'))
    runtime = ordinary(Path(obj['runtime']))
    work = plan_path.parent
    journal_path = work/'transaction.json'
    if journal_path.exists():
        raise ValueError('Transaction already exists; inspect it and use recover before planning again')
    with update_lock(runtime):
        if file_sha(runtime/'SHA256SUMS.txt') != obj['installed_manifest']:
            raise ValueError('Installation changed since planning')
        verify_installed(runtime)
        check_rows(runtime, obj['changes'], ['before'])
        for row in obj['changes']:
            if file_sha(ordinary(work/'payload'/row['path'])) != row['after']:
                raise ValueError('Staged software changed')
        receipt = backup(obj['backup_roots'], work/'backup')
        transaction = {'schema_version': 1, 'state': 'applying', 'runtime': str(runtime),
                       'backup': receipt, 'changes': obj['changes'], 'completed': []}
        save(journal_path, transaction)
        try:
            for row in obj['changes']:
                check_rows(runtime, [row], ['before'])
                atomic(runtime/row['path'], (work/'payload'/row['path']).read_bytes())
                transaction['completed'].append(row['path'])
                save(journal_path, transaction)
            check_rows(runtime, obj['changes'], ['after'])
            verify_installed(runtime)
            # Every pre-existing user/config/data byte must still match the full backup.
            saved = verify_backup(receipt['archive'], receipt['sha256'])
            changed = {row['path'] for row in obj['changes']}
            for label, root in obj['backup_roots'].items():
                now = inventory(root)
                before = saved['files'][label]
                protected = set(before) - (changed if label == 'runtime' else set())
                if any(now.get(n) != before[n] for n in protected):
                    raise ValueError('Concurrent change to preserved files; inspect before resuming')
            transaction['state'] = 'completed'
            save(journal_path, transaction)
        except BaseException:
            transaction['state'] = 'recovery_required'
            save(journal_path, transaction)
            raise
    return {'updated': True, 'version': obj['to_version'], 'transaction': str(journal_path),
            'backup': receipt, 'services_started': False}


def recover(transaction_path):
    path = ordinary(Path(transaction_path).absolute())
    obj = json.loads(path.read_text(encoding='utf-8'))
    if obj['state'] not in ('applying', 'recovery_required'):
        raise ValueError('Recovery is only for an interrupted update; completed upgrades require a new plan')
    runtime = ordinary(Path(obj['runtime']))
    receipt = obj['backup']
    manifest = verify_backup(receipt['archive'], receipt['sha256'])
    for row in obj['changes']:
        if row['before'] is not None and manifest['files']['runtime'][row['path']]['sha256'] != row['before']:
            raise ValueError('Recovery baseline mismatch')
    with update_lock(runtime):
        check_rows(runtime, obj['changes'], ['before', 'after'])
        with zipfile.ZipFile(receipt['archive']) as z:
            for row in reversed(obj['changes']):
                p = ordinary(runtime/row['path'])
                if row['before'] is None:
                    if p.exists():
                        p.unlink()  # Only unchanged new software introduced by this transaction.
                else:
                    if manifest['files']['runtime'][row['path']]['sha256'] != row['before']:
                        raise ValueError('Recovery baseline mismatch')
                    atomic(p, z.read('runtime/'+row['path']))
        check_rows(runtime, obj['changes'], ['before'])
        obj['state'] = 'recovered'
        save(path, obj)
    return {'recovered': True, 'data_and_configuration_restored': False, 'services_started': False}


def remote(url, limit):
    request = urllib.request.Request(url, headers={'User-Agent': 'OpenSci-Updater', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        from urllib.parse import urlsplit
        host = urlsplit(response.url).hostname or ''
        if host not in ('api.github.com', 'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'):
            raise ValueError('Unexpected download destination')
        data = response.read(limit+1)
    if len(data) > limit:
        raise ValueError('Download exceeds size limit')
    return data


def latest():
    obj = json.loads(remote(REPOSITORY+'/releases/latest', 2*1024**2))
    tag = obj['tag_name']
    if obj.get('draft') or obj.get('prerelease') or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('No supported stable release')
    return obj


def download(output):
    release = latest()
    ver = release['tag_name'][1:]
    wanted = 'OpenSci-'+ver+'.zip'
    assets = {item['name']: item for item in release['assets']}
    prefix = 'https://github.com/yanboyang97/OpenSci/releases/download/v'+ver+'/'
    for name in (wanted, 'SHA256SUMS.txt'):
        if assets[name]['browser_download_url'] != prefix+name:
            raise ValueError('Unexpected release asset URL')
    sums = remote(prefix+'SHA256SUMS.txt', 1024*1024)
    digest = next(line.split('  ', 1)[0] for line in sums.decode().splitlines() if line.endswith('  '+wanted))
    data = remote(prefix+wanted, 128*1024**2)
    if sha(data) != digest:
        raise ValueError('Downloaded package checksum mismatch')
    if assets[wanted].get('digest') not in (None, 'sha256:'+digest):
        raise ValueError('GitHub asset digest mismatch')
    folder = private_directory(output)
    (folder/wanted).write_bytes(data)
    (folder/'SHA256SUMS.txt').write_bytes(sums)
    package_contents(folder/wanted, digest)
    return {'package': str(folder/wanted), 'sha256': digest, 'version': ver,
            'release_url': 'https://github.com/yanboyang97/OpenSci/releases/tag/v'+ver}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    sub.add_parser('check')
    d = sub.add_parser('download'); d.add_argument('--output', required=True)
    for name in ('plan', 'backup'):
        c = sub.add_parser(name)
        c.add_argument('--runtime', required=True); c.add_argument('--coordinator')
        c.add_argument('--extra', action='append', default=[])
        if name == 'plan':
            c.add_argument('--package', required=True); c.add_argument('--sha256', required=True); c.add_argument('--work', required=True)
        else:
            c.add_argument('--output', required=True); c.add_argument('--quiesced', action='store_true', required=True)
    c = sub.add_parser('apply'); c.add_argument('--plan', required=True)
    c.add_argument('--quiesced', action='store_true', required=True)
    c.add_argument('--backup-confirmed', action='store_true', required=True)
    c = sub.add_parser('recover'); c.add_argument('--transaction', required=True)
    c.add_argument('--quiesced', action='store_true', required=True)
    for name in ('verify-backup', 'restore-backup'):
        c = sub.add_parser(name); c.add_argument('--archive', required=True); c.add_argument('--sha256', required=True)
        if name == 'restore-backup': c.add_argument('--destination', required=True)
    a = p.parse_args()
    if a.action == 'check':
        r = latest(); result = {'version': r['tag_name'][1:], 'url': 'https://github.com/yanboyang97/OpenSci/releases/tag/'+r['tag_name']}
    elif a.action == 'download': result = download(a.output)
    elif a.action == 'plan': result = plan(a.package, a.sha256, a.runtime, a.coordinator, a.work, a.extra)
    elif a.action == 'apply': result = apply(a.plan)
    elif a.action == 'recover': result = recover(a.transaction)
    elif a.action == 'backup': result = backup(roots_for(a.runtime, a.coordinator, a.extra), a.output)
    elif a.action == 'verify-backup':
        verify_backup(a.archive, a.sha256); result = {'verified': True}
    else: result = restore_backup(a.archive, a.sha256, a.destination)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Do not echo network bodies, URLs with credentials, config contents or OS exception arguments.
        message = str(exc) if isinstance(exc, ValueError) else 'Operation failed ('+type(exc).__name__+'); retain the backup and transaction record.'
        print(json.dumps({'error': message}), file=sys.stderr)
        sys.exit(1)
