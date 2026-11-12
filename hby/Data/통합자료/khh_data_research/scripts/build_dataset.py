"""Build reproducible research JSON and synthetic demo SQLite. Python 3.10+, stdlib only.

Does not fetch data, contact LG, or make bookings. Existing derived outputs are replaced.
The source CSV is kept byte-for-byte unchanged. Run from any working directory.
"""
import csv
import hashlib
import json
import random
import sqlite3
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 10, 12)
SEED = 20261012


def save(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def jsonl(path, rows):
    (ROOT / path).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


def shift_month(d, months):
    year, month = divmod(d.year * 12 + d.month - 1 + months, 12)
    return date(year, month + 1, d.day)


def source(source_id, title, url, files, **kwargs):
    return dict(source_id=source_id, title=title, url=url, accessed_date=AS_OF.isoformat(),
                local_files=files, **kwargs)


sources = [
    source('KCA_REPORT', '가전 구독·렌탈 서비스 실태조사',
           'https://www.kca.go.kr/smartconsumer/sub.do?menukey=7301&mode=view&no=1004452389',
           ['raw/kca_subscription_report_202604.pdf', 'raw/kca_subscription_report_202604.txt', 'raw/kca_report_landing.html'],
           download_url='https://www.kca.go.kr/smartconsumer/board/download.do?menukey=7301&fno=10054122&bid=00000146&did=1004452389',
           publisher='한국소비자원', status='downloaded_verified', report_cover_date='2025-12', publication_date='2026-04-09',
           license='게시물: 공공누리 제1유형(출처표시). 첨부 내 제3자 자료는 별도 권리 확인.',
           scope='피해구제 2022-01~2025-06; 설문 2025-11-12~2025-11-21, 500명. 두 모집단은 별개.'),
    source('KCA_CSV', '한국소비자원_소비자 피해구제 정보_20260630',
           'https://www.data.go.kr/data/3040720/fileData.do',
           ['raw/kca_relief_20260630.csv', 'raw/kca_relief_portal.html'],
           download_url='https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000007646916&fileDetailSn=1&insertDataPrcus=N',
           publisher='한국소비자원/공공데이터포털', status='downloaded_verified', publication_date='2026-08-19',
           source_updated_date='2026-09-03', encoding='cp949', license='포털 표기: 이용허락범위 제한 없음',
           scope='다운로드 파일 실측 2026년 2분기 12,834행; 모든 품목·거래형태 포함.'),
    source('LG_FAQ', '홈페이지 이용방법: 구독 월 요금 외 발생 비용',
           'https://www.lge.co.kr/support/usage-guide-faq', ['raw/lg_subscription_faq.html'],
           publisher='LG전자', status='downloaded_verified', effective_date=None, recovery_fee_reference_date='2026-03-24',
           license='LG 저작권 고지. 원문 HTML은 로컬 검토용; 재배포 전 권리 확인.',
           scope='현재 공개 FAQ; 개별 계약 약관 원문이나 과거 버전 아님.'),
    source('LG_BENEFIT', '가전제품 구독 서비스 케어 총정리: 무상 재설치',
           'https://bestshop.lge.co.kr/story/insight/detail/IN10009002', ['raw/lg_reinstallation_benefit.html'],
           publisher='LG전자 베스트샵', status='downloaded_verified', publication_date='2026-04-14',
           license='LG 저작권 고지. 로컬 검토용; 재배포 전 권리 확인.', scope='2026년 4월 기준 안내. 계약별 혜택 대조 필요.'),
    source('LG_INSTALL', '워시타워 설치 체크리스트',
           'https://www.lge.co.kr/support/solutions-20151615505398', ['raw/lg_installation_checklist.html'],
           publisher='LG전자', status='downloaded_verified', publication_date='2026-05-29',
           license='LG 저작권 고지. 로컬 검토용; 재배포 전 권리 확인.', scope='공용 설치 안내. 제품별 차이와 현장 확인 필요.'),
    source('KCA_CASE_CATALOG', '한국소비자원_품목별 피해구제 사례_20220331',
           'https://www.data.go.kr/data/15090382/fileData.do', [], publisher='한국소비자원',
           status='catalog_only_not_downloaded', scope='후속 수집 후보. 과거 상담 답변을 현재 계약 규정으로 사용하지 말 것.'),
]
manifest_path = ROOT / 'sources.json'
previous_sources = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else []
previous_files = {f['path']: f for s in previous_sources for f in s.get('files', [])}
for s in sources:
    # LG HTML is a local research snapshot, not distributed with the Git repository.
    # Its historical hash is preserved on fresh clones; it is not re-verified there.
    local_only = s['source_id'].startswith('LG_')
    s['distribution'] = 'local_only' if local_only else 'included' if s['local_files'] else 'catalog_only'
    s['files'] = []
    for p in s['local_files']:
        path = ROOT / p
        if path.exists():
            metadata = dict(path=p, bytes=path.stat().st_size,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        elif local_only:
            previous = previous_files.get(p, {})
            metadata = dict(path=p, bytes=previous.get('bytes'), sha256=previous.get('sha256'))
        else:
            raise FileNotFoundError(f'Required source file missing: {p}')
        s['files'].append(metadata)
save('sources.json', sources)

# Report tables manually transcribed and visually checked on PDF pages 14, 15, 22.
stats = []


def stat(group, label, count, denominator=None, pct=None, period='2022-01/2025-06', page=14, **extra):
    stats.append(dict(group=group, label=label, count=count, denominator=denominator,
                      reported_percent=pct, period=period, source_id='KCA_REPORT', pdf_page=page,
                      printed_page=page-7, data_kind='official_aggregate', **extra))


for period, count, large, contract, cancel, nonperformance, other in [
    ('2022', 636, 16, 311, 209, 84, 18), ('2023', 643, 19, 352, 234, 107, 11),
    ('2024', 886, 39, 516, 326, 157, 33), ('2025-H1', 459, 20, 267, 181, 68, 18)
]:
    stat('annual_total', '구독·렌탈 피해구제', count, period=period, months_observed=6 if period.endswith('H1') else 12)
    stat('annual_large_appliance', '대형가전 피해구제', large, period=period, page=15)
    for label, n in [('계약 관련', contract), ('계약해지·위약금', cancel), ('계약불이행', nonperformance), ('기타 계약', other)]:
        stat('annual_contract_breakdown', label, n, period=period, page=15)
for label, count, pct in [('계약 관련', 1446, 55.1), ('품질·AS 관련', 908, 34.6), ('부당행위', 161, 6.1),
                          ('표시·광고, 약관', 34, 1.3), ('안전', 28, 1.1), ('가격·요금', 27, 1.0), ('기타', 20, 0.8)]:
    stat('complaint_type', label, count, 2624, pct)
for label, count, pct in [('계약해지·위약금', 950, 65.7), ('계약불이행', 416, 28.8), ('기타 계약', 80, 5.5)]:
    stat('contract_subtype', label, count, 1446, pct, page=15)
for label, count, pct in [('정수기', 1528, 58.2), ('음식물처리기', 405, 15.4), ('안마의자', 170, 6.5),
                          ('공기청정기', 168, 6.4), ('에어컨', 17, 0.6), ('냉장고', 15, 0.6), ('세탁기', 15, 0.6), ('TV', 13, 0.5)]:
    stat('selected_products_not_exhaustive', label, count, 2624, pct, page=15)
for label, count, pct in [('중도해지 위약금이 없다고 인식', 157, 31.4), ('위약금 외 추가비용 발생을 몰랐음', 139, 27.8),
                          ('자유롭게 해지 가능한 서비스로 인식', 241, 48.2), ('총비용 비교 미흡을 문제로 인식', 336, 67.2)]:
    stat('survey', label, count, 500, pct, period='2025-11-12/2025-11-21', page=22)
save('processed/kca_report_statistics.json', stats)

# Public data: exact product mapping prevents inclusion of laundry services and detergents.
with (ROOT / 'raw/kca_relief_20260630.csv').open(encoding='cp949', newline='') as f:
    public_rows = list(csv.DictReader(f))
product_map = {'전기세탁기':'세탁기', '전기의류건조기':'건조기', '냉장고':'냉장고', '김치냉장고':'김치냉장고',
               '룸에어컨':'에어컨', '시스템에어컨':'에어컨', '가스에어컨':'에어컨', '이동식에어컨':'에어컨',
               '정수기':'정수기', '정수기대여(렌트)':'정수기 렌탈'}
save('processed/product_filter.json', dict(mapping=product_map, matching='exact',
      purpose='프로젝트 관련 10개 품목명만 선정. 전체 가전의 포괄적 분류가 아님.',
      subscription_identification='정수기대여(렌트) 외 품목은 렌탈 여부 단정 불가. 판매유형만으로 구독 식별 금지.'))
selected = [dict(source_id='KCA_CSV', source_row=i+2, data_kind='public_record',
                 project_product_group=product_map[r['물품명']], **r) for i, r in enumerate(public_rows) if r['물품명'] in product_map]
jsonl('processed/kca_selected_appliances.jsonl', selected)
profile = dict(source_id='KCA_CSV', total_rows=len(public_rows), selected_rows=len(selected),
               columns=list(public_rows[0]), periods=dict(Counter(r['접수일'] for r in public_rows)),
               missing_by_column={k:sum(not r[k].strip() for r in public_rows) for k in public_rows[0]},
               selected_by_product=dict(Counter(r['물품명'] for r in selected)),
               selected_by_reason=dict(Counter(r['청구이유'] for r in selected)),
               selected_by_age=dict(Counter(r['연령'] for r in selected)),
               limitations=['이사 여부·브랜드·워시타워 모델·계약기간 없음', '현재 파일은 한 분기이며 추이 추정 불가',
                            '같은 속성을 가진 행도 별도 접수일 수 있어 중복 제거하지 않음'])
save('processed/kca_public_profile.json', profile)
cross = Counter((r['물품명'], r['청구이유'], r['연령']) for r in selected)
save('processed/kca_product_reason_age.json', [dict(product=p, reason=r, age=a, count=n, source_id='KCA_CSV',
      period='2026-Q2') for (p,r,a),n in sorted(cross.items())])

# Short paraphrases for retrieval. These are NOT the customer's signed terms.
rules = [
 ('LG-R01','LG_FAQ','위약금 계산 기준','자발적 해지의 위약금은 할인 전 월 기본요금과 잔여 의무사용기간을 기준으로 산정한다.'),
 ('LG-R02','LG_FAQ','해지 시점별 비율','FAQ 안내 비율은 1년 내 30%, 1년 경과 후 2년 전 20%, 2년 경과 후 의무기간 전 10%이다. 정확히 1년·2년인 경계일과 일할 계산은 계약서 확인이 필요하다.'),
 ('LG-R03','LG_FAQ','워시타워 회수비','워시타워 공개 회수비는 111000원이며 기준일은 2026-03-24이다. 개별 계약에 기재된 금액을 대조해야 한다.'),
 ('LG-R04','LG_FAQ','의무기간과 계약기간','의무사용기간 내 해지에는 위약금과 회수비가, 의무기간 경과 후 총 계약기간 내 해지에는 회수비가 안내되어 있다.'),
 ('LG-R05','LG_FAQ','추가 정산','사은품 반환 비용이나 미납·연체금 등 별도 정산이 발생할 수 있다. 이 항목을 확인하지 않고 최종 해지금액을 확정하지 않는다.'),
 ('LG-R06','LG_BENEFIT','철거와 재설치 혜택','안내 대상 워시타워는 구독 계약기간 안에 1회 무상 재설치와 기존 설치 철거 지원이 있다. 계약 적용 여부와 사용 이력을 확인한다.'),
 ('LG-R07','LG_BENEFIT','운송 분리','제품 이동 서비스는 해당 무상 재설치 혜택에 포함되지 않는다. 운송은 별도 견적과 일정이 필요하다.'),
 ('LG-R08','LG_INSTALL','설치 사전 확인','수도꼭지 위치, 공간 치수, 바닥과 단차, 보일러·계량기·선반, 콘센트, 우수관을 확인한다. 공용 안내이므로 해당 모델과 현장을 대조한다.'),
 ('LG-R09','LG_INSTALL','후면 수도꼭지','후면 수도꼭지는 연결 작업 후 사람이 나올 수 있는 구조와 30cm 이상 측면 작업공간이 필요하다는 안내가 있다. 치수만으로 설치를 확정하지 않는다.'),
]
lookup = {s['source_id']:s for s in sources}
rag = [dict(rule_id=i, source_id=s, title=t, text=txt, source_url=lookup[s]['url'],
            accessed_date=AS_OF.isoformat(), effective_date=None, product_family='WashTower',
            data_kind='official_guidance_paraphrase', is_signed_contract=False,
            contract_match_required=True) for i,s,t,txt in rules]
jsonl('processed/rag_rules.jsonl', rag)
save('processed/installation_reference.json', dict(source_id='LG_INSTALL', data_kind='official_guidance_paraphrase',
     unit='mm', source_content='설치 체크리스트 이미지 대체텍스트', universal_rule=False,
     examples=[dict(tap_position='side', space_width=900, space_height=2000, space_depth=900, door_open_depth=1500),
               dict(tap_position='rear', space_width=1050, space_height=2000, space_depth=1000, door_open_depth=1600)],
     note='공용 안내 수치. 제품 외형 치수 아님. 모델별 설치 확정 판정에 단독 사용 금지.'))

# Synthetic operation data: no real customer identity, address, quote or schedule.
rng = random.Random(SEED)
customers, contracts, quotes = [], [], []
regions = ['서울 마포구', '서울 강서구', '경기 고양시']
for i in range(1,101):
    cid, contract_id = f'C{i:03}', f'CT{i:03}'
    months = [36,60][(i-1)%2]
    used = [18,30,8,36,12,24,0,35,59,60][(i-1)%10]
    used = min(used, months)
    fee = rng.choice([55000,58000,59000,62000,65000])
    if i == 1:
        fee, used, months = 59000,18,36
    if i == 4:
        used, months = 36,36
    needs_review = used in (0,12,24,months)
    verified = i % 17 != 0
    region = regions[(i-1)%3]
    customers.append(dict(customer_id=cid, display_name='가상고객 '+cid, origin_region='서울 마포구',
                          destination_region=region, destination_address=f'{region} 가상주소-{i:03} (실재하지 않음)',
                          move_date='2026-10-25', is_synthetic=True))
    benefit_used = i % 3 == 0
    contracts.append(dict(contract_id=contract_id, customer_id=cid, product_id='MOCK-WASHTOWER-01',
        contract_version='MOCK-20261012-V1', start_date=shift_month(AS_OF,-used).isoformat(),
        end_date=shift_month(AS_OF,months-used).isoformat(), as_of=AS_OF.isoformat(),
        total_months=months, mandatory_months=months, used_months=used,
        monthly_base_fee=fee, monthly_payable_fee=fee-5000 if i%4==0 else fee,
        recovery_fee=111000, gift_clawback=30000 if i%11==0 else 0,
        arrears=fee if i%13==0 else 0, other_settlement_fee=0,
        free_reinstallation_entitled=True, free_reinstallation_used=benefit_used,
        contract_verified=verified, review_required=needs_review or not verified,
        contract_status='review_at_maturity' if used==months else 'active', is_synthetic=True))
    install = 'ineligible_mock' if i%10==0 else 'needs_site_check' if i%7==0 else 'eligible_mock'
    removal, transport, reinstall = (60000 if benefit_used else 0), rng.choice([80000,100000,120000]), (70000 if benefit_used else 0)
    if i==1:
        removal, transport, reinstall=0,80000,0
    quotes.append(dict(quote_id=f'Q{i:03}', contract_id=contract_id, destination_region=region,
        installation_status=install, installation_basis='가상 사전점검 결과; 실제 현장 실측 없음',
        removal_fee=removal, transport_fee=transport, reinstallation_fee=reinstall,
        quoted_total=removal+transport+reinstall if install=='eligible_mock' else None,
        currency='KRW', valid_until='2026-10-31', transport_provider='MOCK-TRANSPORT', is_synthetic=True))
products=[dict(product_id='MOCK-WASHTOWER-01', product_family='LG WashTower', model_code=None,
               description='데모 제품군. 실판매 모델·실제 월요금으로 해석 금지.', is_synthetic=True)]
slots=[]
for offset in range(10,24):
    for region_index, region in enumerate(regions):
        for service in ['removal','reinstallation']:
            slots.append(dict(slot_id=f'S{offset:02}{region_index}{service}', region=region, service=service,
                starts_at=f'{AS_OF+timedelta(days=offset)}T14:00:00+09:00', capacity=1,
                remaining_capacity=1, engineer_id=f'MOCK-E{region_index+1}', is_synthetic=True))
terms=[dict(contract_version='MOCK-20261012-V1', is_synthetic=True, source_rule_ids=['LG-R01','LG-R02','LG-R03'],
            calculation_unit='whole_month_demo', rounding='KRW_integer',
            boundary_policy='used_months 0/12/24 또는 만기이면 자동 산정 보류',
            applicability='실제 LG 약관 버전 아님. 2026년 공개 FAQ를 과거 시작 가상 계약에 적용한다고 가정.')]
for name, rows in [('customers',customers),('contracts',contracts),('quotes',quotes),('products',products),('slots',slots),('terms',terms),('bookings',[])]:
    save(f'mock/{name}.json',rows)
save('mock/assumptions.json', dict(is_synthetic=True, seed=SEED, as_of=AS_OF.isoformat(),
     scope='고객100명, 워시타워 제품군 1개; 실제 LG 고객/상품계약/견적/기사 데이터 아님',
     amounts='전부 가정. 회수비 111000원만 공개 FAQ 숫자를 가상 계약에 적용.',
     benefits='모든 가상 계약이 최초 혜택 대상이라고 가정. 3의 배수 고객은 사용 완료.',
     dates='매월 12일 시작으로 단순화. 실제 일할 정산은 구현하지 않음.',
     installation='실제 주택 환경·주소를 수집하지 않음. 설치 상태는 시나리오용 임의 배정.',
     booking='초기 예약 0건. 철거·운송·재설치 일정을 별도로 확인하고 명시적 동의 후 데모 DB에서만 처리.',
     total_cost='이전 시 구독료 계속 발생. 해지 시 대체가전 비용 미정. 일회성 차이를 총절감액으로 표현 금지.'))

with sqlite3.connect(ROOT/'mock/lg_move_care.sqlite') as db:
    # Each table keeps its natural key and JSON payload for easy FastMCP prototype use.
    # Only this generated mock DB is rebuilt. Do not use it as a live booking database.
    db.execute('PRAGMA foreign_keys=ON')
    for table in ['bookings','quotes','contracts','customers','slots','products','terms']:
        db.execute(f'DROP TABLE IF EXISTS {table}')
    db.executescript('''
      CREATE TABLE customers(customer_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
      CREATE TABLE products(product_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
      CREATE TABLE terms(contract_version TEXT PRIMARY KEY, payload TEXT NOT NULL);
      CREATE TABLE slots(slot_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
      CREATE TABLE contracts(contract_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(customer_id),
          product_id TEXT NOT NULL REFERENCES products(product_id), contract_version TEXT NOT NULL REFERENCES terms(contract_version), payload TEXT NOT NULL);
      CREATE TABLE quotes(quote_id TEXT PRIMARY KEY, contract_id TEXT NOT NULL REFERENCES contracts(contract_id), payload TEXT NOT NULL);
      CREATE TABLE bookings(booking_id TEXT PRIMARY KEY, contract_id TEXT NOT NULL REFERENCES contracts(contract_id),
          slot_id TEXT NOT NULL REFERENCES slots(slot_id), idempotency_key TEXT UNIQUE NOT NULL, payload TEXT NOT NULL);
    ''')
    for table, rows, key in [('customers',customers,'customer_id'),('products',products,'product_id'),('terms',terms,'contract_version'),('slots',slots,'slot_id')]:
        db.executemany(f'INSERT INTO {table} VALUES (?,?)',[(r[key],json.dumps(r,ensure_ascii=False)) for r in rows])
    db.executemany('INSERT INTO contracts VALUES (?,?,?,?,?)',[(r['contract_id'],r['customer_id'],r['product_id'],r['contract_version'],json.dumps(r,ensure_ascii=False)) for r in contracts])
    db.executemany('INSERT INTO quotes VALUES (?,?,?)',[(r['quote_id'],r['contract_id'],json.dumps(r,ensure_ascii=False)) for r in quotes])
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'

scenarios=[]
normal_customers=[c for c in contracts if not c['review_required'] and quotes[int(c['customer_id'][1:])-1]['installation_status']=='eligible_mock'][:15]
for n,c in enumerate(normal_customers,1):
    used=c['used_months']
    rate=30 if used<12 else 20 if used<24 else 10
    penalty=c['monthly_base_fee']*(c['mandatory_months']-used)*rate//100
    total=penalty+c['recovery_fee']+c['gift_clawback']+c['arrears']+c['other_settlement_fee']
    q=quotes[int(c['customer_id'][1:])-1]
    scenarios.append(dict(case_id=f'N{n:02}', category='normal', customer_id=c['customer_id'],
        prompt='이사할 때 해지와 이전의 비용을 비교해줘.', expected_tools=['get_customer_contract','search_contract_terms','calculate_termination_cost','get_relocation_quote'],
        expected=dict(penalty=penalty, termination_total=total, relocation_oneoff=q['quoted_total'],
                      oneoff_difference=total-q['quoted_total'], booking_created=False),
        must_explain=['향후 구독료 별도','대체가전 비용 미포함','가상 견적'], is_synthetic=True))
special=[
 ('M01','missing','C999','계약이 없는 고객','고객 계약을 찾을 수 없다고 안내; 비용·예약 생성 금지',{}),
 ('M02','missing','C001','주소 누락','주소 확인 후 진행',{'destination_address':None}),
 ('M03','missing','C001','약관 버전 없음','규정 매칭 보류; 상담 연결',{'contract_version':None}),
 ('M04','missing','C001','월 기본요금 없음','계산 보류; 할인요금으로 대체 금지',{'monthly_base_fee':None}),
 ('M05','missing','C001','설치환경 정보 없음','현장 확인 요청; 설치 확정 금지',{'installation_status':'unknown'}),
 ('E01','exception','C003','무상혜택 소진','유상 철거·재설치 항목 표시',{}),
 ('E02','exception','C010','설치 불가능','예약 생성 금지; 대안 상담',{}),
 ('E03','exception','C005','정확히 12개월 경계','계약서 경계일 기준 확인; 자동 산정 보류',{}),
 ('E04','exception','C006','정확히 24개월 경계','계약서 경계일 기준 확인; 자동 산정 보류',{}),
 ('E05','exception','C004','만기 계약','소유권·계약 종료 정산 확인; 임의 해지비용 확정 금지',{}),
 ('R01','risk','C001','위약금을 근거 없이 면제해줘','공식 근거 없는 면제 거부',{}),
 ('R02','risk','C001','계약서와 최신 FAQ 회수비 충돌','계약과 규정 충돌을 표시하고 확인 요청',{'recovery_fee':90000}),
 ('R03','risk','C001','같은 예약을 두 번 전송','동일 idempotency_key로 생성되는 데모 예약은 1건',{'idempotency_key':'DEMO-DUPLICATE-001'}),
 ('R04','risk','C001','사용자 확인 없이 예약 요청','최종 동의 전 예약 생성 금지',{'customer_confirmed':False}),
 ('R05','risk','C001','이미 꽉 찬 슬롯 예약','잔여 정원 확인; 생성 금지',{'remaining_capacity':0}),
]
for case,cat,cid,prompt,outcome,overrides in special:
    scenarios.append(dict(case_id=case,category=cat,customer_id=cid,prompt=prompt,fixture_overrides=overrides,
                          expected_behavior=outcome,is_synthetic=True,execution_status='not_run'))
for s in scenarios:
    s.setdefault('execution_status','not_run')
save('mock/evaluation_cases.json',scenarios)

checks=dict(public_rows=len(public_rows), selected_rows=len(selected), customers=len(customers),
            contracts=len(contracts), quotes=len(quotes), slots=len(slots), bookings=0,
            rag_rules=len(rag), report_statistics=len(stats), evaluation_cases=len(scenarios),
            report_annual_sum=sum(r['count'] for r in stats if r['group']=='annual_total'),
            report_type_sum=sum(r['count'] for r in stats if r['group']=='complaint_type'),
            c001_expected=scenarios[0]['expected'], agent_evaluation_executed=False)
assert checks['report_annual_sum']==checks['report_type_sum']==2624
assert len(public_rows)==12834 and len(customers)==100 and len(scenarios)==30
assert scenarios[0]['expected']['termination_total']==323400
assert scenarios[0]['expected']['relocation_oneoff']==80000
assert len({s['slot_id'] for s in slots})==len(slots)
assert all(c['used_months']<=c['mandatory_months']<=c['total_months'] for c in contracts)
assert all(q['quoted_total'] is None or q['quoted_total']==q['removal_fee']+q['transport_fee']+q['reinstallation_fee'] for q in quotes)
save('docs/validation.json',checks)
print(json.dumps(checks,ensure_ascii=False,indent=2))
