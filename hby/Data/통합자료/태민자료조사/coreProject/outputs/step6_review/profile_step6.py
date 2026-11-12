"""STEP 6 review: profile standard-answer CSV and propose, but do not apply, Q4 rules."""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
PREV_LOG = ROOT / "outputs" / "step5_final" / "preprocessing_log.md"

files = [path for path in (ROOT / "data").rglob("*")
         if path.is_file() and path.suffix.lower() == ".csv"
         and "소비자상담 표준답변" in unicodedata.normalize("NFC", path.name)]
assert len(files) == 1, f"Expected one standard-answer file, found {len(files)}"
source_path = files[0]
source_name = unicodedata.normalize("NFC", source_path.name)

for encoding in ("utf-8-sig", "cp949"):
    try:
        data = pd.read_csv(source_path, encoding=encoding, dtype=str,
                           keep_default_na=False, low_memory=False)
        break
    except UnicodeDecodeError:
        continue
else:
    raise RuntimeError("Unable to read as utf-8-sig or cp949")

assert data.columns.tolist() == ["번호", "품목명", "구분", "질문", "답변"]
assert data["번호"].is_unique
assert data["번호"].str.fullmatch(r"\d+").all()
assert len(data) == 1332

profile = pd.DataFrame({
    "컬럼명": data.columns,
    "읽기자료형": [str(data[column].dtype) for column in data.columns],
    "빈칸_공백포함_건수": [int(data[column].str.strip().eq("").sum()) for column in data.columns],
    "고유값수": [int(data[column].nunique()) for column in data.columns],
})
profile.to_csv(OUT / "column_profile.csv", index=False, encoding="utf-8-sig")

# The trimmed value is for proposal display only. The original source column
# and the full source rows remain untouched; no cohort is extracted here.
item_counts = data.groupby("품목명", dropna=False).size().rename("행수").reset_index()
item_counts = item_counts.rename(columns={"품목명": "품목명_원문"})
item_counts["품목명_표시안"] = item_counts["품목명_원문"].str.strip()
item_counts = item_counts[["품목명_원문", "품목명_표시안", "행수"]]
item_counts = item_counts.sort_values("품목명_표시안").reset_index(drop=True)
assert item_counts["품목명_원문"].nunique() == 56
assert item_counts["품목명_표시안"].nunique() == 56
assert int(item_counts["행수"].sum()) == len(data)
item_counts.to_csv(OUT / "all_product_names.csv", index=False, encoding="utf-8-sig")

proposal = {
    "TV": ("가전 본체 포함 제안", "STEP 2 가전 본체와 동일 원문 표기"),
    "냉장고": ("가전 본체 포함 제안", "STEP 2 가전 본체와 동일 원문 표기"),
    "룸에어컨": ("가전 본체 포함 제안", "STEP 2 에어컨 직계 라인업"),
    "정수기대여": ("렌탈 제외 제안", "STEP 2 확정 렌탈 제외 기준"),
}
candidate = item_counts.loc[item_counts["품목명_표시안"].isin(proposal)].copy()
candidate["제안상태"] = candidate["품목명_표시안"].map(lambda value: proposal[value][0])
candidate["제안근거"] = candidate["품목명_표시안"].map(lambda value: proposal[value][1])
candidate.to_csv(OUT / "appliance_name_candidates.csv", index=False,
                 encoding="utf-8-sig")
candidate_preview = data.loc[data["품목명"].str.strip().isin(["TV", "냉장고", "룸에어컨"])]
candidate_duplicate_questions = int(candidate_preview["질문"].duplicated().sum())
candidate_same_product_duplicates = int(candidate_preview.duplicated(["품목명", "질문"]).sum())

# Read-only source examples used to design the lexicon. These are not labels.
example_ids = ["1", "2", "7", "12", "13", "17", "19", "22", "23", "25", "26",
               "321", "322", "329", "334", "387", "389", "391", "401", "405"]
examples = data.loc[data["번호"].isin(example_ids),
                    ["번호", "품목명", "구분", "질문"]].copy()
examples["품목명_표시안"] = examples["품목명"].str.strip()
examples.to_csv(OUT / "source_question_examples_for_dictionary.csv", index=False,
                encoding="utf-8-sig")

proposal_text = """# STEP 6 질문 유형 키워드 사전 제안 — 적용 전 승인 대기

## 분석 단위와 범위

- 분모 후보는 `품목명`의 앞뒤 공백만 제거한 뒤 `TV`, `냉장고`, `룸에어컨`과 정확히 일치하는 표준답변 행. `정수기대여`는 이전 렌탈 제외 결정에 따라 제외 제안. 질문 중복은 임의 제거하지 않음.
- 분류 입력은 **질문 원문만** 사용. `답변`을 사용하면 답변에만 있는 제도·구제 단어가 질문 유형을 오염시킬 수 있으므로 제외. `구분`은 검수용 참고열로만 보존.
- 원본 질문은 그대로 저장하고, 검색용 사본에서만 Unicode NFC 정규화, 연속 공백 단일화, 영문 대소문자 통일. 분류 기준은 표준답변 *항목 수*에 대한 비율이며 실제 소비자 상담 발생 빈도가 아님.

## 제안 사전 (질문에서 현재 묻는 쟁점 기준)

| 유형 | 검색어·표현 예시 | 포함 조건·주의 |
|---|---|---|
| 감가상각·보상액 | `감가상각`, `내용연수`, `잔존가치`, `환급금액`, `환급액`, `보상액`, `배상액`, `보상금`, `구입가`, `출고가`, `출고가격`, `50%`, `금액을 기준` | 고장·수리불가 등에 따른 금액 **산정 기준**을 묻는 경우. 단순 `보상`/`배상`이나 매장 가격 `차액 보상`은 제외. |
| 부품 | `부품`, `보유부품`, `부품 미보유`, `부품이 없어`, `단종` | 부품 부족·단종 때문에 수리 가능 여부나 구제 기준을 묻는 경우. `수리`와 함께 있어도 부품 우선. |
| 교환·환급 | `새 제품으로 교환`, `교환받을 수`, `교환을 요구`, `환급받을 수`, `환불받을 수`, `구입가 환급`, `교환이나 환불` | **현재 구제 수단으로** 교환·환급을 요구하고 고장·하자·결함·수리불가 등 제품 A/S 맥락이 있는 경우. 과거 이력 `교환받은 제품`만으로는 매칭하지 않음. |
| 보증기간·무상수리 | `품질보증기간`, `보증기간`, `무상수리`, `무상 수리`, `유상수리`, `유상 수리`, `보증하는`, `보증기간 경과` | 보증기간의 길이·적용 여부 또는 수리비 유·무상을 묻는 경우. 단순 배송·택배 비용 질문은 `설치·배송` 우선 예외. |
| 설치·배송 | `설치기사`, `설치 도중`, `설치비`, `배송 중`, `배송 지연`, `배송비`, `택배비`, `출장비`, `받침대 설치` | 설치/배송 과정·비용·파손·지연이 주된 쟁점인 경우. 단지 `설치 전`이라는 시간 표현만으로는 매칭하지 않음. |
| 수리·고장 일반 | `수리`, `고장`, `하자`, `불량`, `결함`, `작동하지`, `과도한 소음`, `냉방이 안`, `냉장이 안` | 위 세부 기준·구제 수단에 속하지 않는 제품 작동/품질 문의. |
| 기타 | 위 유형 미해당, 단순 청약철회·반품, 가격 차이, 사은품 분쟁 | 무관·애매한 질문을 억지로 A/S 기준 범주에 넣지 않음. |

## 중복 매칭 우선순위

1. 감가상각·보상액: 금액 **산정** 질문은 환급/수리 단어와 겹쳐도 우선.
2. 부품: 부품 미보유·단종은 수리/환급 단어와 겹쳐도 우선.
3. 교환·환급: 현재 요구하는 구제 수단이며 제품 A/S 맥락이 확인된 경우.
4. 보증기간·무상수리: 유·무상 수리 여부가 핵심인 경우.
5. 설치·배송: 설치·배송 쟁점. 단순 `택배비` 질문은 보증기간 문구가 함께 있어도 이 유형으로 보내는 예외.
6. 수리·고장 일반.
7. 기타.

## 명시적 예외·검수 필요 사례

- `청약철회`, 단순변심, 배송 지연에 따른 계약 철회/미환급은 제품 A/S 교환·환급과 구별하여 `기타` 또는 주 쟁점이 배송이면 `설치·배송`으로 제안. 이 결정은 `기준 판정 관련` 비중에 크게 영향을 주므로 승인 필요.
- `차액 보상`(매장별 판매가격 차이)은 감가상각·보상액에서 제외. `사은품` 자체의 하자·피해 질문도 가전 본체 A/S가 아니므로 `기타` 제안. 다만 해당 행을 분모에서 빼지는 않음.
- `교환받은 TV가 또 고장`은 과거 교환 이력이므로 현재의 교환 요구가 없으면 `수리·고장 일반` 후보. `보증기간 이내 무상수리인데 택배비 부담`은 비용 쟁점으로 `설치·배송` 후보.
- 위 기준으로 분류한 뒤 난수 시드 `20260924`로 **중복 없이 30행**을 표본 추출하고 질문 원문·분류 결과·매칭 근거를 검수표에 제시. 사용자 검수 전에는 일치율 계산 안 함.
"""
(OUT / "keyword_dictionary_proposal.md").write_text(proposal_text, encoding="utf-8")

# Structural plot only; it is not a Q4 type distribution chart.
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
title_font = ImageFont.truetype(font_path, 22)
label_font = ImageFont.truetype(font_path, 16)
figure = Image.new("RGB", (1050, 350), "white")
draw = ImageDraw.Draw(figure)
draw.text((24, 22), "Only three product labels are proposed for appliance standard answers.",
          fill="#17344a", font=title_font)
bar_specs = [("TV", 26), ("Refrigerator", 22), ("Room air conditioner", 23),
             ("Water purifier rental - exclude", 43)]
for index, (label, count) in enumerate(bar_specs):
    y = 83 + index*59
    draw.text((25, y+6), label, fill="#17344a", font=label_font)
    color = "#a6b4bf" if index == 3 else "#277da8"
    draw.rectangle((335, y, 335 + round(count/43*570), y+29), fill=color)
    draw.text((345 + round(count/43*570), y+4), str(count),
              fill="#17344a", font=label_font)
figure.save(OUT / "product_name_candidate_counts.png")

log = PREV_LOG.read_text(encoding="utf-8")
log += """\n\n## STEP 6 표준답변 구조·분류안 검토 (미확정)\n\n1. 파일명 NFC 정규화로 `소비자상담 표준답변` CSV 1개만 확인. UTF-8-SIG 읽기 실패 후 CP949로 읽음. 모든 원본 열을 문자열로 읽고 원본 행을 수정·제외하지 않음.\n2. 원본 `품목명`은 모든 행에 선행 공백이 있음. `품목명_표시안`은 후보 검토용 앞뒤 공백 제거값이며 최종 가전 매핑이나 분모에는 아직 적용하지 않음. 공백 제거 전후 고유값 수를 모두 기록.\n3. `TV`, `냉장고`, `룸에어컨`은 가전 본체 후보로 제안만 함. `정수기대여`는 앞서 확정한 렌탈 제외 기준에 따른 제외 후보로 표시. 아직 가전 질문 데이터셋, 유형 분류, Q4 비중, 무작위 검수 표본을 생성하지 않음.\n4. 키워드 사전과 다중 매칭 우선순위는 `keyword_dictionary_proposal.md`에 제안만 기록. 분류 입력은 질문 원문, `구분`은 참고, `답변`은 미사용을 제안. 사용자 승인 후 적용 예정.\n5. 표준답변은 사전 작성된 질문·답변 항목이므로 항목 비중을 실제 상담 발생 빈도·소비자 질문 빈도로 해석할 수 없음.\n6. `product_name_candidate_counts.png`는 원문 품목명 후보의 구조 그래프일 뿐 유형 비중 분석이 아님.\n"""
log += "7. 후보 3품목에는 서로 다른 품목의 동일 질문 문구가 있으나, 품목별 표준답변 행이라는 원본 단위를 존중하여 중복 제거하지 않는 안을 제안. 같은 품목 내 질문 중복도 별도 점검.\n"
(OUT / "preprocessing_log.md").write_text(log, encoding="utf-8")

print("SOURCE", source_name, "ENCODING", encoding)
print("SHAPE", data.shape, "COLUMNS", data.columns.tolist())
print("COLUMN PROFILE")
print(profile.to_string(index=False))
print("PRODUCT_UNIQUES_RAW", data["품목명"].nunique(),
      "PRODUCT_UNIQUES_TRIMMED_DISPLAY", data["품목명"].str.strip().nunique(),
      "PRODUCT_ROWS_WITH_EDGE_WHITESPACE", int(data["품목명"].ne(data["품목명"].str.strip()).sum()))
print("ALL PRODUCT NAMES")
print(item_counts[["품목명_표시안", "행수"]].to_string(index=False))
print("APPLIANCE NAME PROPOSAL")
print(candidate[["품목명_표시안", "행수", "제안상태", "제안근거"]].to_string(index=False))
print("QUESTION_DUPLICATES_ALL", int(data["질문"].duplicated().sum()))
print("CANDIDATE_PREVIEW_ROWS", len(candidate_preview),
      "DUPLICATE_QUESTIONS_ACROSS_PRODUCTS", candidate_duplicate_questions,
      "DUPLICATE_QUESTIONS_WITHIN_PRODUCT", candidate_same_product_duplicates)
