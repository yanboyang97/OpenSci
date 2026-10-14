"""Bounded project heads with immutable previous-version bytes.

The atomic head replacement is the commit point. Snapshot files not reachable
from that head are uncommitted staging, never inferred to be history.
Callers must hold the coordinator and per-project FileLock for every write.
"""
import copy
import getpass
import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from common import atomic_write, canonical, digest, parse_json, require_hash, stamp, valid_id
from storage_paths import plain_path

PROJECT_LIMIT = 4_000_000
LEGACY_LIMIT = 64_000_000
PHASES = ('evidence', 'plan_review', 'implementation', 'awaiting_approval', 'experiment_running', 'analysis', 'archived')


def bounded_read(path, limit):
    path = plain_path(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Only regular files are accepted')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Only regular files are accepted')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Project exceeds read limit; use legacy-large diagnosis if applicable')
    return raw


def validate_record(record, study=None):
    if (not isinstance(record, dict) or type(record.get('schema_version')) is not int
            or record['schema_version'] not in (1, 2, 3, 4) or not valid_id(record.get('study_id'))
            or study is not None and record['study_id'] != study
            or type(record.get('revision')) is not int or record['revision'] < 1
            or record.get('phase') not in PHASES or not isinstance(record.get('runs'), dict)
            or not isinstance(record.get('references'), list) or not isinstance(record.get('history'), list)
            or not isinstance(record.get('goal'), str) or not record['goal'].strip()
            or not (isinstance(record.get('anchor'), dict) or record['schema_version'] == 4 and record.get('anchor') is None)
            or not isinstance(record.get('agent_snapshot'), dict)):
        raise ValueError('Invalid project record; preserve the original and restore verified evidence')
    if record['schema_version'] in (2, 3, 4):
        journal = record.get('journal')
        if (record['history'] or not isinstance(journal, dict)
                or set(journal) != ({'previous_sha256', 'event', 'actor', 'reason', 'legacy_history_incomplete'}
                                    | ({'command'} if record['schema_version'] in (3, 4) else set()))
                or not all(isinstance(journal[k], str) and journal[k].strip() for k in ('event', 'actor', 'reason'))
                or type(journal['legacy_history_incomplete']) is not bool):
            raise ValueError('Invalid project snapshot journal')
        if journal['previous_sha256'] is not None:
            require_hash(journal['previous_sha256'])
        elif record['revision'] != 1:
            raise ValueError('A noninitial project must reference its previous version')
        if record['schema_version'] in (3, 4) and journal['command'] is not None:
            command = journal['command']
            if (not isinstance(command, dict) or set(command) != {'request_id', 'request_sha256', 'principal',
                    'role', 'operation', 'outcome', 'revision', 'study_id'}
                    or type(command['revision']) is not int or command['revision'] != record['revision']
                    or command['study_id'] != record['study_id']
                    or command['role'] not in ('operator', 'agent', 'observer')
                    or command['outcome'] not in ('changed', 'no_effect')
                    or any(not isinstance(command[k], str) or not command[k] or len(command[k]) > 256
                           for k in ('request_id', 'principal', 'operation'))):
                raise ValueError('Invalid committed command receipt')
            require_hash(command['request_sha256'])
    for ref in record['references']:
        if isinstance(ref, dict) and ref.get('kind') == 'literature':
            if (record['schema_version'] not in (3, 4) or set(ref) != {'kind','path','sha256','schema_version','request_id','operation'}
                    or ref['schema_version'] != 1 or not isinstance(ref['path'],str)
                    or ref['path'] != 'coordination/literature/blobs/'+ref['sha256']+'.json'):
                raise ValueError('Invalid versioned literature result reference')
            require_hash(ref['sha256'])
            from literature_contract import OPERATIONS
            if ref['operation'] not in OPERATIONS or not isinstance(ref['request_id'],str):
                raise ValueError('Unsupported literature result operation')
    if record['schema_version'] == 4:
        from study_context import validate_study
        validate_study(record)
    return record


def decode_record(raw, study=None, legacy_large=False):
    if len(raw) > (LEGACY_LIMIT if legacy_large else PROJECT_LIMIT):
        raise ValueError('Project exceeds read limit; use explicit legacy-large diagnosis, never overwrite it')
    record = validate_record(parse_json(raw), study)
    if record['schema_version'] in (2, 3, 4) and len(raw) > PROJECT_LIMIT:
        raise ValueError('Study Record exceeds the shared read/write limit')
    return record


def previous_path(study, checksum):
    if not valid_id(study):
        raise ValueError('Invalid study ID')
    require_hash(checksum)
    return f'coordination/projects/history/{study}/{checksum}.json'


def finalize_record(record, previous, previous_sha256, event, reason, actor=None, command=None):
    """Shared exact serialized-capacity check for preflight and commit; no I/O."""
    record = copy.deepcopy(record)
    record['schema_version'] = max(2, record['schema_version'], previous['schema_version'] if previous else 0)
    record['history'] = []
    record['journal'] = {
        'previous_sha256': previous_sha256,
        'event': event, 'actor': actor or getpass.getuser(), 'reason': reason,
        'legacy_history_incomplete': bool(previous and (previous['schema_version'] == 1 or previous['journal']['legacy_history_incomplete'])),
    }
    if record['schema_version'] in (3, 4):
        record['journal']['command'] = copy.deepcopy(command)
    elif command is not None:
        raise ValueError('Operation receipts require a study prepared for the Operation Service')
    record['updated_utc'] = datetime.now(timezone.utc).isoformat(timespec='microseconds')
    validate_record(record, record['study_id'])
    raw = canonical(record)
    if len(raw) > PROJECT_LIMIT:
        raise ValueError('Project write exceeds 4000000 bytes capacity; previous head unchanged. Split large notes/evidence into referenced files.')
    return record, raw


def publish_snapshot(stage, path):
    # Windows rename refuses an existing target. POSIX rename replaces it, so
    # use an exclusive hard link there. Both publish only the complete file.
    if os.name == 'nt':
        os.rename(stage, path)
    else:
        os.link(stage, path)


class ProjectStore:
    def __init__(self, root):
        self.root = plain_path(root)

    def path(self, study):
        if not valid_id(study):
            raise ValueError('Invalid study ID')
        return plain_path(self.root/'coordination/projects'/f'{study}.json')

    def read(self, study, legacy_large=False):
        raw = bounded_read(self.path(study), LEGACY_LIMIT if legacy_large else PROJECT_LIMIT)
        return decode_record(raw, study, legacy_large), raw

    def snapshot(self, study, raw):
        checksum = digest(raw)
        path = plain_path(self.root/previous_path(study, checksum))
        if path.exists():
            if bounded_read(path, LEGACY_LIMIT) != raw:
                raise ValueError('Immutable history snapshot changed')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Never expose a partial file under the final immutable checksum name.
            # Platform-specific exclusive publication leaves the old head intact
            # when the filesystem cannot support the operation.
            stage = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.snapshot-', suffix='.tmp', delete=False) as stream:
                    stage = Path(stream.name)
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                if bounded_read(stage, LEGACY_LIMIT) != raw:
                    raise ValueError('Staged history snapshot verification failed')
                try:
                    publish_snapshot(stage, path)
                except FileExistsError:
                    if bounded_read(path, LEGACY_LIMIT) != raw:
                        raise ValueError('Immutable history snapshot changed')
            finally:
                if stage is not None:
                    stage.unlink(missing_ok=True)
        if digest(bounded_read(path, LEGACY_LIMIT)) != checksum:
            raise ValueError('History snapshot verification failed')
        return checksum

    def commit(self, previous_raw, record, event, reason, actor=None, command=None):
        record = copy.deepcopy(record)
        study = record['study_id']
        path = self.path(study)
        if previous_raw is None:
            if path.exists() or record['revision'] != 1:
                raise ValueError('Project already exists or initial revision invalid')
            previous = None
        else:
            if not path.exists() or bounded_read(path, LEGACY_LIMIT) != previous_raw:
                raise ValueError('Project changed before commit')
            previous = decode_record(previous_raw, study, legacy_large=True)
            if record['revision'] != previous['revision'] + 1:
                raise ValueError('Revision must increase exactly once')
        record, raw = finalize_record(record, previous, digest(previous_raw) if previous_raw is not None else None,
                                      event, reason, actor, command)
        # Validate everything and the byte limit BEFORE creating any snapshot.
        if previous_raw is not None:
            self.snapshot(study, previous_raw)
        atomic_write(path, raw)
        return record

    def versions(self, study, legacy_large=False):
        record, raw = self.read(study, legacy_large)
        seen = set()
        while True:
            checksum = digest(raw)
            if checksum in seen:
                raise ValueError('Cycle in history chain')
            seen.add(checksum)
            yield record, raw
            if record['schema_version'] == 1 or record['journal']['previous_sha256'] is None:
                break
            key = record['journal']['previous_sha256']
            old = bounded_read(self.root/previous_path(study, key), LEGACY_LIMIT)
            if digest(old) != key:
                raise ValueError('History snapshot checksum mismatch')
            previous = decode_record(old, study, legacy_large=True)
            if previous['revision'] != record['revision'] - 1:
                raise ValueError('Nonconsecutive history revisions')
            record, raw = previous, old

    def version(self, study, revision):
        for record, raw in self.versions(study):
            if record['revision'] == revision:
                return record, raw
        raise ValueError('Requested revision is not in the committed history')

    def history(self, study, limit=20, before_revision=None):
        if not 1 <= limit <= 100:
            raise ValueError('History page size must be 1..100')
        items = []
        for record, raw in self.versions(study):
            if before_revision is not None and record['revision'] >= before_revision:
                continue
            items.append({'revision': record['revision'], 'sha256': digest(raw), 'phase': record['phase'],
                          'checkpoint_note': record.get('checkpoint_note'), 'updated_utc': record['updated_utc'],
                          'journal': record.get('journal'), 'legacy_history_unrecoverable': record['schema_version'] == 1})
            if len(items) == limit:
                break
        return {'study_id': study, 'versions': items, 'next_before_revision': items[-1]['revision'] if items else None,
                'scope': 'Committed study history only; missing progress notes cannot be reconstructed'}

    def check(self, study, legacy_large=False):
        count = sum(1 for _ in self.versions(study, legacy_large))
        record, raw = self.read(study, legacy_large)
        return {'committed_versions_verified': count, 'bytes': len(raw), 'limit': PROJECT_LIMIT,
                'near_capacity': len(raw) >= int(PROJECT_LIMIT * .8), 'schema_version': record['schema_version'],
                'legacy_history_incomplete': record['schema_version'] == 1 or record['journal']['legacy_history_incomplete']}
