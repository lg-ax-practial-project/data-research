"""가공 시트의 댓글/리뷰를 보존 수집본과 완전일치 대조. 식별자 출력 없음."""
from collections import defaultdict
import csv
import json
from pathlib import Path
from verify_existing_v1 import DATA, sheet_rows


def main():
    out = Path(__file__).resolve().parent / '추적검증_v2'
    out.mkdir(exist_ok=False)
    base = DATA / 'drive-download-20261109T000429Z-1-001'
    jobs = [
        ('LG에어컨_유튜브댓글_3차_표본분석_가설종합.xlsx', '표본 분류결과', ('H',),
         'LG에어컨_유튜브댓글_3차_대량.xlsx', '댓글', ('I',)),
        ('LG에어컨_가설검증_최종.xlsx', '구글플레이 표본 분류', ('E',),
         'ThinQ_구글플레이_1-3점_리뷰.xlsx', '리뷰', ('D',)),
        ('LG공식답변_해결과정_분석.xlsx', '구글플레이 답변분류', ('C', 'E'),
         'LG공식답변_구글플레이_리뷰.xlsx', '리뷰와 답변', ('C', 'G')),
    ]
    records, summary = [], []
    for child, sheet, cols, raw, raw_sheet, raw_cols in jobs:
        raw_path = next(base.rglob(raw))
        child_path = next(base.rglob(child))
        source_rows = dict(sheet_rows(raw_path))[raw_sheet][1:]
        index = defaultdict(list)
        for i, r in source_rows:
            index[tuple(r.get(c, '') for c in raw_cols)].append(i)
        rows = dict(sheet_rows(child_path))[sheet][1:]
        matched, unique, prefix_matched = 0, 0, 0
        for i, r in rows:
            positions = index.get(tuple(r.get(c, '') for c in cols), [])
            matched += bool(positions)
            unique += len(positions) == 1
            method = '+'.join(cols) + ' 내용 완전일치; 식별자 미사용'
            if not positions and len(cols) == 2 and len(r.get(cols[0], '')) == 400:
                positions = [j for j, q in source_rows
                             if q.get(raw_cols[0], '').startswith(r.get(cols[0], ''))
                             and len(q.get(raw_cols[0], '')) > 400
                             and q.get(raw_cols[1], '') == r.get(cols[1], '')]
                prefix_matched += bool(positions)
                method = '리뷰 앞400자+답변 완전일치; 전체리뷰 일치와 구분'
            records.append({'가공파일': child, '가공시트': sheet, '가공엑셀행': i,
                            '보존수집본': 'Data\\' + str(raw_path.relative_to(DATA)).replace('/', '\\'),
                            '수집본시트': raw_sheet, '수집본엑셀행후보': '|'.join(map(str, positions)),
                            '일치후보수': len(positions), '일치기준': method})
        summary.append({'가공파일': child, '총행수': len(rows), '원문일치행': matched,
                        '완전일치후보가1개인행': unique, '리뷰앞400자와답변일치행': prefix_matched,
                        '보존수집본행수': len(source_rows)})
    with (out / '가공본_수집본_행연결.csv').open('x', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0])); w.writeheader(); w.writerows(records)
    with (out / '추적검증_요약.json').open('x', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
