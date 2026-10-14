"""Offline, checksummed source/state backup and restore to a NEW workspace.

No network, credentials, external datasets, software or license migration.
Stop all writers first. The Hub lock only coordinates local Hub commands.
"""
import argparse
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
import zipfile

from common import FileLock, canonical, digest, file_hash, parse_json, print_json, require_hash, stamp
from storage_paths import plain_path, safe_name

STATE_DIRS = ('coordination/projects', 'coordination/imports', 'coordination/requests',
              'coordination/reviews', 'coordination/approvals', 'coordination/literature', 'manuscript', 'environments')
LOCAL_FILES = ('config/hub.local.json', 'config/device.local.json', 'config/providers.local.json',
               'config/mcp.policy.local.json', 'config/mcp.chat.local.json', 'config/mcp.local.json', 'config/observer.local.json',
               'config/literature.local.json', 'coordination/resources.json')
MAX_BYTES = 4 * 1024**3
MAX_FILES = 100000
EXCLUSIONS = ['external datasets/models/results (including Git LFS objects)',
              'SSH keys, credentials, license files, OS accounts and permissions',
              'software installations, PDKs, virtual environments, caches',
              'external Zotero database, original attachments and Zotero credentials',
              'Git reflog, unreachable objects, hooks and repository configuration']


def git(root, *args):
    # Scoped to this child only; never write user/system Git configuration.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', '-c', 'core.hooksPath='+os.devnull, '-C', str(root), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=300)
    if result.returncode:
        raise ValueError('Git operation failed: '+args[0]+'; inspect the local repository')
    return result.stdout


def inventory(root, state_only=False):
    tracked = [] if state_only else git(root, 'ls-files', '-z').decode('utf-8').split('\0')
    names = {n for n in tracked if n}
    for folder in STATE_DIRS:
        directory = plain_path(root/folder)
        if directory.exists():
            for parent, dirs, files in os.walk(directory, followlinks=False):
                for name in dirs + files:
                    plain_path(Path(parent)/name)
                if Path(parent)==root/'coordination/literature':
                    dirs[:]=[name for name in dirs if name!='cache']
                for name in files:
                    if not name.endswith('.lock'):
                        names.add((Path(parent)/name).relative_to(root).as_posix())
    names.update(n for n in LOCAL_FILES if (root/n).exists())
    entries = {}
    for name in sorted(names):
        safe_name(name)
        path = plain_path(root/name)
        if '.git' in [p.casefold() for p in path.relative_to(root).parts] or not path.is_file():
            raise ValueError('Unsupported tracked path')
        entries[name] = {'sha256': file_hash(path), 'size': path.stat().st_size}
    if len(entries) > MAX_FILES or sum(v['size'] for v in entries.values()) > MAX_BYTES:
        raise ValueError('Backup size/count limit exceeded; use separate data storage')
    return entries


def check_projects(read, entries):
    from project_store import decode_record, previous_path
    for name in entries:
        if PurePosixPath(name).parent != PurePosixPath('coordination/projects') or not name.endswith('.json'):
            continue
        study = Path(name).stem
        current = name
        seen = set()
        next_revision = None
        while True:
            if current in seen or current not in entries:
                raise ValueError('Missing or cyclic project history')
            seen.add(current)
            record = decode_record(read(current), study, legacy_large=True)
            if next_revision is not None and record['revision'] != next_revision:
                raise ValueError('Nonconsecutive project history')
            refs = list(record['references'])
            for run in record['runs'].values():
                refs.append({'path': run['task_path'], 'sha256': run['task_sha256']})
                if run.get('status_sha256'):
                    refs.append({'path': run['status_path'], 'sha256': run['status_sha256']})
            for ref in refs:
                key = safe_name(ref['path'])
                require_hash(ref['sha256'])
                if entries.get(key, {}).get('sha256') != ref['sha256']:
                    raise ValueError('Missing or changed project evidence: '+key)
            if record['schema_version'] == 1 or record['journal']['previous_sha256'] is None:
                break
            checksum = record['journal']['previous_sha256']
            current = previous_path(study, checksum)
            if entries.get(current, {}).get('sha256') != checksum:
                raise ValueError('Missing or changed project history snapshot')
            next_revision = record['revision'] - 1
    # Referenced literature snapshots and result bytes are part of the recovery
    # boundary, independently of the small reference blob in a project head.
    from literature_contract import validate_snapshot
    for name in entries:
        if name.startswith('coordination/literature/snapshots/') and name.endswith('/manifest.json'):
            manifest=parse_json(read(name)); validate_snapshot(manifest)
            parent=PurePosixPath(name).parent
            for row in manifest['files']:
                target=str(parent/safe_name(row['path']))
                if entries.get(target,{}).get('sha256')!=row['sha256']: raise ValueError('Missing literature snapshot evidence: '+target)
        if name.startswith('coordination/literature/jobs/') and name.endswith('/job.json'):
            result=parse_json(read(name)).get('result')
            if result and entries.get(safe_name(result['path']),{}).get('sha256')!=result['sha256']:
                raise ValueError('Missing literature job result')


def backup(workspace, output, quiesced=False):
    root, output = plain_path(workspace), plain_path(output)
    if not quiesced:
        raise ValueError('Stop all project writers first and pass --quiesced')
    if not root.is_dir() or output.exists() or output.is_relative_to(root) or not output.parent.is_dir():
        raise ValueError('Use a new archive path outside the workspace in an existing directory')
    if Path(git(root, 'rev-parse', '--show-toplevel').decode('utf-8').strip()).resolve() != root.resolve():
        raise ValueError('Workspace must be the Git repository top-level directory')
    with FileLock(root/'coordination/projects/.hub.lock'):
        if git(root, 'status', '--porcelain').strip():
            raise ValueError('Commit/reconcile source changes before backup')
        modes = git(root, 'ls-files', '--stage').decode('utf-8').splitlines()
        if any(line.startswith(('120000 ', '160000 ')) for line in modes):
            raise ValueError('Symlinks and submodules require a separate migration workflow')
        entries = inventory(root)
        check_projects(lambda n: (root/n).read_bytes(), entries)
        head = git(root, 'rev-parse', 'HEAD').decode().strip()
        refs = git(root, 'for-each-ref', '--format=%(objectname) %(refname)').decode().splitlines()
        object_format = git(root, 'rev-parse', '--show-object-format').decode().strip()
        with tempfile.TemporaryDirectory(prefix='opensci-backup-', dir=output.parent) as temp:
            stage = Path(temp)
            bundle = stage/'git-history.bundle'
            git(root, 'bundle', 'create', str(bundle), '--all', 'HEAD')
            payload = {'workspace/'+n: v for n, v in entries.items()}
            payload['git-history.bundle'] = {'sha256': file_hash(bundle), 'size': bundle.stat().st_size}
            if sum(v['size'] for v in payload.values()) > MAX_BYTES:
                raise ValueError('Backup total exceeds 4 GiB limit')
            manifest = {'schema_version': 1, 'created_utc': stamp(), 'git_head': head, 'git_object_format': object_format,
                        'git_refs': refs, 'files': payload, 'excluded': EXCLUSIONS,
                        'writer_stopped_by_operator': True, 'credential_collection': 'not_performed',
                        'note': 'Review tracked history/local JSON for secrets before archiving. No encryption.'}
            archive = stage/'backup.zip'
            with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr('manifest.json', canonical(manifest))
                z.write(bundle, 'git-history.bundle')
                for name in entries:
                    z.write(root/name, 'workspace/'+name)
            if inventory(root) != entries or git(root, 'rev-parse', 'HEAD').decode().strip() != head or git(root, 'for-each-ref', '--format=%(objectname) %(refname)').decode().splitlines() != refs or git(root, 'status', '--porcelain').strip():
                raise ValueError('Workspace changed during backup; stop writers and retry')
            expected = file_hash(archive)
            verify(archive, expected)
            # Exclusive destination: an archive created concurrently is never overwritten.
            with output.open('xb') as target, archive.open('rb') as source:
                import shutil
                shutil.copyfileobj(source, target)
    return {'archive': str(output), 'sha256': expected, 'files': len(payload),
            'git_head': head, 'excluded': EXCLUSIONS, 'complete_project_migration': False}


def backup_state(coordinator_root, output, quiesced=False):
    """Back up an independent record directory without inventing Git provenance."""
    root, output = plain_path(coordinator_root), plain_path(output)
    if not quiesced:
        raise ValueError('Stop all record writers first and pass --quiesced')
    if not root.is_dir() or output.exists() or output.is_relative_to(root) or not output.parent.is_dir():
        raise ValueError('Use a new archive outside the coordinator in an existing directory')
    with FileLock(root/'coordination/projects/.hub.lock'):
        entries = inventory(root, state_only=True)
        check_projects(lambda n: (root/n).read_bytes(), entries)
        payload = {'workspace/'+n: v for n, v in entries.items()}
        manifest = {'schema_version': 2, 'record_type': 'opensci_coordinator_backup',
            'created_utc': stamp(), 'git_head': None, 'files': payload,
            'excluded': EXCLUSIONS + ['OpenSci runtime installation and external research workspaces'],
            'writer_stopped_by_operator': True, 'credential_collection': 'not_performed'}
        with tempfile.TemporaryDirectory(prefix='opensci-state-backup-', dir=output.parent) as temp:
            archive = Path(temp)/'backup.zip'
            with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr('manifest.json', canonical(manifest))
                for name in entries: z.write(root/name, 'workspace/'+name)
            if inventory(root, state_only=True) != entries:
                raise ValueError('Records changed during backup; stop writers and retry')
            expected = file_hash(archive)
            verify(archive, expected)
            with output.open('xb') as target, archive.open('rb') as source:
                import shutil
                shutil.copyfileobj(source, target)
    return {'archive': str(output), 'sha256': expected, 'files': len(payload), 'git_head': None,
            'scope': 'coordinator_state', 'excluded': manifest['excluded'], 'complete_project_migration': False}


@contextmanager
def open_verified(archive, expected):
    require_hash(expected)
    archive = plain_path(archive)
    with archive.open('rb') as handle:
        h = hashlib.sha256()
        for block in iter(lambda: handle.read(1024*1024), b''):
            h.update(block)
        if h.hexdigest() != expected:
            raise ValueError('Archive SHA-256 mismatch')
        handle.seek(0)
        with zipfile.ZipFile(handle) as z:
            yield z


def validate_zip(z):
    infos = z.infolist()
    if len(infos) > MAX_FILES+2 or sum(i.file_size for i in infos) > MAX_BYTES+4000000:
        raise ValueError('Archive size/count limit exceeded')
    names, folded = set(), set()
    for info in infos:
        name = safe_name(info.filename)
        if name in names or name.casefold() in folded or info.is_dir() or info.flag_bits & 1:
            raise ValueError('Duplicate, encrypted or directory archive entry')
        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
            raise ValueError('Archive entry must be a regular file')
        names.add(name); folded.add(name.casefold())
    if 'manifest.json' not in names or z.getinfo('manifest.json').file_size > 4000000:
        raise ValueError('Missing/oversized backup manifest')
    manifest = parse_json(z.read('manifest.json'))
    state_only = manifest.get('schema_version') == 2 and manifest.get('record_type') == 'opensci_coordinator_backup'
    if (manifest.get('schema_version') != 1 and not state_only) or not isinstance(manifest.get('files'), dict):
        raise ValueError('Invalid backup manifest')
    entries = manifest['files']
    if set(entries) | {'manifest.json'} != names or (('git-history.bundle' in entries) == state_only):
        raise ValueError('Archive has missing/unlisted files')
    if state_only and manifest.get('git_head') is not None:
        raise ValueError('A coordinator-only archive cannot claim a research commit')
    if not state_only and not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', manifest.get('git_head', '')):
        raise ValueError('Invalid source commit')
    if not state_only and (manifest.get('git_object_format') not in ('sha1', 'sha256') or len(manifest['git_head']) != {'sha1': 40, 'sha256': 64}[manifest['git_object_format']]):
        raise ValueError('Invalid Git object format')
    for name, entry in entries.items():
        if name != 'git-history.bundle' and (not name.startswith('workspace/') or '.git' in [p.casefold() for p in name.split('/')]):
            raise ValueError('Unsupported backup payload')
        require_hash(entry['sha256'])
        if type(entry['size']) is not int or entry['size'] != z.getinfo(name).file_size:
            raise ValueError('Payload size mismatch')
        h = hashlib.sha256()
        with z.open(name) as source:
            for block in iter(lambda: source.read(1024*1024), b''):
                h.update(block)
        if h.hexdigest() != entry['sha256']:
            raise ValueError('Payload checksum mismatch: '+name)
    state = {n[len('workspace/'):]: v for n, v in entries.items() if n.startswith('workspace/')}
    check_projects(lambda n: z.read('workspace/'+n), state)
    return manifest


def verify(archive, expected):
    with open_verified(archive, expected) as z:
        manifest = validate_zip(z)
    return {'verified': True, 'archive': str(archive), 'sha256': expected,
            'files': len(manifest['files']), 'git_head': manifest['git_head'],
            'excluded': manifest.get('excluded', EXCLUSIONS), 'scientific_reproducibility': 'not_tested'}


def restore(archive, expected, destination):
    destination = plain_path(destination)
    if destination.exists() or not destination.parent.is_dir():
        raise ValueError('Restore requires a NEW destination in an existing directory')
    # Keep the verified archive handle open through extraction (no path reopen race).
    with open_verified(archive, expected) as z:
        manifest = validate_zip(z)
        with tempfile.TemporaryDirectory(prefix='opensci-restore-', dir=destination.parent) as temp:
            stage = Path(temp)
            for name in manifest['files']:
                path = stage/name
                path.parent.mkdir(parents=True, exist_ok=True)
                with z.open(name) as source, path.open('xb') as target:
                    import shutil
                    shutil.copyfileobj(source, target)
            root = stage/'workspace'
            if manifest['schema_version'] == 1:
                git(root, 'init', '--object-format='+manifest['git_object_format'])
                git(root, 'config', '--local', 'core.autocrlf', 'false')
                git(root, 'bundle', 'verify', str(stage/'git-history.bundle'))
                git(root, 'fetch', '--update-head-ok', str(stage/'git-history.bundle'), '+refs/*:refs/*', 'HEAD')
                if git(root, 'for-each-ref', '--format=%(objectname) %(refname)').decode().splitlines() != manifest['git_refs']:
                    raise ValueError('Restored Git refs differ from the manifest')
                git(root, 'update-ref', '--no-deref', 'HEAD', manifest['git_head'])
                git(root, 'reset', '--mixed', manifest['git_head'])
                for entry in git(root, 'ls-files', '--stage', '-z').decode('utf-8').split('\0'):
                    if entry:
                        meta, name = entry.split('\t', 1)
                        mode = meta.split()[0]
                        if mode not in ('100644', '100755'):
                            raise ValueError('Unsupported Git mode in restored history')
                        if os.name == 'posix' and mode == '100755':
                            (root/name).chmod((root/name).stat().st_mode | 0o111)
                if git(root, 'status', '--porcelain').strip():
                    raise ValueError('Restored source differs from Git; preserve original archive for reconciliation')
            # Git reset changes only the index. Preserve project/approval bytes exactly.
            for name, entry in manifest['files'].items():
                if file_hash(stage/name) != entry['sha256']:
                    raise ValueError('Restore changed archived bytes')
            # Exclusive reservation avoids replacing even an empty concurrent directory on POSIX.
            # The resulting workspace lives INSIDE the new recovery directory.
            destination.mkdir(mode=0o700)
            root.rename(destination/'workspace')
    return {'restored': True, 'workspace': str(destination/'workspace'), 'git_head': manifest['git_head'],
            'writable_coordinator_activated': False, 'external_resources_restored': False,
            'next': 'Keep old writer stopped. Reconfigure reviewed origin and device paths; verify resources, accounts, licenses and existing run IDs before activation.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    b = sub.add_parser('backup')
    b.add_argument('--workspace', type=Path, required=True)
    b.add_argument('--output', type=Path, required=True)
    b.add_argument('--quiesced', action='store_true')
    b.add_argument('--state-only', action='store_true', help='Back up an independent coordinator without research Git/source; keep runtime and external folders separately')
    for command in ('verify', 'restore'):
        s = sub.add_parser(command)
        s.add_argument('--archive', type=Path, required=True)
        s.add_argument('--expected-sha256', required=True)
        if command == 'restore': s.add_argument('--destination', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.command == 'backup': result = (backup_state if args.state_only else backup)(args.workspace, args.output, args.quiesced)
        elif args.command == 'verify': result = verify(args.archive, args.expected_sha256)
        else: result = restore(args.archive, args.expected_sha256, args.destination)
        print_json(result)
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        print_json({'blocked': True, 'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__, 'submitted_experiments': 0})
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
