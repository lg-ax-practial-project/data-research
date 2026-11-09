"""Apply the approved STEP 3 groupings and build source-backed tables and charts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
SRC = ROOT / "outputs" / "step2_final" / "appliance_redress.csv"
PREV_LOG = ROOT / "outputs" / "step3_review" / "preprocessing_log.md"

REASON_GROUPS = {
    "품질·A/S 일반": ["품질(물품/용역)", "AS불만"],
    "계약·기타": ["청약철회", "계약해제.해지/위약금", "부당행위", "표시.광고", "가격.요금",
              "거래관행", "이자.수수료", "부당채권추심", "약관", "계약불이행(불완전이행)",
              "안전(제품/시설)", "단순문의.상담", "상담자율처리", "법.제도"],
}
OUTCOME_GROUPS = {
    "직접 구제성 처리결과": ["환급", "수리,보수", "배상", "교환"],
    "계약 조치": ["계약이행", "계약해제", "부당행위시정"],
    "절차 진행": ["조정신청", "처리중"],
    "구제 확인 불가": ["상담기타", "정보제공", "취하,중지", "처리불능"],
}
reason_lookup = {value: group for group, values in REASON_GROUPS.items() for value in values}
outcome_lookup = {value: group for group, values in OUTCOME_GROUPS.items() for value in values}
assert len(reason_lookup) == sum(len(v) for v in REASON_GROUPS.values())
assert len(outcome_lookup) == sum(len(v) for v in OUTCOME_GROUPS.values())

df = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False,
                 low_memory=False)
total = len(df)
assert total == 5554
reason_values = set(df.loc[df["청구이유"].str.strip().ne(""), "청구이유"])
outcome_values = set(df.loc[df["처리결과"].str.strip().ne(""), "처리결과"])
assert reason_values == set(reason_lookup), sorted(reason_values ^ set(reason_lookup))
assert outcome_values == set(outcome_lookup), sorted(outcome_values ^ set(outcome_lookup))

df["청구이유그룹"] = df["청구이유"].map(reason_lookup)
df.loc[df["청구이유"].str.strip().eq(""), "청구이유그룹"] = "미분류"
assert df["청구이유그룹"].notna().all()
df["처리결과그룹"] = df["처리결과"].map(outcome_lookup)
assert df.loc[df["처리결과"].str.strip().ne(""), "처리결과그룹"].notna().all()
assert df.loc[df["처리결과"].str.strip().eq(""), "처리결과그룹"].isna().all()

reason_order = ["품질·A/S 일반", "계약·기타", "미분류"]
reason_counts = pd.crosstab(df["가전품목군"], df["청구이유그룹"]).reindex(columns=reason_order)
assert reason_counts.notna().all().all()
reason_counts = reason_counts.astype(int)
reason_den = reason_counts.sum(axis=1)
reason_pct = reason_counts.div(reason_den, axis=0).mul(100).round(4)
reason_total = reason_counts.sum(axis=0)
assert reason_total.to_dict() == {"품질·A/S 일반": 3205, "계약·기타": 2346, "미분류": 3}
assert int(reason_total.sum()) == total

outcome_df = df[df["처리결과"].str.strip().ne("")].copy()
outcome_total_n = len(outcome_df)
assert outcome_total_n == 416
assert outcome_df["원본파일"].nunique() == 1
assert outcome_df["접수일"].eq("2026년 2분기").all()
outcome_order = ["직접 구제성 처리결과", "계약 조치", "절차 진행", "구제 확인 불가"]
outcome_counts = pd.crosstab(outcome_df["가전품목군"], outcome_df["처리결과그룹"])
outcome_counts = outcome_counts.reindex(columns=outcome_order)
assert outcome_counts.notna().all().all()
outcome_counts = outcome_counts.astype(int)
outcome_den = outcome_counts.sum(axis=1)
outcome_pct = outcome_counts.div(outcome_den, axis=0).mul(100).round(4)
outcome_total = outcome_counts.sum(axis=0)
assert outcome_total.to_dict() == {"직접 구제성 처리결과": 183, "계약 조치": 54,
                                   "절차 진행": 88, "구제 확인 불가": 91}
assert int(outcome_total.sum()) == outcome_total_n

group_order = pd.read_csv(ROOT / "outputs" / "step2_final" / "appliance_group_summary.csv",
                          encoding="utf-8-sig")["가전품목군"].tolist()
group_order = [g for g in group_order if g != "전체 가전"]
assert set(group_order) == set(reason_counts.index) == set(outcome_counts.index)
reason_counts = reason_counts.reindex(group_order)
reason_pct = reason_pct.reindex(group_order)
outcome_counts = outcome_counts.reindex(group_order)
outcome_pct = outcome_pct.reindex(group_order)
reason_den = reason_den.reindex(group_order)
outcome_den = outcome_den.reindex(group_order)

def add_total_and_denominator(counts: pd.DataFrame, percentages: pd.DataFrame,
                              den: pd.Series, total_counts: pd.Series,
                              overall_den: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = counts.copy()
    p = percentages.copy()
    c.insert(0, "행분모", den)
    p.insert(0, "행분모", den)
    c.loc["전체 가전"] = pd.concat([pd.Series({"행분모": overall_den}), total_counts])
    total_pct = total_counts.div(overall_den).mul(100).round(4)
    p.loc["전체 가전"] = pd.concat([pd.Series({"행분모": overall_den}), total_pct])
    # This column is deliberately unavailable, not zero.
    c["기준 판정형"] = pd.NA if overall_den == total else c.get("기준 판정형", pd.NA)
    p["기준 판정형"] = pd.NA if overall_den == total else p.get("기준 판정형", pd.NA)
    c.index.name = "가전품목군"
    p.index.name = "가전품목군"
    return c, p

# The criteria-specific column is only meaningful for the reason table.
reason_count_table, reason_pct_table = add_total_and_denominator(
    reason_counts, reason_pct, reason_den, reason_total, total)
reason_pct_table["행분모"] = reason_pct_table["행분모"].astype(int)
outcome_count_table = outcome_counts.copy()
outcome_pct_table = outcome_pct.copy()
outcome_count_table.insert(0, "행분모", outcome_den)
outcome_pct_table.insert(0, "행분모", outcome_den)
outcome_count_table.loc["전체 가전"] = pd.concat([pd.Series({"행분모": outcome_total_n}), outcome_total])
outcome_pct_table.loc["전체 가전"] = pd.concat([
    pd.Series({"행분모": outcome_total_n}), outcome_total.div(outcome_total_n).mul(100).round(4)])
outcome_count_table.index.name = "가전품목군"
outcome_pct_table.index.name = "가전품목군"
outcome_pct_table["행분모"] = outcome_pct_table["행분모"].astype(int)

reason_long = []
for group in group_order + ["전체 가전"]:
    for category in reason_order + ["기준 판정형"]:
        count = reason_count_table.loc[group, category]
        pct = reason_pct_table.loc[group, category]
        reason_long.append({"가전품목군": group, "청구이유그룹": category,
                            "건수": "" if pd.isna(count) else int(count),
                            "분모": int(reason_count_table.loc[group, "행분모"]),
                            "비중_pct": "" if pd.isna(pct) else float(pct),
                            "상태": "식별 불가(원문 미제공)" if category == "기준 판정형" else "관측"})
reason_long = pd.DataFrame(reason_long)
outcome_long = []
for group in group_order + ["전체 가전"]:
    for category in outcome_order:
        outcome_long.append({"가전품목군": group, "처리결과그룹": category,
                             "건수": int(outcome_count_table.loc[group, category]),
                             "분모": int(outcome_count_table.loc[group, "행분모"]),
                             "비중_pct": float(outcome_pct_table.loc[group, category])})
outcome_long = pd.DataFrame(outcome_long)

df.to_csv(OUT / "appliance_redress_grouped.csv", index=False, encoding="utf-8-sig")
reason_count_table.to_csv(OUT / "reason_group_counts.csv", encoding="utf-8-sig")
reason_pct_table.to_csv(OUT / "reason_group_row_pct.csv", encoding="utf-8-sig")
reason_long.to_csv(OUT / "reason_group_long.csv", index=False, encoding="utf-8-sig")
outcome_count_table.to_csv(OUT / "outcome_group_counts.csv", encoding="utf-8-sig")
outcome_pct_table.to_csv(OUT / "outcome_group_row_pct.csv", encoding="utf-8-sig")
outcome_long.to_csv(OUT / "outcome_group_long.csv", index=False, encoding="utf-8-sig")

english = {"냉장고": "Refrigerator", "김치냉장고": "Kimchi fridge", "냉동고": "Freezer",
           "세탁기": "Washer", "워시타워": "WashTower", "의류건조기": "Clothes dryer",
           "의류관리기": "Clothing care", "에어컨": "Air conditioner", "TV": "TV",
           "식기세척기": "Dishwasher", "식기건조기": "Dish dryer", "청소기": "Vacuum cleaners",
           "공기청정기": "Air purifier", "제습기": "Dehumidifier", "가습기": "Humidifier",
           "정수기": "Water purifier", "음식물처리기": "Food waste processor",
           "인덕션레인지": "Induction range", "오븐·전자레인지": "Oven / microwave"}
assert set(english) == set(group_order)
font = ImageFont.load_default()

# Heatmap: the unavailable criteria-specific group is gray and never rendered as 0%.
cell_w, cell_h = 260, 37
left, top = 190, 125
width, height = left + 4 * cell_w + 35, top + len(group_order) * cell_h + 85
img = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(img)
draw.text((28, 25), "Quality and AS reasons lead among selected appliance cases", fill="#17344a", font=font)
draw.text((28, 47), f"Overall: {reason_total['품질·A/S 일반']:,}/{total:,} ({reason_total['품질·A/S 일반']/total*100:.2f}%). Criteria-specific cases cannot be identified.",
          fill="#526674", font=font)
headers = ["Quality / AS", "Contract / other", "Unclassified", "Criteria-specific"]
for j, header in enumerate(headers):
    draw.text((left + j * cell_w + 8, top - 23), header, fill="#17344a", font=font)
for i, group in enumerate(group_order):
    y = top + i * cell_h
    n = int(reason_den.loc[group])
    draw.text((16, y + 10), f"{english[group]} (n={n:,})", fill="#17344a", font=font)
    for j, category in enumerate(reason_order + ["기준 판정형"]):
        x = left + j * cell_w
        if category == "기준 판정형":
            draw.rectangle((x, y, x + cell_w - 3, y + cell_h - 3), fill="#d9dde3")
            draw.text((x + 12, y + 10), "N/A - source has no detail", fill="#354b58", font=font)
            continue
        count = int(reason_counts.loc[group, category])
        pct = float(reason_pct.loc[group, category])
        intensity = min(pct / 100, 1.0)
        rgb = (int(235 - 190 * intensity), int(246 - 110 * intensity), int(250 - 80 * intensity))
        draw.rectangle((x, y, x + cell_w - 3, y + cell_h - 3), fill=rgb)
        draw.text((x + 12, y + 10), f"{count:,}/{n:,} ({pct:.1f}%)",
                  fill="white" if intensity > 0.55 else "#17344a", font=font)
draw.text((left, height - 50), "Gray N/A means not identifiable, never zero cases.", fill="#526674", font=font)
img.save(OUT / "reason_group_heatmap.png")

# 100% stacked outcome bars; row labels carry the within-period denominator.
bar_x, bar_w, row_h = 220, 680, 38
width, height = 1190, 145 + len(group_order) * row_h + 90
img = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(img)
draw.text((28, 24), "Direct remedies account for 183 of 416 recorded appliance outcomes", fill="#17344a", font=font)
draw.text((28, 47), "Only 2026 Q2 has outcome data; other periods are missing, not zero.", fill="#526674", font=font)
colors = ["#277da8", "#50a895", "#e0a346", "#9aa5b1"]
labels = ["Direct remedy", "Contract action", "In progress", "Remedy unverified"]
legend_x = 28
for color, label in zip(colors, labels):
    draw.rectangle((legend_x, 82, legend_x + 15, 96), fill=color)
    draw.text((legend_x + 21, 83), label, fill="#17344a", font=font)
    legend_x += 170
for i, group in enumerate(group_order):
    y = 125 + i * row_h
    n = int(outcome_den.loc[group])
    draw.text((28, y + 9), f"{english[group]} (n={n})", fill="#17344a", font=font)
    x = bar_x
    cumulative = 0
    for j, category in enumerate(outcome_order):
        count = int(outcome_counts.loc[group, category])
        cumulative += count
        x_end = bar_x + round(bar_w * cumulative / n)
        draw.rectangle((x, y, x_end, y + 26), fill=colors[j])
        x = x_end
    direct = int(outcome_counts.loc[group, "직접 구제성 처리결과"])
    draw.text((bar_x + bar_w + 15, y + 9), f"Direct {direct}/{n} ({direct/n*100:.1f}%)",
              fill="#17344a", font=font)
draw.text((bar_x, height - 50), "Each bar totals 100% of that group's 2026 Q2 recorded outcomes.",
          fill="#526674", font=font)
img.save(OUT / "outcome_group_100pct_stacked.png")

reason_overall = reason_long[reason_long["가전품목군"].eq("전체 가전")]
outcome_overall = outcome_long[outcome_long["가전품목군"].eq("전체 가전")]
log_add = f"""

## STEP 3 청구이유·처리결과 그룹 최종 적용 (2026-09-24)

1. 사용자 확정 원문값 목록을 `analyze_step3.py`의 `REASON_GROUPS`·`OUTCOME_GROUPS`에 명시. 실제 관측된 비결측 원문값이 모두 정확히 한 그룹에 배정되는지 검증.
2. 청구이유 `품질(물품/용역)`·`AS불만`만 `품질·A/S 일반`; 나머지 비결측 14종은 `계약·기타`. 빈칸 3행은 `미분류`로 유지. 분모는 가전 전체 {total:,}행.
3. 수리 지연·부품 미보유·반복 고장·수리 불가를 직접 지시하는 원문값이 없어 `기준 판정형`은 전 품목군에서 `식별 불가(원문 미제공)`. 건수·비중을 0으로 표기하지 않고 CSV를 빈칸 및 상태 열로 나타냄. 히트맵에서도 N/A로 표시.
4. 처리결과 13종을 `직접 구제성 처리결과` 4종, `계약 조치` 3종, `절차 진행` 2종, `구제 확인 불가` 4종으로 분류. 직접 구제성 합계에는 계약 조치를 포함하지 않음.
5. 처리결과 비율 분모는 2026년 2분기 가전 결과기록 {outcome_total_n}행. 다른 9개 파일 가전 {total-outcome_total_n:,}행의 처리결과 결측은 유지하고 0으로 대체하지 않음. 이 결과만으로 소비자분쟁해결기준의 실제 적용 여부를 판정하지 않음.
6. 품목군별 비율은 각각 해당 품목군의 전 기간 가전 행 수 또는 2026년 2분기 결과기록 행 수를 분모로 계산. 전체 비율은 각각 {total:,}행, {outcome_total_n}행을 분모로 계산. 그래프의 영문 표기는 한글 글꼴 문제 방지 목적이며 원본 및 CSV 한글 범주명은 유지.
"""
prior_log = PREV_LOG.read_text(encoding="utf-8")
(OUT / "preprocessing_log.md").write_text(prior_log + log_add, encoding="utf-8")

lines = ["[REASON GROUPS: OVERALL]", reason_overall.to_string(index=False),
         "[REASON GROUP COUNTS BY APPLIANCE]", reason_count_table.to_string(),
         "[REASON GROUP ROW PERCENT BY APPLIANCE]", reason_pct_table.to_string(),
         "[OUTCOME GROUPS: OVERALL, 2026 Q2 ONLY]", outcome_overall.to_string(index=False),
         "[OUTCOME GROUP COUNTS BY APPLIANCE]", outcome_count_table.to_string(),
         "[OUTCOME GROUP ROW PERCENT BY APPLIANCE]", outcome_pct_table.to_string(),
         f"[CHECK] reason_total={total}, reason_group_counts={reason_total.to_dict()}",
         f"[CHECK] outcome_total={outcome_total_n}, outcome_group_counts={outcome_total.to_dict()}"]
(OUT / "execution_output.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:2] + lines[6:8] + lines[-2:]))
print("[FILES]")
for path in sorted(OUT.iterdir()):
    print(path.name, path.stat().st_size, "bytes")
