"""Unified literature commands. Caller policy is never taken from research text."""
import copy
import html
from common import atomic_write, canonical, digest, read_json, stamp
from literature_contract import (AGENT_OPERATIONS, READ_OPERATIONS, bounded_text, default_config,
    effective_config, exact, fail, identifier, integer, item_key, item_ref, no_secrets, validate_config)
from literature_store import LiteratureStore, deterministic_key
from literature_sources import SourceSearch, match_duplicate
from literature_evidence import EvidenceService
from literature_jobs import new_job, request_control
from literature_writing import export_bib, cite_text
from zotero_adapter import ZoteroClient
from storage_paths import plain_path

class LiteratureService:
    def __init__(self,hub,client_factory=None,search_factory=None):
        self.hub=hub; self.store=LiteratureStore(hub.root)
        self.client_factory=client_factory or ZoteroClient; self.search_factory=search_factory or SourceSearch

    def config(self):
        path=plain_path(self.hub.root/'config/literature.local.json')
        return validate_config(read_json(path)[0]) if path.exists() else default_config()

    def client(self,cfg=None):
        cfg=cfg or self.config()
        if not cfg['zotero']['binding_id']: fail('binding_required','Use operator config_update to bind the current personal library')
        client=self.client_factory(cfg['zotero']); client.probe(); return client

    def authorize(self,request,context):
        op=request['operation']; payload=request['arguments']['payload']
        if context.role=='observer': fail('forbidden','Experiment observers cannot execute literature commands')
        if not isinstance(payload,dict): fail('invalid_request','Literature payload must be an object')
        no_secrets(payload)
        if op in READ_OPERATIONS: return
        if context.role=='agent':
            if op not in AGENT_OPERATIONS: fail('forbidden','Operator-only literature operation')
            grant=self.config()['grants'].get(request['study_id'],{})
            if op not in grant.get('operations',[]): fail('forbidden','No protected delegation for this study and literature operation')
            requested_keys=payload.get('item_keys',[])
            if set(requested_keys)-set(grant.get('item_keys',[])): fail('forbidden','Item is outside the delegated scope')
            requested_collections=payload.get('collection_keys',[])
            if set(requested_collections)-set(grant.get('collection_keys',[])): fail('forbidden','Collection is outside the delegated scope')
            if payload.get('change') or payload.get('kind')=='annotation': fail('forbidden','Change previews and annotation writes require operator scope')
            if payload.get('new_collection') or payload.get('annotation'): fail('forbidden','Creating collection structures or annotations requires operator scope')
            if op=='literature.cite' and payload.get('path') not in grant.get('manuscript_paths',[]): fail('forbidden','Manuscript is outside the protected grant')
            if payload.get('snapshot_id'):
                manifest=EvidenceService(self.store).load(payload['snapshot_id'])
                if {x['item_ref']['item_key'] for x in manifest['items']}-set(grant['item_keys']): fail('forbidden','Snapshot evidence exceeds delegated targets')
                if manifest['binding_id']!=self.config()['zotero']['binding_id']: fail('forbidden','Snapshot belongs to another library')

    def read(self,request,context):
        self.authorize(request,context)
        op=request['operation']; p=request['arguments']['payload']; cfg=self.config()
        if op=='literature.capabilities':
            exact(p,())
            try: zotero=self.client_factory(cfg['zotero']).probe()
            except ValueError as exc: zotero={'status':getattr(exc,'code','unavailable'),'reason':str(exc)}
            return {'schema_version':1,'zotero':zotero,'binding_configured':bool(cfg['zotero']['binding_id']),
                'word_native_acceptance':'deployment_validation_required','word_driver':'observed_native_plugin',
                'browsers':{'edge':'not_verified','chrome':'not_verified'},
                'sources':[{'id':s['id'],'adapter':s['adapter'],'configured_capabilities':s['capabilities'],'live_acceptance':'not_verified'} for s in cfg['research']['sources']],
                'models':cfg['models'],'configuration_revision':cfg['revision'],'read_only':True}
        if op=='literature.get':
            exact(p,(),('item_key','kind','request_id','task_id'))
            if 'task_id' in p:
                task=self.store.read('native-word/'+identifier(p['task_id'])+'.json')
                if not task or task['specification']['study_id']!=request['study_id']: fail('not_found','Native task is not in this study')
                return task
            if 'request_id' in p:
                identity='cmd-'+digest(p['request_id'].encode())
                result=self.store.read('commands/'+identity+'.json')
                if result is None: fail('not_found','Literature result not found')
                if result['study_id']!=request['study_id']: fail('forbidden','Result belongs to another study')
                return result.get('result',{'status':result.get('state','intent'),'reason':'Durable command has not completed; recover the original request'})
            if 'item_key' in p: return self.client(cfg).get(p['item_key'],p.get('kind','items'))
            return {'binding':self.store.binding(request['study_id']),'effective_config':effective_config(cfg,self.store.binding(request['study_id']))}
        if op=='literature.search_library':
            exact(p,('query',),('limit','index'))
            bounded_text(p['query'],1000); limit=integer(p.get('limit',20),1,100)
            if p.get('index'):
                evidence=EvidenceService(self.store); rows=evidence.search(p['query'],limit)
                try: states=evidence.freshness(self.client(cfg))
                except ValueError: states={}
                for row in rows: row['freshness']=states.get(row['item_key'],'not_revalidated')
                return {'items':rows,'source':'derived_index','live':False,'note':'Only current rows were revalidated; all others are historical evidence requiring refresh'}
            rows,_=self.client(cfg).list('items',{'q':p['query'],'qmode':'titleCreatorYear','itemType':'-attachment'})
            return {'items':rows[:limit],'total':len(rows),'retrieved_utc':stamp(),'source':'zotero_local','read_only':True}
        if op=='literature.job_status':
            exact(p,('job_id',),('refresh',)); job=self.store.job(p['job_id'])
            if job['study_id']!=request['study_id']: fail('forbidden','Job belongs to another study')
            if p.get('refresh'):
                if not context.allow_remote_checks: fail('remote_check_required','Remote status requires the trusted launch policy')
                from literature_transport import fetch
                node=self.hub.config['nodes'].get(job['node_ref'])
                if not node or not node['enabled'] or node['role']!='agent': fail('forbidden','Invalid executor binding')
                value=fetch(self.store,job['job_id'],node)
                return {'job':value['job'],'formal_result_imported':False,'read_only':True}
            return {'job':job,'control_request':self.store.read('jobs/'+job['job_id']+'/control.json')}
        fail('invalid_request','Unknown read operation')

    def execute(self,request,context):
        self.authorize(request,context)
        operation='cmd-'+digest(request['request_id'].encode())
        relative='commands/'+operation+'.json'
        previous=self.store.read(relative)
        fingerprint=digest(canonical(request))
        if previous:
            if previous['request_sha256']!=fingerprint or previous['principal']!=context.principal or previous['role']!=context.role:
                fail('request_conflict','Literature command conflicts with the durable original request')
            if previous.get('state') == 'complete': return self.store.blob(previous)
        else:
            previous={'schema_version':1,'request_id':request['request_id'],'request_sha256':fingerprint,
                      'study_id':request['study_id'],'principal':context.principal,'role':context.role,
                      'operation':request['operation'],'state':'intent','request':request,'utc':stamp(),
                      'effective_config':effective_config(self.config(),self.store.binding(request['study_id']),request['arguments']['payload'].get('overrides'))}
            self.store.write(relative,previous)
        result=self.dispatch(request,context,operation,previous['effective_config'])
        saved={'schema_version':1,'request_id':request['request_id'],'request_sha256':fingerprint,
               'study_id':request['study_id'],'principal':context.principal,'role':context.role,
               'operation':request['operation'],'state':'complete','result':result,'utc':stamp(),
               'request':request,'effective_config':previous['effective_config']}
        self.store.write(relative,saved)
        return self.store.blob(saved)

    def keys(self,p,binding,client):
        keys=list(p.get('item_keys',[]))
        if not keys:
            for ref in binding['item_refs']:
                if ref['binding_id']!=client.settings['binding_id']: fail('binding_conflict','Study has references to another library binding')
                keys.append(ref['item_key'])
            for ref in binding['collection_refs']:
                if ref['binding_id']!=client.settings['binding_id']: fail('binding_conflict','Collection belongs to another binding')
                try: keys.extend(x['key'] for x in client.collection_items(ref['collection_key']) if x['data'].get('itemType') not in ('attachment','note','annotation'))
                except ValueError as exc:
                    if getattr(exc,'code',None)!='not_found': raise
                    fail('collection_deleted','Associated collection was deleted; repair the link without deleting prior evidence')
        if not keys: fail('scope_required','Select literature items or associate collections')
        if len(keys)>2000: fail('scope_too_large','Use a bounded batch of at most 2000 literature items')
        return list(dict.fromkeys(item_key(k) for k in keys))

    def dispatch(self,request,context,operation,frozen=None):
        p=request['arguments']['payload']; op=request['operation']; study=request['study_id']; cfg=self.config()
        binding=self.store.binding(study)
        if op=='literature.reconcile':
            exact(p,('original_request_id',))
            original_id='cmd-'+digest(p['original_request_id'].encode())
            old=self.store.read('commands/'+original_id+'.json')
            if not old or old['study_id']!=study: fail('not_found','Original operation is not in this study')
            if old['principal']!=context.principal or old['role']!=context.role: fail('forbidden','Recovery requires the original trusted caller')
            if old['operation'] not in ('literature.collect','literature.organize','literature.fetch_fulltext') or not old.get('request'):
                fail('invalid_request','Only a recorded collection, organization or full-text operation can be reconciled')
            self.authorize(old['request'],context)
            return {'original_request_id':p['original_request_id'],'original_operation_id':original_id,
                    'result':self.dispatch(old['request'],context,original_id,old['effective_config']),
                    'history':'Earlier command receipts remain immutable; external intents retain their original IDs'}
        if op=='literature.config_update':
            exact(p,('expected_config_revision','config'))
            candidate=validate_config(copy.deepcopy(p['config']))
            if cfg==candidate:
                return {'configuration_revision':candidate['revision'],'config':candidate,'recovered':True}
            if p['expected_config_revision']!=cfg['revision']: fail('revision_conflict','Literature configuration changed')
            if candidate['revision']!=cfg['revision']+1: fail('invalid_request','Configuration revision must increment once')
            if candidate['accounting']['period_id']!=cfg['accounting']['period_id']:
                ledger=self.store.read('budget/reservations.json',{'reservations':{}})
                if any(x['state']=='reserved' and x.get('analysis_kind')=='model' for x in ledger['reservations'].values()):
                    fail('outcome_unknown','Reconcile outstanding model allocations before changing the accounting period')
            if cfg['zotero']['binding_id'] and candidate['zotero']['binding_id']!=cfg['zotero']['binding_id']:
                fail('rebind_required','Existing library rebind requires explicit migration and reconciliation')
            if candidate['zotero']['binding_id']:
                self.client_factory(candidate['zotero']).probe()
            self.store.blob({'kind':'configuration_before','config':cfg})
            atomic_write(plain_path(self.hub.root/'config/literature.local.json'),canonical(candidate))
            return {'configuration_revision':candidate['revision'],'config':candidate}
        if op=='literature.bind_study':
            exact(p,('config_mode','collection_refs','item_refs'),('item_links','pinned_config'))
            if p['config_mode'] not in ('inherit','pinned'): fail('invalid_request','Unknown configuration mode')
            pinned=copy.deepcopy(cfg) if p['config_mode']=='pinned' else None
            if 'pinned_config' in p:
                if context.role!='operator' or p['config_mode']!='pinned': fail('forbidden','Editing pinned settings requires operator scope and pinned mode')
                pinned=validate_config(copy.deepcopy(p['pinned_config']))
                if pinned['zotero']!=cfg['zotero']: fail('binding_conflict','Pinned research settings cannot rebind or expand Zotero access')
            client=self.client(cfg)
            for ref in p['item_refs']:
                item_ref(ref)
                if ref['binding_id']!=cfg['zotero']['binding_id']: fail('binding_conflict','Item belongs to another library')
                client.get(ref['item_key'])
            for ref in p['collection_refs']:
                exact(ref,('binding_id','collection_key')); identifier(ref['binding_id']); item_key(ref['collection_key'])
                if ref['binding_id']!=cfg['zotero']['binding_id']: fail('binding_conflict','Collection belongs to another library')
                client.get(ref['collection_key'],'collections')
            if context.role=='agent':
                grant=cfg['grants'][study]
                if {r['item_key'] for r in p['item_refs']}-set(grant['item_keys']) or {r['collection_key'] for r in p['collection_refs']}-set(grant['collection_keys']): fail('forbidden','Study binding exceeds delegated targets')
            links=p.get('item_links',binding['item_links'])
            if not isinstance(links,dict): fail('invalid_request','Item links must be an object')
            for key,link in links.items():
                item_key(key); exact(link,('status','reason'))
                if link['status'] not in ('included','excluded','undecided'): fail('invalid_request','Invalid screening status')
                bounded_text(link['reason'])
            binding.update(config_mode=p['config_mode'],pinned_config=pinned,
                           collection_refs=p['collection_refs'],item_refs=p['item_refs'],item_links=links)
            self.store.save_binding(binding); return binding
        if op=='literature.search':
            exact(p,('intent','queries','limit'),('overrides','resume_run'))
            bounded_text(p['intent']); integer(p['limit'],1,50)
            if not isinstance(p['queries'],dict) or not p['queries']: fail('scope_required','Provide explicit source queries')
            effective=copy.deepcopy(frozen) if frozen else effective_config(cfg,binding,p.get('overrides'))
            sources={s['id']:s for s in effective['research']['sources']}
            if set(p['queries'])-set(sources): fail('invalid_request','Query references an unconfigured source')
            attempts=[]; old=None
            if p.get('resume_run'):
                old=self.store.read('searches/'+identifier(p['resume_run'])+'.json')
                if not old or old['study_id']!=study: fail('not_found','Search run not found in this study')
                effective=old['effective_config']; sources={s['id']:s for s in effective['research']['sources']}
                if set(p['queries'])-set(sources): fail('invalid_request','Resume references a source outside the original configuration')
            searcher=self.search_factory()
            for source_id,query in p['queries'].items():
                cursor=0
                if old:
                    previous=[a for a in old['attempts'] if a['source_id']==source_id]
                    if previous:
                        if previous[-1]['query']!=query: fail('request_conflict','Resume must preserve the original source query')
                        cursor=previous[-1]['next_cursor']
                attempts.append(searcher.search(sources[source_id],query,p['limit'],cursor,effective['browser']['preferred']))
            all_attempts=(old['attempts'] if old else [])+attempts
            latest={a['source_id']:a for a in all_attempts}
            run={'schema_version':1,'run_id':operation,'study_id':study,'intent':p['intent'],'effective_config':effective,
                 'attempts':all_attempts,'parent_run':p.get('resume_run'),'complete':all(a['complete'] for a in latest.values()),
                 'created_utc':stamp(),'zotero_writes':0}
            self.store.write('searches/'+operation+'.json',run); return run
        if op=='literature.search_import':
            exact(p,('search_run','source_id','format','text','source_url','coverage_note'))
            from urllib.parse import urlsplit
            from literature_import import parse_export
            old=self.store.read('searches/'+identifier(p['search_run'])+'.json')
            if not old or old['study_id']!=study: fail('not_found','Search run is not in this study')
            source=next((s for s in old['effective_config']['research']['sources'] if s['id']==p['source_id']),None)
            attempts=[a for a in old['attempts'] if a['source_id']==p['source_id']]
            if not source or not attempts: fail('scope_required','Imported source must have an existing query in the search run')
            url=urlsplit(p['source_url'])
            hosts={'web_of_science':'webofscience.com','scopus':'scopus.com','pubmed':'ncbi.nlm.nih.gov','ieee':'ieee.org','google_scholar':'scholar.google.com'}
            host=hosts.get(source['adapter'])
            allowed=([host,'webofscience.clarivate.cn'] if source['adapter']=='web_of_science' else [host]) if host else []
            if not allowed or url.scheme!='https' or not url.hostname or not any(url.hostname==h or url.hostname.endswith('.'+h) for h in allowed) or url.username or url.password: fail('invalid_source','Native export requires the original configured source URL')
            bounded_text(p['coverage_note'],2000)
            candidates=parse_export(p['source_id'],p['format'],p['text'])
            previous=attempts[-1]
            attempt={**previous,'candidates':candidates,'status':'partial','complete':False,'started_utc':stamp(),'finished_utc':stamp(),
                'reason':'Native export imported; completeness of the external search is not asserted','coverage_note':p['coverage_note'],
                'source_url':p['source_url'],'export_sha256':digest(p['text'].encode()),'next_cursor':previous['next_cursor'],
                'capabilities':['export_citation'],'mode':'native_export'}
            run={**old,'run_id':operation,'parent_run':old['run_id'],'attempts':old['attempts']+[attempt],
                 'complete':False,'created_utc':stamp(),'zotero_writes':0}
            self.store.write('searches/'+operation+'.json',run); return run
        if op=='literature.collect':
            exact(p,('search_run','candidate_ids','collection_keys'),('tags','fulltext_urls'))
            run=self.store.read('searches/'+identifier(p['search_run'])+'.json')
            if not run or run['study_id']!=study: fail('not_found','Search run not found')
            if not isinstance(p['candidate_ids'],list) or not p['candidate_ids']: fail('scope_required','Select candidates explicitly')
            candidates={c['candidate_id']:c for a in run['attempts'] for c in a['candidates']}
            if set(p['candidate_ids'])-set(candidates): fail('invalid_request','Unknown search candidate')
            client=self.client(cfg); library,_=client.list('items',{'itemType':'-attachment'}); receipts=[]
            for key in p['collection_keys']: client.get(item_key(key),'collections')
            tags=p.get('tags',[])
            for tag in tags: bounded_text(tag,200)
            for n,cid in enumerate(dict.fromkeys(p['candidate_ids'])):
                candidate=candidates[cid]
                try:
                    duplicate=match_duplicate(candidate,library)
                    prior=self.store.read('operations/'+operation+'-'+str(n)+'.json')
                    if prior and 'kind' in prior['request']:
                        # Recover the original create even if its result now looks like a duplicate.
                        updated=self.create_object(client,'items',prior['request']['data'],operation+'-'+str(n),context)
                        duplicate={'status':'recovered','item_keys':[updated['key']]}
                    if duplicate['status']=='suspected':
                        receipts.append({'candidate_id':cid,'status':'waiting_user','duplicates':duplicate}); continue
                    if duplicate['status']=='recovered':
                        pass
                    elif duplicate['status']=='matched':
                        key=duplicate['item_keys'][0]; row=client.get(key)
                        if context.role=='agent' and key not in cfg['grants'][study]['item_keys']:
                            receipts.append({'candidate_id':cid,'status':'forbidden','reason':'Duplicate target is outside delegated items'}); continue
                        updated=self.add_membership(client,row,p['collection_keys'],tags,operation+'-'+str(n),context)
                    else:
                        data=copy.deepcopy(candidate['metadata']); data.update(key=deterministic_key(operation,n),collections=p['collection_keys'],tags=[{'tag':t} for t in tags])
                        updated=self.create_object(client,'items',data,operation+'-'+str(n),context)
                        library.append(updated)
                except (ValueError,OSError) as exc:
                    receipts.append({'candidate_id':cid,'status':getattr(exc,'code','outcome_unknown'),
                                     'operation_id':operation+'-'+str(n),'reason':str(exc) if hasattr(exc,'code') else type(exc).__name__})
                    continue
                entry={'candidate_id':cid,'item_ref':{'binding_id':cfg['zotero']['binding_id'],'item_key':updated['key']},
                                 'metadata_status':'metadata_saved','duplicate_status':duplicate['status'],
                                 'fulltext_status':'fulltext_missing','fulltext_reason':'Publisher/Connector attachment retrieval requires a verified access path',
                                 'reading_status':'not_read','version':updated['version']}
                url=p.get('fulltext_urls',{}).get(cid) or candidate['raw'].get('pdf_url')
                pmcid=candidate['raw'].get('pmcid')
                if url or pmcid:
                    try:
                        entry.update(self.save_fulltext(client,updated,operation+'-pdf'+str(n),context,url,pmcid))
                    except (ValueError,OSError) as exc:
                        entry.update(fulltext_status='fulltext_missing',fulltext_reason=getattr(exc,'code','fulltext_unavailable'))
                receipts.append(entry)
            return {'receipts':receipts,'status':'partial' if any(x.get('status') for x in receipts) else 'succeeded'}
        if op=='literature.fetch_fulltext':
            exact(p,('item_keys',),('url','pmcid'))
            if len(p['item_keys'])!=1 or bool(p.get('url'))==bool(p.get('pmcid')):
                fail('invalid_request','Select one parent item and one public PDF URL or PMC accession')
            client=self.client(cfg); row=client.get(item_key(p['item_keys'][0]))
            if row['data'].get('itemType') in ('attachment','annotation','note'): fail('invalid_request','Select a literature parent item')
            return self.save_fulltext(client,row,operation,context,p.get('url'),p.get('pmcid'))
        if op=='literature.organize':
            exact(p,('item_keys','collection_keys','tags'),('new_collection','notes','annotation'))
            client=self.client(cfg); receipts=[]
            collection_keys=list(p['collection_keys'])
            if p.get('new_collection'):
                bounded_text(p['new_collection'],200)
                row=self.create_object(client,'collections',{'key':deterministic_key(operation),'name':p['new_collection'],'parentCollection':False},operation+'-collection',context)
                collection_keys.append(row['key'])
            for key in collection_keys: client.get(item_key(key),'collections')
            if p.get('annotation'):
                annotation=p['annotation']
                exact(annotation,('attachment_key','annotationType','annotationText','annotationComment','annotationColor','annotationPageLabel','annotationSortIndex','annotationPosition'))
                if context.role!='operator' or 'annotation' not in cfg['zotero']['allowed_operations']: fail('forbidden','Explicit native annotation permission is required')
                parent=client.get(item_key(annotation['attachment_key']))
                if parent['data'].get('parentItem') not in p['item_keys']: fail('forbidden','Annotation attachment is outside the selected parent items')
                if annotation['annotationType'] not in ('highlight','note'): fail('invalid_request','Supported explicit annotation types are highlight and note')
                import json
                position=json.loads(annotation['annotationPosition'])
                if not isinstance(position,dict) or type(position.get('pageIndex')) is not int or position['pageIndex']<0: fail('invalid_request','Explicit annotation page position is required')
                data={k:v for k,v in annotation.items() if k!='attachment_key'}
                data.update(key=deterministic_key(operation,20000),itemType='annotation',parentItem=annotation['attachment_key'])
                row=self.create_object(client,'items',data,operation+'-annotation',context)
                receipts.append({'item_key':row['key'],'status':'verified','version':row['version'],'kind':'annotation'})
            for n,key in enumerate(p['item_keys']):
                try:
                    row=client.get(item_key(key)); row=self.add_membership(client,row,collection_keys,p['tags'],operation+'-item'+str(n),context)
                    note=p.get('notes',{}).get(key)
                    if note:
                        bounded_text(note,24000)
                        data={'key':deterministic_key(operation,10000+n),'itemType':'note','parentItem':key,
                              'note':'<p>OpenSci AI note; task '+html.escape(request['request_id'])+'</p><pre>'+html.escape(note)+'</pre>',
                              'tags':[{'tag':'OpenSci AI note'}]}
                        note_row=self.create_object(client,'items',data,operation+'-note'+str(n),context)
                    else: note_row=None
                    receipts.append({'item_key':key,'status':'verified','version':row['version'],'note_key':note_row['key'] if note_row else None})
                except (ValueError,OSError) as exc:
                    receipts.append({'item_key':key,'status':getattr(exc,'code','outcome_unknown'),
                                     'operation_id':operation+'-item'+str(n),'reason':str(exc) if hasattr(exc,'code') else type(exc).__name__})
            return {'receipts':receipts,'status':'succeeded' if all(x['status']=='verified' for x in receipts) else 'partial'}
        if op=='literature.read':
            exact(p,('level',),('item_keys','index'))
            client=self.client(cfg); keys=self.keys(p,binding,client)
            if context.role=='agent' and set(keys)-set(cfg['grants'][study]['item_keys']): fail('forbidden','Resolved items exceed delegated read scope')
            before_versions=client.list('items',{'format':'versions'})[0] if p.get('index') else None
            result=EvidenceService(self.store).snapshot(client,keys,p['level'])
            if p.get('index'):
                versions,_=client.list('items',{'format':'versions'})
                result['index']=EvidenceService(self.store).index(result['snapshot_id'],versions if versions==before_versions else None)
            return result
        if op=='literature.analyze':
            exact(p,('snapshot_id','node_ref','analysis_kind'),('overrides','parent_job'))
            node=self.hub.config['nodes'].get(p['node_ref'])
            if not node or not node['enabled'] or node['role']!='agent': fail('forbidden','Choose an existing enabled development node for literature analysis')
            return new_job(self.store,study,operation,p['snapshot_id'],copy.deepcopy(frozen) if frozen else effective_config(cfg,binding,p.get('overrides')),p['node_ref'],p['analysis_kind'],context.principal,p.get('parent_job'))
        if op in ('literature.job_pause','literature.job_resume','literature.job_cancel'):
            exact(p,('job_id',)); job=self.store.job(p['job_id'])
            if job['study_id']!=study: fail('forbidden','Job is outside the requested study')
            result=request_control(self.store,job,op.rsplit('_',1)[1],request['request_id'])
            if context.allow_remote_checks:
                from literature_transport import remote_call
                node=self.hub.config['nodes'].get(job['node_ref'])
                if node and node['enabled'] and node['role']=='agent' and node['transport']=='ssh':
                    try:
                        result['delivery']=remote_call(node,['control','--job',job['job_id']],canonical(result['control_request']))
                        if op=='literature.job_resume':
                            result['executor']=remote_call(node,['launch','--job',job['job_id'],'--node',job['node_ref'],'--resume'])
                        result['control_status']='delivered_awaiting_acknowledgement'
                    except ValueError as exc: result['delivery_error']=getattr(exc,'code','unavailable')
            return result
        if op in ('literature.job_dispatch','literature.job_import'):
            exact(p,('job_id',)); job=self.store.job(p['job_id'])
            if job['study_id']!=study: fail('forbidden','Job belongs to another study')
            if not context.allow_remote_checks: fail('remote_check_required','Remote literature work requires trusted launch policy permission')
            from literature_transport import dispatch,fetch
            node=self.hub.config['nodes'].get(job['node_ref'])
            if not node or not node['enabled'] or node['role']!='agent': fail('forbidden','Executor binding is unavailable')
            if op=='literature.job_dispatch': return dispatch(self.store,job['job_id'],job['node_ref'],node)
            value=fetch(self.store,job['job_id'],node)
            if value.get('result_base64') is None:
                from literature_jobs import import_status
                return import_status(self.store,job['job_id'],value['job'])
            import base64
            from literature_jobs import import_result
            return import_result(self.store,job['job_id'],value['job'],base64.b64decode(value['result_base64'],validate=True))
        if op=='literature.export':
            exact(p,('snapshot_id','manuscript_id'))
            manifest=EvidenceService(self.store).load(p['snapshot_id'])
            return export_bib(self.store,p['manuscript_id'],manifest['items'])
        if op=='literature.cite':
            exact(p,('manuscript_id','path','expected_sha256','format','item_refs','marker'),('phase','task_id','native_action'))
            identifier(p['manuscript_id'])
            if not isinstance(p['item_refs'],list) or len(p['item_refs'])>100: fail('invalid_request','Bounded citation targets required')
            for ref in p['item_refs']:
                item_ref(ref)
                if ref['binding_id']!=cfg['zotero']['binding_id']: fail('binding_conflict','Citation belongs to another personal library')
                if context.role=='agent' and ref['item_key'] not in cfg['grants'][study]['item_keys']: fail('forbidden','Citation item exceeds the delegated scope')
            if p['format']=='word':
                from literature_word import prepare,verify
                if p.get('phase','prepare')=='verify':
                    task=self.store.read('native-word/'+identifier(p.get('task_id'))+'.json')
                    if not task or task['specification']['item_refs']!=p['item_refs']: fail('request_conflict','Native verification targets differ from the prepared task')
                    return verify(self.store,study,p['task_id'],p['path'],p['expected_sha256'])
                if p.get('phase','prepare')!='prepare': fail('invalid_request','Unknown native task phase')
                client=self.client(cfg)
                for ref in p['item_refs']: client.get(ref['item_key'])
                return prepare(self.store,study,operation,p['path'],p['expected_sha256'],p['item_refs'],p['marker'],p.get('native_action','insert'))
            mapping=self.store.read('citations/'+identifier(p['manuscript_id'])+'.json')
            if mapping is None: fail('citation_conflict','Export the task bibliography before inserting references')
            keys=[]
            for ref in p['item_refs']:
                item_ref(ref); identity=ref['binding_id']+':'+ref['item_key']
                if identity not in mapping['keys']: fail('citation_conflict','Citation does not belong to this manuscript map')
                keys.append(mapping['keys'][identity])
            # Text insertion has a deterministic postcondition and is recoverable under the same intent.
            return self.store.operation(operation+'-cite',p,context,
                lambda:cite_text(self.store,p['path'],p['expected_sha256'],p['marker'],keys,p['format']))
        if op=='literature.preview_change':
            exact(p,('kind','item_key','change'))
            if p['kind'] not in ('items','collections'): fail('invalid_request','Unknown object kind')
            client=self.client(cfg); row=client.get(p['item_key'],p['kind'])
            exact(p['change'],('action',),('fields',))
            if p['change']['action'] not in ('update','delete','merge'): fail('invalid_request','Unknown change action')
            if p['change']['action']=='merge':
                return {'status':'waiting_user','reason':'Use Zotero native merge, then reconcile surviving keys; no simulated merge is permitted'}
            if p['change']['action']=='update':
                fields=p['change'].get('fields')
                if not isinstance(fields,dict) or not fields or set(fields)&{'key','version','library','itemType'}: fail('invalid_request','Invalid update fields')
            preview={'schema_version':1,'preview_id':operation,'study_id':study,'instance_id':client.instance,
                     'binding_id':cfg['zotero']['binding_id'],'kind':p['kind'],'key':row['key'],'base_version':row['version'],
                     'before':row['data'],'change':p['change'],'impact':'Existing Zotero content or relationships will change; study evidence remains historical',
                     'recovery':'Use this before-image to prepare a new compensating operation; deletion may require restoring the external Zotero backup',
                     'created_utc':stamp()}
            preview['digest']=digest(canonical(preview)); self.store.write('previews/'+operation+'.json',preview); return preview
        if op=='literature.apply_change':
            exact(p,('preview_id','confirmed_digest'))
            preview=self.store.read('previews/'+identifier(p['preview_id'])+'.json')
            if not preview or preview['study_id']!=study or preview['digest']!=p['confirmed_digest'] or digest(canonical({k:v for k,v in preview.items() if k!='digest'}))!=p['confirmed_digest']:
                fail('confirmation_conflict','Confirmation does not match the stored preview')
            client=self.client(cfg)
            if client.instance!=preview['instance_id']: fail('instance_changed','Preview belongs to another Zotero instance')
            def apply():
                row=client.get(preview['key'],preview['kind'])
                if row['version']!=preview['base_version'] or row['data']!=preview['before']: fail('version_conflict','Human edits made this preview stale')
                if preview['change']['action']=='delete': return client.delete(preview['kind'],row['key'],row['version'])
                return client.update(preview['kind'],row['key'],row['version'],preview['change']['fields'])
            if preview['change']['action']=='delete':
                return self.store.operation(operation+'-delete',preview,context,apply)
            fields=preview['change']['fields']
            return self.store.operation(operation+'-update',preview,context,apply,
                lambda old:self.reconcile_patch(client,preview['kind'],preview['key'],fields))
        fail('not_supported','Literature operation is not implemented')

    def save_fulltext(self,client,row,operation,context,url=None,pmcid=None):
        import hashlib
        import re
        from literature_fulltext import retrieve_pdf,resolve_pmc
        operation='ft-'+digest(operation.encode())
        provenance=None
        if not url:
            pmid=re.search(r'^PMID:\s*(\d+)\s*$',row['data'].get('extra',''),re.M)
            provenance=resolve_pmc(pmcid,row['data'].get('DOI',''),pmid.group(1) if pmid else None)
            url=provenance['pdf_url']
        raw,checks=retrieve_pdf(url); md5=hashlib.md5(raw).hexdigest()
        if provenance and provenance['md5']!=md5: fail('invalid_pdf','Downloaded PMC PDF differs from its published checksum')
        # Reuse a verified existing attachment even under a different command ID.
        saved=next((x for x in client.children(row['key']) if x['data'].get('itemType')=='attachment' and x['data'].get('md5')==md5),None)
        if saved is None:
            att={'key':deterministic_key(operation),'itemType':'attachment','parentItem':row['key'],
                 'title':'Full text','linkMode':'imported_url','contentType':'application/pdf','url':url}
            saved=self.create_object(client,'items',att,operation+'-attachment',context)
            key=saved['key']
            def reconcile_upload(old):
                try: current=client.get(key)
                except ValueError: return None
                return current if current['data'].get('md5')==md5 else None
            saved=self.store.operation(operation+'-upload',{'attachment_key':key,'sha256':checks['sha256']},context,
                lambda:client.upload_pdf(key,raw,key+'.pdf'),reconcile_upload)
        return {'fulltext_status':'fulltext_saved','fulltext_reason':None,'attachment_key':saved['key'],
                'attachment_sha256':checks['sha256'],'bytes':len(raw),'provenance':provenance}

    def create_object(self,client,kind,data,operation,context):
        def reconcile(old):
            try: row=client.get(data['key'],kind)
            except ValueError: return None
            return row if all(row['data'].get(k)==v for k,v in data.items() if k not in ('key','version')) else None
        return self.store.operation(operation,{'kind':kind,'data':data},context,
            lambda:client.create(kind,data,digest(operation.encode())),reconcile)

    def reconcile_patch(self,client,kind,key,fields):
        try: row=client.get(key,kind)
        except ValueError: return None
        return row if all(row['data'].get(k)==v for k,v in fields.items()) else None

    def add_membership(self,client,row,collections,tags,operation,context):
        for tag in tags: bounded_text(tag,200)
        previous=self.store.read('operations/'+operation+'.json')
        if previous:
            original=previous['request']
            if original.get('desired') != {'collections':collections,'tags':tags} or original['key']!=row['key']:
                fail('request_conflict','Membership intent changed during recovery')
            return self.store.operation(operation,original,context,
                lambda:client.update('items',original['key'],original['base_version'],original['fields']),
                lambda old:self.reconcile_patch(client,'items',original['key'],original['fields']))
        data=row['data']; current_tags=copy.deepcopy(data.get('tags',[]))
        names={t['tag'] for t in current_tags}
        current_tags.extend({'tag':t} for t in tags if t not in names)
        fields={'collections':list(dict.fromkeys(data.get('collections',[])+collections)),'tags':current_tags}
        if all(data.get(k,[])==v for k,v in fields.items()): return row
        return self.store.operation(operation,{'key':row['key'],'base_version':row['version'],'fields':fields,'desired':{'collections':collections,'tags':tags}},context,
            lambda:client.update('items',row['key'],row['version'],fields),
            lambda old:self.reconcile_patch(client,'items',row['key'],fields))
