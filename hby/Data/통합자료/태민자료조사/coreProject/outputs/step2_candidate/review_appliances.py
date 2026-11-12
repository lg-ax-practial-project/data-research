"""STEP 2 review-only appliance candidate inventory; no filtered dataset is written."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SRC = ROOT / "outputs" / "step1_standardization" / "standardized_redress.csv"

# Proposed codebook leaf-name allowlist. Labels are grouped for review only.
CORE = {
    "김치냉장고": ["김치냉장고"],
    "냉장고": ["냉장고"],
    "냉동고": ["냉동고"],
    "세탁기": ["전기세탁기"],
    "세탁·건조 복합": ["워시타워"],
    "의류건조기": ["전기의류건조기"],
    "의류관리기": ["의류관리기(스타일러 등)"],
    "에어컨": ["룸에어컨", "시스템에어컨", "가스에어컨", "이동식에어컨"],
    "TV": ["TV"],
    "식기세척기": ["식기세척기"],
    "식기건조기": ["식기건조기"],
    "정수기": ["정수기"],
    "연수기": ["연수기"],
    "음식물처리기": ["음식물처리기"],
    "청소기": ["전기진공청소기", "로봇청소기", "카페트청소기"],
    "공기청정기": ["공기청정기"],
    "제습기": ["제습기"],
    "가습기": ["가습기"],
    "선풍기": ["선풍기"],
    "난방가전": ["전기장판", "전기요", "전기온수장판", "온풍기", "전기팬히터",
              "전기스토브", "전기담요", "전기카페트"],
    "조리가전": ["인덕션레인지", "전기압력밥솥", "믹서기", "커피메이커", "전기밥솥",
              "전기포트", "에어프라이어", "전자레인지", "전기오븐", "전기오븐레인지",
              "전기프라이팬", "전기보온밥솥", "토스터기", "전기냄비", "전기곤로",
              "녹즙기", "핫플레이트"],
    "다리미·탈수기": ["스팀다리미", "전기다리미", "탈수기"],
}

# Separate decision queue: these are not automatically included in CORE.
BOUNDARY = {
    "렌탈": ["정수기대여(렌트)", "음식물처리기대여(렌트)", "공기청정기대여(렌트)",
             "연수기대여(렌트)", "비데대여(렌트)", "안마의자대여(렌트)"],
    "서비스": ["건물청소서비스", "미분류수리가공"],
    "부품·액세서리·주변용품": ["TV대", "전기충전기", "전기어댑터", "전원코드", "세탁물건조용품"],
    "설비·비전기 기기": ["가스레인지", "가스오븐", "휴대용가스레인지", "가스보일러",
                    "기름보일러", "전기보일러", "화목보일러", "전기온수기", "가스온수기",
                    "태양열온수기", "냉난방시스템", "공조시스템", "기타공조·냉난방설비",
                    "레인지후드", "환풍기", "가스팬히터", "가스스토브", "석유스토브",
                    "석유팬히터", "라디에이터"],
    "기타·정체 불명": ["기타냉장·냉동기기", "기타조리기기·기구", "기타식생활기기",
                 "기타공조·냉난방기기", "기타재봉·세탁·청소용품", "기타주방설비",
                 "기타영상기기", "오븐류", "그라인더", "튀김기", "훈제기", "기름제조기",
                 "온장고", "오존살균기", "쓰레기압축기", "재봉틀"],
    "생활·개인 전자기기": ["비데", "안마의자", "헤어드라이어", "전기고데기", "전기면도기",
                    "전기구강세정기", "전동칫솔", "LED마스크", "모니터", "CCTV",
                    "DVD플레이어", "홈씨어터시스템", "오디오세트"],
}

flat_core = {name: group for group, names in CORE.items() for name in names}
flat_boundary = {name: group for group, names in BOUNDARY.items() for name in names}
assert len(flat_core) == sum(map(len, CORE.values()))
assert len(flat_boundary) == sum(map(len, BOUNDARY.values()))
assert not (set(flat_core) & set(flat_boundary))

s = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False,
                usecols=["물품소분류", "품목매핑키", "매핑상태", "대분류품목", "중분류품목"])
names = (s.groupby(["물품소분류", "매핑상태", "대분류품목", "중분류품목"], dropna=False)
         .size().rename("건수").reset_index())
matched_names = set(names.loc[names["매핑상태"].eq("일치"), "물품소분류"])
assert set(flat_core).issubset(matched_names), sorted(set(flat_core) - matched_names)
assert set(flat_boundary).issubset(matched_names), sorted(set(flat_boundary) - matched_names)

core = names[names["물품소분류"].isin(flat_core)].copy()
core.insert(0, "제안품목군", core["물품소분류"].map(flat_core))
core.insert(1, "분류근거", "코드표 소분류품목 완전일치")

# Fallback is considered only for the names still unmatched to the codebook.
# Specific names precede generic names (e.g., kimchi refrigerator before refrigerator).
FALLBACK = [
    ("김치냉장고", r"김치냉장고"),
    ("냉장고", r"냉장고"),
    ("냉동고", r"냉동고"),
    ("의류건조기", r"의류건조기"),
    ("세탁기", r"세탁기"),
    ("에어컨", r"에어컨"),
    ("식기세척기", r"식기세척기"),
    ("TV", r"(?<![A-Za-z])TV(?![A-Za-z])"),
]
unmatched = names[names["매핑상태"].eq("불일치")].copy()
fallback_rows = []
for row in unmatched.itertuples(index=False):
    for group, pattern in FALLBACK:
        if re.search(pattern, row.물품소분류, flags=re.IGNORECASE):
            fallback_rows.append({"제안품목군": group, "분류근거": "코드표 불일치 후 우선순위 키워드",
                                  "물품소분류": row.물품소분류, "매핑상태": row.매핑상태,
                                  "대분류품목": row.대분류품목, "중분류품목": row.중분류품목,
                                  "건수": row.건수})
            break
fallback = pd.DataFrame(fallback_rows, columns=core.columns)
core = pd.concat([core, fallback], ignore_index=True)
core = core.sort_values(["제안품목군", "건수", "물품소분류"], ascending=[True, False, True])

boundary = names[names["물품소분류"].isin(flat_boundary)].copy()
boundary.insert(0, "검토구분", boundary["물품소분류"].map(flat_boundary))
boundary = boundary.sort_values(["검토구분", "건수", "물품소분류"], ascending=[True, False, True])

core.to_csv(OUT / "candidate_appliance_names.csv", index=False, encoding="utf-8-sig")
boundary.to_csv(OUT / "boundary_items.csv", index=False, encoding="utf-8-sig")
boundary_summary = boundary.groupby("검토구분", sort=False)["건수"].sum().reset_index()
boundary_summary.to_csv(OUT / "boundary_group_summary.csv", index=False, encoding="utf-8-sig")

english_groups = {"렌탈": "Rental", "서비스": "Service", "부품·액세서리·주변용품": "Parts / accessories",
                  "설비·비전기 기기": "Fixtures / non-electric", "기타·정체 불명": "Ambiguous labels",
                  "생활·개인 전자기기": "Personal electronics"}
bars = boundary_summary.sort_values("건수", ascending=False)
img = Image.new("RGB", (960, 455), "white")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()
draw.text((34, 26), "Rental labels have the largest count in the boundary review queue", fill="#18354a", font=font)
max_count = int(bars["건수"].max())
for i, row in enumerate(bars.itertuples(index=False)):
    y = 82 + i * 55
    draw.text((35, y + 9), english_groups[row.검토구분], fill="#18354a", font=font)
    width = int(535 * row.건수 / max_count)
    draw.rectangle((235, y, 235 + width, y + 28), fill="#3c83a6")
    draw.text((245 + width, y + 9), f"{row.건수:,}", fill="#18354a", font=font)
draw.text((35, 420), "Review only: counts are source rows, not a final appliance cohort.", fill="#526674", font=font)
img.save(OUT / "boundary_review_counts.png")

def listing(df: pd.DataFrame, group_col: str) -> str:
    return "\n".join(
        f"{g}: " + ", ".join(f"{r.물품소분류} {r.건수:,}" for r in rows.itertuples())
        for g, rows in df.groupby(group_col, sort=False)
    )

output = [
    "[REVIEW ONLY — NO FILTERED DATASET]",
    f"candidate_groups={core['제안품목군'].nunique()}, candidate_raw_names={len(core)}, candidate_rows={int(core['건수'].sum())}",
    f"codebook_candidate_rows={int(core.loc[core['분류근거'].eq('코드표 소분류품목 완전일치'), '건수'].sum())}, keyword_fallback_rows={int(fallback['건수'].sum())}",
    f"boundary_groups={boundary['검토구분'].nunique()}, boundary_raw_names={len(boundary)}",
    "[BOUNDARY GROUP COUNTS]",
    boundary_summary.to_string(index=False),
    "[CANDIDATE ORIGINAL NAMES AND COUNTS]",
    listing(core, "제안품목군"),
    "[BOUNDARY ORIGINAL NAMES AND COUNTS]",
    listing(boundary, "검토구분"),
]
(OUT / "execution_output.txt").write_text("\n".join(output) + "\n", encoding="utf-8")

proposal = """# STEP 2 가전 선별안 — 승인 전 검토용

1. 코드표 `소분류품목`과 표준화된 `물품소분류`의 정규화 완전일치 결과를 우선 사용한다. 대·중분류 전체를 통째로 포함하지 않고, 실제 가전 본체에 해당하는 코드표 소분류값을 명시적 허용 목록으로 제안한다. 같은 중분류에 냄비·수동청소기·서비스 등이 섞이기 때문이다.
2. 코드표 불일치 13개 원문 품목명에만 키워드 보조 분류를 검토한다. 우선순위는 `김치냉장고`→`냉장고`, `의류건조기`→`세탁기`, 구체 에어컨명→`에어컨` 순이며 첫 일치만 채택한다. `TV`는 영문자 경계를 확인한다. 코드표에 이미 매핑된 `카에어컨`·`CCTV`·`TV대`·`IPTV`에는 키워드를 적용하지 않는다.
3. 이번 파일의 명칭·건수는 임시 후보 검토표일 뿐이다. 최종 포함·제외를 나타내는 가전 데이터셋이나 전체 피해구제 대비 비중은 아직 만들지 않는다.
4. `렌탈`, `서비스`, `부품·액세서리·주변용품`, `설비·비전기 기기`, `기타·정체 불명`, `생활·개인 전자기기`는 경계군으로 분리하여 사용자 결정을 기다린다.
5. 사용자 승인 후 검토표의 허용 목록을 확정하고, 각 원본 행에 가전 여부·품목군·근거를 부여한 뒤 전체 피해구제 대비 비중을 계산한다. 그때도 원본 행은 제거하지 않고 별도 가전 데이터셋만 추출한다.
"""
(OUT / "classification_rules_proposal.md").write_text(proposal, encoding="utf-8")

prior_log = (ROOT / "outputs" / "step1_standardization" / "preprocessing_log.md").read_text(encoding="utf-8")
log_add = """

## STEP 2 후보 검토 (미확정)

1. 표준화 파일에서 원문 `물품소분류`별 건수와 이미 연결된 코드표 대·중분류를 읽기 전용으로 집계.
2. `candidate_appliance_names.csv`는 명시적 코드표 소분류 허용 목록 및 코드표 불일치 항목의 우선순위 키워드 검토 결과. 최종 포함 여부는 미확정.
3. `boundary_items.csv`는 서비스·렌탈·주변용품·설비 등 결정을 기다리는 경계군. 제외를 적용하지 않음.
4. 가전 데이터셋, 품목별 최종 건수·비중, Q1~Q5 분석은 아직 생성하지 않음.
"""
(OUT / "preprocessing_log.md").write_text(prior_log + log_add, encoding="utf-8")

print("\n".join(output))
print("[FILES]")
for p in sorted(OUT.iterdir()):
    print(p.name, p.stat().st_size, "bytes")
