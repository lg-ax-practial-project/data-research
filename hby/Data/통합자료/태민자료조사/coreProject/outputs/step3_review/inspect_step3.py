"""STEP 3 raw cross-tabs and grouping proposals; no proposed group is applied."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
SRC = ROOT / "outputs" / "step2_final" / "appliance_redress.csv"
GROUPS = ROOT / "outputs" / "step2_final" / "appliance_group_summary.csv"

df = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False,
                 low_memory=False)
group_order = pd.read_csv(GROUPS, encoding="utf-8-sig")["가전품목군"].tolist()
group_order = [g for g in group_order if g != "전체 가전"]
assert len(df) == 5554 and df["가전품목군"].nunique() == len(group_order)

reason_display = df["청구이유"].mask(df["청구이유"].str.strip().eq(""), "<청구이유 결측>")
reason_values = (reason_display.value_counts().rename_axis("청구이유_원문")
                 .reset_index(name="건수"))
reason_values.to_csv(OUT / "reason_unique_values.csv", index=False, encoding="utf-8-sig")

def make_tables(data: pd.DataFrame, category: pd.Series, prefix: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = pd.crosstab(data["가전품목군"], category)
    counts = counts.reindex(group_order)
    assert counts.notna().all().all(), "Every selected group should be observed in this source slice"
    counts = counts.astype(int)
    denominators = counts.sum(axis=1)
    pct = counts.div(denominators, axis=0).mul(100).round(4)
    count_total = counts.sum(axis=0)
    pct_total = count_total.div(int(count_total.sum())).mul(100).round(4)
    count_table = counts.copy()
    count_table.insert(0, "행분모", denominators)
    count_table.loc["전체 가전"] = pd.concat([pd.Series({"행분모": int(denominators.sum())}), count_total])
    pct_table = pct.copy()
    pct_table.insert(0, "행분모", denominators)
    pct_table.loc["전체 가전"] = pd.concat([pd.Series({"행분모": int(denominators.sum())}), pct_total])
    count_table.index.name = "가전품목군"
    pct_table.index.name = "가전품목군"
    count_table.to_csv(OUT / f"{prefix}_counts.csv", encoding="utf-8-sig")
    pct_table.to_csv(OUT / f"{prefix}_row_pct.csv", encoding="utf-8-sig")
    assert int(count_table.loc["전체 가전", "행분모"]) == len(data)
    return count_table, pct_table

reason_counts, reason_pct = make_tables(df, reason_display, "reason_cross")

outcome_available = df[df["처리결과"].str.strip().ne("")].copy()
assert outcome_available["원본파일"].nunique() == 1
assert outcome_available["접수일"].eq("2026년 2분기").all()
assert len(outcome_available) == 416
outcome_values = (outcome_available["처리결과"].value_counts()
                  .rename_axis("처리결과_원문").reset_index(name="건수"))
outcome_values.to_csv(OUT / "outcome_unique_values.csv", index=False, encoding="utf-8-sig")
outcome_counts, outcome_pct = make_tables(outcome_available,
                                           outcome_available["처리결과"], "outcome_cross")

availability = (df.groupby("원본파일", sort=False)
                .agg(가전행수=("가전품목군", "size"),
                     처리결과_기록행수=("처리결과", lambda x: int(x.str.strip().ne("").sum())))
                .reset_index())
availability.to_csv(OUT / "outcome_availability_by_file.csv", index=False, encoding="utf-8-sig")

reason_proposal = {
    "AS불만": ("품질·A/S 일반", "확정 제안", "세부 수리 사유는 원문값에서 구분할 수 없음"),
    "품질(물품/용역)": ("품질·A/S 일반", "확정 제안", "품질 관련 넓은 범주"),
    "계약불이행(불완전이행)": ("계약·기타", "확인 필요", "수리 지연이 포함될 수 있으나 원문값만으로 분리 불가"),
    "안전(제품/시설)": ("계약·기타", "확인 필요", "제품 하자와의 경계가 애매하며 A/S 세부 사유는 아님"),
    "단순문의.상담": ("계약·기타", "확인 필요", "피해 청구가 아닌 문의일 수 있음"),
    "상담자율처리": ("계약·기타", "확인 필요", "청구 사유보다 처리 형태에 가까움"),
    "법.제도": ("계약·기타", "확인 필요", "개별 가전 고장 청구가 아닐 수 있음"),
    "<청구이유 결측>": ("미분류", "확인 필요", "원문 결측; 세 그룹에 임의 배정하지 않음"),
}
for value in reason_values["청구이유_원문"]:
    if value not in reason_proposal:
        reason_proposal[value] = ("계약·기타", "확정 제안", "품질·A/S 또는 기준 판정형을 직접 지시하지 않는 원문값")
reason_review = reason_values.copy()
reason_review[["제안그룹", "검토상태", "근거"]] = reason_review["청구이유_원문"].map(reason_proposal).apply(pd.Series)
reason_review.to_csv(OUT / "reason_group_proposal.csv", index=False, encoding="utf-8-sig")

outcome_proposal = {
    "환급": ("직접 구제성 결과", "포함 제안"),
    "교환": ("직접 구제성 결과", "포함 제안"),
    "수리,보수": ("직접 구제성 결과", "포함 제안"),
    "배상": ("직접 구제성 결과", "포함 제안"),
    "계약이행": ("계약 조치", "합계 포함 여부 확인 필요"),
    "계약해제": ("계약 조치", "합계 포함 여부 확인 필요"),
    "부당행위시정": ("계약 조치", "합계 포함 여부 확인 필요"),
    "조정신청": ("절차 진행", "합계 제외 제안"),
    "처리중": ("절차 진행", "합계 제외 제안"),
    "상담기타": ("구제 확인 불가", "합계 제외 제안"),
    "정보제공": ("구제 확인 불가", "합계 제외 제안"),
    "취하,중지": ("구제 확인 불가", "합계 제외 제안"),
    "처리불능": ("구제 확인 불가", "합계 제외 제안"),
}
assert set(outcome_values["처리결과_원문"]) == set(outcome_proposal)
outcome_review = outcome_values.copy()
outcome_review[["제안그룹", "합계처리제안"]] = outcome_review["처리결과_원문"].map(outcome_proposal).apply(pd.Series)
outcome_review.to_csv(OUT / "outcome_group_proposal.csv", index=False, encoding="utf-8-sig")

proposal = """# STEP 3 청구이유·처리결과 그룹안 — 사용자 확인 전

## 청구이유

- `품질(물품/용역)`, `AS불만` → `품질·A/S 일반` 제안.
- 수리 지연, 부품 미보유, 동일 하자 반복, 수리 불가를 직접 지시하는 원문 청구이유 값은 없음. 따라서 `기준 판정형`은 이 열로 식별 불가이며 **0건·0%로 표현하지 않음**. AS불만을 이 그룹의 대리값으로 임의 배정하지 않음.
- 계약 관련 및 나머지 원문값 → `계약·기타` 제안. 다만 `계약불이행(불완전이행)`, `안전(제품/시설)`, `단순문의.상담`, `상담자율처리`, `법.제도`는 성격이 애매하여 확인 요청.
- 빈 청구이유는 `미분류`로 남기며 임의 대체하지 않음. 향후 그룹 비중의 분모에 이 결측 행을 포함할지 별도 확인이 필요.

## 처리결과

- `환급`, `교환`, `수리,보수`, `배상`을 `직접 구제성 결과`로 합산하는 안을 제안.
- `계약이행`, `계약해제`, `부당행위시정`은 `계약 조치`로 따로 표시하고 구제성 합계에 포함할지 확인 요청.
- `조정신청`, `처리중`은 진행 중; `상담기타`, `정보제공`, `취하,중지`, `처리불능`은 구제 확인 불가로 합계에서 제외하는 안을 제안.
- 결과 코드만으로 소비자분쟁해결기준이 실제 적용되었는지 확인할 수 없음. 집계 명칭은 `기준이 적용되어 해결된`보다 `직접 구제성 처리결과`가 데이터에 충실함.
- 처리결과는 2026년 2분기 원본의 가전 416행에서만 존재. 다른 기간의 빈 처리결과를 0건 결과로 해석하지 않음.

사용자 확정 전에는 그룹 비중, 구제성 합계 비중, 요청한 그룹 히트맵과 처리결과 100% 누적 그래프를 계산하지 않음.
"""
(OUT / "grouping_proposal.md").write_text(proposal, encoding="utf-8")

prior_log = (ROOT / "outputs" / "step2_final" / "preprocessing_log.md").read_text(encoding="utf-8")
log_add = f"""

## STEP 3 원문 교차표·분류안 검토 (미확정)

1. 최종 가전 {len(df):,}행의 원문 `청구이유`로 품목군별 건수·행 기준 비율 교차표 생성. 행 분모는 해당 품목군의 전체 행 수이며 청구이유 빈칸도 `<청구이유 결측>` 열로 포함.
2. 청구이유 빈칸 {int(df['청구이유'].str.strip().eq('').sum())}행은 원본값을 변경하거나 0으로 대체하지 않음. 교차표에만 표시용 이름을 부여.
3. `처리결과`는 2026년 2분기 파일의 가전 {len(outcome_available)}행에만 있음. 원문 처리결과 건수·행 기준 비율 교차표의 분모는 이 기간 품목군별 기록행 수. 다른 기간의 빈 결과는 결측으로 유지.
4. 교차표에서 관측되지 않은 품목군×범주 조합의 0은 기록된 모집단 내 실제 미출현 건수임. 결측을 0으로 대체한 것이 아님.
5. 청구이유와 처리결과 그룹안은 별도 파일로 제안만 했으며 아직 행에 적용하지 않음. 기준 판정형 세부 사유는 원문 청구이유 열로 식별 불가.
"""
(OUT / "preprocessing_log.md").write_text(prior_log + log_add, encoding="utf-8")

lines = [
    "[SOURCE SCOPE]",
    f"appliance_rows={len(df)}, reason_nonblank={int(df['청구이유'].str.strip().ne('').sum())}, reason_blank={int(df['청구이유'].str.strip().eq('').sum())}",
    f"outcome_recorded_rows={len(outcome_available)}, outcome_missing_other_files={len(df)-len(outcome_available)}",
    "[RAW REASON VALUES]", reason_values.to_string(index=False),
    "[REASON CROSS-TAB COUNTS]", reason_counts.to_string(),
    "[REASON CROSS-TAB ROW PERCENT]", reason_pct.to_string(),
    "[RAW OUTCOME VALUES]", outcome_values.to_string(index=False),
    "[OUTCOME CROSS-TAB COUNTS]", outcome_counts.to_string(),
    "[OUTCOME CROSS-TAB ROW PERCENT]", outcome_pct.to_string(),
    "[SOURCE AVAILABILITY]", availability.to_string(index=False),
    "[PROPOSED REASON GROUPS — NOT APPLIED]", reason_review.to_string(index=False),
    "[PROPOSED OUTCOME GROUPS — NOT APPLIED]", outcome_review.to_string(index=False),
]
(OUT / "execution_output.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:5]))
print("[FILES]")
for path in sorted(OUT.iterdir()):
    print(path.name, path.stat().st_size, "bytes")
