"""Build the approved appliance cohort from the standardized redress records."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "outputs" / "step1_standardization" / "standardized_redress.csv"
REVIEW = ROOT / "outputs" / "step2_candidate"
OUT.mkdir(parents=True, exist_ok=True)

# Exact original labels implementing the user's final inclusion list.
SELECTED = {
    "냉장고": ["냉장고"],
    "김치냉장고": ["김치냉장고"],
    "냉동고": ["냉동고"],
    "세탁기": ["전기세탁기"],
    "워시타워": ["워시타워"],
    "의류건조기": ["전기의류건조기"],
    "의류관리기": ["의류관리기(스타일러 등)"],
    "에어컨": ["룸에어컨", "시스템에어컨", "이동식에어컨", "팬코일(이동식에어컨)"],
    "TV": ["TV"],
    "식기세척기": ["식기세척기"],
    "식기건조기": ["식기건조기"],
    "청소기": ["전기진공청소기", "로봇청소기"],
    "공기청정기": ["공기청정기"],
    "제습기": ["제습기"],
    "가습기": ["가습기"],
    "정수기": ["정수기"],
    "음식물처리기": ["음식물처리기"],
    "인덕션레인지": ["인덕션레인지"],
    "오븐·전자레인지": ["전기오븐", "전자레인지", "전기오븐레인지"],
}
name_to_group = {name: group for group, names in SELECTED.items() for name in names}
assert len(name_to_group) == sum(len(names) for names in SELECTED.values())

source = pd.read_csv(SOURCE, encoding="utf-8-sig", dtype=str, keep_default_na=False,
                     low_memory=False)
denominator = len(source)
selected = source[source["물품소분류"].isin(name_to_group)].copy()
selected.insert(selected.columns.get_loc("물품소분류") + 1, "가전품목군",
                selected["물품소분류"].map(name_to_group))
selected.insert(selected.columns.get_loc("가전품목군") + 1, "선별근거",
                selected["매핑상태"].map({"일치": "코드표 소분류 완전일치",
                                           "불일치": "코드표 불일치 후 이동식에어컨 키워드"}))

# Exact-name allowlist and the prior codebook match state prevent keyword false positives.
assert selected["선별근거"].notna().all()
assert set(selected.loc[selected["매핑상태"].eq("불일치"), "물품소분류"]) == {"팬코일(이동식에어컨)"}
assert not selected["물품소분류"].str.contains("대여|렌트|렌탈|서비스|부품|액세서리", regex=True).any()
explicit_exclusions = {"가스에어컨", "믹서기", "토스터기", "전기포트", "녹즙기",
                       "핫플레이트", "전기장판", "전기요", "전기온수장판", "전기담요",
                       "전기스토브", "스팀다리미", "전기다리미", "카페트청소기"}
assert not (explicit_exclusions & set(selected["물품소분류"]))
assert selected["원본파일"].nunique() == 10

raw_counts = (selected.groupby(["가전품목군", "물품소분류", "선별근거"], sort=False)
              .size().rename("건수").reset_index()
              .sort_values(["가전품목군", "건수", "물품소분류"], ascending=[True, False, True]))
summary = (selected.groupby("가전품목군", sort=False).size().rename("건수").reset_index()
           .sort_values(["건수", "가전품목군"], ascending=[False, True]))
summary["전체피해구제건수"] = denominator
summary["전체대비비중_pct"] = (summary["건수"] / denominator * 100).round(4)
total_selected = len(selected)
summary_with_total = pd.concat([
    summary,
    pd.DataFrame([{"가전품목군": "전체 가전", "건수": total_selected,
                   "전체피해구제건수": denominator,
                   "전체대비비중_pct": round(total_selected / denominator * 100, 4)}])
], ignore_index=True)

review_core = pd.read_csv(REVIEW / "candidate_appliance_names.csv", encoding="utf-8-sig",
                          dtype=str, keep_default_na=False)
review_core["건수"] = review_core["건수"].astype(int)
excluded_core = review_core[~review_core["물품소분류"].isin(name_to_group)].copy()

def exclusion_reason(name: str, candidate_group: str) -> str:
    if name == "가스에어컨":
        return "사용자 지정 제외: 상업용/설비 성격"
    if candidate_group in ("난방가전", "다리미·탈수기"):
        return "사용자 지정 제외: 단순 난방용품·소형 잡화"
    if candidate_group == "조리가전":
        return "사용자 지정 포함 목록 외 조리기기"
    return "사용자 지정 포함 목록 외"

excluded_core["제외사유"] = [exclusion_reason(n, g) for n, g in
                             zip(excluded_core["물품소분류"], excluded_core["제안품목군"])]
excluded_core = excluded_core.sort_values(["건수", "물품소분류"], ascending=[False, True])

boundary = pd.read_csv(REVIEW / "boundary_items.csv", encoding="utf-8-sig",
                       dtype=str, keep_default_na=False)
boundary["제외결정"] = "전량 제외 — 사용자 확정"
assert not (set(selected["물품소분류"]) & set(boundary["물품소분류"]))

selected.to_csv(OUT / "appliance_redress.csv", index=False, encoding="utf-8-sig")
summary_with_total.to_csv(OUT / "appliance_group_summary.csv", index=False, encoding="utf-8-sig")
raw_counts.to_csv(OUT / "included_original_names.csv", index=False, encoding="utf-8-sig")
excluded_core.to_csv(OUT / "excluded_candidate_names.csv", index=False, encoding="utf-8-sig")
boundary.to_csv(OUT / "excluded_boundary_items.csv", index=False, encoding="utf-8-sig")

assert int(summary["건수"].sum()) == total_selected
assert int(raw_counts["건수"].sum()) == total_selected
assert total_selected + int(excluded_core["건수"].sum()) == int(review_core["건수"].sum())
assert len(selected) == selected[["원본파일", "원본행번호"]].drop_duplicates().shape[0]

source_file_counts = source.groupby("원본파일", sort=False).size()
selected_file_counts = selected.groupby("원본파일", sort=False).size()
file_audit = pd.DataFrame({"원본파일": source_file_counts.index,
                           "전체피해구제건수": source_file_counts.values,
                           "선정가전건수": selected_file_counts.reindex(source_file_counts.index, fill_value=0).values})
file_audit["전체대비비중_pct"] = (file_audit["선정가전건수"] / file_audit["전체피해구제건수"] * 100).round(4)
file_audit.to_csv(OUT / "selection_audit_by_file.csv", index=False, encoding="utf-8-sig")
assert int(file_audit["선정가전건수"].sum()) == total_selected

# English labels keep the graph legible on systems without Korean fonts.
english = {"냉장고": "Refrigerator", "김치냉장고": "Kimchi refrigerator",
           "냉동고": "Freezer", "세탁기": "Washer", "워시타워": "WashTower",
           "의류건조기": "Clothes dryer", "의류관리기": "Clothing care",
           "에어컨": "Air conditioner", "TV": "TV", "식기세척기": "Dishwasher",
           "식기건조기": "Dish dryer", "청소기": "Vacuum cleaners",
           "공기청정기": "Air purifier", "제습기": "Dehumidifier",
           "가습기": "Humidifier", "정수기": "Water purifier",
           "음식물처리기": "Food waste processor", "인덕션레인지": "Induction range",
           "오븐·전자레인지": "Oven / microwave"}
assert set(english) == set(SELECTED)
top = summary.iloc[0]
width, height = 1050, 100 + len(summary) * 39 + 60
img = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()
draw.text((30, 24), f"{english[top['가전품목군']]} has the most cases among the selected appliance groups",
          fill="#17344a", font=font)
draw.text((30, 46), "Counts are source records. See appliance_group_summary.csv for the overall denominator.",
          fill="#516774", font=font)
for i, row in enumerate(summary.itertuples(index=False)):
    y = 82 + i * 39
    draw.text((30, y + 7), english[row.가전품목군], fill="#17344a", font=font)
    bar_width = int(570 * row.건수 / int(top["건수"]))
    draw.rectangle((260, y, 260 + bar_width, y + 24), fill="#2f7fa2")
    draw.text((275 + bar_width, y + 7), f"{row.건수:,} / {denominator:,} ({row.전체대비비중_pct:.2f}%)",
              fill="#17344a", font=font)
img.save(OUT / "appliance_group_counts.png")

prior_log = (REVIEW / "preprocessing_log.md").read_text(encoding="utf-8")
final_log = f"""

## STEP 2 가전 대상 최종 확정 및 추출 (2026-09-24)

1. 사용자 확정에 따라 렌탈, 서비스, 부품·액세서리·주변용품, 설비·비전기 기기, 기타·정체 불명, 생활·개인 전자기기 경계군 전량 제외. 원본 표준화 파일의 행을 지우지 않고 별도의 `appliance_redress.csv`만 추출.
2. 포함 품목은 `build_appliance_dataset.py`의 `SELECTED` 원문 품목명 허용 목록 {len(name_to_group)}개. 그 외 원문명은 본 가전 데이터셋에 포함하지 않음.
3. 에어컨은 룸·시스템·이동식과 `팬코일(이동식에어컨)`만 포함. 마지막 항목 {int((selected['물품소분류'] == '팬코일(이동식에어컨)').sum())}건은 코드표 불일치 후 이동식에어컨 키워드 보조 분류. 가스에어컨은 제외.
4. 청소기는 `전기진공청소기`, `로봇청소기`만 포함. `카페트청소기` 등은 사용자 지정 포함 목록 밖이므로 제외.
5. 조리가전은 `인덕션레인지`, `전기오븐`, `전자레인지`, `전기오븐레인지`만 포함. `전기오븐레인지`는 복합오븐으로 해석. 그 외 소형 조리기기는 제외.
6. 난방용품, 다리미·탈수기, 선풍기, 연수기 및 기타 확정 포함 목록 밖 품목은 제외. `excluded_candidate_names.csv`에 이전 후보 중 제외된 원문명·건수·이유를 기록.
7. 품목군별 건수는 추출 행의 개수. 전체 피해구제 대비 비중 분모는 표준화 원본 {denominator:,}행이며, 중복 사건 제거는 하지 않음. 결측을 0으로 대체하지 않음.
8. 최종 가전 {total_selected:,}행, 품목군 {len(SELECTED)}개, 원문 품목명 {len(name_to_group)}개. 이번 단계에서 Q1~Q5 분석은 수행하지 않음.
"""
(OUT / "preprocessing_log.md").write_text(prior_log + final_log, encoding="utf-8")

lines = ["[APPROVED APPLIANCE GROUPS: COUNT / ALL REDRESS ROWS]",
         summary_with_total.to_string(index=False),
         "[ALL INCLUDED ORIGINAL LABELS AND COUNTS]", raw_counts.to_string(index=False),
         "[SOURCE RECONCILIATION]", file_audit.to_string(index=False),
         "[EXCLUDED PREVIOUS CANDIDATES]", excluded_core.to_string(index=False),
         f"[CHECK] source_rows={denominator}, selected_rows={total_selected}, groups={len(SELECTED)}, selected_raw_names={len(name_to_group)}",
         f"[CHECK] selected_codebook_rows={int(selected['매핑상태'].eq('일치').sum())}, selected_keyword_rows={int(selected['매핑상태'].eq('불일치').sum())}"]
(OUT / "execution_output.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:2]))
print(lines[-2])
print(lines[-1])
print("[FILES]")
for path in sorted(OUT.iterdir()):
    print(path.name, path.stat().st_size, "bytes")
