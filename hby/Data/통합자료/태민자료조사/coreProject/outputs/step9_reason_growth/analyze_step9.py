"""Recalculate claim-reason count changes and appliance product contributions."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)


def read(path: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, encoding="utf-8-sig", dtype=str,
                       keep_default_na=False, low_memory=False)


all_cases = read("outputs/step1_standardization/standardized_redress.csv")
appliance = read("outputs/step2_final/appliance_redress.csv")
keys = ["원본파일", "원본행번호"]
all_key = pd.MultiIndex.from_frame(all_cases[keys])
appliance_key = pd.MultiIndex.from_frame(appliance[keys])
assert len(all_cases) == 150_964 and len(appliance) == 5_554
assert all_key.is_unique and appliance_key.is_unique
assert appliance_key.isin(all_key).all()
is_appliance = all_key.isin(appliance_key)
assert int(is_appliance.sum()) == len(appliance)

all_cases["집단"] = "비가전"
all_cases.loc[is_appliance, "집단"] = "가전"
quality_values = {"품질(물품/용역)", "AS불만"}
all_cases["청구이유그룹"] = "계약·기타"
all_cases.loc[all_cases["청구이유"].isin(quality_values), "청구이유그룹"] = "품질·A/S 일반"
all_cases.loc[all_cases["청구이유"].str.strip().eq(""), "청구이유그룹"] = "미분류"
appliance["청구이유그룹"] = "계약·기타"
appliance.loc[appliance["청구이유"].isin(quality_values), "청구이유그룹"] = "품질·A/S 일반"
appliance.loc[appliance["청구이유"].str.strip().eq(""), "청구이유그룹"] = "미분류"

periods = {
    "2024→2025": (("2024", None), ("2025", None)),
    "2025H1→2026H1": (("2025", {"1", "2"}), ("2026", {"1", "2"})),
}
groups = ["품질·A/S 일반", "계약·기타", "미분류"]
populations = ["가전", "비가전"]


def select_period(frame: pd.DataFrame, year: str, quarters: set[str] | None) -> pd.DataFrame:
    result = frame.loc[frame["접수연도"].eq(year)]
    if quarters is not None:
        result = result.loc[result["접수분기"].isin(quarters)]
    return result


def rate(previous: int, current: int) -> float | None:
    return (current - previous) / previous * 100 if previous else None


group_rows = []
for comparison, (previous_spec, current_spec) in periods.items():
    previous = select_period(all_cases, *previous_spec)
    current = select_period(all_cases, *current_spec)
    for population in populations:
        previous_pop = previous.loc[previous["집단"].eq(population)]
        current_pop = current.loc[current["집단"].eq(population)]
        previous_counts = previous_pop["청구이유그룹"].value_counts().reindex(groups, fill_value=0)
        current_counts = current_pop["청구이유그룹"].value_counts().reindex(groups, fill_value=0)
        assert int(previous_counts.sum()) == len(previous_pop)
        assert int(current_counts.sum()) == len(current_pop)
        for group in groups:
            before = int(previous_counts[group])
            after = int(current_counts[group])
            change = after - before
            group_rows.append({"비교": comparison, "집단": population, "청구이유그룹": group,
                               "이전건수_분모": before, "비교건수": after,
                               "증감건수_분자": change,
                               "증감률_pct": rate(before, after),
                               "증감률상태": "산출 가능" if before else "이전기간 0건으로 산출 불가"})
group_change = pd.DataFrame(group_rows)
group_change["증감률_pct"] = group_change["증감률_pct"].round(4)
group_change.to_csv(OUT / "reason_group_count_changes.csv", index=False, encoding="utf-8-sig")

# Reconcile annual counts with the separately computed STEP 8 comparison.
step8 = read("outputs/step8_appliance_vs_nonappliance/reason_group_comparison_long.csv")
for year in ["2024", "2025"]:
    for population in populations:
        for group in groups:
            expected = int(step8.loc[(step8["기간"].eq(f"{year}년")) &
                                     (step8["집단"].eq(population)) &
                                     (step8["청구이유그룹"].eq(group)), "건수_분자"].iloc[0])
            row = group_change.loc[(group_change["비교"].eq("2024→2025")) &
                                   (group_change["집단"].eq(population)) &
                                   (group_change["청구이유그룹"].eq(group))].iloc[0]
            actual = int(row["이전건수_분모"] if year == "2024" else row["비교건수"])
            assert actual == expected, (year, population, group)

product_names = read("outputs/step2_final/appliance_group_summary.csv")["가전품목군"].tolist()
product_names = [name for name in product_names if name != "전체 가전"]
assert len(product_names) == 19
product_rows = []
for comparison, (previous_spec, current_spec) in periods.items():
    previous = select_period(appliance, *previous_spec)
    current = select_period(appliance, *current_spec)
    previous_quality = previous.loc[previous["청구이유그룹"].eq("품질·A/S 일반")]
    current_quality = current.loc[current["청구이유그룹"].eq("품질·A/S 일반")]
    previous_counts = previous_quality["가전품목군"].value_counts().reindex(product_names, fill_value=0)
    current_counts = current_quality["가전품목군"].value_counts().reindex(product_names, fill_value=0)
    for name in product_names:
        before = int(previous_counts[name])
        after = int(current_counts[name])
        product_rows.append({"비교": comparison, "가전품목군": name,
                             "이전_품질AS_건수_증감률분모": before,
                             "비교_품질AS_건수": after,
                             "증감건수": after - before,
                             "증감률_pct": rate(before, after),
                             "이전기간30건미만": before < 30,
                             "증감률상태": "산출 가능" if before else "이전기간 0건으로 산출 불가"})
    overall = group_change.loc[(group_change["비교"].eq(comparison)) &
                               (group_change["집단"].eq("가전")) &
                               (group_change["청구이유그룹"].eq("품질·A/S 일반"))].iloc[0]
    assert int(previous_counts.sum()) == int(overall["이전건수_분모"])
    assert int(current_counts.sum()) == int(overall["비교건수"])
product_change = pd.DataFrame(product_rows)
product_change["증감률_pct"] = product_change["증감률_pct"].round(4)
product_change.to_csv(OUT / "appliance_quality_as_product_changes.csv", index=False,
                      encoding="utf-8-sig")

annual = product_change.loc[product_change["비교"].eq("2024→2025")].copy()
annual = annual.sort_values(["증감건수", "가전품목군"], ascending=[False, True])
h1 = product_change.loc[product_change["비교"].eq("2025H1→2026H1")].copy()
h1 = h1.set_index("가전품목군").loc[annual["가전품목군"]].reset_index()
annual.to_csv(OUT / "appliance_quality_as_2024_2025.csv", index=False, encoding="utf-8-sig")
h1.to_csv(OUT / "appliance_quality_as_2025H1_2026H1.csv", index=False, encoding="utf-8-sig")

def format_change(row: pd.Series) -> str:
    change = int(row["증감건수"])
    pct = "산출 불가" if pd.isna(row["증감률_pct"]) else f"{float(row['증감률_pct']):+.2f}%"
    return f"{change:+d}건 ({pct})"

product_table = [
    "| 가전품목군 | 2024→2025 품질·A/S 건수 | 증감 | 2025H1→2026H1 품질·A/S 건수 | 증감 |",
    "|---|---:|---:|---:|---:|",
]
h1_index = h1.set_index("가전품목군")
for _, row in annual.iterrows():
    other = h1_index.loc[row["가전품목군"]]
    annual_star = "*" if row["이전기간30건미만"] else ""
    h1_star = "*" if other["이전기간30건미만"] else ""
    product_table.append(
        f"| {row['가전품목군']} | {int(row['이전_품질AS_건수_증감률분모'])}{annual_star}→{int(row['비교_품질AS_건수'])} "
        f"| {format_change(row)} | {int(other['이전_품질AS_건수_증감률분모'])}{h1_star}→{int(other['비교_품질AS_건수'])} "
        f"| {format_change(other)} |"
    )
product_table.append("\n* = 이전기간 품질·A/S 일반 건수(증감률 분모)가 30건 미만. 이전기간 0건의 증감률은 산출 불가.")
(OUT / "product_change_table.md").write_text("\n".join(product_table) + "\n", encoding="utf-8")

# An English-label diverging bar chart summarizes every product without dropping
# small-base products. The asterisk marks a prior-period count below 30.
english = {"에어컨": "Air conditioner", "TV": "TV", "청소기": "Vacuum cleaners",
           "냉장고": "Refrigerator", "음식물처리기": "Food waste processor", "세탁기": "Washer",
           "정수기": "Water purifier", "식기세척기": "Dishwasher", "김치냉장고": "Kimchi fridge",
           "가습기": "Humidifier", "인덕션레인지": "Induction range", "의류건조기": "Clothes dryer",
           "오븐·전자레인지": "Oven / microwave", "제습기": "Dehumidifier",
           "공기청정기": "Air purifier", "냉동고": "Freezer", "의류관리기": "Clothing care",
           "워시타워": "Wash tower", "식기건조기": "Dish dryer"}
assert set(english) == set(product_names)
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
title_font = ImageFont.truetype(font_path, 24)
body_font = ImageFont.truetype(font_path, 16)
small_font = ImageFont.truetype(font_path, 14)
height = 90 + len(annual) * 41 + 58
image = Image.new("RGB", (1320, height), "white")
draw = ImageDraw.Draw(image)
net = int(annual["증감건수"].sum())
top = annual.iloc[0]
title = (f"Appliance quality/AS cases rose by {net} in 2025, "
         f"with {english[top['가전품목군']]} adding the most.")
draw.text((25, 19), title, fill="#17344a", font=title_font)
draw.text((25, 52), "Change in recorded cases, 2025 minus 2024; * = 2024 base below 30 cases.",
          fill="#526674", font=small_font)
axis_x = 675
max_abs = max(int(annual["증감건수"].max()), abs(int(annual["증감건수"].min())))
scale = 340 / max_abs if max_abs else 0
draw.line((axis_x, 85, axis_x, height - 45), fill="#aab5bc", width=2)
for index, row in enumerate(annual.itertuples(index=False)):
    y = 91 + index * 41
    if index % 2 == 0:
        draw.rectangle((20, y - 1, 1300, y + 37), fill="#f6f8fa")
    label = english[row.가전품목군] + (" *" if row.이전기간30건미만 else "")
    draw.text((28, y + 8), label, fill="#17344a", font=body_font)
    change = int(row.증감건수)
    extent = round(abs(change) * scale)
    if change > 0:
        draw.rectangle((axis_x, y + 4, axis_x + extent, y + 31), fill="#277da8")
    elif change < 0:
        draw.rectangle((axis_x - extent, y + 4, axis_x, y + 31), fill="#d8864c")
    draw.text((1050, y + 8),
              f"{row.이전_품질AS_건수_증감률분모} -> {row.비교_품질AS_건수}  ({change:+d})",
              fill="#17344a", font=body_font)
draw.text((25, height - 37), "Small bases are displayed for transparency; avoid interpreting their growth rates alone.",
          fill="#526674", font=small_font)
image.save(OUT / "appliance_quality_as_product_change_2024_2025.png")

annual_quality = group_change.loc[(group_change["비교"].eq("2024→2025")) &
                                  (group_change["집단"].eq("가전")) &
                                  (group_change["청구이유그룹"].eq("품질·A/S 일반"))].iloc[0]
h1_quality = group_change.loc[(group_change["비교"].eq("2025H1→2026H1")) &
                              (group_change["집단"].eq("가전")) &
                              (group_change["청구이유그룹"].eq("품질·A/S 일반"))].iloc[0]
top_three = annual.head(3)
top_three_text = ", ".join(f"{r.가전품목군} {int(r.증감건수):+d}건" for r in top_three.itertuples())

prior_log = (ROOT / "outputs/step8_appliance_vs_nonappliance/preprocessing_log.md").read_text(encoding="utf-8")
prior_report_log = (ROOT / "outputs/step8_appliance_vs_nonappliance/preprocessing_log_report.md").read_text(encoding="utf-8")
step_log = """
\n## STEP 9 청구이유 증감률과 품목별 증가 기여

1. STEP 8과 같은 STEP 1 전체 150,964행 및 STEP 2 가전 5,554행을 사용했다. `원본파일`+`원본행번호`의 유일성·부분집합 관계를 재확인해 가전과 비가전을 분리했다. 청구이유는 승인된 두 원문값만 `품질·A/S 일반`, 그 밖의 비결측은 `계약·기타`, 빈칸·공백은 `미분류`로 분류했다.
2. 2024년→2025년은 각 역년의 동일 집단·동일 그룹 건수, 2025H1→2026H1은 `접수연도`와 1·2분기 파생 열의 동일 집단·동일 그룹 건수를 비교했다. 증감건수는 비교기간 건수−이전기간 건수, 증감률은 이 차이를 이전기간 건수로 나눈 값이다. 이전기간 0건이면 증감률은 산출 불가로 남기고 0%로 대체하지 않았다.
3. 품목별 표에는 STEP 2에서 확정한 가전 19품목군을 모두 유지했다. `품질(물품/용역)`·`AS불만`에 해당하는 행만 품목별로 집계했다. 품목별 건수의 합계가 각 기간 가전 `품질·A/S 일반` 그룹 건수와 일치하는지 검증했다. 관측 기간의 특정 품목·그룹 조합에 행이 없을 때 집계 0건과 원문 결측을 구분했다.
4. `이전기간30건미만`은 품목별 증감률의 분모인 이전기간 품질·A/S 일반 건수가 30건 미만인 경우 참이다. 기준기간 0건의 증감률은 별도로 산출 불가다. 이 표시는 승인된 품목을 제외하지 않고 작은 분모를 드러내기 위한 것이다.
5. 2026년 2분기 원본은 `2026년 2분기`라는 분기 표기뿐이어서 일자 수준 완전성을 확인할 수 없다. 따라서 2025H1→2026H1 비교는 잠정적 방향 점검으로 해석하며, 2024→2025 역년 비교와 동일한 확정성으로 다루지 않는다.
6. 품목별 증감 그래프는 19품목을 모두 표시하고 2024년 분모 30건 미만을 별표로 표시했다. 한글 글꼴 문제를 피하려고 그래프 표시명만 영어로 썼으며 분석용 품목군은 변경하지 않았다.
"""
(OUT / "preprocessing_log.md").write_text(prior_log + step_log, encoding="utf-8")
(OUT / "preprocessing_log_report.md").write_text(prior_report_log + step_log, encoding="utf-8")

summary = (
    f"2024→2025년 가전 품질·A/S 일반 청구는 {int(annual_quality['이전건수_분모']):,}건에서 "
    f"{int(annual_quality['비교건수']):,}건으로 {int(annual_quality['증감건수_분자']):+d}건"
    f"({float(annual_quality['증감률_pct']):+.2f}%) 변했고, 증가 건수 상위 품목은 {top_three_text}이다. "
    f"2025H1→2026H1은 {int(h1_quality['이전건수_분모']):,}건에서 "
    f"{int(h1_quality['비교건수']):,}건으로 {int(h1_quality['증감건수_분자']):+d}건"
    f"({float(h1_quality['증감률_pct']):+.2f}%) 변했으나 2026년 2분기 일자 수준 완전성은 확인할 수 없다."
)
(OUT / "summary.md").write_text(summary + "\n", encoding="utf-8")

print("GROUP_CHANGES")
print(group_change.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
print("PRODUCT_ANNUAL")
print(annual.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
print("PRODUCT_H1")
print(h1.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
print("TOP_THREE_ANNUAL", top_three_text)
print("ANNUAL_NET_QUALITY_CHANGE", net)
print("H1_QUALITY_CHANGE", f"{int(h1_quality['비교건수'])}/{int(h1_quality['이전건수_분모'])}",
      f"{int(h1_quality['증감건수_분자']):+d}", f"{float(h1_quality['증감률_pct']):+.4f}%")
print("GRAPH_TITLE", title)
print("SUMMARY", summary)
