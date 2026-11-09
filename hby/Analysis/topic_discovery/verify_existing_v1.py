"""읽기 전용 원자료 분석. 출력은 새 검증_v1 폴더에만 작성한다.

표준 라이브러리만 사용한다. 환경변수·설정·인증정보·워크플로우는 읽지 않는다.
개별 사건번호·사용자 ID·프로필·댓글 전문은 출력하지 않는다.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import posixpath
import statistics
import argparse
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'Data'
BASE = DATA / '통합자료/태민자료조사/coreProject'
OUT = Path(__file__).resolve().parent / '검증_v1'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def read_csv(path):
    raw = path.read_bytes()
    for enc in ('utf-8-sig', 'cp949'):
        try:
            text = raw.decode(enc)
            return list(csv.DictReader(io.StringIO(text))), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f'인코딩 확인 필요: {path.name}')


def write_csv(name, rows, fields):
    with (OUT / name).open('x', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def rel(path):
    return 'Data\\' + str(path.relative_to(DATA)).replace('/', '\\')


def sheet_rows(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(t.text or '' for t in e.findall('.//s:t', NS))
                      for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        targets = {e.attrib['Id']: e.attrib['Target']
                   for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for sh in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS):
            target = targets[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            rows = []
            for row in ET.fromstring(z.read(member)).findall('s:sheetData/s:row', NS):
                cells = {}
                for c in row.findall('s:c', NS):
                    value = c.find('s:v', NS)
                    text = value.text or '' if value is not None else ''
                    if c.attrib.get('t') == 's':
                        text = shared[int(text)] if text else ''
                    elif c.attrib.get('t') == 'inlineStr':
                        text = ''.join(t.text or '' for t in c.findall('.//s:t', NS))
                    cells[''.join(x for x in c.attrib['r'] if x.isalpha())] = text
                rows.append((int(row.attrib['r']), cells))
            yield sh.attrib['name'], rows


def main():
    OUT.mkdir(exist_ok=False)
    inventory = []
    for p in sorted(DATA.rglob('*')):
        if p.is_file():
            inventory.append({'경로': rel(p), '확장자': p.suffix.lower(), '바이트수': p.stat().st_size})
    write_csv('전체_자료목록.csv', inventory, ['경로', '확장자', '바이트수'])

    selected, _ = read_csv(BASE / 'outputs/step2_final/included_original_names.csv')
    allowed = {r['물품소분류']: r['가전품목군'] for r in selected}
    # 기존 선정 범위를 재현한다. 이 목록 자체가 최적 제품 선정이라는 뜻은 아니다.
    raw_dir = BASE / 'data/품목별 상담 현황'
    paths = sorted(raw_dir.glob('*.csv'))
    assert len(paths) == 10, len(paths)
    totals = Counter()
    appliance = Counter()
    quality = Counter()
    other_quality = Counter()
    product_quality = defaultdict(Counter)
    reasons, outcomes, ages = Counter(), Counter(), Counter()
    source_rows = []
    hashes = defaultdict(list)
    for p in paths:
        rows, enc = read_csv(p)
        hashes[hashlib.sha256(p.read_bytes()).hexdigest()].append(rel(p))
        subtotal = Counter()
        for r in rows:
            date = r.get('접수일(년월일)', r.get('접수일', ''))
            year = date[:4]
            item = r.get('물품소분류', r.get('물품명', '')).strip()
            reason = r.get('청구이유', '').strip()
            totals[year] += 1
            subtotal['전체'] += 1
            if item in allowed:
                appliance[year] += 1
                subtotal['가전'] += 1
                reasons[reason] += 1
                ages[r.get('연령대', r.get('연령', ''))] += 1
                if '처리결과' in r:
                    outcomes[r['처리결과'].strip()] += 1
                if reason in {'품질(물품/용역)', 'AS불만'}:
                    quality[year] += 1
                    product_quality[year][allowed[item]] += 1
            elif reason in {'품질(물품/용역)', 'AS불만'}:
                other_quality[year] += 1
        source_rows.append({'경로': rel(p), '인코딩': enc, '전체행수': len(rows), '가전행수': subtotal['가전']})
    write_csv('피해구제_원본파일별.csv', source_rows, ['경로', '인코딩', '전체행수', '가전행수'])
    annual = [{'연도': y, '전체': totals[y], '가전': appliance[y], '가전_품질AS': quality[y],
               '비가전': totals[y] - appliance[y], '비가전_품질AS': other_quality[y]}
              for y in sorted(totals)]
    write_csv('피해구제_연도별.csv', annual, list(annual[0]))
    checks = []

    def check(name, actual, expected, note):
        checks.append({'지표': name, '재계산값': actual, '기존값': expected,
                       '일치': abs(actual - expected) < 0.011, '범위와한계': note})

    check('전체 피해구제 행수', sum(totals.values()), 150964, '2024Q1~2026Q2, 고유 고객 수 아님')
    check('가전 피해구제 행수', sum(appliance.values()), 5554, '기존 25개 원문 품목명 선정 재현')
    check('가전 품질AS 일반', sum(quality.values()), 3205, '품질(물품/용역)+AS불만; 세부 반복고장 식별 불가')
    check('비가전 품질AS 일반', sum(other_quality.values()), 35108, '비가전=전체-선정가전, 렌탈 등 포함 가능')
    check('2024 가전', appliance['2024'], 2392, '완전 역년')
    check('2025 가전', appliance['2025'], 2298, '완전 역년')
    check('2024 가전 품질AS', quality['2024'], 1182, '원문 범주 합')
    check('2025 가전 품질AS', quality['2025'], 1475, '원문 범주 합')
    check('결과가 있는 가전', sum(outcomes.values()), 416, '처리결과 열이 있는 2026Q2 파일만')
    direct = sum(outcomes[k] for k in ['환급', '수리,보수', '배상', '교환'])
    check('직접 구제성 결과명 합', direct, 183, '실제 기준 적용·합의 여부 불명')
    check('30~39세 가전 신청', ages['30 - 39세'], 1705, '연령별 인구 대비 위험 아님; 원문 범주 30 - 39세')

    # 상담 표기 및 날짜 메타데이터만 사용한다.
    monthly_paths = sorted((BASE / 'data').rglob('*상담 현황*'))
    monthly = []
    seen_months = set()
    for p in monthly_paths:
        if not p.is_file() or p.suffix.lower() != '.csv':
            continue
        rows, _ = read_csv(p)
        rows = [{('품목명' if k.strip() == '품목명(소)' else k.strip()): v for k, v in r.items()} for r in rows]
        if '품목명' not in rows[0] or '상담건수' not in rows[0]:
            raise ValueError(f'예상 외 상담 스키마: {p.name}')
        stamp = p.stem.rsplit('_', 1)[-1]
        inferred = stamp in {'20240103', '20240201'}
        date = {'20240103': '2023-12', '20240201': '2024-01'}.get(stamp, stamp[:4] + '-' + stamp[4:6])
        if '연도' in rows[0]:
            assert all(f"{int(r['연도']):04d}-{int(r['월']):02d}" == date for r in rows)
        assert date not in seen_months, date
        seen_months.add(date)
        matches = [(i, r) for i, r in enumerate(rows, 1) if r['품목명'] == '에어컨']
        assert len(matches) == 1
        i, r = matches[0]
        monthly.append({'기준월': date, '에어컨': int(r['상담건수'].replace(',', '')),
                        '기준월추론': inferred, '경로': rel(p), '데이터행': i})
    monthly.sort(key=lambda x: x['기준월'])
    write_csv('에어컨_월별_원본대조.csv', monthly, list(monthly[0]))
    peak = max(monthly, key=lambda x: x['에어컨'])
    winter = [r['에어컨'] for r in monthly if int(r['기준월'][-2:]) in {11, 12, 1, 2, 3}]
    med = statistics.median(winter)
    check('상담 관측월 수', len(monthly), 32, '상위 500위 안의 에어컨 정확 일치')
    check('동절기 관측월 수', len(winter), 14, '11~3월; 초기 2개월 기준월은 기존 추론 유지')
    check('에어컨 피크 건수', peak['에어컨'], 1964, peak['기준월'])
    check('동절기 월간 중앙값', med, 100.5, '계절 전체 평균 아님')
    check('피크/동절기 중앙값', peak['에어컨'] / med, 19.54, '시장 전체 또는 매년 배율 아님')

    faq_path = BASE / 'data/한국소비자원_소비자상담 표준답변_20250725.csv'
    faq, _ = read_csv(faq_path)
    faq_counts = Counter(r['품목명'].strip() for r in faq)
    check('전체 표준답변', len(faq), 1332, '편집된 항목 수')
    for label, n in [('TV', 26), ('냉장고', 22), ('룸에어컨', 23)]:
        check(label + ' 표준답변', faq_counts[label], n, '품목명 strip 후 완전일치')
    tv = [r for r in faq if r['품목명'].strip() == 'TV']
    write_csv('TV_표준질문_원본대조.csv',
              [{'TV내순번': i, '원본번호': r['번호'], '질문': r['질문'],
                '원본데이터행': next(j for j, q in enumerate(faq, 1) if q is r)}
               for i, r in enumerate(tv, 1)], ['TV내순번', '원본번호', '질문', '원본데이터행'])

    # 원문 집계 대조는 기존 AI/규칙 라벨의 정확도 검증과 구별한다.
    xlsx_base = DATA / 'drive-download-20261109T000429Z-1-001'
    workbook_metadata = []
    for name in ['LG에어컨_가설검증_최종.xlsx', 'LG공식답변_해결과정_분석.xlsx',
                 'LG에어컨_유튜브댓글_3차_표본분석_가설종합.xlsx']:
        p = next(xlsx_base.rglob(name))
        for sheet, rows in sheet_rows(p):
            workbook_metadata.append({'경로': rel(p), '시트': sheet, 'XML행수': len(rows)})
            if sheet == '표본 분류결과':
                write_csv('유튜브3차_표본_열구조.csv',
                          [{'엑셀행': i, '셀주소': col + str(i), '열제목': text}
                           for i, cells in rows[:1] for col, text in cells.items()],
                          ['엑셀행', '셀주소', '열제목'])
    write_csv('우선엑셀_시트목록.csv', workbook_metadata, ['경로', '시트', 'XML행수'])

    # 동일한 공식 통계 CSV의 사본만 해시 비교한다. 설정/워크플로우는 열지 않는다.
    official_names = {p.name for p in paths} | {faq_path.name}
    for p in DATA.rglob('*.csv'):
        if p.name in official_names and p not in paths:
            hashes[hashlib.sha256(p.read_bytes()).hexdigest()].append(rel(p))
    duplicates = [{'SHA256': h, '사본수': len(ps), '경로들': ' | '.join(ps)}
                  for h, ps in hashes.items() if len(ps) > 1]
    write_csv('공식통계_동일파일사본.csv', duplicates, ['SHA256', '사본수', '경로들'])
    write_csv('수치_재검산.csv', checks, ['지표', '재계산값', '기존값', '일치', '범위와한계'])
    result = {'연도별': annual, '청구이유': dict(reasons), '처리결과': dict(outcomes),
              '연령': dict(ages), '품질AS_품목연도': dict(product_quality),
              '피크월': peak['기준월'], '검산일치': sum(c['일치'] for c in checks),
              '검산항목수': len(checks), '중복파일그룹수': len(duplicates),
              '검증경계': '원본 행 집계이며 사건 중복·전체 고객 대표성·정책 현행성을 검증하지 않음'}
    with (OUT / '집계결과.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-name', default='검증_v1')
    args = parser.parse_args()
    if Path(args.output_name).name != args.output_name:
        raise ValueError('출력 이름은 하위 폴더 이름이어야 함')
    OUT = Path(__file__).resolve().parent / args.output_name
    main()
