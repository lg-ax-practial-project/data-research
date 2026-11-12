"""STEP 4: quarterly appliance/overall trends and raw age-band comparison."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
ALL_SRC = ROOT / "outputs" / "step1_standardization" / "standardized_redress.csv"
APP_SRC = ROOT / "outputs" / "step2_final" / "appliance_redress.csv"
PREV_LOG = ROOT / "outputs" / "step3_final" / "preprocessing_log.md"

cols_all = ["원본파일", "접수일", "접수연도", "접수분기", "연령대"]
cols_app = cols_all + ["가전품목군"]
all_df = pd.read_csv(ALL_SRC, encoding="utf-8-sig", dtype=str,
                     keep_default_na=False, low_memory=False, usecols=cols_all)
app_df = pd.read_csv(APP_SRC, encoding="utf-8-sig", dtype=str,
                     keep_default_na=False, low_memory=False, usecols=cols_app)
assert len(all_df) == 150964 and len(app_df) == 5554

for data in (all_df, app_df):
    assert data["접수연도"].str.fullmatch(r"\d{4}").all()
    assert data["접수분기"].str.fullmatch(r"[1-4]").all()
    data["분기"] = data["접수연도"] + "Q" + data["접수분기"]

quarters = sorted(all_df["분기"].unique())
assert quarters == [f"{year}Q{q}" for year in range(2024, 2026) for q in range(1, 5)] + ["2026Q1", "2026Q2"]
all_counts = all_df["분기"].value_counts().reindex(quarters)
app_counts = app_df["분기"].value_counts().reindex(quarters)
assert all_counts.notna().all() and app_counts.notna().all()

quarter_summary = pd.DataFrame({"분기": quarters, "전체피해구제건수": all_counts.astype(int).values,
                                "가전피해구제건수": app_counts.astype(int).values})
quarter_summary["가전비중_pct"] = (quarter_summary["가전피해구제건수"] /
                                 quarter_summary["전체피해구제건수"] * 100).round(4)

coverage = []
for quarter in quarters:
    rows = all_df.loc[all_df["분기"].eq(quarter), "접수일"]
    exact_mask = rows.str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    year, q = int(quarter[:4]), int(quarter[-1])
    end_date = pd.Period(f"{year}Q{q}", freq="Q-DEC").end_time.date()
    if exact_mask.all():
        dates = pd.to_datetime(rows, format="%Y-%m-%d", errors="raise")
        minimum, maximum = str(dates.min().date()), str(dates.max().date())
        status = "분기말 날짜 관측; 완전성 미보증" if dates.max().date() == end_date else "분기 중간 종료 관측"
    elif (~exact_mask).all() and rows.nunique() == 1:
        minimum = maximum = "일자 확인 불가"
        status = "분기 표기만 존재; 일자 완전성 검증 불가"
    else:
        minimum = maximum = "혼합 표기"
        status = "일자·분기 표기 혼합; 확인 필요"
    coverage.append({"분기": quarter, "원본파일수": int(all_df.loc[all_df["분기"].eq(quarter), "원본파일"].nunique()),
                     "원문접수일최솟값": minimum, "원문접수일최댓값": maximum,
                     "분기말일": str(end_date), "기간상태": status})
coverage = pd.DataFrame(coverage)
assert coverage["원본파일수"].eq(1).all()
quarter_summary = quarter_summary.merge(coverage, on="분기", validate="one_to_one")
quarter_summary.to_csv(OUT / "quarterly_total_appliance_share.csv", index=False, encoding="utf-8-sig")

group_order = pd.read_csv(ROOT / "outputs" / "step2_final" / "appliance_group_summary.csv",
                          encoding="utf-8-sig")["가전품목군"].tolist()
group_order.remove("전체 가전")
product_counts = (app_df.groupby(["분기", "가전품목군"]).size().rename("건수").reset_index())
grid = pd.MultiIndex.from_product([quarters, group_order], names=["분기", "가전품목군"])
product_counts = (product_counts.set_index(["분기", "가전품목군"])
                  .reindex(grid, fill_value=0).reset_index())
product_counts = product_counts.merge(quarter_summary[["분기", "기간상태"]], on="분기", validate="many_to_one")
assert int(product_counts["건수"].sum()) == len(app_df)
product_counts.to_csv(OUT / "quarterly_appliance_by_product.csv", index=False, encoding="utf-8-sig")

def compare(label: str, prior: list[str], later: list[str], caveat: str) -> dict:
    before = quarter_summary[quarter_summary["분기"].isin(prior)]
    after = quarter_summary[quarter_summary["분기"].isin(later)]
    a0, a1 = int(before["가전피해구제건수"].sum()), int(after["가전피해구제건수"].sum())
    t0, t1 = int(before["전체피해구제건수"].sum()), int(after["전체피해구제건수"].sum())
    s0, s1 = a0/t0*100, a1/t1*100
    return {"비교": label, "이전기간": "+".join(prior), "비교기간": "+".join(later),
            "가전_이전건수": a0, "가전_비교건수": a1, "가전_증감건수": a1-a0,
            "가전_증감률_pct": round((a1-a0)/a0*100, 4),
            "전체_이전건수": t0, "전체_비교건수": t1, "전체_증감건수": t1-t0,
            "전체_증감률_pct": round((t1-t0)/t0*100, 4),
            "가전비중_이전_pct": round(s0, 4), "가전비중_비교_pct": round(s1, 4),
            "가전비중_변화_pp": round(s1-s0, 4), "해석제약": caveat}

comparisons = pd.DataFrame([
    compare("연간 동기간", [f"2024Q{i}" for i in range(1, 5)],
            [f"2025Q{i}" for i in range(1, 5)], "두 연도 모두 분기말 일자 관측"),
    compare("상반기 동기간", ["2025Q1", "2025Q2"], ["2026Q1", "2026Q2"],
            "2026Q2는 분기 표기만 있어 일자 완전성 검증 불가"),
])
comparisons.to_csv(OUT / "period_comparisons.csv", index=False, encoding="utf-8-sig")

age_order = ["10세 미만", "10 - 19세", "20 - 29세", "30 - 39세", "40 - 49세",
             "50 - 59세", "60 - 64세", "65 - 69세", "70 - 79세", "80세이상", "불명", "(미입력)"]
assert set(all_df["연령대"].unique()) == set(age_order)
assert set(app_df["연령대"].unique()).issubset(set(age_order))
assert all_df["연령대"].str.strip().ne("").all() and app_df["연령대"].str.strip().ne("").all()
all_age = all_df["연령대"].value_counts().reindex(age_order, fill_value=0)
app_age = app_df["연령대"].value_counts().reindex(age_order, fill_value=0)
age = pd.DataFrame({"연령대_원문": age_order,
                    "가전건수": app_age.astype(int).values, "가전분모": len(app_df),
                    "전체건수": all_age.astype(int).values, "전체분모": len(all_df)})
age["가전비중_pct"] = (age["가전건수"] / age["가전분모"] * 100).round(4)
age["전체비중_pct"] = (age["전체건수"] / age["전체분모"] * 100).round(4)
age["비중차이_pp"] = (age["가전비중_pct"] - age["전체비중_pct"]).round(4)
assert int(age["가전건수"].sum()) == len(app_df)
assert int(age["전체건수"].sum()) == len(all_df)
age.to_csv(OUT / "age_distribution_comparison.csv", index=False, encoding="utf-8-sig")

english = {"냉장고": "Refrigerator", "김치냉장고": "Kimchi fridge", "냉동고": "Freezer",
           "세탁기": "Washer", "워시타워": "WashTower", "의류건조기": "Clothes dryer",
           "의류관리기": "Clothing care", "에어컨": "Air conditioner", "TV": "TV",
           "식기세척기": "Dishwasher", "식기건조기": "Dish dryer", "청소기": "Vacuum cleaners",
           "공기청정기": "Air purifier", "제습기": "Dehumidifier", "가습기": "Humidifier",
           "정수기": "Water purifier", "음식물처리기": "Food waste processor",
           "인덕션레인지": "Induction range", "오븐·전자레인지": "Oven / microwave"}
assert set(english) == set(group_order)
font = ImageFont.load_default()

def line(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], color: str,
         dashed_final: bool = False, width: int = 3) -> None:
    if dashed_final and len(points) >= 2:
        draw.line(points[:-1], fill=color, width=width)
        x0, y0 = points[-2]
        x1, y1 = points[-1]
        for k in range(0, 12, 2):
            f0, f1 = k/12, (k+1)/12
            draw.line((x0+(x1-x0)*f0, y0+(y1-y0)*f0,
                       x0+(x1-x0)*f1, y0+(y1-y0)*f1), fill=color, width=width)
    else:
        draw.line(points, fill=color, width=width)

# Product small multiples retain all 19 product groups without an arbitrary top-N cutoff.
tile_w, tile_h, cols = 320, 205, 4
rows = (len(group_order) + cols - 1) // cols
img = Image.new("RGB", (cols * tile_w + 40, rows * tile_h + 100), "white")
draw = ImageDraw.Draw(img)
draw.text((22, 18), "Appliance redress counts fluctuate across quarters by product", fill="#17344a", font=font)
draw.text((22, 40), "Open final point = 2026 Q2 date-level coverage unverified; no mid-quarter cutoff is observed in dated files.",
          fill="#526674", font=font)
for idx, group in enumerate(group_order):
    row, col = divmod(idx, cols)
    x0, y0 = 20 + col * tile_w, 75 + row * tile_h
    values = product_counts.loc[product_counts["가전품목군"].eq(group), "건수"].to_numpy()
    maximum = max(int(values.max()), 1)
    draw.text((x0+9, y0+6), f"{english[group]}  max={maximum}", fill="#17344a", font=font)
    left, right, top, bottom = x0+35, x0+tile_w-18, y0+32, y0+tile_h-38
    draw.line((left, bottom, right, bottom), fill="#bcc8cf", width=1)
    draw.line((left, top, left, bottom), fill="#bcc8cf", width=1)
    pts = [(round(left + i*(right-left)/(len(values)-1)),
            round(bottom - int(v)*(bottom-top)/maximum)) for i, v in enumerate(values)]
    line(draw, pts, "#277da8", dashed_final=True, width=3)
    for px, py in pts[:-1]:
        draw.ellipse((px-3, py-3, px+3, py+3), fill="#277da8")
    px, py = pts[-1]
    draw.ellipse((px-5, py-5, px+5, py+5), fill="white", outline="#277da8", width=2)
    for j in (0, 3, 7, 9):
        draw.text((pts[j][0]-15, bottom+8), quarters[j].replace("20", ""), fill="#526674", font=font)
img.save(OUT / "quarterly_appliance_lines_by_product.png")

# Aligned trend panels plus exact quarter-level numerators and denominators.
img = Image.new("RGB", (1360, 700), "white")
draw = ImageDraw.Draw(img)
draw.text((25, 22), "Appliance redress fell from 2024 to 2025 while total redress rose", fill="#17344a", font=font)
draw.text((25, 45), "2026 Q2 has only a quarter label, so its day-level coverage is unverified.", fill="#526674", font=font)
panel_specs = [("All redress cases", quarter_summary["전체피해구제건수"].tolist(), "#9aa5b1", 95),
               ("Appliance redress cases", quarter_summary["가전피해구제건수"].tolist(), "#277da8", 275),
               ("Appliance share (%)", quarter_summary["가전비중_pct"].tolist(), "#d8864c", 455)]
for title, values, color, top in panel_specs:
    left, right, bottom = 195, 900, top+125
    draw.text((25, top+47), title, fill="#17344a", font=font)
    draw.line((left, bottom, right, bottom), fill="#bcc8cf", width=1)
    ymax = max(values) * 1.12
    draw.rectangle((round(left+8*(right-left)/9)-18, top+5, right+18, bottom+1), fill="#f3f4f5")
    pts = [(round(left+i*(right-left)/9), round(bottom-v/ymax*110)) for i,v in enumerate(values)]
    line(draw, pts, color, dashed_final=True, width=3)
    for px,py in pts[:-1]:
        draw.ellipse((px-3, py-3, px+3, py+3), fill=color)
    px,py = pts[-1]
    draw.ellipse((px-5, py-5, px+5, py+5), fill="white", outline=color, width=2)
    draw.text((left, bottom+7), "2024Q1", fill="#526674", font=font)
    draw.text((pts[4][0]-25, bottom+7), "2025Q1", fill="#526674", font=font)
    draw.text((pts[8][0]-25, bottom+7), "2026Q1", fill="#526674", font=font)
draw.text((960, 98), "Quarter  appliance / all  (share)", fill="#17344a", font=font)
for i, row in enumerate(quarter_summary.itertuples(index=False)):
    marker = "*" if row.분기 == "2026Q2" else " "
    draw.text((960, 122+i*42),
              f"{row.분기}{marker}  {row.가전피해구제건수:,}/{row.전체피해구제건수:,} ({row.가전비중_pct:.2f}%)",
              fill="#17344a", font=font)
draw.text((960, 560), "* date-level coverage unverified", fill="#526674", font=font)
img.save(OUT / "quarterly_total_appliance_share.png")

# Side-by-side shares make the different source denominators explicit.
age_labels = {"10세 미만":"Under 10", "10 - 19세":"10-19", "20 - 29세":"20-29",
              "30 - 39세":"30-39", "40 - 49세":"40-49", "50 - 59세":"50-59",
              "60 - 64세":"60-64", "65 - 69세":"65-69", "70 - 79세":"70-79",
              "80세이상":"80+", "불명":"Unknown", "(미입력)":"Not entered"}
img = Image.new("RGB", (1310, 780), "white")
draw = ImageDraw.Draw(img)
draw.text((25, 23), "Ages 30-39 have the most cases in both appliance and all redress", fill="#17344a", font=font)
draw.text((25, 46), "Bars compare within-population shares; counts and denominators appear at right.", fill="#526674", font=font)
draw.rectangle((260, 82, 275, 97), fill="#277da8")
draw.text((281, 83), "Appliance", fill="#17344a", font=font)
draw.rectangle((390, 82, 405, 97), fill="#9aa5b1")
draw.text((411, 83), "All redress", fill="#17344a", font=font)
bar_left, scale = 260, 13.5
for i,row in enumerate(age.itertuples(index=False)):
    y = 119 + i*52
    draw.text((25, y+13), age_labels[row.연령대_원문], fill="#17344a", font=font)
    draw.rectangle((bar_left, y, bar_left+round(row.가전비중_pct*scale), y+18), fill="#277da8")
    draw.rectangle((bar_left, y+21, bar_left+round(row.전체비중_pct*scale), y+39), fill="#9aa5b1")
    draw.text((735, y+2), f"Appliance {row.가전건수:,}/{row.가전분모:,} ({row.가전비중_pct:.2f}%)",
              fill="#17344a", font=font)
    draw.text((735, y+24), f"All {row.전체건수:,}/{row.전체분모:,} ({row.전체비중_pct:.2f}%)",
              fill="#17344a", font=font)
draw.text((25, 752), "Unknown and Not entered remain separate original categories.", fill="#526674", font=font)
img.save(OUT / "age_distribution_comparison.png")

prior = PREV_LOG.read_text(encoding="utf-8")
log_add = f"""

## STEP 4 분기 추이·연령대 분포 (2026-09-24)

1. 가전은 최종 선별된 {len(app_df):,}행, 전체 피해구제는 표준화 원본 {len(all_df):,}행 사용. 중복 제거·행 제외·결측 대체 없음. `접수연도`·`접수분기`로 2024Q1~2026Q2를 집계.
2. 품목별 분기 건수는 각 분기의 가전 원문 행을 세어 산출. 관측된 분기·품목 조합에 행이 없으면 집계 건수 0으로 기록하며, 원본 결측값을 0으로 채운 것이 아님.
3. 전체 대비 가전 비중은 각 분기 `가전 건수 / 전체 피해구제 건수 × 100`. 전년 동기간 비교는 2024년 연간 대 2025년 연간, 2025년 상반기 대 2026년 상반기로 사전 고정. 증가율은 `(비교기간-이전기간)/이전기간 × 100`, 비중 변화는 두 비중의 차이(pp).
4. 첫 9개 분기에는 행별 YYYY-MM-DD 일자가 있고 최댓값이 해당 분기 말일. 이것만으로 누락 없는 완전한 분기임을 보증하지 않음. 2026Q2는 모든 행이 `2026년 2분기`로만 표기되고 파일명은 20260630이므로 일자 수준 완전성을 확인할 수 없음. 확인된 중간 종료 분기는 없으나 2026Q2는 그래프에서 빈 점과 별표로 표시.
5. 연령대는 원문 범주 그대로 집계. `불명`과 `(미입력)`을 합치거나 제외하지 않음. 가전·전체 각각의 모든 행을 분모로 연령대 비율 산출. 그래프의 영문 표기는 글꼴 호환 목적.
6. 2026년 비교는 2026Q2 일자 범위 검증 한계를 포함해 해석. 이 자료는 피해구제 접수 데이터이며 LG전자 고객·수리 사건만을 식별하지 않음.
"""
(OUT / "preprocessing_log.md").write_text(prior + log_add, encoding="utf-8")

lines = ["[QUARTERLY TOTAL, APPLIANCE, SHARE, COVERAGE]", quarter_summary.to_string(index=False),
         "[PERIOD COMPARISONS]", comparisons.to_string(index=False),
         "[AGE DISTRIBUTION]", age.to_string(index=False),
         "[PRODUCT QUARTERLY COUNTS — FULL]", product_counts.to_string(index=False),
         f"[CHECK] all_rows={len(all_df)}, appliance_rows={len(app_df)}, quarter_rows={len(quarter_summary)}, product_quarter_rows={len(product_counts)}"]
(OUT / "execution_output.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:6]))
print(lines[-1])
print("[FILES]")
for path in sorted(OUT.iterdir()):
    print(path.name, path.stat().st_size, "bytes")
