"""Apply the user-approved STEP 1 column and product-name standardization rules."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from unicodedata import normalize

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)


def load(path: Path) -> tuple[pd.DataFrame, str]:
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding, dtype=str,
                               keep_default_na=False, low_memory=False), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Could not decode {path}")


def key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def save_csv(filename: str, df: pd.DataFrame) -> None:
    df.to_csv(OUT / filename, index=False, encoding="utf-8-sig")


paths = sorted((p for p in DATA.rglob("*") if p.is_file() and p.suffix.lower() == ".csv"),
               key=lambda p: normalize("NFC", p.name))
redress_paths = [p for p in paths if "소비자 피해구제 정보_" in normalize("NFC", p.name)]
code_paths = [p for p in paths if "소비자 피해구제 품목 정보_" in normalize("NFC", p.name)]
assert len(redress_paths) == 10 and len(code_paths) == 1

code, code_encoding = load(code_paths[0])
assert list(code.columns) == ["번호", "대분류품목", "중분류품목", "소분류품목"]
code["품목매핑키"] = code["소분류품목"].map(key)
if code["품목매핑키"].eq("").any() or code["품목매핑키"].duplicated().any():
    raise ValueError("Codebook normalized keys are blank or duplicated; join would be ambiguous")

frames = []
source_rows = []
for path in redress_paths:
    df, encoding = load(path)
    source_name = normalize("NFC", path.name)
    rename = {c: "물품소분류" for c in ["물품명"] if c in df.columns}
    rename.update({c: "연령대" for c in ["연령"] if c in df.columns})
    rename.update({c: "접수일" for c in ["접수일(년월일)"] if c in df.columns})
    df = df.rename(columns=rename)
    if df.columns.duplicated().any():
        raise ValueError(f"Duplicate columns after approved renaming: {source_name}")
    required = {"접수일", "연령대", "물품소분류"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing standard columns in {source_name}: {required - set(df.columns)}")

    raw_period = df["접수일"].astype(str)
    is_date = raw_period.str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    quarter_parts = raw_period.str.extract(r"^(\d{4})년\s*([1-4])분기$")
    is_quarter = quarter_parts[0].notna()
    if (~(is_date | is_quarter)).any():
        raise ValueError(f"Unrecognized date/quarter text in {source_name}: "
                         f"{raw_period[~(is_date | is_quarter)].value_counts().to_dict()}")
    year = pd.Series(pd.NA, index=df.index, dtype="Int64")
    quarter = pd.Series(pd.NA, index=df.index, dtype="Int64")
    if is_date.any():
        parsed = pd.to_datetime(raw_period[is_date], format="%Y-%m-%d", errors="raise")
        year.loc[is_date] = parsed.dt.year.astype("Int64")
        quarter.loc[is_date] = parsed.dt.quarter.astype("Int64")
    if is_quarter.any():
        year.loc[is_quarter] = quarter_parts.loc[is_quarter, 0].astype("Int64")
        quarter.loc[is_quarter] = quarter_parts.loc[is_quarter, 1].astype("Int64")
    df["접수연도"] = year
    df["접수분기"] = quarter
    df.insert(0, "원본행번호", range(2, len(df) + 2))
    df.insert(0, "원본파일", source_name)
    frames.append(df)
    source_rows.append({"file": source_name, "encoding": encoding, "source_rows": len(df),
                        "exact_date_rows": int(is_date.sum()), "quarter_label_rows": int(is_quarter.sum())})

standard = pd.concat(frames, ignore_index=True, sort=False)
source_product = standard["물품소분류"].astype(str)
normalized = source_product.map(key)
standard["품목매핑키"] = normalized.mask(normalized.eq(""), pd.NA)

lookup = code[["품목매핑키", "번호", "대분류품목", "중분류품목", "소분류품목"]].rename(columns={"번호": "코드표_번호"})
mapped = standard.merge(lookup, on="품목매핑키", how="left", validate="many_to_one", indicator=True)
mapped["매핑상태"] = "불일치"
mapped.loc[mapped["_merge"].eq("both"), "매핑상태"] = "일치"
mapped.loc[mapped["품목매핑키"].isna(), "매핑상태"] = "원문결측"
mapped = mapped.drop(columns="_merge")

column_order = ["원본파일", "원본행번호", "사건번호", "접수일", "접수연도", "접수분기",
                "성별", "연령대", "지역", "판매유형", "판매방법", "물품소분류", "청구이유",
                "처리결과", "품목매핑키", "매핑상태", "코드표_번호", "대분류품목", "중분류품목", "소분류품목"]
mapped = mapped.reindex(columns=column_order)

audit = mapped.groupby("원본파일", sort=False).agg(
    source_rows=("원본파일", "size"),
    item_missing=("매핑상태", lambda s: int(s.eq("원문결측").sum())),
    match_eligible=("매핑상태", lambda s: int(s.ne("원문결측").sum())),
    matched=("매핑상태", lambda s: int(s.eq("일치").sum())),
    unmatched=("매핑상태", lambda s: int(s.eq("불일치").sum())),
).reset_index().rename(columns={"원본파일": "file"})
audit["match_pct_of_eligible"] = (audit["matched"] / audit["match_eligible"] * 100).round(4)
audit = audit.merge(pd.DataFrame(source_rows), on=["file", "source_rows"], validate="one_to_one")

unmatched = mapped.loc[mapped["매핑상태"].eq("불일치")]
unmatched_items = (unmatched.groupby(["품목매핑키", "물품소분류"], dropna=False)
                   .size().rename("건수").reset_index().sort_values(["건수", "품목매핑키"], ascending=[False, True]))
unmatched_by_file = (unmatched.groupby(["원본파일", "품목매핑키", "물품소분류"], dropna=False)
                     .size().rename("건수").reset_index().sort_values(["원본파일", "건수"], ascending=[True, False]))

raw_exact_keys = set(code["소분류품목"])
normalization_only_matches = int((mapped["매핑상태"].eq("일치") & ~mapped["물품소분류"].isin(raw_exact_keys)).sum())

assert len(mapped) == sum(x["source_rows"] for x in source_rows)
assert mapped["접수연도"].notna().all() and mapped["접수분기"].notna().all()
assert audit["source_rows"].sum() == len(mapped)
assert audit["matched"].sum() + audit["unmatched"].sum() + audit["item_missing"].sum() == len(mapped)
assert len(unmatched) == int(unmatched_items["건수"].sum())

save_csv("standardized_redress.csv", mapped)
save_csv("mapping_audit_by_file.csv", audit)
save_csv("unmatched_items.csv", unmatched_items)
save_csv("unmatched_items_by_file.csv", unmatched_by_file)

base_log = (ROOT / "outputs" / "step1_structure" / "preprocessing_log.md").read_text(encoding="utf-8")
new_log = f"""

## 승인 및 적용: STEP 1 표준화 (2026-09-24)

1. 사용자 승인에 따라 파일별 `물품명`→`물품소분류`, `연령`→`연령대`, `접수일(년월일)`→`접수일`로 열 이름만 통일. 원본 값은 그대로 보존.
2. CSV는 UTF-8-SIG 우선, 실패 시 CP949로 읽음. 이번 11개 원본은 CP949. 식별자 보존을 위해 이번 표준화 단계는 모든 원본 열을 문자열로 읽음. `접수연도`·`접수분기`만 nullable 정수로 생성.
3. `접수일`은 원문 문자열로 유지. YYYY-MM-DD 값은 날짜를 검증한 뒤 연도·분기를 추출. `2026년 2분기`는 정규식으로 연도 2026·분기 2를 추출. 후자의 일자는 임의 생성하거나 NaT로 변환하지 않음.
4. 품목 매핑 키는 원본 품목명과 코드표 `소분류품목` 양쪽에서 앞뒤 공백 제거 및 연속 공백을 단일 공백으로 치환한 값. 대소문자·구두점·철자·동의어는 변경하지 않음. 원본 `물품소분류`는 별도 유지.
5. 코드표 정규화 키 중복 0건을 확인한 뒤 다대일 완전일치 left join 수행. 매핑되지 않은 값은 임의 변환 없이 `unmatched_items.csv`, `unmatched_items_by_file.csv`에 원문·정규화 키·빈도 기록.
6. 원본 물품명이 빈칸인 행은 `원문결측`으로 별도 상태 기록. 결측값을 0으로 채우지 않고 행도 제외하지 않음.
7. 원본 추적을 위해 `원본파일`과 CSV 헤더 포함 1기준의 `원본행번호`를 추가. 파일 간 같은 사건번호 여부는 검사·제거하지 않음.
8. `판매유형`과 `판매방법`은 이번 승인 범위에 없으므로 별도 열로 유지. `사건번호`가 없는 2026년 2분기와 `처리결과`가 없는 이전 파일도 결측 상태로 유지.
9. 표준화된 피해구제 원본 전체 {len(mapped):,}행을 보존. 매핑 적격 {int(audit['match_eligible'].sum()):,}행 중 일치 {int(audit['matched'].sum()):,}행, 불일치 {int(audit['unmatched'].sum()):,}행. 원문 품목명 결측 {int(audit['item_missing'].sum()):,}행. 공백 정규화 후에만 일치한 행 {normalization_only_matches:,}행.
10. 가전 선별, 청구이유 재분류, Q1~Q5 산출은 아직 수행하지 않음.
"""
(OUT / "preprocessing_log.md").write_text(base_log + new_log, encoding="utf-8")

# Structural mapping-coverage chart; no hypothesis metrics are calculated.
w, h = 1120, 620
img = Image.new("RGB", (w, h), "white")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()
draw.text((40, 28), "Exact normalized item-name mapping leaves unmatched source labels", fill="#17344a", font=font)
draw.text((40, 50), "Blue = matched; orange = unmatched. Missing source names are excluded from each bar denominator.", fill="#4a6070", font=font)
for i, row in audit.iterrows():
    y = 90 + i * 48
    suffix = re.search(r"(\d{8})\.csv$", row["file"]).group(1)
    draw.text((42, y + 10), suffix, fill="#17344a", font=font)
    x0, bar_w = 165, 620
    frac = row["matched"] / row["match_eligible"]
    draw.rectangle((x0, y, x0 + bar_w, y + 27), fill="#e89154")
    draw.rectangle((x0, y, x0 + int(bar_w * frac), y + 27), fill="#277da8")
    draw.text((810, y + 9), f"{row['matched']:,}/{row['match_eligible']:,} ({row['match_pct_of_eligible']:.1f}%)", fill="#17344a", font=font)
draw.text((165, 588), "Exact source-name coverage by quarterly file", fill="#4a6070", font=font)
img.save(OUT / "mapping_coverage.png")

output = []
output.append("[INPUT AND OUTPUT]")
output.append(f"source_files={len(redress_paths)}, codebook_files={len(code_paths)}, standardized_rows={len(mapped)}")
output.append(f"codebook_rows={len(code)}, normalized_code_keys={code['품목매핑키'].nunique()}, code_key_duplicates=0")
output.append(f"dated_rows={sum(x['exact_date_rows'] for x in source_rows)}, quarter_label_rows={sum(x['quarter_label_rows'] for x in source_rows)}")
output.append("[MAPPING AUDIT BY FILE]")
output.append(audit.to_string(index=False))
output.append("[TOTALS]")
output.append(f"eligible={int(audit['match_eligible'].sum())}, matched={int(audit['matched'].sum())}, unmatched={int(audit['unmatched'].sum())}, missing_product={int(audit['item_missing'].sum())}")
output.append(f"normalization_only_matches={normalization_only_matches}")
output.append(f"unmatched_distinct_raw_values={len(unmatched_items)}")
output.append("[UNMATCHED ITEMS — FULL LIST]")
output.append(unmatched_items.to_string(index=False) if len(unmatched_items) else "None")
(OUT / "execution_output.txt").write_text("\n".join(output) + "\n", encoding="utf-8")

print("\n".join(output[:9]))
print("Saved:")
for path in sorted(OUT.iterdir()):
    print(path.name, path.stat().st_size, "bytes")
