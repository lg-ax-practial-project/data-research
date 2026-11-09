"""STEP 5 final: approved seven-label monthly consultation analysis."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REVIEW = ROOT / "outputs" / "step5_review"
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = REVIEW / "monthly_consultations_combined.csv"
LOG_SOURCE = REVIEW / "preprocessing_log.md"

# Exact raw-label mapping confirmed by the user. Each source label occurs in
# every one of the 32 monthly top-500 files.
LABEL_TO_GROUP = {
    "냉장고": "냉장고",
    "김치냉장고": "김치냉장고",
    "전기세탁기": "세탁기",
    "전기의류건조기": "의류건조기",
    "TV": "TV",
    "식기세척기": "식기세척기",
    "에어컨": "에어컨",
}
GROUP_ORDER = ["냉장고", "김치냉장고", "세탁기", "의류건조기", "TV", "식기세척기", "에어컨"]
EXPECTED_RECORDED_SUMS = {
    "냉장고": 10832,
    "김치냉장고": 3634,
    "세탁기": 5866,
    "의류건조기": 1376,
    "TV": 9024,
    "식기세척기": 2440,
    "에어컨": 13891,
}

data = pd.read_csv(SOURCE, encoding="utf-8-sig", dtype={"품목명_원문": str},
                   low_memory=False)
months = sorted(data["기준월"].unique())
assert len(months) == 32
assert months == pd.period_range(months[0], months[-1], freq="M").astype(str).tolist()
assert not data.duplicated(["기준월", "품목명_원문"]).any()
assert data["상담건수"].notna().all()

selected = data.loc[data["품목명_원문"].isin(LABEL_TO_GROUP)].copy()
selected["가전품목군"] = selected["품목명_원문"].map(LABEL_TO_GROUP)
assert selected["가전품목군"].notna().all()
assert len(selected) == len(months) * len(LABEL_TO_GROUP)
assert selected.groupby("품목명_원문")["기준월"].nunique().eq(len(months)).all()
selected["가전품목군"] = pd.Categorical(selected["가전품목군"], GROUP_ORDER, ordered=True)
selected = selected.sort_values(["기준월", "가전품목군"])

long = selected[["기준월", "기준월_날짜", "연도", "월", "가전품목군",
                 "품목명_원문", "상담건수", "원본파일", "원본행번호"]].copy()
long.to_csv(OUT / "monthly_seven_appliances_long.csv", index=False, encoding="utf-8-sig")

pivot = long.pivot(index="기준월", columns="가전품목군", values="상담건수")
pivot = pivot.reindex(index=months, columns=GROUP_ORDER)
assert pivot.notna().all().all(), "An approved complete label has an unknown month"
pivot.to_csv(OUT / "monthly_seven_appliances_wide.csv", encoding="utf-8-sig", na_rep="")
nan_summary = pd.DataFrame({
    "가전품목군": GROUP_ORDER,
    "관측월수": pivot.notna().sum().reindex(GROUP_ORDER).astype(int).to_numpy(),
    "NaN월수": pivot.isna().sum().reindex(GROUP_ORDER).astype(int).to_numpy(),
    "전체파일월수": len(months),
    "관측월_상담건수합": pivot.sum(min_count=1).reindex(GROUP_ORDER).astype(int).to_numpy(),
})
assert nan_summary["NaN월수"].eq(0).all()
assert dict(zip(nan_summary["가전품목군"], nan_summary["관측월_상담건수합"])) == EXPECTED_RECORDED_SUMS
nan_summary.to_csv(OUT / "seven_appliance_coverage.csv", index=False, encoding="utf-8-sig")

monthly_total = pivot.sum(axis=1, min_count=len(GROUP_ORDER)).rename("7품목_상담건수합")
assert monthly_total.notna().all()
monthly_total.to_csv(OUT / "monthly_seven_appliance_total.csv", encoding="utf-8-sig")
total_peak_month = str(monthly_total.idxmax())
total_peak_count = int(monthly_total.max())

# Keep every searched but unapproved label out of the seven-product series.
reviewed_labels = pd.read_csv(REVIEW / "seven_product_candidate_labels.csv",
                              encoding="utf-8-sig", dtype=str, keep_default_na=False)
excluded = reviewed_labels.loc[~reviewed_labels["품목명_원문"].isin(LABEL_TO_GROUP)].copy()
excluded["최종처리"] = "7품목 월별 시계열에서 제외 — 사용자 확정"
excluded.to_csv(OUT / "excluded_candidate_labels_audit.csv", index=False,
                encoding="utf-8-sig")
assert not set(excluded["품목명_원문"]) & set(LABEL_TO_GROUP)

ac = pivot["에어컨"]
peak_month = str(ac.idxmax())
peak_count = int(ac.max())
winter_mask = pd.PeriodIndex(ac.index, freq="M").month.isin([11, 12, 1, 2, 3])
winter = ac.loc[winter_mask]
winter_median = float(winter.median())
ratio = peak_count / winter_median
assert peak_month == "2025-07" and peak_count == 1964
assert len(winter) == 14 and winter_median == 100.5
assert round(ratio, 2) == 19.54
winter_detail = pd.DataFrame({"기준월": winter.index, "에어컨_상담건수": winter.astype(int).to_numpy()})
winter_detail.to_csv(OUT / "air_conditioner_winter_observations.csv", index=False,
                     encoding="utf-8-sig")
peak_summary = pd.DataFrame([{
    "품목": "에어컨", "분석대상원문": "에어컨", "관측월수": len(ac),
    "피크월": peak_month, "피크월_상담건수_분자": peak_count,
    "비수기정의": "11~3월, 관측 32개월 내 포함 월",
    "비수기_관측월수": len(winter), "비수기_월별상담건수_중앙값_분모": winter_median,
    "피크배율": ratio, "피크배율_소수둘째자리": round(ratio, 2),
    "증감률자료사용여부": "미사용; 월별 상담건수로 직접 계산",
}])
peak_summary.to_csv(OUT / "air_conditioner_peak_ratio.csv", index=False,
                    encoding="utf-8-sig")

# English figure labels avoid Korean font substitution. Count values are the
# raw monthly observations, and all lines would break on NaN (none for these 7).
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
title_font = ImageFont.truetype(font_path, 23)
label_font = ImageFont.truetype(font_path, 16)
small_font = ImageFont.truetype(font_path, 13)
english = {"냉장고": "Refrigerator", "김치냉장고": "Kimchi refrigerator",
           "세탁기": "Washer", "의류건조기": "Clothes dryer", "TV": "TV",
           "식기세척기": "Dishwasher", "에어컨": "Air conditioner"}


def draw_series(draw: ImageDraw.ImageDraw, values: pd.Series, left: int, top: int,
                right: int, bottom: int, color: str, *, peak_marker: str | None = None) -> None:
    ymax = int(math.ceil(values.max() / 100) * 100)
    draw.line((left, top, left, bottom), fill="#a6b4bf", width=1)
    draw.line((left, bottom, right, bottom), fill="#a6b4bf", width=1)
    draw.text((left-46, top-7), f"{ymax:,}", fill="#516774", font=small_font)
    draw.text((left-14, bottom-6), "0", fill="#516774", font=small_font)
    previous = None
    for i, value in enumerate(values):
        point = None
        if pd.notna(value):
            x = round(left + i * (right-left) / (len(values)-1))
            y = round(bottom - float(value) / ymax * (bottom-top))
            point = (x, y)
            if previous is not None:
                draw.line((previous, point), fill=color, width=3)
            draw.ellipse((x-3, y-3, x+3, y+3), fill=color)
            if peak_marker is not None and values.index[i] == peak_marker:
                draw.ellipse((x-6, y-6, x+6, y+6), fill="white", outline="#dc6845", width=3)
        previous = point
    for index in (0, 7, 19, len(values)-1):
        x = round(left + index * (right-left) / (len(values)-1))
        draw.text((x-21, bottom+8), str(values.index[index])[2:], fill="#516774", font=small_font)


series = [(english[group], pivot[group], "#2585a9") for group in GROUP_ORDER]
series.append(("Seven-label total", monthly_total, "#de784b"))
tile_w, tile_h, cols = 650, 305, 2
rows = (len(series) + cols - 1) // cols
figure = Image.new("RGB", (cols*tile_w+30, rows*tile_h+95), "white")
draw = ImageDraw.Draw(figure)
draw.text((26, 18), f"The seven appliance labels reach their combined peak in {total_peak_month}.",
          fill="#17344a", font=title_font)
draw.text((27, 53), "Each panel has its own count scale; all seven source labels appear in every month.",
          fill="#516774", font=label_font)
for k, (name, values, color) in enumerate(series):
    row, col = divmod(k, cols)
    x0, y0 = 15 + col*tile_w, 83 + row*tile_h
    draw.text((x0+18, y0+6), name, fill="#17344a", font=label_font)
    draw.text((x0+18, y0+29), f"32/32 months   max {int(values.max()):,}",
              fill="#516774", font=small_font)
    draw_series(draw, values, x0+75, y0+64, x0+tile_w-28, y0+tile_h-44,
                color, peak_marker=total_peak_month if name == "Seven-label total" else
                peak_month if name == "Air conditioner" else None)
figure.save(OUT / "monthly_seven_appliance_timeseries.png")

# Show the exact denominator behind the approved peak multiple.
figure = Image.new("RGB", (1380, 560), "white")
draw = ImageDraw.Draw(figure)
draw.text((30, 22),
          f"Air conditioner consultations in {peak_month} are {ratio:.2f} times the winter median.",
          fill="#17344a", font=title_font)
draw.text((32, 58),
          f"Peak {peak_count:,} consultations / median {winter_median:g} across {len(winter)} observed Nov-Mar months",
          fill="#516774", font=label_font)
left, right, top, bottom = 88, 1110, 112, 468
for i, month in enumerate(months):
    if pd.Period(month, freq="M").month in [11, 12, 1, 2, 3]:
        x = round(left + i*(right-left)/(len(months)-1))
        draw.rectangle((x-8, top, x+8, bottom), fill="#eaf4fa")
draw_series(draw, ac, left, top, right, bottom, "#247fa3", peak_marker=peak_month)
ymax = int(math.ceil(ac.max()/100)*100)
median_y = round(bottom - winter_median/ymax*(bottom-top))
draw.line((left, median_y, right, median_y), fill="#e19a4e", width=2)
draw.text((1128, median_y-9), f"Winter median {winter_median:g}",
          fill="#a9601c", font=small_font)
peak_i = months.index(peak_month)
peak_x = round(left + peak_i*(right-left)/(len(months)-1))
peak_y = round(bottom - peak_count/ymax*(bottom-top))
draw.text((min(peak_x+12, 1070), max(peak_y-29, 105)),
          f"{peak_month}: {peak_count:,}", fill="#b9482d", font=label_font)
draw.rectangle((30, 512, 47, 527), fill="#eaf4fa")
draw.text((55, 509), "Nov-Mar months", fill="#516774", font=small_font)
figure.save(OUT / "air_conditioner_peak_vs_winter.png")

log = LOG_SOURCE.read_text(encoding="utf-8")
log += """\n\n## STEP 5 최종 7품목 월별 상담 시계열 (사용자 확정)\n\n1. 월별 상위 500위 결합 자료의 원문 품목명에서 냉장고→냉장고, 김치냉장고→김치냉장고, 전기세탁기→세탁기, 전기의류건조기→의류건조기, TV→TV, 식기세척기→식기세척기, 에어컨→에어컨만 정확히 일치 매핑. 부분 문자열 매핑은 사용하지 않음.\n2. 이동식에어컨·팬코일(이동식에어컨), 워시타워, 냉동고, 식기건조기, 기타냉장·냉동기기, 각종냉장·냉동기기와 용역·주변용품·방송서비스 유사어는 승인된 7품목 시계열에서 제외. 원본 결합 자료는 수정하지 않음. `excluded_candidate_labels_audit.csv`에 검토 표기별 제외 기록.\n3. 선택한 원문 7종 각각 32개월 모두 상위 500위에 관측되는지 검증한 뒤 월별 7품목 원문 건수 224행만 추출. 집계·피벗에서 결측을 0으로 채우지 않음. 7종은 실제 NaN 월이 모두 0개.\n4. 7품목 월별 합계는 그 달 7종 모두 관측된 경우에만 산출하도록 `min_count=7` 사용. 이 합계는 선정 7개 원문 표기의 합이며 전체 가전 상담이나 전체 소비자 상담이 아님.\n5. 에어컨 피크는 32개월 중 월간 상담건수 최대값. 비수기는 관측 기간 중 11·12·1·2·3월의 14개 월간 상담건수 중앙값. 피크 배율은 최대 월간 건수 / 비수기 중앙값으로 계산. 사전 승인된 기준 외 월 제외·0 대체 없음.\n6. 원문 전월·전년동월 증감률은 시계열·피크·배율 계산에 사용하지 않음. 그래프는 실제 월별 상담건수만 사용하며 영문 라벨은 한글 글꼴 깨짐 방지 목적. 월별 7개 품목 시계열은 각 패널별 독립적인 건수 축을 사용함.\n"""
(OUT / "preprocessing_log.md").write_text(log, encoding="utf-8")

print(f"SOURCE_ROWS={len(data)} SELECTED_ROWS={len(long)} MONTHS={len(months)} "
      f"GROUPS={len(GROUP_ORDER)} ALL_SELECTED_NAN_MONTHS={int(nan_summary['NaN월수'].sum())}")
print("SEVEN LABEL COVERAGE AND RECORDED SUMS")
print(nan_summary.to_string(index=False))
print(f"SEVEN_LABEL_TOTAL_SUM={int(monthly_total.sum())} "
      f"PEAK={total_peak_month}:{total_peak_count}")
print("AC WINTER MONTHS")
print(winter_detail.to_string(index=False))
print(f"AC_PEAK={peak_month}:{peak_count} WINTER_MONTHS={len(winter)} "
      f"WINTER_MEDIAN={winter_median:g} RATIO={ratio:.6f} ROUNDED={ratio:.2f}")
print("OUTPUTS")
for path in sorted(OUT.iterdir()):
    if path.is_file():
        print(path.name)
