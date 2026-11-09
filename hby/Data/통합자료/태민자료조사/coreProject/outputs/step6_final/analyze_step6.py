"""STEP 6 final: approved Q4 standard-answer template classification."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REVIEW = ROOT / "outputs" / "step6_review"
OUT.mkdir(parents=True, exist_ok=True)

source_paths = [p for p in (ROOT / "data").rglob("*")
                if p.is_file() and p.suffix.lower() == ".csv"
                and "소비자상담 표준답변" in unicodedata.normalize("NFC", p.name)]
assert len(source_paths) == 1
source_path = source_paths[0]
for encoding in ("utf-8-sig", "cp949"):
    try:
        raw = pd.read_csv(source_path, encoding=encoding, dtype=str,
                          keep_default_na=False, low_memory=False)
        break
    except UnicodeDecodeError:
        continue
else:
    raise RuntimeError("Neither UTF-8-SIG nor CP949 can decode the source")
assert raw.columns.tolist() == ["번호", "품목명", "구분", "질문", "답변"]
assert len(raw) == 1332 and raw["번호"].is_unique

ALLOWED_PRODUCTS = {"TV": "TV", "냉장고": "냉장고", "룸에어컨": "에어컨"}
raw["품목명_표준"] = raw["품목명"].str.strip()
selected = raw.loc[raw["품목명_표준"].isin(ALLOWED_PRODUCTS)].copy()
selected["가전품목군"] = selected["품목명_표준"].map(ALLOWED_PRODUCTS)
assert len(selected) == 71
assert selected.groupby("품목명_표준").size().to_dict() == {
    "TV": 26, "냉장고": 22, "룸에어컨": 23}
assert selected["번호"].is_unique
assert selected.duplicated(["품목명_표준", "질문"]).sum() == 0
assert selected["질문"].duplicated().sum() == 2  # Different product templates retained.
assert not selected["품목명_표준"].eq("정수기대여").any()

TYPE_ORDER = ["감가상각·보상액", "부품", "교환·환급", "보증기간·무상수리",
              "설치·배송", "수리·고장 일반", "기타"]
CRITERIA_TYPES = TYPE_ORDER[:4]


def normalized_question(value: str) -> str:
    """Normalize only a search copy; keep original question in every output."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def first_match(pattern: str, value: str) -> str | None:
    match = re.search(pattern, value, flags=re.IGNORECASE)
    return match.group(0) if match else None


# Ordered exception rules use the same approved content criteria for every row.
GIFT = r"사은품"
PRICE_GAP = r"차액\s*(?:만큼\s*)?보상|판매가격이\s*다른|더\s*싸게\s*파는"
FEE_DISPUTE = r"왕복\s*택배비|택배비|배송비|반품비|출장비|설치비|추가\s*요금.*설치|추가\s*대금.*설치"
CONTRACT_WITHDRAWAL = r"청약철회|단순\s*변심|반품|적립금으로만|카드\s*취소|배송\s*지연.*취소"
PAST_EXCHANGE = r"교환받은\s*[^.?!]{0,30}(?:고장|하자|작동하지)"
CURRENT_EXCHANGE = r"교환(?:을|을\s*요구|해|받을|하고|이나|이\s*가능|이\s*어렵)"
AMOUNT = r"감가상각|내용연수|잔존가치|환급\s*금액|환급액|보상액|배상액|보상금|출고\s*가격|출고가|50\s*%|금액을\s*기준"
PARTS = r"부품|단종"
EXCHANGE_REFUND = r"환급받|환불받|교환받을|교환을\s*요구|새\s*제품으로\s*교환|교환이나\s*환불|교환하고\s*싶|교환이\s*가능|교환이\s*어렵"
AS_CONTEXT = r"고장|하자|불량|결함|수리|작동하지|소음|파손"
WARRANTY = r"품질\s*보증\s*기간|보증\s*기간|무상\s*수리|무상수리|유상\s*수리|유상수리|무상으로|유상으로"
INSTALL_DELIVERY = r"설치\s*기사|설치\s*도중|설치하던\s*중|설치\s*과정|배송\s*중|배송\s*지연|설치비|배송비|택배비|출장비|받침대\s*설치|파손"
REPAIR_FAULT = r"수리|고장|하자|불량|결함|작동하지|소음|냉방이\s*잘\s*안|냉장이\s*잘\s*안"


def classify(question: str) -> tuple[str, str, str]:
    text = normalized_question(question)
    # Explicit user-approved exclusions before the general priority ladder.
    for pattern, rule in ((GIFT, "사은품 자체 분쟁 예외"),
                          (PRICE_GAP, "매장별 가격 차액 예외")):
        hit = first_match(pattern, text)
        if hit:
            return "기타", rule, hit
    hit = first_match(FEE_DISPUTE, text)
    if hit:
        return "설치·배송", "배송비·택배비·출장비·설치비 쟁점 예외", hit
    hit = first_match(CONTRACT_WITHDRAWAL, text)
    if hit:
        return "기타", "청약철회·계약 미환급 예외", hit
    historical = first_match(PAST_EXCHANGE, text)
    if historical and not first_match(CURRENT_EXCHANGE, text.replace(historical, "")):
        return "수리·고장 일반", "과거 교환 이력만 언급한 경우", historical

    amount_hit = first_match(AMOUNT, text)
    if amount_hit and first_match(AS_CONTEXT, text):
        return "감가상각·보상액", "금액 산정 표현 + 제품 A/S 맥락", amount_hit
    parts_hit = first_match(PARTS, text)
    if parts_hit:
        return "부품", "부품·단종 우선", parts_hit
    remedy_hit = first_match(EXCHANGE_REFUND, text)
    if remedy_hit and first_match(AS_CONTEXT, text):
        return "교환·환급", "현재 A/S 구제 수단 요구", remedy_hit
    warranty_hit = first_match(WARRANTY, text)
    if warranty_hit:
        return "보증기간·무상수리", "보증 또는 수리비 유·무상", warranty_hit
    delivery_hit = first_match(INSTALL_DELIVERY, text)
    if delivery_hit:
        return "설치·배송", "설치·배송 과정", delivery_hit
    repair_hit = first_match(REPAIR_FAULT, text)
    if repair_hit:
        return "수리·고장 일반", "제품 고장·하자 일반", repair_hit
    return "기타", "키워드 미해당", ""


classified = selected[["번호", "품목명", "품목명_표준", "가전품목군", "구분", "질문"]].copy()
classified[["질문유형", "판정규칙", "매칭표현"]] = pd.DataFrame(
    [classify(question) for question in classified["질문"]],
    index=classified.index,
)
classified["기준판정관련"] = classified["질문유형"].isin(CRITERIA_TYPES)
assert classified["질문유형"].isin(TYPE_ORDER).all()
assert len(classified) == 71 and classified["번호"].is_unique
classified["번호_정렬"] = classified["번호"].astype(int)
classified = classified.sort_values("번호_정렬").drop(columns="번호_정렬")
classified.to_csv(OUT / "classified_appliance_questions.csv", index=False,
                  encoding="utf-8-sig")

counts = classified["질문유형"].value_counts().reindex(TYPE_ORDER, fill_value=0)
summary = pd.DataFrame({"질문유형": TYPE_ORDER, "건수_분자": counts.values,
                        "전체가전표준답변_분모": len(classified)})
summary["비중_pct"] = (summary["건수_분자"] /
                       summary["전체가전표준답변_분모"] * 100).round(2)
summary["기준판정관련포함"] = summary["질문유형"].isin(CRITERIA_TYPES)
assert int(summary["건수_분자"].sum()) == len(classified)
summary.to_csv(OUT / "question_type_summary.csv", index=False,
               encoding="utf-8-sig")

criteria_n = int(classified["기준판정관련"].sum())
criteria = pd.DataFrame([{
    "지표": "기준 판정 관련 표준답변 항목 비중",
    "포함유형": "교환·환급 + 보증기간·무상수리 + 부품 + 감가상각·보상액",
    "건수_분자": criteria_n,
    "전체가전표준답변_분모": len(classified),
    "비중_pct": round(criteria_n / len(classified) * 100, 2),
    "해석범위": "표준답변 항목 구성; 실제 소비자 문의 발생 빈도 아님",
}])
criteria.to_csv(OUT / "criteria_related_share.csv", index=False,
                encoding="utf-8-sig")

by_product = (classified.groupby(["품목명_표준", "질문유형"], observed=True)
              .size().rename("건수").reset_index())
by_product.to_csv(OUT / "question_type_by_product.csv", index=False,
                  encoding="utf-8-sig")

SAMPLE_SEED = 20260924
sample = classified.sample(n=30, replace=False, random_state=SAMPLE_SEED).copy()
sample["번호_정렬"] = sample["번호"].astype(int)
sample = sample.sort_values("번호_정렬").drop(columns="번호_정렬")
sample = sample.drop(columns="품목명").rename(
    columns={"품목명_표준": "품목명", "질문유형": "분류결과"})
sample = sample[["번호", "품목명", "구분", "질문", "분류결과", "판정규칙", "매칭표현"]]
sample["검수자_정답유형"] = ""
sample["일치여부_검수후입력"] = ""
assert len(sample) == 30 and sample["번호"].is_unique
sample.to_csv(OUT / "random_30_review_sample.csv", index=False,
              encoding="utf-8-sig")
markdown_rows = ["| 번호 | 품목명 | 질문 원문 | 분류 결과 |",
                 "|---:|---|---|---|"]
for row in sample.itertuples(index=False):
    question = row.질문.replace("|", "\\|").replace("\n", "<br>")
    markdown_rows.append(f"| {row.번호} | {row.품목명} | {question} | {row.분류결과} |")
(OUT / "random_30_review_sample.md").write_text(
    "# STEP 6 무작위 30건 검수표\n\n난수 시드 `20260924`, 비복원 추출. 검수자 정답과 일치율은 아직 미기입.\n\n"
    + "\n".join(markdown_rows) + "\n", encoding="utf-8")

# Render seven type bars with exact numerator/denominator labels.
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
title_font = ImageFont.truetype(font_path, 24)
label_font = ImageFont.truetype(font_path, 17)
small_font = ImageFont.truetype(font_path, 14)
english = {"감가상각·보상액": "Depreciation / amount",
           "부품": "Parts availability", "교환·환급": "Exchange / refund",
           "보증기간·무상수리": "Warranty / free repair",
           "설치·배송": "Installation / delivery",
           "수리·고장 일반": "General repair / failure", "기타": "Other"}
figure = Image.new("RGB", (1260, 650), "white")
draw = ImageDraw.Draw(figure)
draw.text((28, 20),
          f"Criteria-related topics account for {criteria_n} of {len(classified)} appliance FAQ entries.",
          fill="#17344a", font=title_font)
draw.text((29, 57), "These are standard-answer templates, not observed consultation volumes.",
          fill="#526674", font=small_font)
bar_left, max_width = 310, 680
max_count = max(int(counts.max()), 1)
for index, row in enumerate(summary.itertuples(index=False)):
    y = 105 + index * 67
    draw.text((28, y+7), english[row.질문유형], fill="#17344a", font=label_font)
    width = round(row.건수_분자 / max_count * max_width)
    color = "#287da0" if row.기준판정관련포함 else "#9daeb9"
    draw.rectangle((bar_left, y, bar_left + width, y + 35), fill=color)
    draw.text((bar_left + width + 12, y+6),
              f"{row.건수_분자}/{row.전체가전표준답변_분모} ({row.비중_pct:.2f}%)",
              fill="#17344a", font=label_font)
draw.rectangle((29, 590, 46, 607), fill="#287da0")
draw.text((55, 588), f"Criteria-related: {criteria_n}/{len(classified)} "
                     f"({float(criteria.iloc[0]['비중_pct']):.2f}%)",
          fill="#17344a", font=small_font)
figure.save(OUT / "question_type_bar_chart.png")

log = (REVIEW / "preprocessing_log.md").read_text(encoding="utf-8")
log += """\n\n## STEP 6 가전 표준답변 질문 유형 최종 분류 (사용자 확정)\n\n1. 원본 CSV를 UTF-8-SIG 우선, 실패 시 CP949로 읽고 모든 열을 문자열로 보존. `품목명` 양끝 공백만 제거한 별도 `품목명_표준` 열로 TV·냉장고·룸에어컨과 정확히 일치하는 행을 추출. 정수기대여 등 나머지 품목명 제외.\n2. 품목별 표준답변 행을 분석 단위로 삼아 품목 간 동일 질문 문구를 중복 제거하지 않음. 최종 71행, TV 26·냉장고 22·룸에어컨 23.\n3. `질문` 원문만 유형 분류에 사용. 원문은 보존하고 검색 사본에서만 Unicode NFC 정규화·연속 공백 단일화·영문 대소문자 무시. `구분`은 검수 참고열로 유지, `답변`은 분류에 사용하지 않음.\n4. 사전 우선순위는 감가상각·보상액→부품→교환·환급→보증기간·무상수리→설치·배송→수리·고장 일반→기타. 각 행의 적용 규칙과 매칭 표현을 `classified_appliance_questions.csv`에 기록.\n5. 사용자 확정 예외를 일반 우선순위보다 먼저 적용: 사은품 자체 분쟁, 매장 가격 차액은 기타; 핵심 쟁점이 택배비·배송비·출장비·설치비이면 설치·배송; 단순 청약철회·계약 미환급은 기타; 과거 교환 이력만 있으면 수리·고장 일반. 배송 지연에 따른 계약 취소는 기타.\n6. 교환·환급은 현재 구제 요구와 제품 고장·하자·수리 맥락이 함께 있을 때만 부여. 감가상각·보상액은 금액 산정 표현과 A/S 맥락이 함께 있을 때만 부여. 단순 `보상`·`배상` 단어만으로 금액 산정으로 분류하지 않음.\n7. 유형 비중은 각 유형 항목 수 / 가전 표준답변 71행. `기준 판정 관련`은 교환·환급, 보증기간·무상수리, 부품, 감가상각·보상액의 합집합 항목 수 / 71행. 실제 소비자 상담 발생 빈도로 해석하지 않음.\n8. 검수표는 pandas `sample(n=30, replace=False, random_state=20260924)`로 추출 후 번호 순서로 정렬. 검수자 정답·일치여부 열은 비워 두며 사용자 검수 전 일치율은 계산하지 않음.\n"""
log += "9. 전수 대조 중 `구입가 환급받을 수 있나요`는 금액 산정이 아니라 환급 가능 여부임을 확인해 `구입가` 단독을 금액 사전에서 제외. 출고가격·50% 등 산정 표현은 유지. `소음이 과도하게` 같은 어순을 놓치지 않도록 일반 고장 사전에 `소음`을 포함.\n"
log += "10. 교환·환급의 매칭 근거는 `환급받`, `교환을 요구`, `새 제품으로 교환` 같은 현재 구제 요구 표현을 우선 기록. 검수 편의를 위해 동일한 무작위 30행을 CSV와 Markdown 표로 저장.\n"
(OUT / "preprocessing_log.md").write_text(log, encoding="utf-8")

print(f"SOURCE_ROWS={len(raw)} ENCODING={encoding} APPLIANCE_ROWS={len(classified)} "
      f"UNIQUE_PRODUCTS={classified['품목명_표준'].nunique()} SAMPLE_SEED={SAMPLE_SEED} "
      f"SAMPLE_ROWS={len(sample)}")
print("TYPE COUNTS AND DENOMINATORS")
print(summary.to_string(index=False))
print("CRITERIA RELATED")
print(criteria.to_string(index=False))
print("CLASSIFICATION AUDIT")
for row in classified.itertuples(index=False):
    question_excerpt = re.sub(r"\s+", " ", row.질문).strip()[:105]
    print(f"{row.번호:>4} | {row.품목명_표준:<5} | {row.질문유형:<12} | "
          f"{row.판정규칙:<24} | {row.매칭표현:<10} | {question_excerpt}")
print("REVIEW SAMPLE IDS", ",".join(sample["번호"].tolist()))
