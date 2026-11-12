"""Offline evidence curation only. No network, embeddings, search, or cost calculation.

The format is personal research data, not the team's shared API schema.
Usage: python curate_evidence_20261013.py --source-root BUNDLE --output-root BUNDLE
"""
from pathlib import Path
import argparse, collections, hashlib, html, json, re
import xml.etree.ElementTree as ET

p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True)
args=p.parse_args();root=args.source_root;out=args.output_root
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
encode=lambda value:json.dumps(value,ensure_ascii=False,indent=2)+'\n'
def write(rel,text):
 path=out/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
def dump(rel,value):write(rel,encode(value))
def read(rel):return (root/rel).read_text(encoding='utf-8-sig')
manifest=json.loads(read('metadata/source_manifest.json'));sources={s['id']:s for s in manifest['sources']}
assert len(sources)==30
for s in sources.values():
 for k,h in [('raw_capture','raw_sha256'),('markdown_capture','markdown_sha256'),('html_capture','html_sha256'),('raw_pdf','raw_pdf_sha256')]:
  if k in s:assert sha(root/s[k])==s[h],(s['id'],k)

groups={
 'dispute_reference':('분쟁해결기준·적용 성격. LG의 실제 승인/계산 규칙으로 대체하지 않음',['FTC-LAW-001','KCA-CRITERIA-001']),
 'product_reference':('구독 운영 확인용 상품 목록. 실시간 가격이나 계약정책 색인에서 분리',['LG-AIR-CATEGORY-001']),
 'cx_only':('CX통계/확보 경로. 정책 검색 색인에서 제외',['KCA-SUBSCRIPTION-REPORT-001','KCA-REDRESS-METADATA-001','KCA-COUNSEL-MONTHLY-METADATA-001','FTC-1372-DETAIL-API-001']),
 'historical_reference':('과거 개정/시정 이력. 현행 계약정책으로 자동 적용 금지',['LG-RENTAL-NOTICE-2022-001','LG-RENTAL-REVISION-2022-001','LG-TERMS-NOTICE-2021-001','FTC-RENTAL-CORRECTION-2021-001']),
 'general_terms_reference':('일반 웹서비스·상거래 약관. 구독 개별약관을 대체하지 않음',['LG-SERVICE-TERMS-PUBLIC-001','LG-ECOM-TERMS-PUBLIC-001']),
 'excluded_from_air_policy':('버전 미확정 약관 또는 타제품/타사 사례. 공기청정기 정책 후보에서 제외',['LG-RENTAL-TERMS-LINKED-001','KCA-STANDARD-2025-001','KCA-CASE-2008-001'])}
routes={sid:(key,note) for key,(note,ids) in groups.items() for sid in ids}
for sid in sources:routes.setdefault(sid,('policy_candidate','공식 공개 안내의 조건부 검색 후보. 문서 전체 자동 색인 금지; 검토된 근거 단위만 사용 검토'))
assert len(routes)==30

def document(sid,rel=None):
 rel=rel or sources[sid]['markdown_capture']
 return dict(source_id=sid,path=rel,text=read(rel),locator={'format':'markdown'},file_sha256=sha(root/rel))
def pdf_document(page):
 rel='metadata/pdf_relevant_pages.json';d=json.loads(read(rel));key='공정거래위원회_소비자분쟁해결기준_20251218.pdf';entry=d[key]
 item=next(x for x in entry['pages'] if x['physical_page']==page)
 assert sha(root/entry['path'])==entry['sha256']
 return dict(source_id='FTC-LAW-001',path=rel,text=item['text'],file_sha256=sha(root/rel),locator={'format':'cached_pdf_page_text','json_key':key,'physical_page':page,'original_pdf':entry['path'],'original_pdf_sha256':entry['sha256']})
def span(doc,start,end=None,include_end=False,occurrence=0):
 text=doc['text'];positions=[m.start() for m in re.finditer(re.escape(start),text)]
 assert len(positions)>occurrence,(doc['source_id'],start)
 a=positions[occurrence];z=len(text) if end is None else text.index(end,a+len(start))+(len(end) if include_end else 0)
 while z>a and text[z-1].isspace():z-=1
 assert z>a
 return dict(kind='verbatim',source_id=doc['source_id'],capture_path=doc['path'],capture_sha256=doc['file_sha256'],locator=doc['locator'],start_character=a,end_character_exclusive=z,start_line=text.count('\n',0,a)+1,quote=text[a:z],quote_sha256=hashlib.sha256(text[a:z].encode()).hexdigest())
def exact(doc,text):
 pos=doc['text'].index(text)
 return dict(kind='verbatim',source_id=doc['source_id'],capture_path=doc['path'],capture_sha256=doc['file_sha256'],locator=doc['locator'],start_character=pos,end_character_exclusive=pos+len(text),start_line=doc['text'].count('\n',0,pos)+1,quote=text,quote_sha256=hashlib.sha256(text.encode()).hexdigest())
def section(doc,heading):
 a=doc['text'].index(heading);n=re.search(r'\n###? ',doc['text'][a+len(heading):])
 end=None if not n else doc['text'][a+len(heading)+n.start():].split('\n',2)[1]
 return span(doc,heading,end)

units=[]
def add(title,topic,segments,conditions,missing,notes,product_scope='air_purifier_or_common',contract_kind='appliance_subscription',groups=None):
 n=len(units)+1;ids=list(dict.fromkeys(s['source_id'] for s in segments))
 assert all(routes[s][0] in ['policy_candidate','dispute_reference'] for s in ids)
 u=dict(evidence_id=f'MC-E{n:03}',title=title,topic=topic,source_ids=ids,
  official_sources=[{'id':s,'title':sources[s]['document_name'],'issuer':sources[s]['issuer'],'url':sources[s]['url'],'captured_on':sources[s]['collected_on_kst'],'source_status':sources[s]['status']} for s in ids],
  date_records=[{'source_id':s,**{k:sources[s].get(k) for k in ['published_at','updated_at','effective_date','policy_reference_date','information_as_of','distribution_date','contract_date_scope']}} for s in ids],
  curated_on_kst='2026-10-13',freshness='2026-10-12 보존 자료에서 정제;2026-10-13 웹 재검증 아님',
  product_scope=product_scope,contract_kind=contract_kind,segments=segments,
  curation_notes={'conditions_to_keep':conditions,'missing_contract_context':missing,'interpretation_and_limits':notes},
  related_evidence_ids=[],review_groups=groups or [],curation_status='draft_reviewed_for_provenance',index_approved=False,can_determine_customer_cost=False,
  source_and_interpretation_separated=True)
 units.append(u);return u['evidence_id']

faq=document('LG-FAQ-001');guide=document('LG-AIR-GUIDE-001');service=document('LG-SERVICE-001');product=document('LG-AIR-PRODUCT-001');care=document('LG-CARE-ABOUT-001')
criteria=document('KCA-CRITERIA-001');best=document('LG-BESTSHOP-CARE-GUIDE-001');compare=document('LG-AIR-CARE-COMPARISON-001');plan=document('LG-AIR-PLAN-GUIDE-001');cat=document('LG-CATALOGUE-20260226-001');lx=document('LX-RELOCATION-PRICE-001')
add('공기청정기 회수비39,000원과 계약서 기준','recovery_fee',[
 span(faq,'\\- 회수비 :','※ 제품별 회수비'),exact(faq,'공기청정기/가습기/제습기 39,000원'),span(faq,'※ 상기금액은','추가 궁금하신 사항은')],
 ['총 계약기간 내 고객 임의 해지','2026-03-24는 안내 기준일','계약서 금액 확인','다른 제품 금액 제외'],['계약성립일','계약서 회수비','약관버전'],'35,000원 자료와 함께 보여야 한다. 최신 수집일만으로 자동 선택하지 않는다.',groups=['recovery_fee_version'])
add('공기청정기 회수비35,000원과2021-11-05 이후 계약 문구','recovery_fee',[
 span(guide,'- **② 회수비 :** 의무 사용 기간 경과 여부와 관계없이 총계약 기간','- 제품별 회수비'),exact(guide,'공기청정기 35,000원'),span(guide,'- 상기 금액은 2021년 11월 5일','- **③ 소모성 부품 비용'),span(guide,'- 계약 후 고객의 요청으로 임의 해지하는 경우','- 추가로 궁금한 사항은')],
 ['안내에 표시된2021-11-05 이후 계약','종료/전환일 미확인','계약서 금액 확인'],['해당 계약 버전','35,000/39,000 전환 근거'],'계약일이2021-11-05 이후라는 조건만으로 현재 모든 계약에35,000원을 적용하지 않는다.',groups=['recovery_fee_version'])
add('LG 중도해지 위약금·2년 상품 예외·부대비용','termination_rate',[
 span(guide,'- **해약금 정산 기준(아래 항목의 합계)**','- **④ 현금성 사은품'),span(guide,'- **④ 현금성 사은품','- **⑤',False) if '- **⑤' in guide['text'] else exact(guide,'- **④ 현금성 사은품 :** 사은품 액면 금액 / **비현금성 사은품 :** LG전자 사은품 구매 단가 기준 적용')],
 ['할인 전 기본요금','1년/2년 사용 경과 기준','계약기간2년 상품20/10 예외','위약금 외 항목 구분'],['총기간/의무기간','정확한 해지일','계약버전','원 단위 처리'],'고시와 권한/적용 성격이 다르다. 계산식 실행·비율 선택은 하지 않는다.',groups=['lg_vs_dispute_criteria'])
pg69=pdf_document(69);pg70=pdf_document(70)
add('고시 장기 물품대여: 의무기간별 위약금·별도 비용 조건','dispute_termination',[
 span(pg69,'4) 소비자의 귀책사유로 인한 계약해지')],
 ['의무사용기간 유무와1년 이하/초과 구분','철거비 청구사실·금액의 계약 고지','장기유지 할인 잔여기간 정산'],['계약유형','의무기간/임대차기간','적용 고시/계약 관계'],'고시의 합의/권고 성격도 함께 확인. LG규칙을 자동 대체하지 않는다.',product_scope='long_term_rental_including_applicable_appliances',groups=['lg_vs_dispute_criteria'])
add('고시 이사·해외 이주 예외와 별도 비용','relocation_waiver',[
 span(pg70,'12) 계약기간 이내에 다른 지역으로 이사 시'),span(pg69,'* 위약금과 별도로','* 장기유지조건')],
 ['정기관리가 안 되는 지역/본래 기능 상실 우려/해외 이주 구분','해외 이주 관련 자료 제출','위약금과 별도 비용 구분'],['방문/자가관리','LG실제 관리 가능 판정','인정증빙','계약 적용'],'표 순서상 국내 두 사유는 위약금 없이 해지, 해외는50%감면이다. LG승인 완료 또는 전체비용0원을 뜻하지 않는다.',product_scope='long_term_rental_including_applicable_appliances',groups=['waiver_scope'])
add('분쟁해결기준의 적용 성격','dispute_criteria_scope',[
 span(criteria,'- 소비자와 사업자 사이에 발생하는 분쟁','- **소비자분쟁해결기준**')],
 ['합의 또는 권고 기준','별도의 의사표시/다른 법령/복수기준 조건'],['분쟁/계약 적용 관계'],'약관이 없을 때 확정 견적을 만드는 대체 계산표로 사용하지 않는다.',product_scope='general_consumer_dispute',groups=['lg_vs_dispute_criteria','waiver_scope'])
add('예시상품 계약 성립과 해약금 안내','contract_formation',[
 span(product,'- 상품 인도/설치 후 계약이 성립되며','- 제휴카드는')],
 ['상품 인도/설치 후 성립','고객 임의 해지·귀책/비정상 거래 조건','본 계약서 상세 확인'],['선정모델','계약성립일','채널','약관버전'],'AS192DSFAM은 예시이며 팀의 최종 모델로 확정하지 않았다.',product_scope='AS192DSFAM_example')
add('결합상품 일부 해지 시 남은 제품 요금','bundle_discount',[
 span(product,'- 결합상품 할인은 두 제품 이상','- 계약자 명의변경')],
 ['일부해지·명의변경·만기 등 후 한 제품만 잔존','다음달 정상요금','당월1~4일 예외'],['결합제품 수','해지 기준일','각 계약 할인 조건'],'남은 구독료 비교 시 검토할 조건. 이 자료로 실제 청구일이나 총금액을 확정하지 않는다.',product_scope='AS192DSFAM_example')
add('설치 후 타입 변경과 단순변심 제한','contract_type_change',[
 span(product,'- 제품 인수(설치) 완료 후에는 단순 변심','- 배송지역: 전국')],
 ['단순 변심이라는 원문 한정','방문/무방문 타입 변경','일시불 구매 변경','계약/약관 참조'],['거래유형','설치일','변경/철회 사유'],'법정 예외를 포함해 모든 청약철회가 불가하다고 일반화하지 않는다.',product_scope='AS192DSFAM_example',groups=['withdrawal_scope'])
add('만기 소유권 이전과3년 약정 예외','ownership_at_maturity',[
 span(service,'- **소유권 이전**','## 구독하면')],
 ['총 계약기간','3년 약정 별도 선택','전자칠판/마이컵 제외','일반 판매가10% 선택과 반납 선택','케어십 별도 신청'],['선정모델의3년 계약 적용','기준 판매가','반납 비용'],'반납0원 또는 모든 계약 만기 무조건 무상소유로 답하지 않는다.',groups=['ownership_scope'])
add('계약자와 실사용자·인수정보 변경','address_and_user',[
 section(service,'### Q계약자와 실사용자가 다른 경우 어떻게 변경할 수 있을지 궁금해요.')],
 ['인수정보 변경과 계약 명의 변경 구분','계약자 책임','제3자 상담/실사용자 등록 조건'],['계약자 승인','변경할 정보 종류'],'실제 주소 변경 처리나 예약을 실행한 근거가 아니다.')
add('해지 신청·정산 항목 안내','termination_process',[
 section(service,'### Q가전 구독 계약 해지시 어떻게 되는지 궁금해요.')],
 ['상담 후 해지 처리','해약금 항목','장기미납 조건','약정할인/선납 선택 조건'],['계약별 청구내역','해지 효력일','미납/선납/할인내역'],'항목 전부가 모든 계약에 발생한다는 뜻이 아니다. 자동 합산 규칙으로 사용하지 않는다.')
add('공식 보이는ARS 주소변경·방문 요청 경로','service_channel',[
 span(care,'원하는 시간에 고객센터(1544-7777)','### 고객센터에 전화')],
 ['구독/케어십 가입자 및 개인 고객','주소변경·매니저 방문요청 등 지원','본인인증'],['실제 이용자 자격'],'안내 채널 정보. 운영시간·앱 상세는 사용 시 재확인하며 실제 처리 완료를 주장하지 않는다.')
add('2026년4월 무상 재설치 대상·철거 지원·운송 제외','relocation_benefit',[
 span(best,'### 무상 재설치 대상 제품 및 조건','## 가전 구독 가격')],
 ['대상 제품 목록','계약기간 내1회','철거 지원 제품','제품 이동/운송 제외'],['공기청정기 별도혜택','선정계약 적용'],'공기청정기는 이 표의 대상 목록에 없다. 모든 과거 계약의 혜택 부재로 단정하지 않는다.',product_scope='listed_products_not_air_purifier',groups=['free_relocation_scope'])
add('에어케어 비교표의 무상 이전 대상 제한','relocation_benefit',[
 exact(compare,'| 무상 철거/재설치 | 없음 | 스탠드/벽걸이 에어컨 계약기간 내 1회 제공 |'),span(compare,'- **무상 재설치**','- **무상 A/S**')],
 ['비교표는 스탠드/벽걸이 에어컨 명시','본문 별도 대상 목록','운송 제외'],['공기청정기 선정계약 혜택'],'같은 페이지의 상충하는 중도해지 소유권 문단은 별도 제외목록에 둔다.',product_scope='listed_products_not_air_purifier',groups=['free_relocation_scope'])

xmlrel='raw/additional_02/LX-RELOCATION-PRICE-001.public-response.xml';tree=ET.fromstring(read(xmlrel));fields=['attribute1','cdNm','olType2Nm','rmvSaleCost','instSaleCost','mvSaleCost']
columns={f:[n.text or '' for n in tree.findall('.//'+f)] for f in fields};assert all(len(v)==78 for v in columns.values())
rows=[dict(zip(fields,vals)) for vals in zip(*(columns[f] for f in fields))];indexes=[i for i,r in enumerate(rows) if r['cdNm']=='공기청정기'];assert indexes==[71]
row=rows[71];assert [row[x] for x in fields[3:]]==['24,000','34,000','98,000']
price=dict(kind='normalized_table',source_id='LX-RELOCATION-PRICE-001',capture_path=xmlrel,capture_sha256=sha(root/xmlrel),locator={'format':'parallel_xml_columns','record_number_1based':72,'row_count':78,'column_mapping_reference':'metadata/air_relocation_price_review_02.json','column_mapping_sha256':sha(root/'metadata/air_relocation_price_review_02.json')},
 table={'headers':['품목','철거비용','설치비용','이전설치(철거+설치+기본운송4만원)'],'rows':[[row['cdNm'],row['rmvSaleCost'],row['instSaleCost'],row['mvSaleCost']]],'unit':'원','raw_fields':row},normalization='공개XML의 동일 순번6열을 결합. 금액 계산·수정 없음.')
add('공기청정기 일반 이전설치 표준요금 행','general_relocation_price',[price,span(lx,'※ 운송비용 안내','※ LG 멤버십 포인트')],
 ['기본운송0~10km미만','일반 유상 이전설치 표','장거리 조건 별도'],['모델/거리/현장비','구독혜택','실제견적','세금/거리 경계 처리'],'98,000원을 해지 회수비나 모든 구독 유지 비용으로 쓰지 않는다.',groups=['general_relocation_price_scope'])
add('일반 이전설치 운송·현장 추가 조건','general_relocation_conditions',[
 span(lx,'※ 운송비용 안내','닫기')],
 ['거리별 운송비','일부 장거리 이동 불가','작업 불가 출장비','다수량 할인 제외품목','온라인접수 제한 품목'],['실제 작업/모델/거리','기사 확인'],'정기 방문관리 가능 지역과 이전설치 가능 지역은 다른 정보다.',groups=['general_relocation_price_scope'])

gj=json.loads(read('raw/LG-AIR-GUIDE-001.firecrawl.json'));gh=gj['html'];tables=[m for m in re.finditer(r'<table\b.*?</table>',gh,re.S) if '정기 케어 주기' in m.group()];assert len(tables)==1
match=tables[0]
def clean(t):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>','',t))).strip()
header=clean(match.group().split('</thead>')[0]);positions=[header.index(x) for x in ['프리미엄','라이트플러스','베이직']];assert positions==sorted(positions)
tr=[re.findall(r'<td\b[^>]*>(.*?)</td>',r,re.S) for r in re.findall(r'<tr\b[^>]*>(.*?)</tr>',match.group(),re.S)]
grid=[[clean(c) for c in row] for row in tr if row];assert len(grid)==6 and all(len(r)==4 for r in grid)
assert grid[1]==['정기 케어 주기','3/6개월','3/6개월','해당 없음']
assert grid[0][1:]==['3/4/5/6년형']*3
guide_table=dict(kind='normalized_table',source_id='LG-AIR-GUIDE-001',capture_path='raw/LG-AIR-GUIDE-001.firecrawl.json',capture_sha256=sha(root/'raw/LG-AIR-GUIDE-001.firecrawl.json'),
 locator={'format':'html_table_in_json','json_field':'html','start_character':match.start(),'end_character_exclusive':match.end(),'html_table_sha256':hashlib.sha256(match.group().encode()).hexdigest()},
 table={'headers':['항목','프리미엄','라이트플러스','베이직'],'rows':grid},normalization='구분용rowspan/colspan셀과 요금제 열을 구분해 원표td4열을 복원. 헤더에 있는 요금제명을 대응하고 숫자는 변경하지 않음.')
add('요금제별 케어 주기 표와 모델 예외','care_plan',[guide_table,span(guide,'- 정기 케어에는 클린부스터 분해','유의사항 확인하기'),span(guide,'- 라이트플러스 요금제 클린부스터 점검은','- 복합필터는 12개월마다 교체, 극세필터는 방문 주기마다 교체합니다.',True)],
 ['프리미엄/라이트플러스/베이직 구분','3/6개월 방문','자가관리12개월 배송','알파UP/UV모델 예외','필터/방문/분해주기 구분'],['모델/요금제/채널/계약시점'],'Markdown의 어긋난 표 열을 복원했다. 모든 제품 계약조건으로 확대하지 않는다.',groups=['filter_interval_conflict','cleanbooster_interval_conflict'])
add('공기청정기 영상설명의13개월 필터 문구','care_plan_conflict',[
 span(care,'- 해당 서비스는 공기청정기 프리미엄 케어서비스이며','(안내)분해 세척')],
 ['영상설명 문맥','프리미엄','모델별 클린부스터 예외'],['선정모델 실제주기','12/13개월 문구 차이 확인'],'13개월을 자동 정답으로 사용하지 않는다.12개월 안내와의 미해결 차이를 보여주는 근거다.',groups=['filter_interval_conflict'])
add('프리미엄 분해/스팀의 제품·주기 조건','premium_care',[
 span(plan,'- \\- 해당 서비스는 25년 출시 이후 제품에만','![공기청정기 팬을 스팀'),span(plan,'- \\- 해당 서비스는 25년 출시 이후 제품에만','![공기청정기 필터를 장착',False,1)],
 ['2025년 출시 이후 제품','프리미엄30/60개월','상하단 분리2단 제품 한정'],['모델/출시시점/케어등급'],'제품 출시 조건은 약관의 계약 시행일이 아니다.')
add('사은품 환수12개월·해지 사유·종류별 기준','gift_recovery',[
 span(plan,'계약조건으로 지급 된 사은품에 대한, 비용 환수 기준','비현금성 사은품 : LG전자 사은품 구매단가 기준 적용',True)],
 ['계약조건 지급 사은품','12개월 이내','고객 요청 해지','현금성/비현금성 산정 구분'],['계약성립일','수령 사은품','해지사유/버전','경계일'],'할인 환수와 같은 항목으로 간주하여 중복 청구하지 않는다. 실제 금액은 계산하지 않는다.')
add('카탈로그 공기청정기 케어 조건','care_plan',[
 span(cat,'※ 프리미엄 케어서비스는','※ 분실료 기준'),span(cat,'※ 의무 사용기간 내에 해지 시','※ 채널별/지점별 판촉에 따라 할인적용 여부 및 적용가는 상이할 수 있습니다.',True)],
 ['2026-02-26 매장 배포용','모델/채널별 차이','25년 출시 이후 프리미엄','6개월 클린부스터·12개월 복합필터·30개월 분해','계약 중도해지 별도 비용'],['모델/채널/계약버전'],'카탈로그 발행/배포일은 정책 시행일이 아니다. 오탈자·괄호 불명확한 분실료 수식은 계산에 쓰지 않는다.',groups=['cleanbooster_interval_conflict'])
add('베스트샵4월 안내의 클린부스터 연1회 문구','care_plan_conflict',[
 exact(best,'| **공기청정기** | 필터 클리닝, 클린 부스터 클리닝(연 1회), 내/외부 토탈클리닝, 공기질 센서 점검 | 복합필터·극세 필터 주기별 교체 |'),span(best,'제품별 케어 방문 주기 및 횟수는 모델·계약 기간에 따라 상이합니다.','상기 서비스는 2026년 4월 기준이며, 당사 사정에 따라 변경될 수 있습니다.',True)],
 ['2026년4월 기준','모델·계약기간별 차이'],['동일 모델의6개월/연1회 적용 차이'],'안내 간 차이를 계약조건 없이 하나로 통합하지 않는다.',groups=['cleanbooster_interval_conflict'])
add('가전구독과 별도 케어십의 구분','contract_type',[
 span(cat,'일시불로 제품을 구매하거나 가전 구독 계약기간이 끝난 고객의 제품을','서비스 구독',True)],
 ['일시불 구매 또는 구독 만기 제품의 별도 케어십','소모품 정기배송과 구분'],['고객 계약이 가전구독인지 케어십인지'],'케어십 규칙을 본체 가전구독의 위약금/기간 규칙에 섞지 않는다.',contract_kind='careship_or_recurring_supplies')
add('별도 케어십 계약기간·자동연장·사은품 조건','careship_terms',[
 section(service,'### Q케어십 계약기간과 해지에 따른 위약금은 없는지 궁금해요.')],
 ['별도 케어십 계약','제품별 기간·연장 예외','사은품 비용 별도'],['계약유형/제품/버전','사은품 여부'],'공기청정기 가전구독 본체에 위약금이 없다고 답하는 근거로 쓰지 않는다.',contract_kind='careship_only')
add('구독 선납금 정산 안내','prepayment_settlement',[
 span(service,'- 선납금 납부 유형 선택 시 선납금은 청약시점에 청구됩니다.','### Q가전 구독 제품을 설치 후')],
 ['선납 선택 계약','의무기간 내 해지','사용기간 할인 차감 후 잔액 조건'],['선납금/월 할인금액','실사용일수','약관버전','금액 처리 기준'],'정산 안내만 보존. 계산 Tool이나 환급 확정 금액을 만들지 않는다.')
add('예시 공기청정기의 구독·관리 옵션 확인','product_presence',[
 exact(product,'AS192DSFAM제품코드 복사하기'),span(product,'계약기간\n','케어서비스 유형')],
 ['AS192DSFAM 예시','표시된 계약기간/관리 주기는 선택 옵션'],['최종모델','선택 조합 제공 가능 여부'],'옵션의 모든 조합이 가능한 것으로 추정하지 않는다. 변동하는 가격은 이 근거에서 제외한다.',product_scope='AS192DSFAM_example')

members=collections.defaultdict(list)
for u in units:
 for g in u['review_groups']:members[g].append(u['evidence_id'])
for u in units:u['related_evidence_ids']=sorted({x for g in u['review_groups'] for x in members[g]}-{u['evidence_id']})
for u in units:
 assert u['segments'] and not u['index_approved'] and not u['can_determine_customer_cost']
 for seg in u['segments']:
  assert sha(root/seg['capture_path'])==seg['capture_sha256']
  if seg['kind']=='verbatim':
   doc=pdf_document(seg['locator']['physical_page']) if seg['locator']['format']=='cached_pdf_page_text' else document(seg['source_id'],seg['capture_path'])
   assert doc['text'][seg['start_character']:seg['end_character_exclusive']]==seg['quote']
   assert hashlib.sha256(seg['quote'].encode()).hexdigest()==seg['quote_sha256']

blocked_phrase='중도해지한 경우 방문 서비스 중단되며, 고객은 월 요금 납입 없이 제품을 사용할 수 있습니다.'
blocked=[dict(source_id=compare['source_id'],reason='같은 페이지의 총 계약기간 경과 후 소유권 문구 및 다른 계약 안내와 적용 시점이 상충. 중도해지 후 무상 소유 결론에 사용 금지.',evidence=exact(compare,blocked_phrase),policy_index_allowed=False)]
blocked.append(dict(source_id=cat['source_id'],reason='괄호 구조·오탈자가 있는 분실/파손료 수식. 계산 규칙 및 현재 검색 후보에서 제외하고 계약 원문 확인 필요.',evidence=span(cat,'※ 분실료 기준','※ 의무 사용기간 내에 해지 시'),policy_index_allowed=False))
assert all(blocked_phrase not in seg.get('quote','') for u in units for seg in u['segments'])
assert all('※ 분실료 기준' not in seg.get('quote','') for u in units for seg in u['segments'])
registry=[]
for sid,s in sources.items():
 route,note=routes[sid];used=[u['evidence_id'] for u in units if sid in u['source_ids']]
 registry.append(dict(source_id=sid,title=s['document_name'],url=s['url'],route=route,reason=note,source_status=s['status'],source_capture=s['raw_capture'],source_capture_sha256=s['raw_sha256'],curated_evidence_ids=used,
  selection_status='근거 단위 정제' if used else '출처 분류만 완료; 이번 정제 묶음 미선정',full_document_ingestion_allowed=False,index_approved=False))

base='processed/curation_20261013'
write(base+'/evidence_units.draft.jsonl',''.join(json.dumps(u,ensure_ascii=False)+'\n' for u in units))
dump('metadata/curation_source_registry_20261013.json',dict(curated_on_kst='2026-10-13',input_manifest='metadata/source_manifest.json',input_manifest_sha256=sha(root/'metadata/source_manifest.json'),source_count=len(sources),routes=dict(collections.Counter(x['route'] for x in registry)),sources=registry,
 folder_rules={'raw':'原文保管' if False else '원본 보존; 폴더 전체 자동 색인 금지','references':'기획·팀·Mock 참고자료로 정책 색인 제외','reports':'조사자 해석·문의 초안·평가 질문으로 정책 색인 제외','processed/review_06':'자료 검토용 추출/이미지; 근거 묶음과 별도','processed/curation_20261013':'검토용 근거 단위 초안; 아직 색인 승인 아님'},shared_interface_changed=False))
dump('metadata/curation_review_groups_20261013.json',dict(groups=[dict(group_id=g,evidence_ids=ids,selection_rule='함께 검토하고 계약/제품/근거 성격을 확인. 최신 수집본 우선이나 평균값 선택 금지.') for g,ids in members.items()],blocked_fragments=blocked))
dump(base+'/normalized_tables.json',{'care_plan':guide_table,'relocation_price':price})
report=['# 정제한 공식 근거 묶음 — 검토용 초안','', '2026-10-13. 보존 자료는2026-10-12 수집본이다. 새 정책 확인·검색 실행·계산 결과가 아니다. 원문과 조사자 해석을 분리했다. 이 문서 전체는 검색 색인에 넣지 않는다.','']
for u in units:
 report += [f"## {u['evidence_id']} {u['title']}",'',f"- 공식 출처: {', '.join('['+s['id']+']('+s['url']+')' for s in u['official_sources'])}",f"- 계약 종류: `{u['contract_kind']}` / 제품 범위: `{u['product_scope']}`",'- 함께 보존할 조건: '+' / '.join(u['curation_notes']['conditions_to_keep']),'- 추가 확인: '+' / '.join(u['curation_notes']['missing_contract_context']),'- 해석·제한: '+u['curation_notes']['interpretation_and_limits'],'- 관련 근거: '+(', '.join(u['related_evidence_ids']) or '없음'),'']
 for seg in u['segments']:
  if seg['kind']=='verbatim':report+=['**보존 수집본의 발췌**', '', '> '+seg['quote'].replace('\n','\n> '),'']
  else:
   t=seg['table'];report+=['**원표 구조를 정리한 표 — 원문 형식 그대로의 인용 아님**','','| '+' | '.join(t['headers'])+' |','| '+' | '.join(['---']*len(t['headers']))+' |']+['| '+' | '.join(r)+' |' for r in t['rows']]+['',seg['normalization'],'']
write(base+'/근거묶음_검토본.md','\n'.join(report))

checks={
 'source_manifest_hash_match':True,'all_30_sources_classified':len(registry)==30,
 'verbatim_offsets_and_hashes_match':True,'table_cells_checked_against_captured_html_and_xml':True,
 'recovery_fee_pair_preserves_contract_date_and_fee_guard':all(x in json.dumps(units[:2],ensure_ascii=False) for x in ['2026-03-24','2021년 11월 5일','39,000','35,000','계약서']),
 'two_year_exception_preserved':'계약 기간이 2년' in str(units[2]),
 'waiver_preserves_proof_and_extra_fee_conditions':all(x in str(units[4]) for x in ['관련 자료 제출','50%','철거비용']),
 'transport_exclusion_and_product_list_preserved':all(x in str(units[13]) for x in ['운송','워시타워','계약 기간 내 1회']),
 'conflicting_ownership_fragment_excluded':True,'no_cx_historical_general_terms_or_team_data_in_evidence':all(routes[s][0] in ['policy_candidate','dispute_reference'] for u in units for s in u['source_ids']),
 'careship_and_appliance_contracts_separated':units[24]['contract_kind']=='careship_only',
 'all_units_explicitly_unapproved_for_index_and_cost':all(not u['index_approved'] and not u['can_determine_customer_cost'] for u in units)}
assert all(checks.values()),checks
dump('metadata/curation_validation_20261013.json',dict(curated_on_kst='2026-10-13',status='오프라인 자료 정제 검증 완료 / D 반영 전',source_count=30,evidence_unit_count=len(units),evidence_source_count=len({s for u in units for s in u['source_ids']}),verbatim_segments=sum(seg['kind']=='verbatim' for u in units for seg in u['segments']),normalized_tables=2,review_group_count=len(members),excluded_fragment_count=len(blocked),checks=checks,
 retrieval_test_executed=False,agent_evaluation_executed=False,embedding_or_index_created=False,api_calls_made=False,shared_interface_changed=False,
 limitation='문자열/표/범위 무결성 검증이며 정책의 현행성·개별계약 적용·검색 정확도 검증이 아님.'))
print(json.dumps(dict(evidence_units=len(units),sources_used=len({s for u in units for s in u['source_ids']}),routes=dict(collections.Counter(x['route'] for x in registry)),checks=checks),ensure_ascii=False))
