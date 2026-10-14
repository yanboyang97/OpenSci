"""Stable manuscript mappings and guarded native Word integration readiness."""
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from common import atomic_write, canonical, digest
from literature_contract import fail, identifier, bounded_text
from storage_paths import safe_name, plain_path

def bib_escape(value):
    return ''.join({'\\':r'\textbackslash{}','{':r'\{','}':r'\}','&':r'\&','%':r'\%','#':r'\#','_':r'\_','$':r'\$','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in str(value)).replace('\n',' ')

def explicit_key(data):
    found=re.findall(r'^(?:Citation Key|bibtex):\s*([^\s]+)\s*$',data.get('extra',''),re.M|re.I)
    return found[0] if found else None

def export_bib(store,manuscript_id,items):
    identifier(manuscript_id)
    relative='citations/'+manuscript_id+'.json'
    mapping=store.read(relative,{'schema_version':1,'manuscript_id':manuscript_id,'keys':{},'conflicts':[]})
    occupied={v:k for k,v in mapping['keys'].items()}; entries=[]
    for item in items:
        ref=item['item_ref']; identity=ref['binding_id']+':'+ref['item_key']; data=item['metadata']
        key=mapping['keys'].get(identity)
        requested=explicit_key(data)
        if key is None:
            key=requested or 'zotero'+ref['item_key']
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:+/-]{0,119}',key): fail('citation_conflict','Invalid fixed citation key')
            if key in occupied and occupied[key]!=identity: fail('citation_conflict','Fixed citation key is already assigned to another item')
            mapping['keys'][identity]=key; occupied[key]=identity
        elif requested and requested!=key:
            mapping['conflicts'].append({'item_ref':ref,'kept_key':key,'requested_key':requested})
        kind={'journalArticle':'article','conferencePaper':'inproceedings','book':'book','bookSection':'incollection','thesis':'phdthesis'}.get(data.get('itemType'),'misc')
        creators=data.get('creators',[])
        authors=' and '.join(bib_escape(x.get('name') or (x.get('lastName','')+', '+x.get('firstName',''))) for x in creators if x.get('creatorType')=='author')
        fields={'title':bib_escape(data.get('title','')),'author':authors,'year':re.search(r'\d{4}',data.get('date','')).group() if re.search(r'\d{4}',data.get('date','')) else '',
                'doi':bib_escape(data.get('DOI','')),'url':bib_escape(data.get('url','')),'journal':bib_escape(data.get('publicationTitle','')),
                'volume':bib_escape(data.get('volume','')),'number':bib_escape(data.get('issue','')),'pages':bib_escape(data.get('pages',''))}
        entries.append('@'+kind+'{'+key+',\n'+',\n'.join('  '+k+' = {'+v+'}' for k,v in fields.items() if v)+'\n}\n')
    store.write(relative,mapping)
    raw=('\n'.join(entries)).encode('utf-8'); path=store.path('exports/'+manuscript_id+'/references.bib')
    atomic_write(path,raw)
    keys=[mapping['keys'][x['item_ref']['binding_id']+':'+x['item_ref']['item_key']] for x in items]
    tex='\\documentclass{article}\n\\begin{document}\n'+('\\cite{'+','.join(keys)+'}' if keys else '')+'\n\\bibliographystyle{plain}\n\\bibliography{references}\n\\end{document}\n'
    qmd='---\ntitle: Literature export\nbibliography: references.bib\nformat: html\n---\n\n'+ '; '.join('@'+k for k in keys)+'\n'
    atomic_write(path.with_name('sample.tex'),tex.encode()); atomic_write(path.with_name('sample.qmd'),qmd.encode())
    return {'manuscript_id':manuscript_id,'bibliography':path.relative_to(store.root).as_posix(),
            'sha256':digest(raw),'entry_count':len(items),'citation_map':mapping,
            'latex_acceptance':'not_compiled','quarto_acceptance':'not_compiled'}

def inspect_manuscript(path):
    path=plain_path(path); raw=path.read_bytes()
    result={'sha256':digest(raw),'bytes':len(raw),'filename':path.name,'citation_keys':[], 'native_fields':[]}
    if path.suffix.lower()=='.docx':
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.filename.startswith('word/') and info.filename.endswith('.xml'):
                    if info.file_size>16000000: fail('manuscript_too_large','Word XML exceeds inspection limit')
                    tree=ET.fromstring(archive.read(info))
                    for element in tree.iter():
                        if element.tag.endswith('}instrText') and 'ZOTERO' in (element.text or ''):
                            result['native_fields'].append({'part':info.filename,'field_sha256':digest(element.text.encode()),
                                                           'kind':'citation' if 'CSL_CITATION' in element.text else 'bibliography'})
        result['native_field_count']=len(result['native_fields'])
    elif path.suffix.lower() in ('.tex','.qmd','.md','.bib'):
        text=raw.decode('utf-8')
        result['citation_keys']=sorted(set(re.findall(r'@[A-Za-z]+\s*\{\s*([^,\s]+)',text) if path.suffix.lower()=='.bib' else
            [k.strip() for group in re.findall(r'\\(?:[a-zA-Z]*cite[a-zA-Z]*)\*?(?:\[[^\]]*\])*\{([^}]+)\}',text) for k in group.split(',')]+
            re.findall(r'(?<!\w)@([A-Za-z0-9][A-Za-z0-9_.:+/-]+)',text)))
    else: fail('unsupported_manuscript','Supported manuscript formats: docx, tex, qmd, md, bib')
    return result

def cite_text(store,relative,expected_sha256,marker,keys,format):
    if not relative.startswith('manuscript/'): fail('forbidden','Manuscript edits must be inside manuscript/')
    path=plain_path(store.root/safe_name(relative)); raw=path.read_bytes()
    if digest(raw)!=expected_sha256: fail('version_conflict','Manuscript changed since preview')
    if format not in ('latex','quarto'): fail('unsupported_format','Use a verified native adapter for Word')
    bounded_text(marker,200)
    text=raw.decode('utf-8')
    if text.count(marker)!=1: fail('ambiguous_location','Insertion marker must occur exactly once')
    for key in keys:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:+/-]{0,119}',key): fail('citation_conflict','Invalid citation key')
    citation='\\cite{'+','.join(keys)+'}' if format=='latex' else '['+'; '.join('@'+k for k in keys)+']'
    backup=store.path('manuscript-recovery/'+digest(raw)+path.suffix)
    if not backup.exists(): atomic_write(backup,raw)
    if path.read_bytes()!=raw: fail('version_conflict','Concurrent manuscript edit detected')
    updated=text.replace(marker,citation,1).encode('utf-8'); atomic_write(path,updated)
    return {'path':relative,'sha256':digest(updated),'previous_sha256':digest(raw),'citation_keys':keys,
            'recovery':backup.relative_to(store.root).as_posix()}

