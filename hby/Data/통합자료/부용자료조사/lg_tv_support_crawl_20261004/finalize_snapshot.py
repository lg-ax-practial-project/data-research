"""Generate derived FAQ subsets and verification report; preserve raw snapshots."""
import json, sys
from pathlib import Path
from verify_collection import verify
import hashlib

root=Path(sys.argv[1]); run=Path(sys.argv[2])
rows=[json.loads(s) for s in (run/'processed/faqs.jsonl').read_text(encoding='utf-8').splitlines()]
for filename,kind in [('faq_catalog.jsonl','official_tv_faq_catalog'),('self_help_faqs.jsonl','official_self_help')]:
    target=run/'processed'/filename
    content=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows if r['source_type']==kind)
    if target.exists(): assert target.read_text(encoding='utf-8')==content
    else: target.write_text(content,encoding='utf-8')
result=verify(run)
count=0
for path in (root/'runs').glob('*/manifest.json'):
    if path.parent==run: continue
    for e in json.loads(path.read_text(encoding='utf-8')):
        if 'raw_path' in e:
            assert hashlib.sha256((path.parent/e['raw_path']).read_bytes()).hexdigest()==e['sha256']
            count+=1
result.update(prior_raw_files_unchanged=count,faq_catalog_pairs=sum(r['source_type']=='official_tv_faq_catalog' for r in rows),self_help_faq_pairs=sum(r['source_type']=='official_self_help' for r in rows))
out=root/'repair_20261005'/'verification.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
