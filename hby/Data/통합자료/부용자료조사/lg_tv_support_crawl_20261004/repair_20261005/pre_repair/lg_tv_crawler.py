"""Bounded official LG TV collector and loopback-only n8n bridge (stdlib only)."""
import argparse, hashlib, json, re, time, threading
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = 'https://www.lge.co.kr'
UA = 'CXPlanningTVResearch/1.0 (manual bounded public support collection)'
SEEDS = ['1777897', '20152183148933', '20150903914041', '20150195460917', '20155301642915', '20152087489076', '20150371175052', '20153749094807', '1777854', '1333004114799', '1300176600136', '20151952645799', '20152081551580']
LOCK = threading.Lock()

class Element:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c, Element): yield from c.walk()
    def text(self):
        if self.tag in ('script', 'style', 'noscript'): return ''
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

def extract(html, url):
    nodes = list(Tree(html).root.walk())
    title = next((n.text().split(' | ')[0] for n in nodes if n.tag == 'title'), '')
    if not re.search(r'\bTV\b|텔레비전|올레드', title, re.I): raise ValueError('Non-TV title excluded: '+title)
    # Require the official solution article container; never use whole-page text.
    candidates = [n for n in nodes if any(x in n.attrs.get('class','').split() for x in ('view-content','view-con','view-contents','solution-content','editor-content','detail-content'))]
    if not candidates: raise ValueError('Article selector not found; manual review required')
    body = max(candidates, key=lambda n: len(n.text()))
    text = body.text()
    if len(text) < 100: raise ValueError('Empty or truncated article')
    faqs = []
    for n in body.walk():
        if n.tag == 'dl':
            q = next((c.text() for c in n.walk() if c.tag == 'dt'), '')
            a = next((c.text() for c in n.walk() if c.tag == 'dd'), '')
            if q and a: faqs.append({'question':q,'answer':a})
    dates = re.findall(r'20\d{2}[.\-]\d{2}[.\-]\d{2}', html)
    media = sorted({n.attrs.get('src','') for n in body.walk() if n.tag in ('img','iframe') and n.attrs.get('src','').startswith('https://')})
    return {'source_id':url.rsplit('-',1)[1], 'url':url,'title':title,'provider':'LG전자','type':'official_self_help',
            'page_date_candidates':sorted(set(dates)), 'page_date_status':'manual verification required',
            'text':text,'faqs':faqs,'media_urls':media,'extraction_selector':body.attrs.get('class',''),
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
    for sid in SEEDS:
        url=BASE+'/support/solutions-'+sid
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
        except Exception as exc: entry.update(status='needs_review',error=str(exc))
        manifest.append(entry)
    (processed/'articles.jsonl').write_text(''.join(json.dumps(a,ensure_ascii=False)+'\n' for a in articles),encoding='utf-8')
    faqs=[dict(source_id=a['source_id'],url=a['url'],retrieved_at=a['retrieved_at'],**q) for a in articles for q in a['faqs']]
    (processed/'faqs.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in faqs),encoding='utf-8')
    write_json(run/'manifest.json',manifest)
    integrity=all(hashlib.sha256((run/e['raw_path']).read_bytes()).hexdigest()==e['sha256'] for e in manifest if 'raw_path' in e)
    result={'run':str(run),'seed_count':len(SEEDS),'article_count':len(articles),'faq_count':len(faqs),'review_count':sum(e['status']!='extracted' for e in manifest),'raw_hashes_verified':integrity,'coverage':'Curated public TV URLs; not the entire LG FAQ catalog'}
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
