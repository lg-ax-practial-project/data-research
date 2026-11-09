"""Compare approved claim-reason groups in appliance, non-appliance and all redress."""

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
key_columns = ["원본파일", "원본행번호"]
assert len(all_cases) == 150_964 and len(appliance) == 5_554
assert not all_cases.duplicated(key_columns).any()
assert not appliance.duplicated(key_columns).any()
all_key = pd.MultiIndex.from_frame(all_cases[key_columns])
appliance_key = pd.MultiIndex.from_frame(appliance[key_columns])
is_appliance = all_key.isin(appliance_key)
assert int(is_appliance.sum()) == len(appliance)
assert appliance_key.isin(all_key).all()

# Check that the STEP 2 rows retain the relevant STEP 1 source values.
shared = ["청구이유", "접수연도", "접수분기", "물품소분류"]
match = appliance[key_columns + shared].merge(
    all_cases[key_columns + shared], on=key_columns, how="left",
    validate="one_to_one", suffixes=("_가전", "_전체"), indicator=True)
assert match["_merge"].eq("both").all()
for column in shared:
    assert match[f"{column}_가전"].eq(match[f"{column}_전체"]).all(), column

all_cases["집단"] = "비가전"
all_cases.loc[is_appliance, "집단"] = "가전"
quality_values = {"품질(물품/용역)", "AS불만"}
reason = all_cases["청구이유"]
step3_other_values = {"청약철회", "계약해제.해지/위약금", "부당행위", "표시.광고", "가격.요금",
                      "거래관행", "이자.수수료", "부당채권추심", "약관", "계약불이행(불완전이행)",
                      "안전(제품/시설)", "단순문의.상담", "상담자율처리", "법.제도"}
additional_other = sorted(set(reason.loc[reason.str.strip().ne("")]) - quality_values - step3_other_values)
additional_other_counts = reason.loc[reason.isin(additional_other)].value_counts().to_dict()
all_cases["청구이유그룹"] = "계약·기타"
all_cases.loc[reason.isin(quality_values), "청구이유그룹"] = "품질·A/S 일반"
all_cases.loc[reason.str.strip().eq(""), "청구이유그룹"] = "미분류"
assert all_cases["청구이유그룹"].notna().all()
assert set(all_cases["집단"]) == {"가전", "비가전"}

groups = ["품질·A/S 일반", "계약·기타", "미분류"]
populations = ["가전", "비가전", "전체"]
periods = [("전체기간", all_cases),
           ("2024년", all_cases.loc[all_cases["접수연도"].eq("2024")]),
           ("2025년", all_cases.loc[all_cases["접수연도"].eq("2025")])]
rows = []
for period_name, source in periods:
    assert len(source) > 0
    for population in populations:
        population_rows = source if population == "전체" else source.loc[source["집단"].eq(population)]
        denominator = len(population_rows)
        assert denominator > 0
        counts = population_rows["청구이유그룹"].value_counts().reindex(groups, fill_value=0)
        assert int(counts.sum()) == denominator
        for group in groups:
            numerator = int(counts[group])
            rows.append({"기간": period_name, "집단": population, "청구이유그룹": group,
                         "건수_분자": numerator, "전체행수_분모": denominator,
                         "비중_pct": numerator / denominator * 100})

result = pd.DataFrame(rows)
result["비중_pct"] = result["비중_pct"].round(4)
assert len(result) == len(periods) * len(populations) * len(groups)
assert result.loc[(result["기간"] == "전체기간") & (result["집단"] == "가전"),
                  "전체행수_분모"].unique().tolist() == [5554]
assert result.loc[(result["기간"] == "전체기간") & (result["집단"] == "비가전"),
                  "전체행수_분모"].unique().tolist() == [145410]
assert result.loc[(result["기간"] == "전체기간") & (result["집단"] == "전체"),
                  "전체행수_분모"].unique().tolist() == [150964]

result.to_csv(OUT / "reason_group_comparison_long.csv", index=False, encoding="utf-8-sig")
wide_counts = result.pivot(index=["기간", "집단", "전체행수_분모"],
                           columns="청구이유그룹", values="건수_분자").reset_index()
wide_pct = result.pivot(index=["기간", "집단", "전체행수_분모"],
                        columns="청구이유그룹", values="비중_pct").reset_index()
wide_counts = wide_counts[["기간", "집단", "전체행수_분모"] + groups]
wide_pct = wide_pct[["기간", "집단", "전체행수_분모"] + groups]
wide_counts.to_csv(OUT / "reason_group_counts_wide.csv", index=False, encoding="utf-8-sig")
wide_pct.to_csv(OUT / "reason_group_pct_wide.csv", index=False, encoding="utf-8-sig")

quality = result.loc[result["청구이유그룹"].eq("품질·A/S 일반")]
gap_rows = []
for period_name, _ in periods:
    item = quality.loc[quality["기간"].eq(period_name)].set_index("집단")
    appliance_pct = float(item.loc["가전", "비중_pct"])
    other_pct = float(item.loc["비가전", "비중_pct"])
    gap_rows.append({"기간": period_name,
                     "가전_품질AS_건수": int(item.loc["가전", "건수_분자"]),
                     "가전_분모": int(item.loc["가전", "전체행수_분모"]),
                     "가전_품질AS_비중_pct": appliance_pct,
                     "비가전_품질AS_건수": int(item.loc["비가전", "건수_분자"]),
                     "비가전_분모": int(item.loc["비가전", "전체행수_분모"]),
                     "비가전_품질AS_비중_pct": other_pct,
                     "가전_빼기_비가전_pp": round(appliance_pct - other_pct, 4)})
gap = pd.DataFrame(gap_rows)
gap.to_csv(OUT / "quality_as_share_gap.csv", index=False, encoding="utf-8-sig")
assert (gap["가전_빼기_비가전_pp"] > 0).all()

whole_gap = gap.loc[gap["기간"].eq("전체기간")].iloc[0]
year_2024 = gap.loc[gap["기간"].eq("2024년")].iloc[0]
year_2025 = gap.loc[gap["기간"].eq("2025년")].iloc[0]
report_sentence = (
    f"전체 피해구제 {len(all_cases):,}건을 동일 기준으로 분류하면 품질·A/S 일반 청구는 "
    f"가전 {whole_gap['가전_품질AS_건수']:,}/{whole_gap['가전_분모']:,}건({whole_gap['가전_품질AS_비중_pct']:.2f}%)으로 "
    f"비가전 {whole_gap['비가전_품질AS_건수']:,}/{whole_gap['비가전_분모']:,}건({whole_gap['비가전_품질AS_비중_pct']:.2f}%)보다 "
    f"{whole_gap['가전_빼기_비가전_pp']:.2f}%p 높았으며, 이 차이는 "
    f"2024년 가전 {year_2024['가전_품질AS_건수']:,}/{year_2024['가전_분모']:,}건({year_2024['가전_품질AS_비중_pct']:.2f}%) 대 "
    f"비가전 {year_2024['비가전_품질AS_건수']:,}/{year_2024['비가전_분모']:,}건({year_2024['비가전_품질AS_비중_pct']:.2f}%), "
    f"2025년 가전 {year_2025['가전_품질AS_건수']:,}/{year_2025['가전_분모']:,}건({year_2025['가전_품질AS_비중_pct']:.2f}%) 대 "
    f"비가전 {year_2025['비가전_품질AS_건수']:,}/{year_2025['비가전_분모']:,}건({year_2025['비가전_품질AS_비중_pct']:.2f}%)에서도 관측됐다."
)
(OUT / "report_sentence.md").write_text(report_sentence + "\n", encoding="utf-8")

# English chart labels avoid Korean font incompatibility. Segment widths use the
# unrounded counts, so the tiny missing portions are retained in the 100% bars.
whole = result.loc[result["기간"].eq("전체기간")]
chart = whole.set_index(["집단", "청구이유그룹"])
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
title_font = ImageFont.truetype(font_path, 25)
body_font = ImageFont.truetype(font_path, 18)
small_font = ImageFont.truetype(font_path, 15)
image = Image.new("RGB", (1500, 430), "white")
draw = ImageDraw.Draw(image)
overall_gap = gap.loc[gap["기간"].eq("전체기간")].iloc[0]
title = ("Quality/AS reasons are "
         f"{overall_gap['가전_빼기_비가전_pp']:.2f} percentage points more common in appliance redress.")
draw.text((34, 26), title, fill="#17344a", font=title_font)
draw.text((35, 67), "All recorded periods, including 2026 Q2; every bar includes missing reasons in its denominator.",
          fill="#536675", font=small_font)
colors = {"품질·A/S 일반": "#277da8", "계약·기타": "#d89641", "미분류": "#9aa5b1"}
legend = [("Quality / AS", colors["품질·A/S 일반"]),
          ("Contract / other", colors["계약·기타"]),
          ("Unclassified", colors["미분류"])]
for index, (label, color) in enumerate(legend):
    left = 35 + index * 250
    draw.rectangle((left, 114, left + 18, 132), fill=color)
    draw.text((left + 27, 112), label, fill="#17344a", font=small_font)

bar_left, bar_right = 260, 1220
bar_width = bar_right - bar_left
for index, population in enumerate(["가전", "비가전"]):
    top = 177 + index * 102
    label = "Appliance" if population == "가전" else "Non-appliance"
    denominator = int(chart.loc[(population, groups[0]), "전체행수_분모"])
    draw.text((34, top + 11), f"{label} (n={denominator:,})", fill="#17344a", font=body_font)
    current = bar_left
    for group in groups:
        numerator = int(chart.loc[(population, group), "건수_분자"])
        width = bar_width * numerator / denominator
        next_x = current + width
        draw.rectangle((round(current), top, round(next_x), top + 52), fill=colors[group])
        current = next_x
    draw.text((1240, top + 4),
              f"Quality/AS {int(chart.loc[(population, groups[0]), '건수_분자']):,}/{denominator:,}",
              fill="#17344a", font=small_font)
    draw.text((1240, top + 28),
              f"{float(chart.loc[(population, groups[0]), '비중_pct']):.2f}%",
              fill="#277da8", font=small_font)
draw.text((35, 390), "Unclassified remains in the denominator; its small segment may be less than one pixel wide.",
          fill="#536675", font=small_font)
image.save(OUT / "appliance_vs_nonappliance_reason_100pct.png")

log_prefix = (ROOT / "outputs/step7_report/preprocessing_log_full.md").read_text(encoding="utf-8")
log_step8 = """
\n## STEP 8 가전·비가전 청구이유 구성 비교

1. STEP 1 표준화 피해구제 150,964행과 STEP 2 확정 가전 5,554행을 사용했다. 두 파일의 `원본파일`+`원본행번호` 복합키가 각각 유일하고 가전 키가 전체의 부분집합임을 검증했다. 공통 원문 청구이유·접수연도·접수분기·품목명도 행별로 일치했다.
2. 전체에서 가전 복합키에 속하지 않는 행을 비가전으로 정의했다. 비가전은 새로운 품목 매핑이나 독자적인 제외 기준을 적용한 집단이 아니라 승인된 가전 집단의 여집합이다. 원본 행을 삭제하거나 중복 제거하지 않았다.
3. STEP 3과 동일하게 원문 `품질(물품/용역)`·`AS불만`만 `품질·A/S 일반`, 그 밖의 비결측 원문 청구이유는 `계약·기타`, 빈칸·공백 청구이유는 `미분류`로 배정했다. 전체 자료에만 추가로 나타나는 `무능력자계약`·`결제`도 사용자가 승인한 `그 밖의 비결측` 규칙대로 `계약·기타`에 포함했다. 결측을 0으로 채우지 않았고, 미분류 행도 해당 집단의 비율 분모에 포함했다. 기준 판정형 세부 사유는 이 비교에서도 식별 불가다.
4. 집단별 분모는 가전 5,554행, 비가전 145,410행, 전체 150,964행이다. 2024년·2025년 표는 각각 그 연도의 해당 집단 전체 행을 분모로 다시 계산했다. `전체기간`에는 2024~2026년 2분기 관측분이 들어가며, 2026년 2분기는 일자 수준 완전성을 확인할 수 없다.
5. 각 기간·집단에서 세 그룹 건수의 합이 분모와 일치하는지 검증했다. 관측 집단 안에서 발생하지 않은 그룹의 0건과 원본 결측을 구분했다. 가전과 비가전의 품질·A/S 비중 차이는 가전 비중에서 비가전 비중을 뺀 퍼센트포인트(pp)다.
6. 100% 누적 막대는 전체기간의 가전·비가전 구성을 원건수로 그렸고, 미분류도 분모와 막대에 포함했다. 한글 글꼴 호환을 위해 그래프 라벨을 영어로 표기했다. 연도별 차이는 별도 CSV로 보존했다.
"""
(OUT / "preprocessing_log.md").write_text(log_prefix + log_step8, encoding="utf-8")
report_log_prefix = (ROOT / "outputs/step7_report/preprocessing_log_report.md").read_text(encoding="utf-8")
(OUT / "preprocessing_log_report.md").write_text(report_log_prefix + log_step8, encoding="utf-8")

print("SCOPE", f"all={len(all_cases)}", f"appliance={len(appliance)}",
      f"nonappliance={(~is_appliance).sum()}", "keys_unique_and_subset=True")
print("ADDITIONAL_CONTRACT_OTHER_VALUES", additional_other_counts)
print("COUNTS_WIDE")
print(wide_counts.to_string(index=False))
print("PCT_WIDE")
print(wide_pct.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
print("QUALITY_AS_GAP")
print(gap.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
print("ANNUAL_DIRECTION_MAINTAINED", bool((gap.loc[gap["기간"].isin(["2024년", "2025년"]),
                                                "가전_빼기_비가전_pp"] > 0).all()))
print("GRAPH_TITLE", title)
print("REPORT_SENTENCE", report_sentence)
