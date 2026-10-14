"""Build/check OpenSci's offline handbook from explicitly listed Markdown sources."""
import argparse
import ast
import base64
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

try:
    from markdown_it import MarkdownIt
except ImportError:
    raise SystemExit('Documentation build requires markdown-it-py; see requirements-docs.txt. No package is installed automatically.')

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {'en': ROOT / 'OpenSci-Manual.html', 'zh-CN': ROOT / 'OpenSci-Manual.zh-CN.html'}
LABELS_EN = {'guides': 'Guides', 'references': 'Reference', 'source': 'Source', 'contents': 'Chapter contents', 'back': 'Back to top', 'title': 'OpenSci User and Maintainer Handbook', 'navigation': 'Documentation navigation', 'icon': 'OpenSci icon', 'brand': 'Use · Maintain · Extend · Upgrade', 'menu': 'Menu', 'search': 'Search', 'placeholder': 'Keyword · Ctrl K', 'clear': 'Clear', 'print': 'Print', 'hero': 'OFFLINE HANDBOOK', 'description': 'From first use to operation, development and upgrades.', 'code': 'Code', 'docs': 'Docs', 'sources': 'source documents', 'results': 'Search results', 'footer': 'Generated from Markdown. Edit the source documents to update.', 'fingerprint': 'Build source SHA-256', 'all': 'All {count} documents', 'matches': '{hits} matching sections in {count} documents', 'no_matches': 'No matches. Try a shorter term or filename.', 'limit': 'Showing the first 80 results; refine your search.'}
MANIFEST = ROOT / 'tools/docs_manifest.json'

STYLE = r'''
:root{color-scheme:light;--ink:#14313c;--muted:#536b74;--line:#d6e4e6;--paper:#fff;--accent:#087e83;--wash:#eef7f7;--nav:#102e3b}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:6rem}body{margin:0;background:#f5f8f8;color:var(--ink);font:16px/1.8 "Segoe UI","Microsoft YaHei",system-ui,sans-serif}
a{color:#08777d;text-underline-offset:3px}a:hover{color:#064c57}button,input{font:inherit}button{cursor:pointer}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #40caba;outline-offset:3px}
aside{position:fixed;inset:0 auto 0 0;width:278px;background:var(--nav);color:#d5e8e9;overflow:auto;padding:30px 22px;z-index:10}
.brand{display:flex;gap:12px;align-items:center;color:white;font-size:25px;font-weight:700}.brand img{width:42px;height:42px}.brand-note{font-size:13px;line-height:1.6;color:#acd0d1;margin:12px 0 25px}
nav a{display:block;color:#dcebed;text-decoration:none;padding:9px 11px;border-radius:8px;font-size:14px;line-height:1.5;margin:3px 0;overflow-wrap:anywhere}nav a:hover,nav a.active{background:#204957;color:#7ee6d0}
.nav-group{font-size:12px;letter-spacing:.06em;color:#7fb3b6;margin:25px 10px 8px}.nav-group:first-child{margin-top:0}
.workspace{margin-left:278px}.toolbar{position:sticky;top:0;z-index:5;background:rgba(245,248,248,.97);border-bottom:1px solid var(--line);padding:15px clamp(20px,4vw,56px);display:flex;align-items:center;gap:12px}
.search-wrap{flex:1;display:flex;align-items:center;border:1px solid #aec9ca;border-radius:10px;background:white;overflow:hidden;max-width:800px}.search-wrap label{padding:0 12px;font-size:13px;color:var(--muted);white-space:nowrap}.search-wrap input{min-width:0;width:100%;border:0;background:transparent;padding:9px 4px;color:var(--ink);outline:none}.search-wrap button{border:0;background:transparent;color:var(--muted);padding:7px 13px;white-space:nowrap}
.print-button,.menu-button{border:1px solid #b8ced0;border-radius:9px;background:white;padding:8px 12px;color:var(--ink);white-space:nowrap}.menu-button{display:none}
main{max-width:1240px;padding:30px clamp(20px,4vw,56px) 70px;margin:auto}.hero{background:linear-gradient(115deg,#dcefea,#eff7f9);border:1px solid #c6e0dc;border-radius:17px;padding:28px 32px;margin-bottom:28px}.eyebrow{font-size:13px;font-weight:600;color:#26766e}.hero h1{font-size:30px;line-height:1.45;margin:8px 0}.hero p{margin:8px 0;color:#385d65}.meta{font-size:13px;color:var(--muted)}
article{background:var(--paper);border:1px solid var(--line);border-radius:15px;padding:28px clamp(20px,3vw,40px);margin:24px 0;overflow-wrap:anywhere;scroll-margin-top:6rem}article>header{border-bottom:1px solid var(--line);padding-bottom:17px;margin-bottom:20px}.chapter-tag{font-size:12px;color:var(--accent);font-weight:700;letter-spacing:.05em}.source-link{display:inline-block;font-size:13px;color:var(--muted);margin:5px 0}.source-link a{color:inherit}
h1,h2,h3,h4{line-height:1.5;color:#163d47}article h1{font-size:27px;margin:8px 0}article h2{font-size:22px;margin:30px 0 14px;padding-top:4px}article h3{font-size:18px;margin:24px 0 12px}p{margin:14px 0}li{margin:6px 0}blockquote{border-left:4px solid #60c7b4;background:var(--wash);margin:20px 0;padding:8px 18px}blockquote p{margin:6px 0}
pre{background:#122e3b;color:#e4f3f3;border-radius:10px;padding:18px 20px;overflow:auto;font-size:13px;line-height:1.75;white-space:pre;tab-size:4}code{font-family:Consolas,"Cascadia Code",monospace;font-size:.89em}p code,li code,td code{background:#edf3f3;color:#254d58;padding:2px 4px;border-radius:4px;overflow-wrap:anywhere}pre code{font-size:inherit;background:none;color:inherit;padding:0}
.table-wrap{overflow-x:auto;margin:20px 0;border:1px solid var(--line);border-radius:9px}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.7}th,td{padding:12px 14px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);min-width:120px}th{background:#eaf3f3;font-weight:650}tr:last-child td{border-bottom:0}tr:nth-child(even) td{background:#fbfdfd}img{max-width:100%;height:auto}hr{border:0;border-top:1px solid var(--line);margin:26px 0}
.article-contents{font-size:14px;margin:16px 0;padding:12px 16px;background:#f5f9f9;border-radius:9px}.article-contents a{display:inline-block;margin-right:17px;margin-bottom:3px}.section{scroll-margin-top:6rem}.search-results{border:1px solid #bcded7;background:#f2fbf8;border-radius:12px;padding:18px 22px;margin:20px 0}.search-results h2{font-size:18px;margin:0 0 8px}.search-results a{display:block;margin:8px 0}.search-results small{display:block;color:var(--muted);line-height:1.6}.search-status{font-size:13px;margin:10px 2px;color:var(--muted)}[hidden]{display:none!important}.back-top{font-size:13px;display:block;text-align:right;margin-top:20px}.footer{font-size:12px;color:var(--muted);overflow-wrap:anywhere}
@media(max-width:1050px){aside{width:232px;padding:24px 15px}.workspace{margin-left:232px}main{padding-left:24px;padding-right:24px}.toolbar{padding:13px 24px}.hero{padding:24px}}
@media(max-width:760px){aside{position:static;width:auto;max-height:42vh;display:none}body.nav-open aside{display:block}.workspace{margin-left:0}.menu-button{display:block}.toolbar{padding:10px 12px;gap:8px}.search-wrap label{display:none}.search-wrap input{padding:8px 10px}.print-button{display:none}main{padding:18px 12px 40px}.hero{padding:20px}.hero h1{font-size:25px}article{padding:20px 17px}article h1{font-size:24px}article h2{font-size:20px}pre{padding:14px;font-size:12px}th,td{padding:10px;min-width:150px}}
@media print{aside,.toolbar,.hero,.search-results,.search-status,.article-contents,.back-top{display:none!important}.workspace{margin:0}main{max-width:none;padding:0}body{font-size:10pt;background:white}article{display:block!important;border:0;padding:0;margin:0;page-break-before:always}article:first-of-type{page-break-before:auto}article h1{font-size:20pt}article h2{font-size:15pt}pre{color:black;background:#f4f4f4;white-space:pre-wrap;overflow-wrap:anywhere}.table-wrap{overflow:visible}table{font-size:8pt}th,td{min-width:0}a{color:inherit;text-decoration:none}h1,h2,h3{break-after:avoid}tr{break-inside:avoid}.source-link{font-size:9pt}}
'''

SCRIPT = r'''
const input=document.querySelector('#search');
const status=document.querySelector('#search-status');
const results=document.querySelector('#search-results');
const resultList=document.querySelector('#result-list');
const articles=[...document.querySelectorAll('article')];
const sections=[...document.querySelectorAll('.section')].map(el=>({el,article:el.closest('article'),text:el.textContent.toLocaleLowerCase(),title:el.dataset.title}));
let timer;
function search(){
 const query=input.value.trim().toLocaleLowerCase();
 const terms=query.split(/\s+/).filter(Boolean);
 resultList.replaceChildren();
 if(!terms.length){articles.forEach(a=>a.hidden=false);results.hidden=true;status.textContent=labels.all.replace('{count}',articles.length);return;}
 const hits=sections.filter(s=>terms.every(t=>s.text.includes(t)||(s.article.dataset.title+' '+s.article.dataset.source).toLocaleLowerCase().includes(t)));
 const visible=new Set(hits.map(h=>h.article));articles.forEach(a=>a.hidden=!visible.has(a));
 status.textContent=labels.matches.replace('{hits}',hits.length).replace('{count}',visible.size);
 results.hidden=false;
 hits.slice(0,80).forEach(h=>{
  const link=document.createElement('a');link.href='#'+h.el.id;link.textContent=h.article.dataset.title+' · '+h.title;
  const snippet=document.createElement('small');const raw=h.el.textContent.replace(/\s+/g,' ').trim();
  const pos=raw.toLocaleLowerCase().indexOf(terms[0]);const start=Math.max(0,pos-45);snippet.textContent=(start?'… ':'')+raw.slice(start,start+180)+(raw.length>start+180?' …':'');
  link.append(snippet);resultList.append(link);
 });
 if(!hits.length){const p=document.createElement('p');p.textContent=labels.no_matches;resultList.append(p);}
 if(hits.length>80){const p=document.createElement('p');p.textContent=labels.limit;resultList.append(p);}
}
function revealHash(){
 const id=decodeURIComponent(location.hash.slice(1));const target=document.getElementById(id);if(!target)return;
 const article=target.closest('article');if(article&&article.hidden){input.value='';search();}
 document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('active',article&&a.hash==='#'+article.id));
}
input.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(search,130)});
document.querySelector('#clear-search').addEventListener('click',()=>{input.value='';search();input.focus()});
document.querySelector('#print').addEventListener('click',()=>window.print());
document.querySelector('#menu').addEventListener('click',()=>{const open=document.body.classList.toggle('nav-open');document.querySelector('#menu').setAttribute('aria-expanded',String(open))});
document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();input.focus()}if(event.key==='Escape'){input.value='';search()}});
document.querySelector('nav').addEventListener('click',event=>{if(event.target.closest('a')){input.value='';search();document.body.classList.remove('nav-open');document.querySelector('#menu').setAttribute('aria-expanded','false')}});
document.addEventListener('click',event=>{const link=event.target.closest('a[href^="#"]');if(!link)return;const target=document.getElementById(decodeURIComponent(link.hash.slice(1)));if(target&&target.closest('article')?.hidden){input.value='';search()}});
window.addEventListener('hashchange',revealHash);search();revealHash();
'''


def identifier(path):
    return 'doc-' + re.sub(r'[^A-Za-z0-9_-]', '-', path)


def check_rendered_markup(content, source):
    """Reject unrendered Markdown in prose without altering code examples."""
    class VisibleProse(HTMLParser):
        def __init__(self):
            super().__init__()
            self.excluded = 0
            self.fragments = []

        def handle_starttag(self, tag, attrs):
            if tag in ('code', 'pre', 'script', 'style'):
                self.excluded += 1

        def handle_endtag(self, tag):
            if tag in ('code', 'pre', 'script', 'style'):
                self.excluded -= 1

        def handle_data(self, data):
            if not self.excluded:
                self.fragments.append(data)

    prose = VisibleProse()
    prose.feed(content)
    pattern = re.compile(r'\*\*|```|!?\[[^\]\n]+\]\([^\)\n]+\)')
    if any(pattern.search(fragment) for fragment in prose.fragments):
        raise ValueError('Unrendered Markdown in visible prose: ' + source + '; fix the Markdown source instead of stripping its symbols')


def load_sources(language='en'):
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported Documentation Builder manifest; use the supplied manifest format')
    english_names = manifest['guides'] + manifest['references']
    translation_names = list(manifest.get('translations', {}).values())
    standalone_names = manifest.get('standalone', [])
    names = english_names + standalone_names if language == 'en' else [manifest['translations'][language]]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate documentation source')
    maintained = {p.relative_to(ROOT).as_posix() for p in ROOT.glob('*.md') if not p.name.endswith('.local.md')}
    maintained.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'docs').rglob('*.md') if not p.name.endswith('.local.md'))
    if maintained - set(english_names + translation_names + standalone_names):
        raise ValueError('Register maintained Markdown in tools/docs_manifest.json: ' + ', '.join(sorted(maintained - set(english_names + translation_names + standalone_names))))
    tree = ast.parse((ROOT / 'scripts/common.py').read_text(encoding='utf-8'))
    version = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'VERSION' for target in node.targets))
    if manifest['code_version'] != version:
        raise ValueError('Documentation code_version must match scripts/common.py VERSION')
    sources = {}
    for name in names:
        path = ROOT / name
        if not name.isascii() or not path.resolve().is_relative_to(ROOT) or path.suffix != '.md' or path.name.endswith('.local.md') or path.is_symlink():
            raise ValueError('Unsafe source: ' + name)
        sources[name] = path.read_text(encoding='utf-8')
    return manifest, sources


def build(language='en'):
    manifest, sources = load_sources(language)
    rendered_names = set(manifest['guides'] + manifest['references']) if language == 'en' else {manifest['translations'][language]}
    labels = dict(LABELS_EN)
    if language != 'en':
        name = manifest['translations'][language]
        metadata = re.match(r'<!-- handbook-ui\n(.*?)\n-->\n*', sources[name], re.S)
        if not metadata:
            raise ValueError('Missing handbook UI metadata')
        labels = json.loads(metadata[1])
        if set(labels) != set(LABELS_EN) or not all(isinstance(v, str) for v in labels.values()):
            raise ValueError('Invalid handbook UI labels')
        sources[name] = sources[name][metadata.end():]
    def label(key):
        return html.escape(labels[key], quote=True)
    md = MarkdownIt('commonmark', {'html': True}).enable('table')
    anchors = {name: set(re.findall(r'<a id="([A-Za-z0-9_-]+)"></a>', raw)) for name, raw in sources.items()}
    errors = []

    def resolve_link(name, target):
        parts = urlsplit(target)
        if parts.scheme or parts.netloc:
            if parts.scheme not in ('https', 'http', 'mailto'):
                errors.append('Unsupported link: ' + name + ' -> ' + target)
            return target
        if not target.isascii():
            errors.append('Non-ASCII reference: ' + name + ' -> ' + target)
        destination = ((ROOT / name).parent / unquote(parts.path)).resolve() if parts.path else ROOT / name
        if not destination.is_relative_to(ROOT) or (not destination.is_file() and destination not in OUTPUTS.values()):
            errors.append('Missing/escaping link: ' + name + ' -> ' + target)
            return target
        relative = destination.relative_to(ROOT).as_posix()
        if parts.fragment and relative in sources and parts.fragment not in anchors[relative]:
            errors.append('Missing explicit anchor: ' + name + ' -> ' + target)
        if relative in rendered_names:
            return '#' + identifier(relative) + ('--' + parts.fragment if parts.fragment else '')
        return relative + ('#' + parts.fragment if parts.fragment else '')

    original_link = md.renderer.rules.get('link_open')
    def link(tokens, index, options, env):
        token = tokens[index]
        token.attrSet('href', resolve_link(env['source'], token.attrGet('href') or ''))
        return original_link(tokens, index, options, env) if original_link else md.renderer.renderToken(tokens, index, options, env)
    md.renderer.rules['link_open'] = link

    def raw_html(tokens, index, options, env):
        value = tokens[index].content
        if re.fullmatch(r'\s*</a>\s*', value):
            return value
        if re.fullmatch(r'\s*<a id="[A-Za-z0-9_-]+">(?:</a>)?\s*', value):
            return re.sub(r'id="([A-Za-z0-9_-]+)"', lambda m: 'id="' + identifier(env['source']) + '--' + m[1] + '"', value)
        return html.escape(value)
    md.renderer.rules['html_inline'] = raw_html
    md.renderer.rules['html_block'] = raw_html

    original_image = md.renderer.rules.get('image')
    def image_rule(tokens, index, options, env):
        token = tokens[index]
        src = token.attrGet('src') or ''
        path = ((ROOT / env['source']).parent / src).resolve()
        if urlsplit(src).scheme or not path.is_relative_to(ROOT) or not path.is_file():
            errors.append('Image must be a local file: ' + src)
        else:
            types = {'.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif'}
            if path.suffix.lower() not in types:
                errors.append('Unsupported image: ' + src)
            else:
                token.attrSet('src', 'data:' + types[path.suffix.lower()] + ';base64,' + base64.b64encode(path.read_bytes()).decode())
        return original_image(tokens, index, options, env)
    md.renderer.rules['image'] = image_rule

    def heading_rule(tokens, index, options, env):
        env['section_number'] += 1
        section_id = identifier(env['source']) + '-section-' + str(env['section_number'])
        title = tokens[index + 1].content
        env['sections'].append((section_id, title))
        if tokens[index].tag == 'h2':
            env['chapters'].append((section_id, title))
        prefix = '</section>' if env['section_number'] > 1 else ''
        return prefix + '<section class="section" id="' + section_id + '" data-title="' + html.escape(title, quote=True) + '">' + md.renderer.renderToken(tokens, index, options, env)
    md.renderer.rules['heading_open'] = heading_rule

    # The bilingual project introduction is checked, but stays outside both
    # single-language handbooks. Links to it remain ordinary file links.
    for name in sorted(set(sources) - rendered_names):
        env = {'source': name, 'section_number': 0, 'sections': [], 'chapters': []}
        check_rendered_markup(md.render(sources[name], env), name)

    chapters, navigation = [], []
    fingerprint = hashlib.sha256()
    fingerprint.update(json.dumps(labels, sort_keys=True, ensure_ascii=True).encode('utf-8'))
    groups = [(labels['guides'], manifest['guides']), (labels['references'], manifest['references'])] if language == 'en' else [(labels['guides'], list(sources))]
    for group, names in groups:
        navigation.append('<div class="nav-group">' + html.escape(group) + '</div>')
        for name in names:
            raw = sources[name]
            title_match = re.search(r'^# (.+)$', raw, re.M)
            title = title_match[1].strip() if title_match else name
            fingerprint.update(name.encode() + b'\0' + raw.encode('utf-8'))
            env = {'source': name, 'section_number': 0, 'sections': [], 'chapters': []}
            # Preserve pre-heading anchors outside the first section.
            content = md.render(raw, env)
            check_rendered_markup(content, name)
            if env['section_number']:
                content += '</section>'
            content = content.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')
            toc = ''.join('<a href="#' + key + '">' + html.escape(title) + '</a>' for key, title in (env['sections'][1:] if language == 'en' else env['chapters']))
            header = '<header><div class="chapter-tag">' + html.escape(group) + '</div><div class="source-link">' + label('source') + ': <a href="' + name + '">' + name + '</a></div>'
            if toc:
                header += '<div class="article-contents" aria-label="' + label('contents') + '">' + toc + '</div>'
            header += '</header>'
            chapters.append('<article id="' + identifier(name) + '" data-title="' + html.escape(title, quote=True) + '" data-source="' + html.escape(name, quote=True) + '">' + header + content + '<a class="back-top" href="#top">' + label('back') + ' ↑</a></article>')
            navigation.append('<a href="#' + identifier(name) + '">' + html.escape(title) + '</a>')
            if language != 'en':
                navigation.extend('<a href="#' + key + '">' + html.escape(text) + '</a>' for key, text in env['chapters'])
    if errors:
        raise ValueError('\n'.join(sorted(set(errors))))
    fingerprint.update(Path(__file__).read_bytes())
    fingerprint.update(MANIFEST.read_bytes())
    logo = 'data:image/svg+xml;base64,' + base64.b64encode((ROOT / 'assets/opensci-icon.svg').read_bytes()).decode()
    version, revision = html.escape(manifest['code_version']), html.escape(manifest['revision'])
    output = '<!doctype html>\n<html lang="' + language + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>' + label('title') + '</title><link rel="icon" href="' + logo + '"><style>' + STYLE + '</style></head><body id="top">'
    output += '<aside aria-label="' + label('navigation') + '"><div class="brand"><img src="' + logo + '" alt="' + label('icon') + '">OpenSci</div><p class="brand-note">' + label('brand') + '<br>v' + version + ' · ' + revision + '</p><nav>' + ''.join(navigation) + '</nav></aside>'
    output += '<div class="workspace"><div class="toolbar"><button id="menu" class="menu-button" aria-expanded="false">' + label('menu') + '</button><div class="search-wrap"><label for="search">' + label('search') + '</label><input id="search" type="search" placeholder="' + label('placeholder') + '" autocomplete="off"><button id="clear-search" title="' + label('clear') + '">' + label('clear') + '</button></div><button id="print" class="print-button">' + label('print') + '</button></div><main>'
    output += '<div class="hero"><div class="eyebrow">' + label('hero') + '</div><h1>' + label('title') + '</h1><p>' + label('description') + '</p><div class="meta">' + label('code') + ' ' + version + ' · ' + label('docs') + ' ' + revision + ' · ' + str(len(rendered_names)) + ' ' + label('sources') + '</div></div>'
    output += '<div id="search-status" class="search-status" role="status" aria-live="polite"></div><section id="search-results" class="search-results" hidden><h2>' + label('results') + '</h2><div id="result-list"></div></section>'
    label_script = 'const labels=' + json.dumps(labels, ensure_ascii=True).replace('<', '\\u003c') + ';\n'
    output += ''.join(chapters) + '<footer class="footer">' + label('footer') + '<br>' + label('fingerprint') + ': ' + fingerprint.hexdigest() + '</footer></main></div><script>' + label_script + SCRIPT + '</script></body></html>\n'
    return output, len(rendered_names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only: validate links and compare generated HTML')
    args = parser.parse_args()
    for language, destination in OUTPUTS.items():
        output, count = build(language)
        expected = output.encode('utf-8')
        if args.check:
            if not destination.is_file() or destination.read_bytes() != expected:
                raise SystemExit(f'{destination.name} is missing or stale. Run tools/build_docs.py first.')
            print(f'Checked {language}: {count} Markdown sources, links and current offline HTML; no writes.')
        else:
            destination.write_bytes(expected)
            print(f'Built {destination.name} from {count} Markdown sources. No network access.')



if __name__ == '__main__':
    main()
