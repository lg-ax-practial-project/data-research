"""Critical audit of STEP 7 claims against the row-level derived datasets."""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

def load(path):
    return pd.read_csv(ROOT / path, encoding="utf-8-sig", dtype=str,
                       keep_default_na=False)

appliance = load("outputs/step2_final/appliance_redress.csv")
all_redress = load("outputs/step1_standardization/standardized_redress.csv")
monthly = load("outputs/step5_final/monthly_seven_appliances_long.csv")
classified = load("outputs/step6_final/classified_appliance_questions.csv")

# Recalculate without using the STEP 7 summary or precalculated percentage CSVs.
quality = int(appliance["청구이유"].isin(["품질(물품/용역)", "AS불만"]).sum())
quality_den = len(appliance)
q2 = appliance.loc[(appliance["접수연도"] == "2026") &
                   (appliance["접수분기"] == "2")]
direct_labels = ["환급", "수리,보수", "배상", "교환"]
direct = int(q2["처리결과"].isin(direct_labels).sum())
direct_den = len(q2)
three_remedies = int(q2["처리결과"].isin(["환급", "교환", "수리,보수"]).sum())
ac = monthly.loc[monthly["품목명_원문"] == "에어컨"].copy()
ac["상담건수"] = pd.to_numeric(ac["상담건수"], errors="raise")
peak = ac.loc[ac["상담건수"].idxmax()]
winter = ac.loc[ac["월"].astype(int).isin([11, 12, 1, 2, 3])]
winter_median = float(winter["상담건수"].median())

assert (quality, quality_den) == (3205, 5554)
assert (direct, direct_den) == (183, 416)
assert three_remedies == 147
assert (peak["기준월"], int(peak["상담건수"]), len(winter), winter_median) == ("2025-07", 1964, 14, 100.5)

appliance_year = appliance["접수연도"].value_counts()
all_year = all_redress["접수연도"].value_counts()
faq_criteria = int(classified["기준판정관련"].eq("True").sum())
assert (int(appliance_year["2024"]), int(appliance_year["2025"])) == (2392, 2298)
assert (int(all_year["2024"]), int(all_year["2025"])) == (57657, 63671)
assert (faq_criteria, len(classified)) == (30, 71)
share_2024 = int(appliance_year["2024"]) / int(all_year["2024"]) * 100
share_2025 = int(appliance_year["2025"]) / int(all_year["2025"]) * 100

checks = pd.DataFrame([
    ["품질·A/S 일반", quality, quality_den, quality / quality_den * 100, "전 기간 가전 피해구제"],
    ["직접 구제성 처리결과", direct, direct_den, direct / direct_den * 100, "2026Q2만"],
    ["에어컨 피크/동절기 중앙값", int(peak["상담건수"]), winter_median,
     int(peak["상담건수"]) / winter_median, "2025-07 피크 vs 동절기 14개월"],
    ["가전 2025/2024 증감률", int(appliance_year["2025"]), int(appliance_year["2024"]),
     (int(appliance_year["2025"]) / int(appliance_year["2024"]) - 1) * 100, "완전한 두 연도"],
    ["전체 2025/2024 증감률", int(all_year["2025"]), int(all_year["2024"]),
     (int(all_year["2025"]) / int(all_year["2024"]) - 1) * 100, "완전한 두 연도"],
    ["표준답변 기준 판정 관련", faq_criteria, len(classified),
     faq_criteria / len(classified) * 100, "질문 템플릿 항목 비중"],
], columns=["지표", "분자", "분모_또는_비교기준", "재계산값", "해석범위"])
checks.to_csv(OUT / "key_number_recheck.csv", index=False, encoding="utf-8-sig")

outcome_product = q2.groupby("가전품목군").size().sort_values()
redress_product = appliance.groupby("가전품목군").size().sort_values()
faq_type = classified.groupby("질문유형").size().sort_values()
faq_product = classified.groupby("품목명_표준").size().sort_values()
outcome_type = q2.groupby("처리결과").size().sort_values()
small = pd.concat([
    pd.DataFrame({"표본단위": "2026Q2 처리결과 품목별 분모", "범주": outcome_product.index,
                  "건수": outcome_product.values}),
    pd.DataFrame({"표본단위": "가전 피해구제 품목별 분모", "범주": redress_product.index,
                  "건수": redress_product.values}),
    pd.DataFrame({"표본단위": "표준답변 질문유형별 건수", "범주": faq_type.index,
                  "건수": faq_type.values}),
    pd.DataFrame({"표본단위": "표준답변 품목별 분모", "범주": faq_product.index,
                  "건수": faq_product.values}),
    pd.DataFrame({"표본단위": "2026Q2 원문 처리결과별 건수", "범주": outcome_type.index,
                  "건수": outcome_type.values}),
], ignore_index=True)
small = small.loc[small["건수"] < 30].sort_values(["표본단위", "건수", "범주"])
small.to_csv(OUT / "small_cells_under_30.csv", index=False, encoding="utf-8-sig")

print("RECHECK_1 quality", f"{quality}/{quality_den}={quality/quality_den*100:.2f}%")
print("RECHECK_2 direct_remedy", f"{direct}/{direct_den}={direct/direct_den*100:.2f}%", "scope=2026Q2")
print("RAW_THREE_REMEDIES", f"{three_remedies}/{direct_den}={three_remedies/direct_den*100:.2f}%", "settlement_and_standard_application=not_recorded")
print("RECHECK_3 ac_peak", f"{int(peak['상담건수'])}/{winter_median:g}={int(peak['상담건수'])/winter_median:.2f}x", f"winter_months={len(winter)}")
print("TREND appliance", f"{int(appliance_year['2025'])}/{int(appliance_year['2024'])}={(int(appliance_year['2025'])/int(appliance_year['2024'])-1)*100:+.2f}%")
print("TREND all", f"{int(all_year['2025'])}/{int(all_year['2024'])}={(int(all_year['2025'])/int(all_year['2024'])-1)*100:+.2f}%")
print("TREND appliance_share", f"{share_2024:.2f}%->{share_2025:.2f}%")
print("FAQ", f"{faq_criteria}/{len(classified)}={faq_criteria/len(classified)*100:.2f}%")
for unit, rows in small.groupby("표본단위", sort=False):
    print("SMALL", unit, "count=", len(rows), ", ".join(f"{r.범주}:{r.건수}" for r in rows.itertuples()))

review = f"""# STEP 7 인사이트 비판적 검증

## 판정

주요 계산값은 재계산과 일치한다. 다만 해석의 범위와 작은 분모 표시를 고쳐야 한다.

| 점검 대상 | 확인 결과 | 수정안 |
|---|---|---|
| 품질·A/S 일반 {quality:,}/{quality_den:,}건({quality/quality_den*100:.2f}%) | `품질(물품/용역)`과 `AS불만`의 승인된 합이다. 이 중 세부 수리 지연·반복 고장 건수는 알 수 없다. | `품질·A/S 일반 청구 비중`이라고 쓰고 Agent의 세부 판정 수요로 대체하지 않는다. |
| 직접 구제성 결과 {direct}/{direct_den}건({direct/direct_den*100:.2f}%) | 2026년 2분기에 한정되며 환급·수리·배상·교환의 결과명 합이다. 환급·교환·수리만은 {three_remedies}/{direct_den}건({three_remedies/direct_den*100:.2f}%)이다. 합의·기준 적용 기록은 없다. | `직접 구제성 처리결과로 기록`이라고 쓰고 `기준 적용 시 해결 가능한 분쟁`이라는 결론은 삭제한다. |
| 에어컨 {int(peak['상담건수']):,}/{winter_median:g}건({int(peak['상담건수'])/winter_median:.2f}배) | 단일 최고 월과 동절기 {len(winter)}개 관측월의 월간 중앙값 비교다. 계절 전체 평균이나 매년 반복되는 배율이 아니다. | `2025년 7월 관측치가 동절기 월간 중앙값의 19.54배 수준`이라고 쓴다. |
| 표준답변 {faq_criteria}/{len(classified)}항목({faq_criteria/len(classified)*100:.2f}%) | 편집된 질문 템플릿의 키워드 분류 비중이며 무작위 30건 사용자 검수 전이다. | `실제 소비자 질문의 비중` 대신 `선정한 가전 표준답변 항목 중 비중`이라고 쓴다. |
| 연령대 | 접수자의 연령 분포이지 연령별 인구 대비 피해 위험이 아니다. | `30대 신청자가 가장 많다`고만 쓴다. |

## 증가 주장 점검

2024년 대비 2025년 가전 피해구제는 {int(appliance_year['2025']):,}/{int(appliance_year['2024']):,}건({(int(appliance_year['2025'])/int(appliance_year['2024'])-1)*100:+.2f}%)으로 감소했다. 전체 피해구제는 {int(all_year['2025']):,}/{int(all_year['2024']):,}건({(int(all_year['2025'])/int(all_year['2024'])-1)*100:+.2f}%)으로 증가했으며, 전체 대비 가전 비중은 {share_2024:.2f}%에서 {share_2025:.2f}%로 내려갔다. 따라서 `가전 피해구제가 증가한다`거나 `전체보다 빠르게 증가한다`는 문장은 쓰지 않는다. 관측된 두 역년의 비교를 장기 추세로 확장하지 않는다.

## 30건 미만의 작은 분모

- 2026년 2분기 품목별 처리결과 비율의 분모가 30건 미만인 품목은 {len(outcome_product[outcome_product < 30])}개다. 특히 식기건조기 1건, 냉동고 4건, 워시타워·의류관리기·제습기 각 5건이다. 100% 누적 막대에서 이들의 비율을 품목 비교의 근거로 삼지 않는다.
- 전 기간 품목별 청구이유 비율의 분모가 30건 미만인 품목은 워시타워 18건, 식기건조기 14건이다.
- 표준답변의 품목별 분모는 TV 26개, 냉장고 22개, 룸에어컨 23개로 모두 30개 미만이다. 일곱 질문유형의 개별 **분자**도 모두 30개 미만이지만, 전체 유형 비중의 분모는 71개다. 이를 `분모 30 미만`과 혼동하지 않는다.
- 에어컨 비수기 기준은 사례 14건이 아니라 **월간 관측치 14개**의 중앙값이다. 한 달의 극값과 이 중앙값의 비율을 계절 평균 배율로 일반화하지 않는다.

전체 목록과 건수는 `small_cells_under_30.csv`에 있다. 신규 품목 제외·그룹 변경은 수행하지 않았다.

## 리포트용 수정 문장

가전 피해구제 {quality_den:,}건 중 `품질(물품/용역)`·`AS불만`은 {quality:,}건({quality/quality_den*100:.2f}%)이었다. 2024년 대비 2025년 가전 피해구제는 {int(appliance_year['2025']):,}/{int(appliance_year['2024']):,}건({(int(appliance_year['2025'])/int(appliance_year['2024'])-1)*100:+.2f}%)으로 감소했다. 처리결과가 기록된 2026년 2분기 가전 {direct_den}건 중 환급·수리·배상·교환은 {direct}건({direct/direct_den*100:.2f}%)이었다. 별도 상담 자료에서 `에어컨`의 2025년 7월 {int(peak['상담건수']):,}건은 동절기 {len(winter)}개 관측월의 월간 중앙값 {winter_median:g}건의 {int(peak['상담건수'])/winter_median:.2f}배 수준이었다. 선정한 가전 표준답변 {len(classified)}항목 중 검수 전 키워드 분류상 기준 판정 관련 항목은 {faq_criteria}개({faq_criteria/len(classified)*100:.2f}%)였다. 이 자료만으로 세부 판정 사유, 실제 기준 적용, 상담 대기·이탈, 실제 문의 빈도는 확인할 수 없다.
"""
(OUT / "critical_review.md").write_text(review, encoding="utf-8")
