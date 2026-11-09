"""Bounded official LG TV collector and loopback-only n8n bridge (stdlib only)."""
import argparse, hashlib, json, re, time, threading
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = 'https://www.lge.co.kr'
UA = 'CXPlanningTVResearch/1.0 (manual bounded public support collection)'
SEEDS = ['1777897', '20152183148933', '20150903914041', '20150195460917', '20155301642915', '20152087489076', '20150371175052', '20153749094807', '1777854', '1333004114799', '1300176600136', '20151952645799', '20152081551580']
LOCK = threading.Lock()
FAQ_URL = BASE + '/story/faq/tvs-faq'
CONFIG = Path(__file__).with_name('collection_sources.json')
PARSER_VERSION = '2.0'

class Element:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c, Element): yield from c.walk()
    def text(self):
        if self.tag in ('script', 'style', 'noscript'): return ''
        if self.tag == 'img': return self.attrs.get('alt', '').strip()
        parts = [c.text() if isinstance(c, Element) else c for c in self.children]
        return ' '.join(' '.join(parts).split())

class Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Element(); self.stack = [self.root]; self.feed(html)
    def handle_starttag(self, tag, attrs):
        el = Element(tag, attrs); self.stack[-1].children.append(el)
        if tag not in ('img','br','hr','meta','link','input','source','area','embed','wbr'): self.stack.append(el)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]; break
    def handle_data(self, data): self.stack[-1].children.append(data)

def has_class(node, name):
    return name in node.attrs.get('class', '').split()

def blocks(node):
    """Retain source block order and element type, including table cells and alt text."""
    result = []
    leaf_blocks = {'p', 'li', 'dt', 'dd', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr'}
    def visit(n):
        if n.tag in ('script', 'style', 'noscript'): return
        if n.tag in leaf_blocks and n.text():
            row = {'type': n.tag, 'text': n.text()}
            if n.tag == 'tr': row['cells'] = [c.text() for c in n.children if isinstance(c, Element) and c.tag in ('td', 'th')]
            result.append(row)
            return
        if n.tag == 'img' and n.text(): result.append({'type': 'image_alt', 'text': n.text()})
        for c in n.children:
            if isinstance(c, Element): visit(c)
    visit(node)
    return result

def faq_pairs(body):
    pairs = []
    issues = []
    for dl in body.walk():
        if dl.tag != 'dl': continue
        q, answers = None, []
        def flush():
            if q and answers: pairs.append({'question': q, 'answer': ' '.join(answers), 'category': None})
            elif q: issues.append('Unmatched dt: ' + q)
        for c in dl.children:
            if not isinstance(c, Element): continue
            if c.tag == 'dt':
                flush(); q, answers = c.text(), []
            elif c.tag == 'dd':
                if q: answers.append(c.text())
                else: issues.append('Unmatched dd')
        flush()
    return pairs, issues

def extract(html, url):
    nodes = list(Tree(html).root.walk())
    title = next((n.text().split(' | ')[0] for n in nodes if n.tag == 'title'), '')
    is_catalog = url.split('?')[0] == FAQ_URL
    if not is_catalog and not re.search(r'(?<![A-Za-z])TV(?![A-Za-z])|텔레비전|올레드', title, re.I): raise ValueError('Non-TV title excluded: '+title)
    # Require the official solution article container; never use whole-page text.
    selectors = ('machine-faq__detail-content',) if is_catalog else ('view-content','view-con','view-contents','solution-content','editor-content','detail-content')
    candidates = [n for n in nodes if any(has_class(n, x) for x in selectors)]
    if not candidates: raise ValueError('Article selector not found; manual review required')
    body = max(candidates, key=lambda n: len(n.text()))
    text = body.text()
    if len(text) < 100: raise ValueError('Empty or truncated article')
    faqs, issues = faq_pairs(body)
    if is_catalog:
        items = [n for n in body.walk() if has_class(n, 'machine-faq__item')]
        for item in items:
            qnode = next((n for n in item.walk() if has_class(n, 'machine-faq__title')), None)
            anode = next((n for n in item.walk() if has_class(n, 'machine-faq__content')), None)
            category = next((n.text().removeprefix('카테고리').strip() for n in item.walk() if has_class(n, 'machine-faq__category')), None)
            if qnode and anode and 'Q.' in qnode.text() and anode.text():
                faqs.append({'question': 'Q.' + qnode.text().split('Q.', 1)[1], 'answer': anode.text().removeprefix('답변').strip(), 'category': category})
            else: issues.append('FAQ item missing question or answer')
        if not items: raise ValueError('FAQ catalog item selector not found')
    date_nodes = [n for n in nodes if has_class(n, 'head-infos')]
    dates = [d for n in date_nodes for d in re.findall(r'20\d{2}[.\-]\d{2}[.\-]\d{2}', n.text())]
    media = sorted({urljoin(url,n.attrs.get('src','')) for n in body.walk() if n.tag in ('img','iframe') and n.attrs.get('src')})
    return {'source_id':'tvs-faq' if is_catalog else url.rsplit('-',1)[1], 'url':url,'title':title,'provider':'LG전자','type':'official_tv_faq_catalog' if is_catalog else 'official_self_help',
            'page_date_candidates':sorted(set(dates)), 'page_date_status':'manual verification required',
            'text':text,'content_blocks':blocks(body),'faqs':faqs,'extraction_issues':issues,'media_urls':media,'image_alts':[{'url':urljoin(url,n.attrs.get('src','')),'alt':n.text()} for n in body.walk() if n.tag=='img'], 'extraction_selector':body.attrs.get('class',''), 'parser_version':PARSER_VERSION,
            'limitations':['Not a customer incident or frequency statistic','Model-specific applicability requires review','Not a confirmed diagnosis or compensation decision']}

def fetch(url):
    with urlopen(Request(url, headers={'User-Agent':UA}), timeout=30) as response:
        if response.status != 200: raise ValueError('HTTP '+str(response.status))
        final = response.geturl()
        if not final.startswith(BASE+'/'): raise ValueError('Off-domain redirect')
        return response.read(5_000_001), final

def write_json(path, data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def collect(output):
    output = Path(output).resolve()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run = output/'runs'/stamp; raw=run/'raw'; processed=run/'processed'
    raw.mkdir(parents=True); processed.mkdir()
    robots, _ = fetch(BASE+'/robots.txt'); (raw/'robots.txt').write_bytes(robots)
    rp=RobotFileParser(); rp.parse(robots.decode('utf-8').splitlines())
    manifest=[]; articles=[]
    config = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {'additional_urls': [], 'max_documents': 30}
    max_documents = min(40, max(14, int(config.get('max_documents', 30))))
    queue = [FAQ_URL] + [BASE+'/support/solutions-'+sid for sid in SEEDS] + config.get('additional_urls', [])
    queue = list(dict.fromkeys(queue))
    discovered = []
    def allowed_url(url):
        return url == FAQ_URL or bool(re.fullmatch(re.escape(BASE)+r'/support/solutions-\d+', url))
    initial_count = len(queue)
    for url in queue:
        if len(manifest) >= max_documents: break
        if not allowed_url(url):
            discovered.append({'url':url,'status':'excluded_unsupported_url'}); continue
        sid = 'tvs-faq' if url == FAQ_URL else url.rsplit('-', 1)[1]
        entry={'source_id':sid,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat()}
        try:
            if not rp.can_fetch(UA,url): raise ValueError('Blocked by robots.txt')
            time.sleep(2)
            data, final=fetch(url)
            if len(data)>5_000_000: raise ValueError('Response too large')
            (raw/(sid+'.html')).write_bytes(data)
            entry.update(raw_path='raw/'+sid+'.html',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),final_url=final)
            article=extract(data.decode('utf-8'),url)
            article.update(retrieved_at=entry['retrieved_at'],raw_sha256=entry['sha256'])
            articles.append(article); entry['status']='extracted'
            if article['extraction_issues']: entry['status']='needs_review'
            # Discover only observed public links, never invent IDs or private API endpoints.
            if url == FAQ_URL:
                for n in Tree(data.decode('utf-8')).root.walk():
                    if n.tag != 'a': continue
                    link = urljoin(url,n.attrs.get('href','')).split('?')[0].split('#')[0]
                    if allowed_url(link) and link != FAQ_URL and link not in queue:
                        queue.append(link); discovered.append({'url':link,'discovered_from':url,'status':'queued'})
        except Exception as exc: entry.update(status='needs_review',error=str(exc))
        manifest.append(entry)
    (processed/'articles.jsonl').write_text(''.join(json.dumps(a,ensure_ascii=False)+'\n' for a in articles),encoding='utf-8')
    faqs=[dict(source_id=a['source_id'],url=a['url'],source_type=a['type'],raw_sha256=a['raw_sha256'],retrieved_at=a['retrieved_at'],faq_index=i,**q) for a in articles for i,q in enumerate(a['faqs'],1)]
    (processed/'faqs.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in faqs),encoding='utf-8')
    for filename, source_type in [('faq_catalog.jsonl','official_tv_faq_catalog'),('self_help_faqs.jsonl','official_self_help')]:
        (processed/filename).write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in faqs if q['source_type']==source_type),encoding='utf-8')
    write_json(run/'manifest.json',manifest)
    write_json(run/'discovery.json',{'list_url':BASE+'/support/solutions','faq_url':FAQ_URL,'initial_count':initial_count,'candidate_urls':queue,'links_discovered':discovered,'not_attempted':queue[len(manifest):], 'site_total':None,'coverage_complete':False,'limitation':'Public list needs product selection; not an exhaustive TV inventory'})
    integrity=all(hashlib.sha256((run/e['raw_path']).read_bytes()).hexdigest()==e['sha256'] for e in manifest if 'raw_path' in e)
    result={'run':str(run),'seed_count':initial_count,'article_count':len(articles),'self_help_count':sum(a['type']=='official_self_help' for a in articles),'faq_catalog_count':sum(a['type']=='official_tv_faq_catalog' for a in articles),'faq_count':len(faqs),'review_count':sum(e['status']!='extracted' for e in manifest),'raw_hashes_verified':integrity,'parser_version':PARSER_VERSION,'coverage_complete':False,'coverage':'One official TV FAQ page, curated TV self-help and observed FAQ links; not exhaustive site coverage'}
    write_json(run/'validation.json',result)
    return result

def serve(output, port):
    class Handler(BaseHTTPRequestHandler):
        def send(self, code, obj):
            data=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        def do_GET(self): self.send(200 if self.path=='/health' else 404, {'ready':self.path=='/health'})
        def do_POST(self):
            if self.path!='/collect' or self.headers.get('X-LG-Crawler')!='manual-local': return self.send(403,{'error':'Not allowed'})
            if int(self.headers.get('Content-Length','0'))>1024: return self.send(413,{'error':'Body too large'})
            if not LOCK.acquire(blocking=False): return self.send(409,{'error':'Collection already running'})
            try: self.send(200,collect(output))
            except Exception as exc: self.send(500,{'error':str(exc)})
            finally: LOCK.release()
        def log_message(self, *args): pass
    print('Loopback collector ready on port '+str(port),flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True); parser.add_argument('--serve',action='store_true'); parser.add_argument('--port',type=int,default=8766); parser.add_argument('--inspect',action='store_true'); args=parser.parse_args()
    if args.inspect:
        data,_=fetch(BASE+'/support/solutions-1777897'); tree=Tree(data.decode()).root
        print(json.dumps([(n.tag,n.attrs.get('class',''),len(n.text())) for n in tree.walk() if 'qna-list' in n.attrs.get('class','') or any(x in n.attrs.get('class','') for x in ['view-con','detail-con','editor'])],ensure_ascii=False))
    elif args.serve: serve(args.output,args.port)
    else: print(json.dumps(collect(args.output),ensure_ascii=False))
