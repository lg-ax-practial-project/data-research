"""STEP 7: reproduce cross-step evidence and prepare report-ready artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)


def read(relative_path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / relative_path, encoding="utf-8-sig", **kwargs)


reason = read("outputs/step3_final/reason_group_counts.csv")
reason_total = reason.loc[reason["가전품목군"].eq("전체 가전")].iloc[0]
appliance_n = int(reason_total["행분모"])
quality_n = int(reason_total["품질·A/S 일반"])
quality_pct = quality_n / appliance_n * 100
assert (appliance_n, quality_n) == (5554, 3205)
assert pd.isna(reason_total["기준 판정형"])

outcome = read("outputs/step3_final/outcome_group_counts.csv")
outcome_total = outcome.loc[outcome["가전품목군"].eq("전체 가전")].iloc[0]
outcome_n = int(outcome_total["행분모"])
direct_n = int(outcome_total["직접 구제성 처리결과"])
direct_pct = direct_n / outcome_n * 100
assert (outcome_n, direct_n) == (416, 183)

grouped_redress = read("outputs/step3_final/appliance_redress_grouped.csv",
                       dtype=str, keep_default_na=False)
outcome_rows = grouped_redress.loc[grouped_redress["처리결과"].ne("")]
assert len(outcome_rows) == outcome_n
three_remedies = {"환급", "교환", "수리,보수"}
three_n = int(outcome_rows["처리결과"].isin(three_remedies).sum())
quality_q2 = outcome_rows.loc[outcome_rows["청구이유그룹"].eq("품질·A/S 일반")]
quality_three_n = int(quality_q2["처리결과"].isin(three_remedies).sum())
assert (three_n, len(quality_q2), quality_three_n) == (147, 271, 112)

period = read("outputs/step4_trend_age/period_comparisons.csv")
annual = period.loc[period["비교"].eq("연간 동기간")].iloc[0]
assert (int(annual["가전_이전건수"]), int(annual["가전_비교건수"])) == (2392, 2298)
appliance_change_pct = (int(annual["가전_비교건수"]) /
                        int(annual["가전_이전건수"]) - 1) * 100
all_change_pct = (int(annual["전체_비교건수"]) /
                  int(annual["전체_이전건수"]) - 1) * 100
assert round(appliance_change_pct, 4) == round(float(annual["가전_증감률_pct"]), 4)
assert round(all_change_pct, 4) == round(float(annual["전체_증감률_pct"]), 4)

age = read("outputs/step4_trend_age/age_distribution_comparison.csv")
age30 = age.loc[age["연령대_원문"].eq("30 - 39세")].iloc[0]
age40 = age.loc[age["연령대_원문"].eq("40 - 49세")].iloc[0]
age30_n, age40_n = int(age30["가전건수"]), int(age40["가전건수"])
assert (age30_n, age40_n) == (1705, 1643)
age30_pct = age30_n / appliance_n * 100
age40_pct = age40_n / appliance_n * 100
all_age30_n, all_age_den = int(age30["전체건수"]), int(age30["전체분모"])
all_age30_pct = all_age30_n / all_age_den * 100
age3049_n = age30_n + age40_n
age3049_pct = age3049_n / appliance_n * 100

ac = read("outputs/step5_final/air_conditioner_peak_ratio.csv").iloc[0]
ac_peak_n = int(ac["피크월_상담건수_분자"])
ac_winter_median = float(ac["비수기_월별상담건수_중앙값_분모"])
ac_ratio = ac_peak_n / ac_winter_median
assert ac["피크월"] == "2025-07" and int(ac["비수기_관측월수"]) == 14
assert (ac_peak_n, ac_winter_median, round(ac_ratio, 2)) == (1964, 100.5, 19.54)

seven_monthly = read("outputs/step5_final/monthly_seven_appliance_total.csv")
seven_peak = seven_monthly.loc[seven_monthly["7품목_상담건수합"].idxmax()]
seven_peak_month = str(seven_peak["기준월"])
seven_peak_n = int(seven_peak["7품목_상담건수합"])
assert (seven_peak_month, seven_peak_n) == ("2025-07", 3586)

faq = read("outputs/step6_final/criteria_related_share.csv").iloc[0]
faq_n, faq_den = int(faq["건수_분자"]), int(faq["전체가전표준답변_분모"])
faq_pct = faq_n / faq_den * 100
assert (faq_n, faq_den) == (30, 71)

evidence = pd.DataFrame([
    {"질문": "Q1", "한문장답": f"가전 피해구제 중 품질·A/S 일반 청구는 {quality_n:,}/{appliance_n:,}건({quality_pct:.2f}%)이며, 수리 지연·부품 미보유·반복 고장 등 기준 판정형 세부 사유의 건수와 비중은 원문에서 식별할 수 없다.",
     "자료범위": "피해구제 가전 2024Q1~2026Q2", "판정": "부분 확인"},
    {"질문": "Q2", "한문장답": f"가전 피해구제는 2024→2025년 {int(annual['가전_비교건수']):,}/{int(annual['가전_이전건수']):,}건({appliance_change_pct:.2f}%)으로 감소해 전체 피해구제 {int(annual['전체_비교건수']):,}/{int(annual['전체_이전건수']):,}건({all_change_pct:+.2f}%)과 반대였으며, 별도 2026Q2의 직접 구제성 처리결과는 {direct_n}/{outcome_n}건({direct_pct:.2f}%)이다.",
     "자료범위": "2024~2025 연간; 처리결과는 2026Q2만", "판정": "시점 구분 필요"},
    {"질문": "Q3", "한문장답": f"월별 상위 500위 자료의 '에어컨' 표기는 2025년 7월 {ac_peak_n:,}건으로, 관측된 동절기 14개월의 월간 중앙값 {ac_winter_median:g}건 대비 {ac_ratio:.2f}배다.",
     "자료범위": "에어컨 원문 표기 2023-12~2026-07", "판정": "관측 표기 내 확인"},
    {"질문": "Q4", "한문장답": f"가전 표준답변에서 교환·환급·보증·부품·보상액 등 기준 판정 관련 항목은 {faq_n}/{faq_den}개({faq_pct:.2f}%)이며, 이는 실제 소비자 문의 빈도가 아니다.",
     "자료범위": "표준답변 TV·냉장고·룸에어컨 71항목", "판정": "표준답변 항목 비중만 확인"},
    {"질문": "Q5", "한문장답": f"가전 피해구제 신청자는 30~39세가 {age30_n:,}/{appliance_n:,}건({age30_pct:.2f}%)으로 가장 많고, 전체 피해구제에서도 같은 연령대가 {all_age30_n:,}/{all_age_den:,}건({all_age30_pct:.2f}%)으로 최다다.",
     "자료범위": "피해구제 가전 2024Q1~2026Q2", "판정": "신청자 분포 확인"},
])
evidence.to_csv(OUT / "q1_q5_evidence.csv", index=False, encoding="utf-8-sig")

claim_audit = pd.DataFrame([
    {"문장_칸": "품질·A/S 관련 청구", "채움값": f"{quality_pct:.2f}%",
     "분자": quality_n, "분모": appliance_n, "상태": "확인", "근거/제약": "품질(물품/용역)+AS불만"},
    {"문장_칸": "그중 기준 판정이 필요한 유형", "채움값": "___%",
     "분자": pd.NA, "분모": pd.NA, "상태": "확인 불가",
     "근거/제약": "피해구제 청구이유에 수리지연·부품미보유·반복고장 세부값 없음"},
    {"문장_칸": "이 중 환급·교환·수리로 합의·기준 적용", "채움값": "___%",
     "분자": pd.NA, "분모": pd.NA, "상태": "확인 불가",
     "근거/제약": f"2026Q2 환급·교환·수리 기록은 {three_n}/{outcome_n}건, 품질·A/S 일반 내에서는 {quality_three_n}/{len(quality_q2)}건이나 합의·기준 적용 여부 미기록"},
    {"문장_칸": "에어컨 피크/동절기 중앙값", "채움값": f"{ac_ratio:.2f}배",
     "분자": ac_peak_n, "분모": ac_winter_median, "상태": "조건부 확인",
     "근거/제약": "2025-07 피크 vs 관측 11~3월 14개 월간 건수 중앙값; 에어컨 원문 표기만"},
    {"문장_칸": "실제 소비자가 묻는 가전 질문 중 비중", "채움값": "___%",
     "분자": pd.NA, "분모": pd.NA, "상태": "확인 불가",
     "근거/제약": f"실제 문의 빈도 자료 없음; 대체 관측치인 표준답변 항목은 {faq_n}/{faq_den}개({faq_pct:.2f}%)"},
])
claim_audit.to_csv(OUT / "insight_claim_audit.csv", index=False,
                   encoding="utf-8-sig")

graph_items = [
    ("outputs/step3_final/reason_group_heatmap.png",
     "Quality and AS reasons lead among selected appliance cases",
     f"품질(물품/용역)·AS불만의 합은 {quality_n:,}/{appliance_n:,}건({quality_pct:.2f}%); 세부 기준 판정형은 N/A, 품목 2개는 분모 30건 미만."),
    ("outputs/step3_final/outcome_group_100pct_stacked.png",
     "Direct remedies account for 183 of 416 recorded appliance outcomes",
     f"2026Q2에만 처리결과가 있으며 직접 구제성 결과는 {direct_n}/{outcome_n}건({direct_pct:.2f}%); 품목 13개의 분모는 30건 미만."),
    ("outputs/step4_trend_age/quarterly_total_appliance_share.png",
     "Appliance redress fell from 2024 to 2025 while total redress rose",
     f"2024→2025 가전 {int(annual['가전_비교건수']):,}/{int(annual['가전_이전건수']):,}건({appliance_change_pct:.2f}%), 전체 피해구제 {int(annual['전체_비교건수']):,}/{int(annual['전체_이전건수']):,}건({all_change_pct:+.2f}%)."),
    ("outputs/step4_trend_age/quarterly_appliance_lines_by_product.png",
     "Appliance redress counts fluctuate across quarters by product",
     "가전 피해구제의 분기별 움직임은 품목마다 달라 일괄 증가로 요약할 수 없음; 2026Q2 일자 수준 완전성은 미확인."),
    ("outputs/step4_trend_age/age_distribution_comparison.png",
     "Ages 30-39 have the most cases in both appliance and all redress",
     f"가전 피해구제 신청자 중 30~39세 {age30_n:,}/{appliance_n:,}건({age30_pct:.2f}%)이 최다."),
    ("outputs/step5_final/monthly_seven_appliance_timeseries.png",
     f"The seven appliance labels reach their combined peak in {seven_peak_month}",
     f"상위 500위에서 32개월 모두 관측된 7개 표기의 상담 합계는 {seven_peak_month}에 {seven_peak_n:,}건으로 최대."),
    ("outputs/step5_final/air_conditioner_peak_vs_winter.png",
     "Air conditioner consultations in 2025-07 are 19.54 times the winter median",
     f"에어컨 원문 표기 2025-07 한 달 {ac_peak_n:,}건 / 동절기 관측 14개월의 월간 중앙값 {ac_winter_median:g}건 = {ac_ratio:.2f}배; 계절 평균 비교는 아님."),
    ("outputs/step6_final/question_type_bar_chart.png",
     "Criteria-related topics account for 30 of 71 appliance FAQ entries",
     f"기준 판정 관련 표준답변은 {faq_n}/{faq_den}항목({faq_pct:.2f}%); 실제 문의 빈도가 아니며 무작위 30건 검수 전 분류."),
]
graphs = pd.DataFrame(graph_items, columns=["파일명", "제목", "보여주는 결론"])
assert all((ROOT / item).is_file() for item in graphs["파일명"])
graphs.to_csv(OUT / "report_graph_inventory.csv", index=False,
              encoding="utf-8-sig")

report_log = f"""# 전처리 로그 — 리포트 수록용 최종본

## 공통 원칙과 원본 보존

1. 공공데이터 원본 CSV를 수정하지 않고, 단계별 파생 CSV로 저장했다. macOS의 분해형 한글 파일명을 찾을 때 파일명 비교에만 Unicode NFC 정규화를 사용했다.
2. CSV는 UTF-8-SIG로 먼저 읽고 실패하면 CP949로 읽었다. 피해구제 원본 10개와 코드표는 CP949, 표준답변 1개도 CP949였다. 월별 상담 32개는 파일별로 인코딩을 확인해 읽었다.
3. 결측은 null 및 빈칸·공백으로 확인했다. `불명`, `(미입력)` 같은 원문 범주는 임의로 결측으로 바꾸지 않았다. 결측을 0으로 대체하지 않았다. 원본 문자열, 파일명, 행 번호를 가능한 범위에서 보존했다.

## 소비자 피해구제 정보와 품목 코드표 — STEP 1

4. 분기별 피해구제 CSV 10개의 150,964행을 결합했다. `물품명`과 `물품소분류`를 표준 열 `물품소분류`로, `연령`과 `연령대`를 `연령대`로, `접수일(년월일)`과 `접수일`을 `접수일`로 통일했다. 원문 값은 보존했다.
5. `접수일`이 YYYY-MM-DD인 행은 날짜를 검증해 `접수연도`·`접수분기`를 만들었다. `2026년 2분기` 표기는 연도·분기만 추출하고 일자를 만들어 넣지 않았다. 2026Q2의 일자 수준 완전성은 검증할 수 없다.
6. 코드표 `소분류품목`과 피해구제 품목명은 양끝 공백을 제거하고 연속 공백을 한 칸으로 치환한 키로 완전일치 연결했다. 철자·동의어·구두점은 임의 변경하지 않았다. 매핑 적격 150,960행 중 150,288행 일치, 672행 불일치, 원문 품목명 결측 4행이었다. 코드표 키 중복은 0건이었고 불일치 목록을 별도 보존했다.
7. 파일 간 같은 사건번호를 임의로 중복 제거하지 않았다. 판매유형·판매방법은 별도 열로 유지했다. 2026Q2의 사건번호 부재와 이전 9개 파일의 처리결과 부재는 결측으로 유지했다.

## 가전 대상 선별 — STEP 2

8. 사용자 확정 기준에 따라 렌탈, 서비스, 부품·액세서리·주변용품, 설비·비전기 기기, 기타·정체 불명, 생활·개인 전자기기 경계군을 제외했다. 가스에어컨, 소형 조리·난방 잡화, 다리미 등 지정 제외 품목도 포함하지 않았다.
9. 가전 본체는 원문 품목명 허용 목록 25개를 19개 품목군으로 분류했다. 룸·시스템·이동식에어컨과 `팬코일(이동식에어컨)`을 포함했다. 마지막 표기 25건은 코드표 불일치 뒤 이동식에어컨 키워드로 보조 판정했다. 청소기는 전기진공·로봇, 조리가전은 인덕션·전기오븐·전자레인지·복합오븐만 포함했다.
10. 최종 가전 피해구제는 5,554행이며 전체 피해구제 비중의 분모는 150,964행이다. 원본 전체에서 행을 삭제하지 않고 가전 데이터셋을 별도로 추출했다.

## 청구이유와 처리결과 — STEP 3

11. `품질(물품/용역)`과 `AS불만`만 `품질·A/S 일반`으로 묶었다. 그 밖의 비결측 청구이유 14종은 사용자 승인대로 `계약·기타`로, 결측 3행은 `미분류`로 유지했다. 세 범주의 비중 분모에는 결측을 포함한 가전 5,554행을 사용했다.
12. 원문 청구이유에 수리 지연·부품 미보유·동일 하자 반복·수리 불가를 직접 식별하는 별도 값이 없어 `기준 판정형`은 **식별 불가**로 표시했다. 0건·0% 또는 품질·A/S 일반의 대리값으로 표시하지 않았다.
13. 처리결과는 2026Q2 가전 416행에만 기록되어 있다. 다른 9개 파일 가전 5,138행의 빈 처리결과를 0건으로 처리하지 않았다. `환급`·`수리,보수`·`배상`·`교환`을 직접 구제성 처리결과, `계약이행`·`계약해제`·`부당행위시정`을 계약 조치, `조정신청`·`처리중`을 절차 진행, 나머지 4종을 구제 확인 불가로 분류했다.
14. 처리결과 비중의 분모는 2026Q2 결과기록 416행이다. 처리결과 명칭만으로 합의 여부나 소비자분쟁해결기준의 실제 적용 여부를 판정하지 않았다. 품목×범주 교차표에서 관측 집단 내 미출현 조합의 0과 원본 결측을 구별했다.

## 분기 추이와 연령대 — STEP 4

15. 2024Q1~2026Q2 피해구제는 `접수연도`·`접수분기`로 집계했다. 연간 비교는 완전한 2024년과 2025년, 상반기 비교는 2025H1과 2026H1로 고정했다. 2026Q2는 분기 표기뿐이라 일자별 완전성을 보증할 수 없음을 별도 표시했다.
16. 분기별 가전 비중은 그 분기 가전 행 수 / 전체 피해구제 행 수, 증감률은 (비교기간−이전기간) / 이전기간으로 계산했다. 관측된 분기 안에서 품목이 나타나지 않은 조합의 집계 0은 원본 결측 대체와 다르다.
17. 연령대는 원문 범주 그대로 계산했다. `불명`과 `(미입력)`을 합치거나 제외하지 않았고, 가전·전체 각각 모든 행을 비율 분모로 사용했다.

## 월별 품목 상담 현황 — STEP 5

18. 월별 상위 500위 CSV 32개, 총 16,000행을 결합했다. 초기 4열 스키마와 이후 6열 스키마의 열 이름을 통일했고 2024-06 파일의 헤더 양끝 공백만 제거했다. 원문 품목명은 변경하지 않았다.
19. 원본 `연도`·`월` 열이 있는 파일은 파일명과 일치 검증했다. `20240103.CSV`의 기준월은 2023-12, `20240201.csv`는 2024-01로 전월 건수·증감률을 근거로 추론했다. 이 두 기준월은 원본 날짜 열로 직접 검증할 수 없다. `기준월_날짜`는 시계열 결합용 해당 월 1일이지 상담 접수일이 아니다.
20. 천 단위 쉼표는 수치 변환 시에만 제거하고 원문 문자열도 별도 보존했다. 원문 전월·전년동월 증감률은 동일 품목의 비교월이 관측될 때만 대조했다. 2024-07 제공 전월률은 직전 6월보다 5월 건수와 대부분 부합하므로 원인을 단정하지 않고 최종 추이에는 원문 증감률을 사용하지 않았다.
21. 어떤 품목이 특정 월 상위 500위에 없으면 알 수 없음(NaN)으로 유지했다. 원문 품목명 기준 월별 피벗에서 빈칸을 0으로 채우지 않았다.
22. 최종 7품목 시계열에는 32개월 모두 관측된 원문 `냉장고`, `김치냉장고`, `전기세탁기`, `전기의류건조기`, `TV`, `식기세척기`, `에어컨`만 정확히 일치 매핑했다. 이동식에어컨·팬코일, 워시타워·냉동고·식기건조기·포괄 냉장냉동기기, 서비스·용품·방송서비스 유사어는 제외했다. 선택 7종의 224개 월별 셀에는 NaN이 없었다.
23. 7품목 월별 합계는 모두 관측된 달에만 합산했다(`min_count=7`). 이는 선정 7개 표기의 합이며 전체 가전 상담이 아니다. 에어컨 피크는 관측 32개월 중 최대 월, 비수기는 관측 기간 11~3월 14개 월간 건수의 중앙값으로 정의했다.

## 소비자상담 표준답변 — STEP 6

24. 표준답변 CSV는 1,332행, 56개 원문 품목명이다. 모든 행의 품목명 선행 공백을 별도 표준 열에서 `strip`하고 `TV` 26행, `냉장고` 22행, `룸에어컨` 23행만 정확히 일치 추출했다. 정수기대여 43행은 렌탈 제외 기준에 따라 제외했다. 최종 분석 단위는 71개 표준답변 항목이다.
25. 서로 다른 품목의 동일 질문 문구도 품목별 표준답변 항목으로 유지해 중복 제거하지 않았다. `질문` 원문만 분류 입력으로 사용하고 `답변`은 사용하지 않았다. `구분`은 검수용으로만 보존했다. 검색용 질문 사본에서만 NFC 정규화·연속 공백 단일화·영문 대소문자 무시를 적용했다.
26. 사용자 승인 우선순위는 감가상각·보상액→부품→교환·환급→보증기간·무상수리→설치·배송→수리·고장 일반→기타다. 사은품 자체 분쟁·매장 가격 차액·단순 청약철회/계약 미환급은 기타, 비용 쟁점인 택배비·배송비·출장비·설치비는 설치·배송, 과거 교환 이력만 있는 고장 문의는 수리·고장 일반으로 우선 예외 처리했다.
27. 감가상각·보상액은 금액 **산정** 표현과 제품 A/S 맥락이 함께 있을 때만, 교환·환급은 현재 구제 요구와 A/S 맥락이 함께 있을 때만 부여했다. 전수 대조 후 `구입가 환급받을 수 있나요`의 `구입가` 단독은 금액 산정 키워드에서 제외하고, 일반 고장의 `소음` 표현을 추가했다. 적용 규칙·매칭 표현을 행별 파일에 남겼다.
28. 유형 비중은 각 유형 항목 수 / 71개 표준답변 항목이다. `기준 판정 관련`은 교환·환급·보증기간·무상수리·부품·감가상각·보상액 네 유형의 합집합 항목 수 / 71개다. 표준답변은 사전 작성된 템플릿이므로 이 비중을 실제 소비자 문의 발생 빈도로 해석하지 않는다.
29. 검수표는 71개 중 난수 시드 `20260924`, 비복원 추출로 30개를 뽑고 번호순으로 정렬했다. 사용자 검수자 정답과 일치여부는 비워 두었으며 검수 전 일치율은 계산하지 않았다.

## 보고서 종합 — STEP 7

30. 본 단계는 위 파생 CSV에서 수치를 다시 계산하고 시점·모집단·분모를 대조했다. 원문에 없는 기준 판정형 사유, 합의·기준 적용, 실제 소비자 문의 비중은 미확인으로 남겼다. 새로운 제외·결측 대체·분류를 적용하지 않았다.
"""
(OUT / "preprocessing_log_report.md").write_text(report_log, encoding="utf-8")
prior_log = (ROOT / "outputs/step6_final/preprocessing_log.md").read_text(encoding="utf-8")
full_log = (
    "# 누적 전처리 로그 전체 — STEP 1~7\n\n"
    "각 단계의 '미확정'·'아직 수행하지 않음'은 해당 단계 시점의 상태이며, 이후 승인·적용 기록이 뒤따른다.\n\n"
    + prior_log
    + "\n\n## STEP 7 보고서 종합 (2026-09-24)\n\n"
    "1. 앞 단계의 파생 CSV에서 Q1~Q5의 분자·분모·시점을 다시 계산하고 확인했다. 새로운 원본 행 제외, 결측 대체, 범주 매핑은 수행하지 않았다.\n"
    "2. 원문에 없는 기준 판정형 세부 사유, 합의·기준 적용 여부, 실제 소비자 문의 빈도는 확인 불가로 표시했다. 서로 다른 표본의 비율을 한 분모로 합산하지 않았다.\n"
    "3. 리포트용 정리본은 `preprocessing_log_report.md`, 주장별 확인 여부는 `insight_claim_audit.csv`, 재현 코드는 `synthesize_step7.py`에 저장했다.\n"
)
(OUT / "preprocessing_log_full.md").write_text(full_log, encoding="utf-8")

template = (
    f"가전 피해구제 중 품질·A/S 관련 청구가 {quality_pct:.2f}%({quality_n:,}/{appliance_n:,}건)이며, "
    "그중 기준 판정이 필요한 유형이 ___%[확인 불가]를 차지한다. "
    "이 중 ___%[확인 불가]는 환급·교환·수리로 합의되어 기준 적용 시 해결 가능한 분쟁임을 보여준다. "
    f"한편 에어컨 상담은 성수기 피크 월에 비수기 대비 {ac_ratio:.2f}배"
    f"({ac_peak_n:,}건/{ac_winter_median:g}건)로 늘고, "
    "소비자가 묻는 가전 질문의 ___%[확인 불가]가 교환·환급·보상 기준에 관한 것이다."
)
accurate = (
    f"가전 피해구제 {appliance_n:,}건 중 `품질(물품/용역)`·`AS불만`은 {quality_n:,}건({quality_pct:.2f}%)이었다. "
    f"2024년 대비 2025년 가전 피해구제는 {int(annual['가전_비교건수']):,}/{int(annual['가전_이전건수']):,}건({appliance_change_pct:.2f}%)으로 감소했고, "
    f"전체 피해구제는 {int(annual['전체_비교건수']):,}/{int(annual['전체_이전건수']):,}건({all_change_pct:+.2f}%)이었다. "
    f"처리결과가 기록된 2026년 2분기 가전 {outcome_n}건 중 환급·수리·배상·교환은 {direct_n}건({direct_pct:.2f}%)이었다. "
    f"별도 월별 자료에서 `에어컨`의 2025년 7월 {ac_peak_n:,}건은 동절기 14개 관측월의 월간 중앙값 {ac_winter_median:g}건의 {ac_ratio:.2f}배 수준이었다. "
    f"가전 표준답변 {faq_den}항목 중 검수 전 키워드 분류상 기준 판정 관련 항목은 {faq_n}개({faq_pct:.2f}%)였다. "
    "이 자료만으로 세부 판정 사유, 실제 기준 적용 및 실제 소비자 문의 빈도는 확인할 수 없다."
)
limits = [
    "공공 피해구제·상담 자료는 LG전자 고객이나 실제 A/S 접수·수리 사건만을 식별하지 못하므로 Agent 도입 효과나 이탈 원인을 인과적으로 입증하지 못한다.",
    "피해구제 청구이유에 수리 지연·부품 미보유·반복 고장 등 세부 사유가 없어 기준 판정형 건수·비중을 계산할 수 없고, 처리결과만으로 합의·기준 적용 여부를 알 수 없다.",
    "처리결과는 10개 분기 파일 중 2026Q2 가전 416행에만 있으며, 2026Q2는 일자 아닌 분기 표기라 완전성을 일자 단위로 확인할 수 없다. 품목별 처리결과 비율 중 13개 품목의 분모는 30건 미만이다.",
    "월별 상담은 월마다 상위 500품목만 있어 목록 밖 품목의 건수는 알 수 없다. 7개 연속 관측 표기만 Q3에 사용했고 초기 두 기준월은 추론값이며 2024-07 제공 전월률도 직접 계산과 맞지 않는다. 19.54배의 기준은 관측된 동절기 14개월의 월간 중앙값이다.",
    "표준답변 71항목은 편집된 질문 템플릿이므로 Q4의 30/71은 실제 문의 빈도가 아니다. 일곱 질문유형의 개별 건수는 모두 30건 미만이고 난수 30건의 사용자 검수·분류 일치율 계산도 아직 끝나지 않았다.",
]
report_parts = ["# STEP 7 인사이트 리포트용 분석 종합", "", "## Q1~Q5 한 문장 답", ""]
report_parts += [f"- **{row.질문}.** {row.한문장답}" for row in evidence.itertuples(index=False)]
report_parts += ["", "## 요청한 문장 — 미확인 칸 표시(보고서 사용 불가)", "",
                 "원안의 합의·기준 적용·실제 질문 빈도 표현은 데이터가 직접 뒷받침하지 않는다.",
                 "", template,
                 "", "## 자료 범위에 맞춘 권장 문장", "", accurate,
                 "", "## 그래프 목록", "",
                 "| 파일명 | 제목 | 보여주는 결론 |", "|---|---|---|"]
for row in graphs.itertuples(index=False, name=None):
    report_parts.append(f"| `{row[0]}` | {row[1]} | {row[2]} |")
report_parts += ["", "## 분석의 한계", ""]
report_parts += [f"{index}. {limit}" for index, limit in enumerate(limits, 1)]
report_parts += ["", "## 전처리 로그", "", report_log]
(OUT / "report_ready_summary.md").write_text("\n".join(report_parts), encoding="utf-8")

# Evidence matrix presents scopes without putting incompatible percentages on
# one shared quantitative axis.
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
title_font = ImageFont.truetype(font_path, 23)
body_font = ImageFont.truetype(font_path, 16)
small_font = ImageFont.truetype(font_path, 14)
figure = Image.new("RGB", (1330, 540), "white")
draw = ImageDraw.Draw(figure)
draw.text((26, 20), "Public data answers the fixed questions, while three proposed claims remain unverified.",
          fill="#17344a", font=title_font)
draw.text((27, 55), "Different rows use different source populations; each value shows its own denominator.",
          fill="#526674", font=small_font)
cards = [
    ("Q1  Reason", f"{quality_n:,}/{appliance_n:,} = {quality_pct:.2f}%", "Criteria-specific detail unavailable", "#277da8"),
    ("Q2  Trend / outcome", f"{int(annual['가전_비교건수']):,}/{int(annual['가전_이전건수']):,} = {appliance_change_pct:+.2f}%", f"Direct remedy {direct_n}/{outcome_n} = {direct_pct:.2f}% (2026 Q2)", "#277da8"),
    ("Q3  Air conditioner", f"{ac_peak_n:,}/{ac_winter_median:g} = {ac_ratio:.2f}x", "2025-07 peak / 14-month winter median", "#277da8"),
    ("Q4  FAQ templates", f"{faq_n}/{faq_den} = {faq_pct:.2f}%", "Not actual contact frequency", "#cf8b48"),
    ("Q5  Applicant age", f"{age30_n:,}/{appliance_n:,} = {age30_pct:.2f}%", "Age 30-39 is the largest appliance band", "#277da8"),
]
for index, (label, metric, note, color) in enumerate(cards):
    top = 100 + index * 84
    draw.rounded_rectangle((25, top, 1303, top+72), radius=9, fill="#f5f8fa")
    draw.rectangle((25, top, 34, top+72), fill=color)
    draw.text((53, top+11), label, fill="#17344a", font=body_font)
    draw.text((380, top+11), metric, fill=color, font=body_font)
    draw.text((380, top+40), note, fill="#526674", font=small_font)
figure.save(OUT / "q1_q5_evidence_matrix.png")

print("Q1", f"{quality_n}/{appliance_n}={quality_pct:.4f}%", "criteria_specific=NA")
print("Q2", f"appliance_2025/2024={int(annual['가전_비교건수'])}/{int(annual['가전_이전건수'])} "
      f"change={appliance_change_pct:.4f}%",
      f"all_2025/2024={int(annual['전체_비교건수'])}/{int(annual['전체_이전건수'])} "
      f"change={all_change_pct:.4f}%",
      f"direct_remedy={direct_n}/{outcome_n}={direct_pct:.4f}%")
print("Q2_TEMPLATE_AUDIT", f"refund_exchange_repair={three_n}/{outcome_n}={three_n/outcome_n*100:.4f}%",
      f"within_quality_Q2={quality_three_n}/{len(quality_q2)}={quality_three_n/len(quality_q2)*100:.4f}%",
      "settlement_and_standard_application=NA")
print("Q3", f"AC_peak={ac_peak_n}/{ac_winter_median:g}={ac_ratio:.6f}x")
print("Q3_SEVEN", f"seven_label_peak={seven_peak_month}:{seven_peak_n}")
print("Q4", f"faq_templates={faq_n}/{faq_den}={faq_pct:.4f}%", "actual_question_frequency=NA")
print("Q5", f"age30={age30_n}/{appliance_n}={age30_pct:.4f}%",
      f"all_age30={all_age30_n}/{all_age_den}={all_age30_pct:.4f}%",
      f"age40={age40_n}/{appliance_n}={age40_pct:.4f}%",
      f"age30_49={age3049_n}/{appliance_n}={age3049_pct:.4f}%")
print("GRAPH_COUNT", len(graphs), "LIMIT_COUNT", len(limits))
print("TEMPLATE", template)
print("ACCURATE", accurate)
