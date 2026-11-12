"""STEP 1: read-only structural profile of consumer redress CSVs and item codebook."""

from __future__ import annotations

import csv
import io
import re
from contextlib import redirect_stdout
from pathlib import Path
from unicodedata import normalize

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> tuple[pd.DataFrame, str]:
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False,
                               keep_default_na=False), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Could not decode {path}")


def missing_mask(series: pd.Series) -> pd.Series:
    # Inspect blanks without altering the loaded table.
    return series.isna() | series.astype(str).str.strip().eq("")


def save_csv(name: str, rows: list[dict], columns: list[str]) -> None:
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


names = sorted(
    (p for p in DATA.rglob("*") if p.is_file() and p.suffix.lower() == ".csv"),
    key=lambda p: normalize("NFC", p.name),
)
redress_paths = [p for p in names if "소비자 피해구제 정보_" in normalize("NFC", p.name)]
code_paths = [p for p in names if "소비자 피해구제 품목 정보_" in normalize("NFC", p.name)]
assert len(redress_paths) == 10 and len(code_paths) == 1, (redress_paths, code_paths)
paths = redress_paths + code_paths

file_rows: list[dict] = []
column_rows: list[dict] = []
category_rows: list[dict] = []
product_rows: list[dict] = []
tables: dict[str, pd.DataFrame] = {}

for path in paths:
    df, encoding = read_csv(path)
    name = normalize("NFC", path.name)
    tables[name] = df
    period_col = next((x for x in ("접수일(년월일)", "접수일") if x in df.columns), None)
    period_min = period_max = period_kind = "해당 없음"
    if period_col:
        values = df.loc[~missing_mask(df[period_col]), period_col].astype(str)
        exact_dates = pd.to_datetime(values, format="%Y-%m-%d", errors="coerce")
        if len(values) and exact_dates.notna().all():
            period_min, period_max = exact_dates.min().strftime("%Y-%m-%d"), exact_dates.max().strftime("%Y-%m-%d")
            period_kind = "일자"
        else:
            period_min = values.min() if len(values) else "알 수 없음"
            period_max = values.max() if len(values) else "알 수 없음"
            period_kind = "원문 기간 표기(일자 변환 불가)"
    file_rows.append(dict(file=name, encoding=encoding, rows=len(df), columns=len(df.columns),
                          column_names=" | ".join(df.columns), period_column=period_col or "없음",
                          period_min=period_min, period_max=period_max, period_kind=period_kind))

    for col in df.columns:
        count = int(missing_mask(df[col]).sum())
        column_rows.append(dict(file=name, column=col, dtype=str(df[col].dtype),
                                missing_count=count, row_count=len(df),
                                missing_pct=round(count / len(df) * 100, 4)))

    for col in ("청구이유", "처리결과", "연령대", "연령"):
        if col not in df.columns:
            continue
        mask = missing_mask(df[col])
        counts = df.loc[~mask, col].value_counts(dropna=False, sort=False)
        for value, count in sorted(counts.items(), key=lambda pair: str(pair[0])):
            category_rows.append(dict(file=name, column=col, value=str(value), count=int(count)))
        if mask.any():
            category_rows.append(dict(file=name, column=col, value="<빈칸/결측>", count=int(mask.sum())))

    product_col = next((x for x in ("물품소분류", "물품명") if x in df.columns), None)
    if product_col:
        counts = df.loc[~missing_mask(df[product_col]), product_col].value_counts(dropna=False)
        for rank, (value, count) in enumerate(counts.head(50).items(), start=1):
            product_rows.append(dict(file=name, column=product_col, rank=rank,
                                     value=str(value), count=int(count)))

save_csv("file_summary.csv", file_rows,
         ["file", "encoding", "rows", "columns", "column_names", "period_column", "period_min", "period_max", "period_kind"])
save_csv("column_profile.csv", column_rows,
         ["file", "column", "dtype", "missing_count", "row_count", "missing_pct"])
save_csv("category_values.csv", category_rows, ["file", "column", "value", "count"])
save_csv("product_top50_by_file.csv", product_rows, ["file", "column", "rank", "value", "count"])

code_name = normalize("NFC", code_paths[0].name)
code = tables[code_name]
code_key = "소분류품목"
code_nonblank = code.loc[~missing_mask(code[code_key]), code_key]
code_duplicate_values = code_nonblank.value_counts().loc[lambda s: s > 1]

# The reporting table describes the source files; no product mapping or cross-file union is performed.
redress_dates = [r for r in file_rows if r["file"] != code_name]
earliest = min(r["period_min"] for r in redress_dates if r["period_kind"] == "일자")
latest = redress_dates[-1]["period_max"]
description = [
    {"데이터명": "소비자 피해구제 정보 (분기별 원본 10개)", "제공기관": "한국소비자원",
     "수집 기간": f"{earliest} ~ {latest}", "행 수": sum(r["rows"] for r in redress_dates),
     "주요 컬럼": "접수일/접수일(년월일), 연령/연령대, 물품명/물품소분류, 청구이유, 처리결과(일부 파일)",
     "비고": "분기별 원본 행 수 단순합계; 2026년 2분기는 분기 단위 표기. 파일 간 열 이름이 다르며 미통합."},
    {"데이터명": "소비자 피해구제 품목 정보", "제공기관": "한국소비자원",
     "수집 기간": "해당 없음 (파일명 기준 2025-08-08)", "행 수": len(code),
     "주요 컬럼": "번호, 대분류품목, 중분류품목, 소분류품목",
     "비고": "품목 코드표. 피해구제 원본과 공통 코드 열 없음; 소분류 명칭 연결 가능성은 승인 후 확인."},
]
save_csv("data_description.csv", description,
         ["데이터명", "제공기관", "수집 기간", "행 수", "주요 컬럼", "비고"])

log = f"""# 전처리 로그 — STEP 1 구조 점검

1. 범위: 파일명에 `소비자 피해구제 정보_`가 포함된 CSV {len(redress_paths)}개와 `소비자 피해구제 품목 정보_` 코드표 {len(code_paths)}개만 열람. 월별 상담/표준답변 파일은 미열람.
2. 파일명 검색: macOS에서 분해형 한글 파일명을 찾기 위해 파일명 비교에 NFC 정규화를 사용. 원본 파일명이나 데이터 값은 변경하지 않음.
3. 인코딩: UTF-8-SIG 읽기를 먼저 시도하고 UnicodeDecodeError 시 CP949로 읽음. 이번 {len(paths)}개 파일은 모두 CP949로 읽힘.
4. CSV 파싱: pandas `read_csv(low_memory=False, keep_default_na=False)` 사용. 자료형은 pandas 추론값을 그대로 기록. 원본 파일을 수정하지 않음.
5. 결측 점검: 실제 null 또는 공백/빈 문자열을 결측으로 셈. `불명` 등 텍스트 값은 결측으로 재분류하지 않음. 결측 대체·제거 없음.
6. 기간: `접수일(년월일)` 또는 `접수일` 원본 열을 조회. YYYY-MM-DD 형식은 날짜로 파싱해 최솟값·최댓값 산출. 변환 불가 기간 표기는 원문 최솟값·최댓값을 기록. 코드표는 내부 기간 열 없음.
7. 범주/상위 50개: 각 파일의 원본 열에서 값별 빈도를 따로 계산. 파일 간 결합·열 이름 통일·품목 매핑·가전 선별 없음. 빈칸/결측은 범주 빈도표에 별도 표기.
8. 연결 키: 코드표 `소분류품목`의 중복 여부와 열 이름만 점검. 원본과 실제 병합하지 않음.
9. 시각화: 파일별·열별 결측 비율을 보여주는 구조 점검 그래프만 생성. 분석 질문 Q1~Q5는 아직 계산하지 않음.

## 승인 대기

- 피해구제 파일의 `물품소분류`와 `물품명`을 동일한 품목명으로 취급할지.
- 코드표 `소분류품목`을 원본 품목명과 어떤 규칙(원문 완전일치, 공백 정리, 별칭 등)으로 연결할지.
- `연령대`와 `연령`, `접수일(년월일)`과 `접수일`을 파일 간 통합할지.
"""
(OUT / "preprocessing_log.md").write_text(log, encoding="utf-8")

# Structural figure only; English labels avoid font issues in the local runtime.
redress_files = [r["file"] for r in redress_dates]
all_cols = sorted({c for r in column_rows if r["file"] in redress_files for c in [r["column"]]})
matrix = pd.DataFrame(float("nan"), index=[re.search(r"(\d{8})\.csv$", n).group(1) for n in redress_files], columns=all_cols)
for r in column_rows:
    if r["file"] in redress_files:
        matrix.loc[re.search(r"(\d{8})\.csv$", r["file"]).group(1), r["column"]] = r["missing_pct"]
save_csv("chart_column_key.csv", [{"chart_id": f"C{i+1}", "source_column": c}
                                  for i, c in enumerate(all_cols)], ["chart_id", "source_column"])
cell_w, cell_h = 82, 41
left, top = 180, 110
width = left + len(all_cols) * cell_w + 45
height = top + len(matrix.index) * cell_h + 100
img = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()
draw.text((30, 27), "Quarterly files differ in column availability and missingness", fill="#18354a", font=font)
draw.text((30, 52), "Gray = absent column; blue = missing data; pale = 0% missing", fill="#526674", font=font)
for j, col in enumerate(all_cols):
    draw.text((left + j * cell_w + 26, top - 25), f"C{j+1}", fill="#18354a", font=font)
for i, suffix in enumerate(matrix.index):
    y = top + i * cell_h
    draw.text((45, y + 12), suffix, fill="#18354a", font=font)
    for j, col in enumerate(all_cols):
        x = left + j * cell_w
        v = matrix.loc[suffix, col]
        color = "#d9dde3" if pd.isna(v) else ("#eaf4fa" if v == 0 else ("#4b90b5" if v < 20 else "#0b5f83"))
        draw.rectangle((x, y, x + cell_w - 3, y + cell_h - 3), fill=color)
        if not pd.isna(v) and v > 0:
            label = "<0.1%" if v < 0.05 else f"{v:.1f}%"
            draw.text((x + 10, y + 12), label, fill="white" if v >= 20 else "#18354a", font=font)
draw.text((left, height - 55), "Column IDs are listed in chart_column_key.csv", fill="#526674", font=font)
img.save(OUT / "structure_missingness.png")

buf = io.StringIO()
with redirect_stdout(buf):
    print("[1] FILE SUMMARY")
    print(pd.DataFrame(file_rows).to_string(index=False))
    print("\n[2] COLUMN TYPES & MISSINGNESS")
    print(pd.DataFrame(column_rows).to_string(index=False))
    print("\n[3] ALL CATEGORY VALUES & COUNTS")
    print(pd.DataFrame(category_rows).to_string(index=False))
    print("\n[4] PRODUCT TOP 50 BY FILE")
    print(pd.DataFrame(product_rows).to_string(index=False))
    print("\n[5] CODEBOOK CANDIDATE KEY")
    print(f"Codebook 소분류품목 nonblank={len(code_nonblank)}, unique={code_nonblank.nunique()}, duplicated labels={len(code_duplicate_values)}")
    print(code_duplicate_values.to_string() if len(code_duplicate_values) else "No duplicate labels")
    print("\n[6] DATA DESCRIPTION")
    print(pd.DataFrame(description).to_string(index=False))
(OUT / "execution_output.txt").write_text(buf.getvalue(), encoding="utf-8")
print("Saved:")
for p in sorted(OUT.iterdir()):
    print(p.name, p.stat().st_size, "bytes")
print("\nFILE SUMMARY")
print(pd.DataFrame(file_rows)[["file", "rows", "columns", "period_min", "period_max", "period_kind"]].to_string(index=False))
print("\nKEY CHECK")
print(f"Codebook 소분류품목 nonblank={len(code_nonblank)}, unique={code_nonblank.nunique()}, duplicated labels={len(code_duplicate_values)}")
