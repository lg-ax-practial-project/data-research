# 데이터 설명서

MCP의 고객 계약·이전 견적·기사 일정·예약 정보별 상세 예시와 도구 연결은 [업무 데이터 설명서](mcp/BUSINESS_DATA_GUIDE.md)를 참고한다.

## 공통 원칙

원본은 `raw/`, 공개 자료의 전사·집계·요약은 `processed/`, 합성 업무 데이터는 `mock/`에 있다. 금액은 원(KRW) 정수, 비율은 `reported_percent`에서 55.1처럼 백분율 수치로 저장한다. 날짜는 ISO 문자열이며 예약 시각은 `+09:00`을 포함한다. `null`은 미확인 또는 산정 불가이며 0원과 다르다.

## 출처 목록 sources.json

`source_id`는 각 가공 레코드의 출처 연결 키다. `url`은 공식 설명 페이지, `download_url`은 확보 당시 다운로드 주소, `accessed_date`는 수집 기준일이다. `publication_date`, `source_updated_date`, `recovery_fee_reference_date`는 서로 다른 의미다. `effective_date=null`은 계약상 시행일을 확인하지 못했다는 뜻이다. `files`는 경로·크기·SHA-256을 기록한다. `status=catalog_only_not_downloaded`인 자료는 원본 미확보다.

## 공개 CSV

| 컬럼 | 의미 / 해석 |
| --- | --- |
| 접수일 | 실제 값은 `2026년 2분기`. 일별 날짜가 아님 |
| 성별 | 원본 분류 보존 |
| 연령 | `30 - 39세` 등의 구간. 정확한 개인 나이 아님 |
| 지역 | 원본 행정구역 표기. 공란 가능 |
| 판매유형 | 일반판매·통신판매 등의 분류. 구독 여부와 같지 않음 |
| 물품명 | 세탁기, 세탁서비스, 세제 등이 섞여 있어 정확한 품목 필터 필요 |
| 청구이유 | 계약해제·해지/위약금, 품질 등 원본 분류 |
| 처리결과 | 환급, 조정신청, 취하·중지 등. 피해의 법적 인정 여부와 동일시하지 않음 |

선정 JSONL에는 `source_row`(헤더 포함 원본 행 번호, 첫 데이터=2), `source_id`, `data_kind`, `project_product_group`을 추가했다. 개인 식별자를 새로 추론하지 않았다. 교차집계는 선택된 행을 품목·이유·연령으로 단순 계수한다. 공란 행도 유지한다.

## 보고서 통계

`group`이 통계 모집단과 표 구분이다. `annual_total`은 전체 접수, `annual_large_appliance`는 그중 대형가전, `annual_contract_breakdown`은 계약관련 세부표다. 전체와 하위항목을 합산하면 중복된다. `selected_products_not_exhaustive`는 원문에 나온 일부 품목만 기록해 합계가 2,624가 되지 않는다.

`count`는 건수 또는 설문 인원, `denominator`는 해당 비율의 분모다. 연도별 건수처럼 분모가 필요 없는 행은 null이다. `reported_percent`는 원문 비율이고 재계산한 수치가 아니다. `pdf_page`는 파일의 1부터 시작하는 페이지, `printed_page`는 본문 인쇄 페이지다. `survey`의 분모는 500명이며 피해구제 2,624건과 섞지 않는다.

## RAG 및 설치 참고

`rag_rules.jsonl`: `rule_id`, `title`, `text`, `source_id`, `source_url`, `accessed_date`, `effective_date`, `product_family`, `data_kind`, `is_signed_contract`, `contract_match_required`.

요약 텍스트는 검색용으로 작성한 문장이다. 원문 조항 인용문처럼 따옴표로 표시하지 않는다. `is_signed_contract=false`이므로 실제 계약서와 일치 검증 없이 정산 확정에 사용하면 안 된다. 설치 참고의 치수는 **제품 크기가 아닌 필요 공간 예시**다. 공용 안내이므로 `universal_rule=false`이며 모델별 설명서와 현장 확인이 필요하다.

## 가상 고객·제품·계약

| 파일 / 주요 필드 | 설명 |
| --- | --- |
| customers.customer_id | C001~C100, 합성 고객 키 |
| display_name, origin_region, destination_region, destination_address, move_date | 데모 이름·지역·가상주소·희망 이사일. 실제 배송·예약에 사용 불가 |
| products.product_id, product_family, model_code | 데모 제품군 키, 워시타워, 실판매 모델 미지정(null) |
| contracts.contract_id, customer_id, product_id | 계약 키 및 고객·제품 연결 |
| contract_version | `MOCK-20261012-V1`. terms와 연결되는 가상 버전 |
| start_date, end_date, as_of | 매월 12일 기준으로 생성한 계약 시작·종료·관측일 |
| total_months, mandatory_months, used_months | 총 계약·의무 사용·사용 경과 개월. 이번 Mock에서는 총기간=의무기간 |
| monthly_base_fee, monthly_payable_fee | 할인 전 기본요금과 현재 납부요금. 위약금 예시에 기본요금 사용 |
| recovery_fee | 공개 FAQ 수치를 가정 적용한 111000원 |
| gift_clawback, arrears, other_settlement_fee | 사은품 정산·미납·기타 비용. 모두 합성값 |
| free_reinstallation_entitled, free_reinstallation_used | 가상 계약의 혜택 대상 여부 및 사용 여부 |
| contract_verified | 데모상 계약 확인 상태. 실제 LG 검증 여부가 아님 |
| review_required | 정보 미확인·경계시점·만기로 자동 계산을 보류하는 데모 플래그 |
| contract_status | active 또는 review_at_maturity |
| is_synthetic | true. 모든 Mock 업무 레코드에 포함 |

`terms`는 계산 단위, 반올림 방식, 경계 정책, 참고 규칙 ID를 가진다. 정확히 0·12·24개월 및 만기는 자동 산정하지 않고 확인 필요로 둔다. 이는 프로젝트 설계 선택이며 공식 LG 규칙이 아니다.

## 가상 견적·일정·예약

`quotes`는 `quote_id`와 `contract_id`로 연결된다. `removal_fee`, `transport_fee`, `reinstallation_fee`는 각각 철거·운송·재설치 금액이다. `quoted_total`은 설치 가능한 가상 사례에서만 숫자이고 `needs_site_check` 또는 `ineligible_mock`이면 null이다. 제시된 구성금액만 더해 확정 견적이라고 오인하지 않는다. `valid_until`은 가상 견적 유효일이다.

`slots`는 `slot_id`, `region`, `service`(removal/reinstallation), `starts_at`, `capacity`, `remaining_capacity`, `engineer_id`, `is_synthetic`으로 구성한다. 슬롯은 2026-10-22~11-04에 있다. 운송 일정은 포함하지 않는다. 고객 희망일과 별도로 철거일·운송일·재설치일의 순서가 맞는지 확인해야 한다.

현재 동일 기사·동일 시각에 철거와 재설치 후보가 함께 있는 조합이 42쌍이다. 84개 슬롯을 서로 독립적인 실제 예약 가능 정원으로 해석하면 안 된다. 작업 종료 시각·이동시간·근무표도 없어, 예약 구현 시 기사별 시간 충돌 검증과 일정 모델 보완이 필요하다.

초기 `bookings.json`은 빈 배열이다. SQLite bookings는 `booking_id`, `contract_id`, `slot_id`, `idempotency_key`, `payload` 컬럼이다. 실제 구현 시 계약·슬롯 FK 및 멱등성 키 외에 사용자 최종동의, 잔여 정원 차감, 중복 활성예약 방지를 같은 트랜잭션에서 처리해야 한다. 현재 DB는 데이터 시드이며 예약 서비스 구현물이 아니다.

SQLite에서 고객·제품·약관·슬롯 테이블은 식별자와 JSON `payload`, 계약·견적·예약 테이블은 관계 키와 JSON `payload`를 가진다. 금액은 `json_extract(payload, '$.monthly_base_fee')` 등으로 조회할 수 있다. 생성기는 외래 키 검사와 무결성 검사를 수행한다.

JSON과 SQLite는 같은 초기 데이터를 담지만 실시간 동기화 기능은 없다. DB에 예약을 생성해도 `bookings.json`과 `slots.json`이 자동 변경되지 않는다.

## 평가 데이터

`case_id`, `category`, `customer_id`, `prompt`, `expected` 또는 `expected_behavior`, `fixture_overrides`, `execution_status`가 핵심이다. `fixture_overrides`는 해당 케이스 실행 전에 테스트 복사본에 적용할 값으로, 원본 Mock에는 반영하지 않는다. 정상 15개는 비용 계산 기대값 비교용이며 전체 예약 E2E 15개가 아니다. 예약 예외·위험은 별도 사례에 포함했다. `execution_status=not_run`은 아직 Agent를 실행하지 않았다는 뜻이다.

실제 기획 평가에서는 정상 예약 성공, 철거/재설치 날짜 조합, 운송 일정 확인, 예약 취소·변경 시나리오를 추가로 구체화해야 한다. 이 데이터만으로 Tool 정확도나 정상 완료율을 달성했다고 주장할 수 없다.
