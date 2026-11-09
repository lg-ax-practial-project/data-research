"""Read-only validation of a collection snapshot and prior raw hashes."""
import hashlib, json, sys
from pathlib import Path
from lg_tv_crawler import extract, Tree, has_class

def verify(run):
    rows=[json.loads(s) for s in (run/'processed/articles.jsonl').read_text(encoding='utf-8').splitlines()]
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    for e in manifest:
        if 'raw_path' in e:
            assert hashlib.sha256((run/e['raw_path']).read_bytes()).hexdigest()==e['sha256'], e['source_id']
    for a in rows:
        raw=(run/'raw'/(a['source_id']+'.html')).read_text(encoding='utf-8')
        b=extract(raw,a['url'])
        for field in ('text','faqs','content_blocks','image_alts','page_date_candidates'):
            assert a[field]==b[field], (a['source_id'],field)
        if a['type']=='official_tv_faq_catalog':
            item_count=sum(has_class(n,'machine-faq__item') for n in Tree(raw).root.walk())
            assert item_count==len(a['faqs'])
    assert len({a['url'] for a in rows})==len(rows)
    return {'run':str(run),'documents_verified':len(rows),'faqs_verified':sum(len(a['faqs']) for a in rows),'raw_hashes_match':True,'reextraction_matches':True,'faq_catalog_items_all_paired':True,'site_coverage_complete':False}

if __name__=='__main__':
    run=Path(sys.argv[1]); result=verify(run)
    if len(sys.argv)>2:
        prior=Path(sys.argv[2]); count=0
        for path in prior.glob('*/manifest.json'):
            if path.parent==run: continue
            for e in json.loads(path.read_text(encoding='utf-8')):
                if 'raw_path' in e:
                    assert hashlib.sha256((path.parent/e['raw_path']).read_bytes()).hexdigest()==e['sha256']
                    count+=1
        result['prior_raw_files_unchanged']=count
    print(json.dumps(result,ensure_ascii=False))
