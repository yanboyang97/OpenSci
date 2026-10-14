"""Bounded native citation export ingestion. Parsing never writes to Zotero."""
import re
from common import digest
from literature_contract import fail,bounded_text
from literature_sources import normalized

def metadata(fields,kind):
    types={'JOUR':'journalArticle','journal':'journalArticle','article':'journalArticle','CONF':'conferencePaper',
           'inproceedings':'conferencePaper','BOOK':'book','book':'book','CHAP':'bookSection','incollection':'bookSection',
           'THES':'thesis','phdthesis':'thesis','mastersthesis':'thesis','RPRT':'report','report':'report','techreport':'report'}
    if kind not in types: fail('unsupported_export','Export item type requires an explicit mapping: '+kind)
    value=lambda *names:next((fields[n][0] for n in names if fields.get(n)),'')
    authors=fields.get('AU',fields.get('A1',fields.get('author',[])))
    creators=[]
    for author in authors:
        for person in re.split(r'\s+and\s+',author):
            if ',' in person:
                last,first=person.split(',',1); creators.append({'creatorType':'author','lastName':last.strip(),'firstName':first.strip()})
            else: creators.append({'creatorType':'author','name':person.strip()})
    data={'itemType':types[kind],'title':value('TI','T1','title'),'DOI':value('DO','doi'),'date':value('PY','Y1','year','date'),
          'url':value('UR','url'),'abstractNote':value('AB','N2','abstract'),'creators':creators}
    if not data['title']: fail('invalid_export','Citation export has no title')
    publication=value('JO','JF','T2','journal','booktitle')
    if data['itemType']=='journalArticle': data['publicationTitle']=publication
    if data['itemType']=='conferencePaper': data['proceedingsTitle']=publication
    for zotero,names in (('volume',('VL','volume')),('issue',('IS','number')),('pages',('SP','pages'))):
        v=value(*names)
        if v: data[zotero]=v+('-'+value('EP') if zotero=='pages' and value('EP') else '')
    return data

def ris(text):
    rows=[]; record=None; last=None
    for line in text.splitlines():
        match=re.match(r'^([A-Z0-9]{2})  - ?(.*)$',line)
        if not match:
            if line.strip() and record is not None and last: record[last][-1]+=' '+line.strip()
            elif line.strip(): fail('invalid_export','Unexpected RIS text outside a record')
            continue
        tag,value=match.groups()
        if tag=='TY':
            if record is not None: fail('invalid_export','Unterminated RIS record')
            record={'TY':[value.strip()]}
        elif tag=='ER':
            if record is None: fail('invalid_export','RIS end without a record')
            rows.append((record['TY'][0],record)); record=None
        elif record is None: fail('invalid_export','RIS record must begin with TY')
        else: record.setdefault(tag,[]).append(value)
        last=tag
    if record is not None: fail('invalid_export','Unterminated RIS record')
    return rows

def bibtex(text):
    """Explicit fields, nested braces and quotes; macros/concatenation fail visibly."""
    rows=[]; pos=0
    def skip():
        nonlocal pos
        while pos<len(text):
            if text[pos].isspace() or text[pos]==',': pos+=1
            elif text[pos]=='%':
                end=text.find('\n',pos); pos=len(text) if end<0 else end+1
            else: break
    def token(pattern):
        nonlocal pos
        m=re.match(pattern,text[pos:])
        if not m: fail('invalid_export','Malformed BibTeX export')
        pos+=m.end(); return m.group(0)
    def value():
        nonlocal pos
        skip()
        if pos>=len(text): fail('invalid_export','Missing BibTeX value')
        delimiter=text[pos]
        if delimiter not in ('{','"'): return token(r'\d+')
        pos+=1; out=[]; depth=1 if delimiter=='{' else 0
        while pos<len(text):
            c=text[pos]; pos+=1
            if c=='\\':
                if pos>=len(text): fail('invalid_export','Trailing BibTeX escape')
                out.extend((c,text[pos])); pos+=1; continue
            if c=='{': depth+=1
            elif c=='}':
                depth-=1
                if delimiter=='{' and depth==0: return ''.join(out)
            elif c=='"' and delimiter=='"' and depth==0: return ''.join(out)
            out.append(c)
        fail('invalid_export','Unterminated BibTeX value')
    while True:
        skip()
        if pos==len(text): break
        if text[pos]!='@': fail('invalid_export','Expected a BibTeX entry')
        pos+=1; kind=token(r'[A-Za-z]+').lower(); skip()
        if kind in ('string','preamble','comment'): fail('unsupported_export','BibTeX macros/preambles/comments require a flattened native export')
        if pos>=len(text) or text[pos]!='{': fail('invalid_export','Braced BibTeX entry required')
        pos+=1; key=token(r'[^,\s{}]+'); skip(); fields={'export_key':[key]}
        while pos<len(text) and text[pos]!='}':
            name=token(r'[A-Za-z][A-Za-z0-9_-]*').lower(); skip()
            if pos>=len(text) or text[pos]!='=': fail('invalid_export','Expected a BibTeX assignment')
            pos+=1; fields.setdefault(name,[]).append(value()); skip()
        if pos>=len(text): fail('invalid_export','Unterminated BibTeX entry')
        pos+=1; rows.append((kind,fields))
    return rows

def parse_export(source,format,text):
    bounded_text(text,2_000_000)
    rows=ris(text) if format=='ris' else bibtex(text) if format=='bibtex' else None
    if rows is None: fail('unsupported_export','Choose ris or bibtex')
    if not rows or len(rows)>500: fail('invalid_export','Expected 1 to 500 exported records')
    checksum=digest(text.encode()); candidates=[]; identities=set()
    for index,(kind,fields) in enumerate(rows):
        data=metadata(fields,kind)
        identity=next(iter(fields.get('ID',fields.get('export_key',[]))),checksum+':'+str(index))
        if identity in identities: fail('invalid_export','Duplicate source identifiers in the same export require review')
        identities.add(identity)
        candidates.append(normalized(source,identity,data,{'export_sha256':checksum,'record_index':index,'format':format,'fields':fields}))
    return candidates
