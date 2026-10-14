"""Coordinator-owned literature records and durable cross-system operation intents."""
import copy
from pathlib import Path
from common import FileLock, atomic_write, canonical, digest, parse_json, stamp
from project_store import bounded_read
from storage_paths import plain_path, safe_name
from literature_contract import LiteratureError, fail, identifier

class LiteratureStore:
    def __init__(self, root):
        self.root = plain_path(root)
        self.base = plain_path(self.root/'coordination/literature')

    def path(self, relative):
        return plain_path(self.base/safe_name(relative))

    def read(self, relative, default=None):
        path = self.path(relative)
        return parse_json(bounded_read(path, 32000000)) if path.exists() else copy.deepcopy(default)

    def write(self, relative, value):
        atomic_write(self.path(relative), canonical(value))

    def blob(self, value):
        raw = canonical(value); sha = digest(raw)
        relative = 'blobs/'+sha+'.json'; path = self.path(relative)
        if path.exists():
            if bounded_read(path,32000000) != raw: fail('history_invalid','Immutable literature evidence changed')
        else: atomic_write(path,raw)
        return {'kind':'literature','path':path.relative_to(self.root).as_posix(),'sha256':sha,
                'schema_version':1}

    def operation(self, operation_id, request, context, execute, reconcile=None):
        """Call only under the coordinator lock. Never resend a started external effect."""
        identifier(operation_id)
        relative = 'operations/'+operation_id+'.json'
        fingerprint = digest(canonical(request))
        old = self.read(relative)
        if old:
            if (old['request_sha256'] != fingerprint or old['principal'] != context.principal or old['role'] != context.role):
                fail('request_conflict','Operation ID belongs to different content or caller')
            if old['state'] == 'verified': return copy.deepcopy(old['result'])
            if old['state'] in ('started','outcome_unknown'):
                result = reconcile(old) if reconcile else None
                if result is None:
                    fail('outcome_unknown','Prior write outcome is unknown; reconcile the same operation before retrying')
                old.update(state='verified',result=result,updated_utc=stamp(),reconciled=True)
                self.write(relative,old)
                return result
            if old['state'] == 'rejected': fail(old['error'],'Prior request was rejected; reread and create a reviewed new intent')
        else:
            old = {'schema_version':1,'operation_id':operation_id,'request_sha256':fingerprint,
                   'request':request,'principal':context.principal,'role':context.role,
                   'state':'intent','created_utc':stamp(),'updated_utc':stamp(),'result':None}
            self.write(relative,old)
        old.update(state='started',updated_utc=stamp()); self.write(relative,old)
        try:
            result = execute()
        except BaseException as exc:
            code = getattr(exc,'code','outcome_unknown')
            # A post-write read failure may hide a committed write, so only known precondition
            # rejections are safely terminal. Recovery must never infer failure from missing receipts.
            old.update(state='intent' if code=='authorization_required' else 'rejected' if code in ('forbidden','version_conflict','api_rejected') else 'outcome_unknown',
                       error=code,updated_utc=stamp())
            self.write(relative,old)
            raise
        old.update(state='verified',result=result,updated_utc=stamp())
        self.write(relative,old)
        return result

    def binding(self, study):
        identifier(study)
        return self.read('studies/'+study+'.json', {'schema_version':1,'study_id':study,
            'config_mode':'inherit','pinned_config':None,'collection_refs':[],'item_refs':[],
            'item_links':{},'invalid_collections':[]})

    def save_binding(self, value):
        self.write('studies/'+identifier(value['study_id'])+'.json',value)

    def job(self, job_id):
        job = self.read('jobs/'+identifier(job_id)+'/job.json')
        if job is None: fail('not_found','Literature job not found')
        return job

    def save_job(self, job):
        self.write('jobs/'+identifier(job['job_id'])+'/job.json',job)

    def event(self, job, kind, data):
        sequence = job.get('event_sequence',0)+1
        value = {'schema_version':1,'job_id':job['job_id'],'attempt_id':job['attempt_id'],
                 'generation':job['generation'],'sequence':sequence,'event':kind,'data':data,'utc':stamp()}
        path = 'jobs/'+job['job_id']+'/events/'+str(sequence).zfill(8)+'.json'
        old = self.read(path)
        if old is not None:
            expected={'job_id':job['job_id'],'attempt_id':job['attempt_id'],'generation':job['generation'],
                      'sequence':sequence,'event':kind,'data':data}
            if any(old.get(k)!=v for k,v in expected.items()): fail('outcome_unknown','Reconcile the event journal before advancing')
            value=old  # Same durable event, with its original timestamp.
        self.write(path,value)
        job['event_sequence']=sequence
        job['updated_utc']=value['utc']; self.save_job(job)

def deterministic_key(operation_id, ordinal=0):
    # Zotero's key alphabet excludes ambiguous characters; stable across process restarts.
    alphabet = '23456789ABCDEFGHIJKLMNPQRSTUVWXYZ'
    raw = bytes.fromhex(digest((operation_id+':'+str(ordinal)).encode()))
    return ''.join(alphabet[b % len(alphabet)] for b in raw[:8])
