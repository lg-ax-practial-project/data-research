"""STEP 5 review: inspect monthly top-500 consultation files without grouping labels.

Run with the bundled Python 3 runtime. The proposed seven-product mapping is
review material only; grouped series and an AC peak ratio require approval.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT.mkdir(parents=True, exist_ok=True)
PREV_LOG = ROOT / "outputs" / "step4_trend_age" / "preprocessing_log.md"


def normalized(text: str) -> str:
    return unicodedata.normalize("NFC", text)


files = sorted(
    (p for p in DATA.rglob("*") if p.is_file() and p.suffix.lower() == ".csv"
     and "품목별 상담 현황_" in normalized(p.name)),
    key=lambda p: normalized(p.name),
)
assert files, "Monthly consultation files not found"


def read_source(path: Path) -> tuple[pd.DataFrame, str]:
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding, dtype=str,
                               keep_default_na=False, low_memory=False), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8/cp949", b"", 0, 1, str(path))


def parse_number(source: pd.Series, column: str, allow_blank: bool = False) -> pd.Series:
    cleaned = source.astype(str).str.strip().str.replace(",", "", regex=False)
    if allow_blank:
        cleaned = cleaned.replace({"": pd.NA, "-": pd.NA, "—": pd.NA})
    out = pd.to_numeric(cleaned, errors="coerce")
    invalid = out.isna() & cleaned.notna()
    assert not invalid.any(), f"Invalid {column}: {source.loc[invalid].unique()[:10]}"
    if not allow_blank:
        assert out.notna().all(), f"Missing {column}"
    return out


all_parts: list[pd.DataFrame] = []
inventory: list[dict] = []
for path in files:
    frame, encoding = read_source(path)
    frame.columns = [column.strip() for column in frame.columns]
    file_date_match = re.search(r"_(\d{8})\.csv$", normalized(path.name), re.I)
    assert file_date_match, path.name
    file_date = file_date_match.group(1)
    if file_date == "20240103":
        year, month = 2023, 12
        month_basis = "파일명 예외: 2024-01 파일의 전월 수치로 2023-12 추론"
    elif file_date == "20240201":
        year, month = 2024, 1
        month_basis = "파일명 예외: 2024-02-01 게시, 2024-01 수치로 추론"
    else:
        year, month = int(file_date[:4]), int(file_date[4:6])
        month_basis = "파일명 연월"
    assert 1 <= month <= 12

    old_schema = "품목명(소)" in frame.columns
    if old_schema:
        required = {"품목명(소)", "상담건수", "증감률_전월", "증감률_전년동월"}
        assert set(frame.columns) == required, (path.name, frame.columns.tolist())
        raw_name = frame["품목명(소)"]
        raw_mom = frame["증감률_전월"]
        raw_yoy = frame["증감률_전년동월"]
        schema = "4열"
    else:
        required = {"연도", "월", "품목명", "상담건수", "전월대비 증감률", "전년동월대비 증감률"}
        assert set(frame.columns) == required, (path.name, frame.columns.tolist())
        assert frame["연도"].str.strip().eq(str(year)).all()
        assert parse_number(frame["월"], "월").eq(month).all()
        raw_name = frame["품목명"]
        raw_mom = frame["전월대비 증감률"]
        raw_yoy = frame["전년동월대비 증감률"]
        month_basis = "원본 연도·월 열과 파일명 일치"
        schema = "6열"

    assert len(frame) == 500, (path.name, len(frame))
    assert raw_name.str.strip().ne("").all(), path.name
    assert raw_name.eq(raw_name.str.strip()).all(), path.name
    assert not raw_name.duplicated().any(), path.name
    count = parse_number(frame["상담건수"], "상담건수").astype("int64")
    assert count.ge(0).all()
    mom = parse_number(raw_mom, "전월대비 증감률", allow_blank=True)
    yoy = parse_number(raw_yoy, "전년동월대비 증감률", allow_blank=True)
    report_month = f"{year:04d}-{month:02d}"
    part = pd.DataFrame({
        "기준월": report_month,
        "기준월_날짜": pd.Timestamp(year=year, month=month, day=1).date().isoformat(),
        "연도": year,
        "월": month,
        "품목명_원문": raw_name,
        "상담건수_원문": frame["상담건수"],
        "상담건수": count,
        "전월증감률_원문": raw_mom,
        "전년동월증감률_원문": raw_yoy,
        "전월증감률_pct": mom,
        "전년동월증감률_pct": yoy,
        "원본파일": normalized(path.name),
        "원본행번호": range(2, len(frame) + 2),
    })
    all_parts.append(part)
    inventory.append({"원본파일": normalized(path.name), "기준월": report_month,
                      "기준월_판단근거": month_basis, "행수": len(frame),
                      "열수": len(frame.columns), "원본구조": schema,
                      "인코딩": encoding, "고유품목명수": raw_name.nunique(),
                      "전월증감률_결측행": int(mom.isna().sum()),
                      "전년동월증감률_결측행": int(yoy.isna().sum())})

combined = pd.concat(all_parts, ignore_index=True)
file_table = pd.DataFrame(inventory).sort_values("기준월").reset_index(drop=True)
assert file_table["기준월"].is_unique
months = pd.period_range(file_table["기준월"].min(), file_table["기준월"].max(), freq="M").astype(str).tolist()
missing_months = sorted(set(months) - set(file_table["기준월"]))
assert len(combined) == int(file_table["행수"].sum())
assert not combined.duplicated(["기준월", "품목명_원문"]).any()
assert set(combined["기준월"]) == set(months) - set(missing_months)

file_table.to_csv(OUT / "file_month_inventory.csv", index=False, encoding="utf-8-sig")
combined.to_csv(OUT / "monthly_consultations_combined.csv", index=False, encoding="utf-8-sig")
pd.DataFrame({"빠진기준월": missing_months}).to_csv(
    OUT / "missing_months.csv", index=False, encoding="utf-8-sig")

# Raw-name pivot only: a missing top-500 appearance remains NaN.
pivot = combined.pivot(index="품목명_원문", columns="기준월", values="상담건수")
pivot = pivot.reindex(columns=months).sort_index()
assert int(pivot.notna().sum().sum()) == len(combined)
pivot.to_csv(OUT / "raw_product_month_pivot.csv", encoding="utf-8-sig", na_rep="")
nan_counts = pd.DataFrame({"품목명_원문": pivot.index,
                           "관측월수": pivot.notna().sum(axis=1).to_numpy(),
                           "NaN월수": pivot.isna().sum(axis=1).to_numpy(),
                           "전체파일월수": len(months)})
assert nan_counts["관측월수"].add(nan_counts["NaN월수"]).eq(len(months)).all()
nan_counts.to_csv(OUT / "raw_product_nan_month_counts.csv", index=False, encoding="utf-8-sig")

# Candidate review is deliberately not written back to the combined dataset.
search = r"냉장|냉동|세탁|워시|건조|에어컨|TV|텔레비|식기세척|식기건조"
labels = combined.loc[combined["품목명_원문"].str.contains(search, regex=True)]
candidate_stats = (labels.groupby("품목명_원문", as_index=False)
                   .agg(관측월수=("기준월", "nunique"), 기록상담건수합=("상담건수", "sum")))
proposed = {
    "냉장고": "냉장고", "김치냉장고": "김치냉장고",
    "전기세탁기": "세탁기", "전기의류건조기": "의류건조기",
    "에어컨": "에어컨", "이동식에어컨": "에어컨",
    "팬코일(이동식에어컨)": "에어컨", "TV": "TV", "식기세척기": "식기세척기",
}
adjacent = {
    "워시타워": "STEP 2에서는 세탁기와 별도 품목군; 7개로 합칠지 확인",
    "냉동고": "STEP 2에서는 냉장고와 별도 품목군",
    "식기건조기": "STEP 2에서는 식기세척기와 별도 품목군",
    "기타냉장·냉동기기": "냉장고·냉동고 구분 불가; 확인 필요",
    "각종냉장·냉동기기": "냉장고·냉동고 구분 불가; 확인 필요",
}
candidate_stats["제안상태"] = candidate_stats["품목명_원문"].map(
    lambda name: "7품목 매핑 제안" if name in proposed else
                 "경계 표기 확인" if name in adjacent else "유사 문자열·제외 제안")
candidate_stats["제안품목"] = candidate_stats["품목명_원문"].map(proposed)
candidate_stats["검토메모"] = candidate_stats["품목명_원문"].map(adjacent).fillna("")
candidate_stats.loc[candidate_stats["제안상태"].eq("유사 문자열·제외 제안"), "검토메모"] = (
    "서비스·용품·자동차용·방송서비스 등 7개 가전 본체와 성격 다름")
status_order = {"7품목 매핑 제안": 0, "경계 표기 확인": 1, "유사 문자열·제외 제안": 2}
candidate_stats["_order"] = candidate_stats["제안상태"].map(status_order)
candidate_stats = candidate_stats.sort_values(["_order", "제안품목", "품목명_원문"],
                                              na_position="last").drop(columns="_order")
candidate_stats.to_csv(OUT / "seven_product_candidate_labels.csv", index=False,
                       encoding="utf-8-sig")

# Compare same raw name only when the earlier month is present in the top 500.
comparison_parts = []
for offset, label, published_col in (
    (1, "전월", "전월증감률_pct"), (12, "전년동월", "전년동월증감률_pct")
):
    current = combined[["기준월", "품목명_원문", "상담건수", published_col, "원본파일"]].copy()
    current["비교기준월"] = (pd.PeriodIndex(current["기준월"], freq="M") - offset).astype(str)
    previous = combined[["기준월", "품목명_원문", "상담건수"]].rename(
        columns={"기준월": "비교기준월", "상담건수": "비교기준월_상담건수"})
    audit = current.merge(previous, on=["비교기준월", "품목명_원문"],
                          how="left", validate="many_to_one")
    audit["비교종류"] = label
    audit = audit.rename(columns={"상담건수": "해당월_상담건수", published_col: "파일증감률_pct"})
    audit["직접계산증감률_pct"] = (
        (audit["해당월_상담건수"] / audit["비교기준월_상담건수"] - 1) * 100)
    audit.loc[audit["비교기준월_상담건수"].eq(0), "직접계산증감률_pct"] = float("nan")
    audit["차이_pp"] = (audit["파일증감률_pct"] - audit["직접계산증감률_pct"]).abs()
    audit["대조상태"] = "반올림 허용범위 이내"
    audit.loc[audit["비교기준월_상담건수"].isna(), "대조상태"] = "이전월 상위500 미관측/파일범위 밖"
    audit.loc[audit["비교기준월_상담건수"].eq(0), "대조상태"] = "이전월 분모 0"
    audit.loc[audit["파일증감률_pct"].isna(), "대조상태"] = "원본 증감률 결측"
    audit.loc[audit["대조상태"].eq("반올림 허용범위 이내") & audit["차이_pp"].gt(0.11),
              "대조상태"] = "차이 0.11%p 초과"
    comparison_parts.append(audit)
comparison = pd.concat(comparison_parts, ignore_index=True)
comparison = comparison.sort_values(["기준월", "품목명_원문", "비교종류"])
comparison.to_csv(OUT / "rate_validation_all.csv", index=False, encoding="utf-8-sig")

# Diagnostic only: the July 2024 published "previous month" rate appears to
# reference May, while the true preceding observed month is June.
july = combined.loc[combined["기준월"].eq("2024-07"),
                    ["품목명_원문", "상담건수", "전월증감률_pct"]].rename(
                        columns={"상담건수": "2024-07_상담건수"})
for earlier in ("2024-06", "2024-05"):
    earlier_counts = combined.loc[combined["기준월"].eq(earlier),
                                  ["품목명_원문", "상담건수"]].rename(
                                      columns={"상담건수": f"{earlier}_상담건수"})
    july = july.merge(earlier_counts, on="품목명_원문", how="left", validate="one_to_one")
    july[f"{earlier}_기준_직접계산_pct"] = (
        (july["2024-07_상담건수"] / july[f"{earlier}_상담건수"] - 1) * 100)
    july[f"{earlier}_기준_차이_pp"] = (
        july["전월증감률_pct"] - july[f"{earlier}_기준_직접계산_pct"]).abs()
july.to_csv(OUT / "july_2024_rate_diagnostic.csv", index=False, encoding="utf-8-sig")

sample_keys = [
    ("2024-01", "헬스장", "전월"),
    ("2024-07", "에어컨", "전월"),
    ("2025-01", "TV", "전월"),
    ("2025-01", "TV", "전년동월"),
    ("2025-07", "냉장고", "전월"),
    ("2025-07", "냉장고", "전년동월"),
    ("2025-12", "김치냉장고", "전월"),
    ("2026-03", "전기세탁기", "전년동월"),
    ("2026-07", "에어컨", "전월"),
    ("2026-07", "식기세척기", "전년동월"),
]
sample_index = pd.MultiIndex.from_tuples(sample_keys, names=["기준월", "품목명_원문", "비교종류"])
samples = comparison.set_index(["기준월", "품목명_원문", "비교종류"]).reindex(sample_index).reset_index()
assert samples["해당월_상담건수"].notna().all()
samples.to_csv(OUT / "rate_comparison_samples.csv", index=False, encoding="utf-8-sig")

# Provisional small multiples show exact original labels without approved grouping.
preview_labels = list(proposed)
english = {"냉장고": "Refrigerator", "김치냉장고": "Kimchi fridge",
           "전기세탁기": "Electric washer", "전기의류건조기": "Electric clothes dryer",
           "에어컨": "Air conditioner", "이동식에어컨": "Portable AC",
           "팬코일(이동식에어컨)": "Fan coil (portable AC)",
           "TV": "TV", "식기세척기": "Dishwasher"}
font = ImageFont.load_default()
cols, tile_w, tile_h = 3, 410, 215
rows = (len(preview_labels) + cols - 1) // cols
image = Image.new("RGB", (cols * tile_w + 35, rows * tile_h + 100), "white")
draw = ImageDraw.Draw(image)
draw.text((20, 18), "Raw appliance labels show different monthly consultation patterns.",
          fill="#17344a", font=font)
draw.text((20, 42), "Each panel is one source label; gaps mean absent from that month's top 500.",
          fill="#516774", font=font)
for k, name in enumerate(preview_labels):
    row, col = divmod(k, cols)
    x0, y0 = 15 + col * tile_w, 75 + row * tile_h
    values = pivot.loc[name, months]
    ymax = max(float(values.max()), 1.0)
    left, right, top, bottom = x0 + 42, x0 + tile_w - 20, y0 + 48, y0 + tile_h - 40
    draw.text((x0 + 10, y0 + 5), english[name], fill="#17344a", font=font)
    draw.text((x0 + 10, y0 + 22), f"observed {int(values.notna().sum())}/{len(months)} months",
              fill="#516774", font=font)
    draw.text((x0 + 10, top - 9), f"{int(values.max()):,}", fill="#516774", font=font)
    draw.text((x0 + 25, bottom - 5), "0", fill="#516774", font=font)
    draw.line((left, top, left, bottom), fill="#9dadb9", width=1)
    draw.line((left, bottom, right, bottom), fill="#9dadb9", width=1)
    points = []
    for i, value in enumerate(values):
        x = round(left + i * (right - left) / (len(months) - 1))
        if pd.isna(value):
            points.append(None)
            continue
        y = round(bottom - float(value) / ymax * (bottom - top))
        points.append((x, y))
        if i > 0 and points[i - 1] is not None:
            draw.line((points[i - 1], points[i]), fill="#247fa3", width=3)
        draw.ellipse((x-2, y-2, x+2, y+2), fill="#247fa3")
    for i in (0, 12, 24, len(months)-1):
        draw.text((round(left+i*(right-left)/(len(months)-1))-17, bottom+7),
                  months[i][2:], fill="#516774", font=font)
image.save(OUT / "raw_candidate_monthly_lines.png")

log = PREV_LOG.read_text(encoding="utf-8")
log += """\n\n## STEP 5 월별 상담 자료 구조·매핑안 검토 (매핑 미확정)\n\n1. 파일명 NFC 정규화로 `품목별 상담 현황_` CSV만 찾음. UTF-8-SIG 우선 읽고 실패할 때 CP949 사용. 모든 원본 열은 문자열로 읽으며 원본 파일은 수정하지 않음.\n2. 초기 4열 스키마 `품목명(소)`/`증감률_전월`/`증감률_전년동월`과 이후 6열 스키마 `품목명`/`전월대비 증감률`/`전년동월대비 증감률`을 표준 열로 결합. 2024-06 파일의 헤더 주변 공백만 제거. 원문 품목명 값은 변경하지 않음.\n3. 기준월은 원본 `연도`·`월` 열이 있으면 파일명 연월과 일치 검증. 초기 파일은 파일명 연월을 사용하되 `20240103.CSV`는 2023-12, `20240201.csv`는 2024-01로 예외 추론. 전월 상담건수와 기재 증감률 대조 근거를 `rate_comparison_samples.csv`에 보존. 이 두 기준월은 원본 열이 없어 추론값임.\n4. `상담건수`와 증감률의 쉼표 천 단위 구분자를 수치 파싱 때만 제거하고 원문 문자열도 별도 보존. 숫자가 아닌 결측 증감률은 결측으로 유지. 상담건수의 결측 대체·행 제외 없음.\n5. 파일별 500위 목록에서 특정 원문 품목명이 빠진 달은 미관측(NaN)으로 보존. 0건 대체 금지. 원문 품목명 기준 피벗 및 NaN 월 수를 저장. 품목명을 7개 가전군으로 합치는 매핑은 제안표에만 기록하고 결합 자료에는 미적용.\n6. 전월·전년동월 증감률 검증은 동일한 원문 품목명의 비교 시점이 파일에 관측될 때만 수행. 비교 월이 상위 500 밖이거나 파일 범위 밖이면 직접 계산 불가로 표시. 차이 0.11%p 이하는 원본의 소수 첫째 자리 반올림 허용 범위로 분류하되 개별 차이는 보존.\n7. `raw_candidate_monthly_lines.png`는 승인 전 9개 원문 표기만 각각 그린 예비 그래프. 원문 품목 간 합산 없음. 미관측 NaN 구간을 연결하지 않음.\n8. 최종 7품목 매핑, 품목군 월별 피벗·그래프, 에어컨 피크/비수기 배율은 사용자 확인 후 수행.\n"""
log += "\n9. 2024-07 원본의 전월 증감률은 직전 2024-06보다 2024-05 상담건수와 대부분 부합함. 두 기준을 july_2024_rate_diagnostic.csv에 대조. 원인은 원본만으로 확정하지 않으며 최종 Q3 추이·피크 계산에는 제공 증감률 대신 월별 상담건수만 사용.\n"
log += "10. `기준월_날짜`는 월별 시계열 결합을 위한 해당 월 1일(YYYY-MM-01)이며 개별 상담 접수일을 뜻하지 않음. `연도`·`월` 정수 열 및 `기준월`(YYYY-MM) 문자열도 함께 보존.\n"
(OUT / "preprocessing_log.md").write_text(log, encoding="utf-8")

print(f"FILES={len(files)} ROWS={len(combined)} MONTHS={len(months)} "
      f"RANGE={months[0]}..{months[-1]} MISSING_MONTHS={missing_months}")
print(f"RAW_PRODUCT_NAMES={pivot.shape[0]} PIVOT_NON_NULL={int(pivot.notna().sum().sum())} "
      f"PIVOT_NAN={int(pivot.isna().sum().sum())}")
print("FILE INVENTORY")
print(file_table[["원본파일", "기준월", "행수", "인코딩", "기준월_판단근거"]].to_string(index=False))
print("CANDIDATE LABELS")
print(candidate_stats.to_string(index=False))
print("NaN COUNTS: proposed core labels")
print(nan_counts[nan_counts["품목명_원문"].isin(proposed)].to_string(index=False))
ac_extra = pivot.loc[["이동식에어컨", "팬코일(이동식에어컨)"]]
print("AC portable variants observed together:",
      ac_extra.columns[ac_extra.notna().all(axis=0)].tolist())
print("RATE VALIDATION STATUS")
print(comparison.groupby(["비교종류", "대조상태"]).size().to_string())
early = comparison.loc[comparison["기준월"].eq("2024-01") &
                       comparison["비교종류"].eq("전월") &
                       comparison["비교기준월_상담건수"].notna()]
print(f"2024-01 vs inferred 2023-12: comparable={len(early)} "
      f"within_0.11pp={int(early['차이_pp'].le(0.11).sum())}")
for earlier in ("2024-06", "2024-05"):
    error = july[f"{earlier}_기준_차이_pp"]
    print(f"2024-07 published MoM vs {earlier}: comparable={int(error.notna().sum())} "
          f"within_0.11pp={int(error.le(0.11).sum())} median_error_pp={error.median():.4f}")
print("RATE VALIDATION SAMPLES")
print(samples[["기준월", "품목명_원문", "비교종류", "해당월_상담건수",
               "비교기준월_상담건수", "파일증감률_pct", "직접계산증감률_pct",
               "차이_pp", "대조상태"]].to_string(index=False,
                                               float_format=lambda value: f"{value:.4f}"))
