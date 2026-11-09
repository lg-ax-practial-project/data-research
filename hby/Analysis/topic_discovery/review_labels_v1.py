"""기존 AI/규칙 라벨을 재집계한다. 정확도나 사람 검수 완료를 뜻하지 않는다."""
from collections import Counter
import csv
import json
import re
from verify_existing_v1 import DATA, OUT, sheet_rows

OUT = OUT.parent / '정성검토_v1'


def clean(text):
    text = re.sub(r'https?://\S+|www\.\S+', '[링크 제외]', text)
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[이메일 제외]', text)
    text = re.sub(r'@[\w가-힣.-]+', '[계정 제외]', text)
    text = re.sub(r'(?<!\d)(?:\+82[- ]?)?0\d{1,2}[- .]?\d{3,4}[- .]?\d{4}(?!\d)', '[연락처 제외]', text)
    return ' '.join(text.split())[:650]


def main():
    OUT.mkdir(exist_ok=False)
    base = DATA / 'drive-download-20261109T000429Z-1-001'
    counts, cases = [], []
    for name, wanted in [
        ('LG에어컨_유튜브댓글_3차_표본분석_가설종합.xlsx', {'표본 분류결과'}),
        ('LG에어컨_가설검증_최종.xlsx', {'구글플레이 표본 분류', '스마트진단 언급 전수'}),
        ('LG공식답변_해결과정_분석.xlsx', {'유튜브 표본150', '유튜브 후속반응70', '구글플레이 답변분류'}),
    ]:
        path = next(base.rglob(name))
        source = 'Data\\' + str(path.relative_to(DATA)).replace('/', '\\')
        for sheet, all_rows in sheet_rows(path):
            if sheet not in wanted:
                continue
            rows = all_rows[1:]

            def aggregate(label, selected, col):
                for key, n in sorted(Counter(r.get(col, '') for _, r in selected).items()):
                    counts.append({'파일': source, '시트': sheet, '선정집단': label, '라벨열': col,
                                   '라벨값': key, '건수': n, '분모': len(selected),
                                   '검증상태': '기존 라벨 재집계; 원문 전수 재분류 아님'})

            def sample(label, subset, textcol, max_cases=2):
                for i, r in subset[:max_cases]:
                    cases.append({'파일': source, '시트': sheet, '엑셀행': i, '선정이유': label,
                                  '내용열': textcol, '발췌': clean(r.get(textcol, '')),
                                  '검토한계': '기존 라벨로 목적 선정; 빈도 추정 또는 외부 검증 아님'})

            if sheet == '표본 분류결과':
                target = [(i, r) for i, r in rows if r.get('J') == '본인 문제·질문'
                          and r.get('K') == 'LG' and r.get('L') == '에어컨']
                aggregate('LG 에어컨 본인 문제', target, 'N')
                for col in ['O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V']:
                    aggregate('LG 에어컨 본인 문제', target, col)
                for label, col in [('자가 시도로 새 문제 주장', 'T'), ('AS 대신 해결 주장', 'R'),
                                   ('이미 시도한 조치 실패', 'O'), ('AS 이후 미해결 주장', 'P')]:
                    sample(label, [(i, r) for i, r in target if r.get(col) == 'Y'], 'H')
                sample('스스로 해결로 분류된 반례', [(i, r) for i, r in target if r.get('N') == '스스로 해결'], 'H', 1)
            elif sheet == '구글플레이 표본 분류':
                for period in ['평상시', '2026-07 장애기간']:
                    target = [(i, r) for i, r in rows if r.get('B') == period and r.get('F') == '문제 리뷰']
                    aggregate(period + ' 문제 리뷰', target, 'H')
                    for col in ['J', 'K', 'L']:
                        aggregate(period + ' 문제 리뷰', target, col)
                sample('권장 조치 이후 악화 주장', [(i, r) for i, r in rows if r.get('K') == 'Y'], 'E')
                sample('문의 경로 막힘 주장', [(i, r) for i, r in rows if r.get('L') == 'Y'], 'E')
            elif sheet == '스마트진단 언급 전수':
                aggregate('진단 언급 17행', rows, 'D')
            elif sheet == '유튜브 표본150':
                for label in ['고장·이상 증상', '사용법·정보·호환']:
                    aggregate(label, [(i, r) for i, r in rows if r.get('D') == label], 'E')
            elif sheet == '유튜브 후속반응70':
                aggregate('후속반응 관측 70행', rows, 'E')
            elif sheet == '구글플레이 답변분류':
                aggregate('답변기록 3033행', rows, 'G')
                target = [(i, r) for i, r in rows if r.get('J') == 'Y']
                aggregate('문의불가 기존 규칙 라벨', target, 'G')
                sample('문의불가 주장인데 이관 분류', [(i, r) for i, r in target if r.get('G') == '이관'], 'C')
    for name, records in [('라벨_재집계.csv', counts), ('목적선정_사례발췌.csv', cases)]:
        with (OUT / name).open('x', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(records[0]))
            w.writeheader()
            w.writerows(records)
    print(json.dumps(cases, ensure_ascii=False, indent=2))
    print('집계 항목', len(counts), '선정 사례', len(cases))


if __name__ == '__main__':
    main()
