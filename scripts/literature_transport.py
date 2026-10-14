"""Fixed-node literature dispatch over the existing SSH resource mapping.

Only validated evidence/job data cross the connection. No Zotero port forwarding,
raw library mirrors, caller-supplied shell commands, or study-head writes.
"""
import argparse
import base64
import io
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from common import FileLock, atomic_write, canonical, digest, parse_json, print_json, read_json, stamp
from hub import transport_command
from literature_contract import fail, identifier
from literature_evidence import EvidenceService
from literature_store import LiteratureStore
from storage_paths import safe_name

MAX_PACKET=64_000_000

def packet(store,job_id):
    job=store.job(job_id)
    if job['status']!='queued' or job['reservation']['state']!='reserved': fail('invalid_state','Only a reserved queued job can be dispatched')
    manifest=EvidenceService(store).load(job['snapshot_id'])
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('job.json',canonical(job)); archive.writestr('manifest.json',canonical(manifest))
        for row in manifest['files']:
            archive.writestr('evidence/'+row['path'],store.path('snapshots/'+job['snapshot_id']+'/'+row['path']).read_bytes())
    raw=stream.getvalue()
    if len(raw)>MAX_PACKET: fail('packet_too_large','Evidence transfer exceeds the packet size limit')
    return raw

def receive(store,raw,node,expected):
    if len(raw)>MAX_PACKET or digest(raw)!=expected: fail('invalid_packet','Packet checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or sum(x.file_size for x in archive.infolist())>MAX_PACKET:
            fail('invalid_packet','Duplicate entries or excessive uncompressed size')
        for name in names: safe_name(name)
        job=parse_json(archive.read('job.json')); manifest=parse_json(archive.read('manifest.json'))
        identifier(job['job_id'])
        if job.get('schema_version')!=1 or job['node_ref']!=node or job['snapshot_id']!=manifest['snapshot_id']:
            fail('generation_conflict','Packet node or snapshot does not match its job')
        expected_names={'job.json','manifest.json'}|{'evidence/'+x['path'] for x in manifest['files']}
        if set(names)!=expected_names: fail('invalid_packet','Unexpected packet files')
        evidence={x['path']:archive.read('evidence/'+x['path']) for x in manifest['files']}
    with FileLock(store.path('jobs/'+job['job_id']+'/.dispatch.lock')):
        existing=store.read('jobs/'+job['job_id']+'/job.json')
        if existing:
            for field in ('job_id','study_id','snapshot_id','attempt_id','generation','node_ref','effective_config','principal'):
                if existing[field]!=job[field]: fail('request_conflict','Existing dispatched task differs; do not replace it')
            EvidenceService(store).load(existing['snapshot_id'])
        else:
            EvidenceService(store).publish(manifest,evidence); store.save_job(job)
        return {'received':True,'job_id':job['job_id'],'generation':job['generation'],'snapshot_id':job['snapshot_id'],'packet_sha256':expected}

def launch(store,job_id,node,resume=False):
    with FileLock(store.path('jobs/'+identifier(job_id)+'/.dispatch.lock')):
        job=store.job(job_id)
        if job['node_ref']!=node: fail('generation_conflict','Wrong executor node')
        marker='jobs/'+job_id+'/launch.json'; old=store.read(marker)
        if old and not resume:
            # A lost SSH response must not launch a second process. A terminated executor
            # is recovered through its original worker state, never by deleting this marker.
            return {'launch':old,'job':job,'reused':True}
        if old and resume:
            if old.get('state')!='launched' or not old.get('pid'):
                fail('outcome_unknown','Prior process launch is unresolved; inspect the node before resuming')
            if os.name=='nt': fail('waiting_user','Windows process recovery needs a verified process identity check')
            try: os.kill(old['pid'],0); alive=True
            except ProcessLookupError: alive=False
            except PermissionError: fail('outcome_unknown','Cannot establish the previous executor process state')
            if alive: return {'launch':old,'job':job,'reused':True,'reason':'Existing process still owns this attempt'}
            if job.get('call_started') and not job.get('call_finished'):
                fail('outcome_unknown','Original model call remains unresolved; no replacement executor was started')
            store.write('jobs/'+job_id+'/launch-history/'+str(old['pid'])+'.json',old)
        before={'job_id':job_id,'generation':job['generation'],'node_ref':node,'state':'launch_intent','utc':stamp()}
        store.write(marker,before)
        directory=store.path('jobs/'+job_id)
        options={'start_new_session':True} if os.name!='nt' else {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW}
        command=[sys.executable,'-B',str(Path(__file__).with_name('literature_jobs.py')),'--workspace',str(store.root),
                 '--job',job_id,'--node',node,'--generation',str(job['generation'])]
        provider=store.root/'config/providers.local.json'
        if job['analysis_kind']=='model': command+=['--providers',str(provider)]
        with (directory/'worker.stdout.log').open('ab') as out,(directory/'worker.stderr.log').open('ab') as err:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err,**options)
        before.update(state='launched',pid=process.pid); store.write(marker,before)
        return {'launch':before,'reused':False}

def remote_call(node,args,body=None,timeout=45):
    if node['transport']!='ssh': fail('not_supported','This transport uses an existing SSH development node')
    script=node['workspace'].rstrip('/')+'/scripts/literature_transport.py'
    command=transport_command(node,[node['python'],'-B',script,'--workspace',node['workspace'],*args])
    try: result=subprocess.run(command,input=body,capture_output=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired): fail('outcome_unknown','SSH outcome unknown; query the same remote job before redispatch')
    if result.returncode:
        fail('remote_unavailable','Remote literature endpoint unavailable; preserve dispatch identity and inspect the node')
    if len(result.stdout)>MAX_PACKET: fail('invalid_result','Remote response exceeds transfer bound')
    return parse_json(result.stdout)

def dispatch(store,job_id,node_ref,node):
    job=store.job(job_id)
    if job['node_ref']!=node_ref: fail('generation_conflict','Job is bound to another node')
    raw=packet(store,job_id)
    ack=remote_call(node,['receive','--node',node_ref,'--expected',digest(raw)],raw)
    if not ack.get('received') or ack.get('snapshot_id')!=job['snapshot_id']: fail('invalid_result','Receiver did not acknowledge this snapshot')
    return remote_call(node,['launch','--node',node_ref,'--job',job_id])

def fetch(store,job_id,node):
    value=remote_call(node,['inspect','--job',job_id])
    remote=value['job']; local=store.job(job_id)
    for field in ('job_id','attempt_id','generation','node_ref','snapshot_id'):
        if local[field]!=remote[field]: fail('generation_conflict','Remote result identity mismatch')
    return value

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--workspace',type=Path,required=True)
    sub=p.add_subparsers(dest='action',required=True)
    receive_p=sub.add_parser('receive'); receive_p.add_argument('--node',required=True); receive_p.add_argument('--expected',required=True)
    launch_p=sub.add_parser('launch'); launch_p.add_argument('--job',required=True); launch_p.add_argument('--node',required=True); launch_p.add_argument('--resume',action='store_true')
    inspect_p=sub.add_parser('inspect'); inspect_p.add_argument('--job',required=True)
    control_p=sub.add_parser('control'); control_p.add_argument('--job',required=True)
    a=p.parse_args(); store=LiteratureStore(a.workspace)
    try:
        if a.action=='receive': result=receive(store,sys.stdin.buffer.read(MAX_PACKET+1),a.node,a.expected)
        elif a.action=='launch': result=launch(store,a.job,a.node,a.resume)
        elif a.action=='control':
            control=parse_json(sys.stdin.buffer.read(64001)); job=store.job(a.job)
            if control.get('job_id')!=a.job or control.get('generation')!=job['generation'] or control.get('attempt_id')!=job['attempt_id']: fail('generation_conflict','Invalid remote control')
            if control.get('action') not in ('pause','resume','cancel'): fail('invalid_request','Unknown control action')
            store.write('jobs/'+a.job+'/control.json',control); result={'delivered':True,'effective':False}
        else:
            job=store.job(a.job); result={'job':job,'result_base64':None}
            if job.get('result'):
                path=store.root/safe_name(job['result']['path']); raw=path.read_bytes()
                if digest(raw)!=job['result']['sha256']: fail('invalid_result','Remote result has changed')
                result['result_base64']=base64.b64encode(raw).decode('ascii')
        print_json(result); return 0
    except (ValueError,OSError,KeyError,zipfile.BadZipFile) as exc:
        print_json({'error':getattr(exc,'code','transport_failed'),'detail':str(exc) if hasattr(exc,'code') else type(exc).__name__}); return 2

if __name__=='__main__': raise SystemExit(main())
