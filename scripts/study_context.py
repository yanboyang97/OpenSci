"""Versioned structured progress and deterministic bounded study context.

No model calls, transcript polling, work dispatch or external file dereferencing.
"""
import copy
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from common import canonical, digest, require_hash
from project_binding import key, text, validate_binding

def progress_text(value, limit):
    return isinstance(value, str) and bool(value.strip()) and len(value.encode('utf-8')) <= limit and not any(ord(c) < 32 and c not in '\n\r\t' for c in value)


PROGRESS_FIELDS = ('summary', 'decisions', 'hypotheses', 'evidence_refs', 'open_questions', 'next_steps')
BRIEF_LIMIT = 8192
UNKNOWN_ENTRY = {'project_type': 'unknown', 'mode': 'unknown', 'host_id': 'unknown', 'conversation_ref': None}


def validate_entry(entry):
    if (not isinstance(entry, dict) or set(entry) != set(UNKNOWN_ENTRY)
            or entry['project_type'] not in ('unknown', 'chatgpt_project', 'local_folder', 'remote_folder')
            or entry['mode'] not in ('unknown', 'chat', 'work') or not text(entry['host_id'])
            or entry['conversation_ref'] is not None and not text(entry['conversation_ref'], 1024)):
        raise ValueError('Invalid trusted source entry')
    return entry


def validate_progress(value):
    if not isinstance(value, dict) or set(value) != set(PROGRESS_FIELDS) or not progress_text(value['summary'], 16000):
        raise ValueError('Progress needs summary, decisions, hypotheses, evidence_refs, open_questions and next_steps')
    for field in PROGRESS_FIELDS[1:]:
        if not isinstance(value[field], list) or len(value[field]) > 64 or any(not progress_text(v, 4000) for v in value[field]):
            raise ValueError('Progress lists require at most 64 bounded text items; evidence references are not fetched')
    if len(canonical(value)) > 48000:
        raise ValueError('Structured progress exceeds 48000 UTF-8 bytes')
    return value


def validate_workspace(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {'primary', 'additional'} or not isinstance(value['additional'], list) or len(value['additional']) > 32:
        raise ValueError('Research workspace needs primary and bounded additional folders')
    for folder in [value['primary'], *value['additional']]:
        if (not isinstance(folder, dict) or set(folder) != {'host_id', 'path'}
                or not text(folder['host_id']) or not text(folder['path'], 4096)
                or not (PurePosixPath(folder['path']).is_absolute() or PureWindowsPath(folder['path']).is_absolute())):
            raise ValueError('Research folders require an explicit host and absolute path')
    return value


def extend_record(record, workspace):
    validate_workspace(workspace)
    record.update(schema_version=4, research_workspace=copy.deepcopy(workspace), project_bindings=[], progress=None)
    return record


def validate_study(record):
    validate_workspace(record.get('research_workspace'))
    if not {'research_workspace', 'project_bindings', 'progress'} <= set(record):
        raise ValueError('Missing study integration fields')
    links = record['project_bindings']
    if not isinstance(links, list) or len(links) > 100:
        raise ValueError('Invalid study links')
    keys = [key(validate_binding(b)['identity']) for b in links]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate study links')
    anchor = record['anchor']
    if anchor is not None:
        if (not isinstance(anchor, dict) or set(anchor) != {'commit', 'origin_sha256'}
                or not isinstance(anchor['commit'], str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', anchor['commit'])
                or record['research_workspace'] is None):
            raise ValueError('Invalid research source provenance')
        if anchor['origin_sha256'] is not None:
            require_hash(anchor['origin_sha256'])
    progress = record['progress']
    if progress is not None:
        if not isinstance(progress, dict) or set(progress) != {'content', 'source_entry'}:
            raise ValueError('Invalid saved progress')
        validate_progress(progress['content']); validate_entry(progress['source_entry'])
    return record


def source_path(record, legacy_root):
    if record['schema_version'] < 4:
        return legacy_root
    workspace = record['research_workspace']
    if workspace is None or record['anchor'] is None:
        raise ValueError('Source verification unavailable: attach a reviewed Git research workspace before a checkpoint or experiment')
    if workspace['additional']:
        raise ValueError('Multiple-folder experiment provenance is not implemented; register a single reviewed repository')
    if workspace['primary']['host_id'] != 'local':
        raise ValueError('Research source is on another host; verify it on its declared host before source-dependent work')
    from storage_paths import plain_path
    return plain_path(workspace['primary']['path'])


def brief(record, raw):
    progress = record.get('progress')
    result = {'schema_version': 1, 'record_type': 'opensci_study_brief', 'study_id': record['study_id'],
        'revision': record['revision'], 'record_sha256': digest(raw), 'updated_utc': record['updated_utc'],
        'status': 'saved_snapshot', 'goal': record['goal'], 'phase': record['phase'],
        'progress': copy.deepcopy(progress), 'checkpoint_note': record.get('checkpoint_note'),
        'evidence_refs': copy.deepcopy(record['references']), 'has_more': False, 'detail_refs': [],
        'source_verification': 'available_to_check' if record['anchor'] is not None else 'unavailable',
        'limitations': ['Saved state is not live file access or experiment status.',
                       'Hypotheses and recorded decisions are not verified scientific conclusions.',
                       'Source entry fields may be unknown; no billing or model usage is inferred.'],
        'submitted_experiments': 0, 'extra_model_calls': 0}
    # Remove whole fields at deterministic boundaries; never truncate JSON or
    # omit the fact that detail was removed. Revision pins every detail read.
    for field in ('evidence_refs', 'checkpoint_note', 'progress', 'goal'):
        if len(canonical(result)) <= BRIEF_LIMIT:
            break
        result[field] = None
        result['has_more'] = True
        result['detail_refs'].append({'field': field, 'revision': record['revision'], 'offset': 0})
    if len(canonical(result)) > BRIEF_LIMIT:
        raise ValueError('Study brief cannot fit the bounded context contract')
    return result


def detail(store, study, revision, field, offset=0):
    if field not in ('goal', 'progress', 'checkpoint_note', 'evidence_refs') or type(revision) is not int or revision < 1 or type(offset) is not int or offset < 0:
        raise ValueError('Invalid detail field, revision or offset')
    record, raw = store.version(study, revision)
    value = record.get('references' if field == 'evidence_refs' else field)
    # A JSON text page is explicitly a fragment, never presented as a full field.
    encoded = canonical(value).decode('utf-8')
    if offset > len(encoded):
        raise ValueError('Detail offset outside the selected field')
    page = encoded[offset:offset+1000]
    return {'study_id': study, 'revision': revision, 'record_sha256': digest(raw), 'field': field,
            'encoding': 'JSON text fragment; concatenate pages before parsing', 'offset': offset,
            'text': page, 'next_offset': offset+len(page) if offset+len(page) < len(encoded) else None,
            'has_more': offset+len(page) < len(encoded), 'external_files_read': False}
