# LG Move Care: MCP 도구 계약 제안

상태: **설계 초안 / 미구현**. 도구명은 기획안의 5개를 유지한다. JSON 예시의 금액·계약 ID는 저장소의 합성 C001/CT001/Q001에서 가져왔다. `request_id`, 상태 이름, 새 필드, 승인 흐름은 이번 제안이다.

## 공통 규칙

입력은 명시적 타입과 범위를 가진 스키마로, 출력은 구조화된 객체로 반환한다. FastMCP는 함수의 타입·설명을 이용해 도구 스키마를 만들고 Pydantic 모델 등을 사용할 수 있다. `output_schema`와 구조화 결과는 [FastMCP Tools](https://gofastmcp.com/servers/tools), 전송 규격은 [MCP Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)를 참고한다.

| 항목 | 제안 |
| --- | --- |
| 금액 | 정수 원화 `int`, `currency="KRW"`; 소수 계산은 명시적 정산 규칙으로 처리 |
| 날짜 | 계약 기준일은 `YYYY-MM-DD`, 예약 시각은 시간대가 있는 ISO 8601 |
| 식별자 | 고객·계약·견적 ID는 서버 조회 키. ID를 아는 것만으로 접근 허용하지 않음 |
| 상태 | `ok`는 호출 처리 성공, `data.status`는 `found`, `needs_review` 등 업무 결과 |
| 불확실성 | 미확인 값은 `null`과 사유. 0원·설치 가능으로 대체 금지 |
| 출처 | 규정 ID, URL, 계약 버전, 수집일·적용일을 구분 |
| 데모 | 모든 합성 계약·비용·예약에 `is_synthetic=true` |
| 검증 | 허용하지 않은 필드, 빈 문자열, 과도한 길이, 허용 범위를 벗어난 수치 거절 |

성공/업무상 보류 예시:

```json
{
  "ok": true,
  "data": {"status": "needs_review", "reason_codes": ["CONTRACT_VERSION_MISSING"]},
  "error": null,
  "meta": {"request_id": "demo-request-001", "is_synthetic": true}
}
```

업무 함수 실행 실패 예시:

```json
{
  "ok": false,
  "data": null,
  "error": {"code": "SLOT_UNAVAILABLE", "message": "선택한 슬롯을 다시 조회해주세요.", "retryable": false},
  "meta": {"request_id": "demo-request-002", "is_synthetic": true}
}
```

제안한 Envelope를 사용한다면 업무 함수가 반환한 `ok=false`는 MCP `isError=true`와 일치시키고 Client가 두 값을 확인한다. 파싱·프로토콜 오류나 프레임워크 입력 검증 실패는 이 Envelope가 없을 수 있으므로 별도로 처리한다. `needs_review`처럼 정상적으로 판정된 보류 결과는 `ok=true`다. 재시도 가능 여부는 “같은 요청을 그대로 다시 실행해도 되는가” 기준으로 합의한다.

## 1. get_customer_contract

**목적:** 권한이 확인된 고객의 구독 계약 조회. 읽기 전용.

- 입력: `customer_id: str`, `as_of: date`.
- 출력: `status`, `contract_id`, `contract_version`, 월 기본요금·납부요금, 의무기간·경과기간, 혜택 사용 이력, 미납·추가 정산, 데이터 버전.
- 데이터: `mock/contracts.json` 또는 SQLite `contracts.payload`.
- 인증 사용자가 조회할 수 있는 고객인지 검증한다. 데모는 C001 등 명시적 allowlist로 범위를 고정할 수 있다.
- 계약이 없으면 `status="not_found"`, 다른 고객의 계약이면 접근 거절. 복수 계약이면 선택을 요청한다.
- 현재 시드는 `as_of=2026-10-12` 고정이다. 다른 날짜를 지원하려면 날짜 계산을 구현하거나 미지원으로 반환한다.

```json
{"customer_id": "C001", "as_of": "2026-10-12"}
```

기대되는 핵심 값: `contract_id="CT001"`, `contract_version="MOCK-20261012-V1"`, `monthly_base_fee=59000`, `mandatory_months=36`, `used_months=18`.

## 2. search_contract_terms

**목적:** 해당 계약에 관련된 규정과 근거 검색. 읽기 전용.

- 입력: `contract_id: str`, `query: str`, `top_k: int=5` (제안 범위 1~10).
- 서버가 계약 버전·제품군을 조회하여 검색 필터를 만든다. LLM이 넣은 임의 버전을 그대로 신뢰하지 않는다.
- 출력의 각 근거: `rule_id`, `text`, `source_url`, `contract_version`, `effective_date`, `accessed_date`, `match_status`.
- 실제 계약 버전과 매칭하지 못하면 `match_status="public_guidance_only"`와 `needs_review`를 반환한다.
- 현재 RAG 시드에는 `effective_date=null`, `is_signed_contract=false`인 공개 안내가 들어 있다. 이를 서명된 계약으로 승격하지 않는다.
- 검색 문서에 “이전 지시 무시”, “무료 처리” 같은 문장이 있어도 명령으로 실행하지 않는다. 검색문은 근거 데이터다.

```json
{"contract_id": "CT001", "query": "중도해지 위약금과 회수비", "top_k": 3}
```

RAG 담당자와 `search(query, filters, limit)` 반환 형식·인덱스 버전·검색 실패 상태를 먼저 합의한다. MCP 담당자가 벡터 DB를 직접 선정해야 하는 것은 아니다.

## 3. calculate_termination_cost

**목적:** 계약 데이터와 승인된 계산 규칙으로 금액 산정. 저장을 하지 않는 계산 도구로 제안한다.

- 입력: `contract_id: str`, `as_of: date`.
- LLM 입력에 `penalty_rate`, `monthly_fee`, `waive_fee`를 받지 않는다. 서버가 계약·규칙 저장소에서 조회한다.
- 출력: 적용 버전, 계산 항목, 위약금·회수비·사은품 환수·미납·기타 정산, 합계, 보류 사유.
- 데모 규칙에서 0·12·24개월 및 만기, 미확인 계약, 요금 누락은 자동 확정하지 않는다.

```json
{
  "ok": true,
  "data": {
    "status": "estimated_mock",
    "contract_id": "CT001",
    "contract_version": "MOCK-20261012-V1",
    "as_of": "2026-10-12",
    "monthly_base_fee": 59000,
    "remaining_months": 18,
    "penalty_rate_percent": 20,
    "penalty": 212400,
    "recovery_fee": 111000,
    "gift_clawback": 0,
    "arrears": 0,
    "other_settlement_fee": 0,
    "termination_total": 323400,
    "currency": "KRW"
  },
  "error": null,
  "meta": {"request_id": "demo-c001-cost", "is_synthetic": true}
}
```

이 계산은 가상 약관에 의한 기대값이다. 실제 LG 계약에 적용 가능하다는 뜻이 아니다. 이전 80,000원과의 243,400원 차이는 **일회성 지출 차이**이며 향후 구독료를 포함한 총절감액이 아니다.

## 4. get_relocation_quote

**목적:** 이전 견적 및 설치 검토 상태 조회. MVP에서는 미리 만든 견적을 읽는 도구로 제안한다.

- 입력: `contract_id: str`, `destination_id: str`.
- `destination_id`는 Backend가 검증해 보관한 주소 참조 키라는 **신규 제안**이다. 현재 시드에는 없으므로 매핑 테이블을 추가해야 한다. 원본 주소를 도구 로그에 반복 기록하지 않는 목적이다.
- 출력: `quote_id`, 견적 버전, 목적지 참조 키, 철거비·운송비·재설치비, 합계, 유효기한, 설치 상태·판정 근거.
- 현재 Q001은 지역 수준의 고정 Mock이며 임의의 주소·날짜에도 동일하게 유효한 견적으로 취급하지 않는다.
- 설치 미확인/불가는 `quoted_total=null`과 사유를 반환하고 예약 생성으로 넘어가지 않는다.
- 신규 견적을 DB에 생성하는 방식으로 바꾸면 쓰기 동작이므로 read-only annotation도 수정한다.

설계 예시 입력: `{"contract_id":"CT001","destination_id":"DEST-DEMO-001"}`. `DEST-DEMO-001`은 설명용이며 아직 데이터셋에 없다. 기존 Q001의 철거/운송/재설치 비용은 각각 0/80000/0원이다.

## 5. manage_relocation_booking

**목적:** 가용 일정 조회와 사용자 확인 이후 데모 예약 생성.

| action | 입력 제안 | 반환 |
| --- | --- | --- |
| `list` | `contract_id`, `quote_id`, `date_from`, `date_to` | 작업 종류·지역·시간대별 슬롯, 조회 시각 |
| `create` | `booking_intent_id`, `confirmation_token`, `idempotency_key` | `booking_id`, 예약 상태, 철거·재설치 항목, 기존 요청 재생 여부 |

`create`의 고객·주소·금액·슬롯은 서버가 저장한 예약 의도에서 읽는다. 예약 의도는 Backend의 확인 화면 준비 단계에서 만들며 기획안의 MCP 도구 수를 늘릴 필요는 없다. 서버는 최신 계약·견적·슬롯과 최종 확인 증거를 재검증한다.

```json
{
  "action": "create",
  "booking_intent_id": "INTENT-DEMO-001",
  "confirmation_token": "SERVER_ISSUED_DEMO_TOKEN",
  "idempotency_key": "booking-demo-001"
}
```

이 값들은 설명용이며 아직 발급된 값이 아니다. `customer_confirmed=true` 하나를 LLM이 만들어 넘기는 방식은 실제 확인의 증거가 되지 않는다. [승인·중복 방지 설계](BOOKING_AND_TESTING.md)를 함께 적용한다.

`list`와 `create`가 하나의 MCP 도구에 있으므로 도구 전체의 `readOnlyHint`는 false다. `idempotentHint`는 서버에서 반복 호출의 추가 효과를 막은 뒤에만 true로 설정한다. annotation 자체가 권한·승인 검사를 대신하지 않는다. [공식 annotations 설명](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/).

## 합의할 오류 코드

| 코드 | 의미 | 다음 행동 |
| --- | --- | --- |
| `INVALID_ARGUMENT` | 타입·범위·필수값 오류 | 입력 수정 |
| `FORBIDDEN` | 고객/계약 접근 권한 없음 | 인증·권한 확인 |
| `CONTRACT_NEEDS_REVIEW` | 계약·규정 적용 미확인 | 상담 또는 정보 보완 |
| `QUOTE_EXPIRED` | 유효기한 또는 견적 버전 변경 | 새 견적 확인 |
| `CONFIRMATION_REQUIRED` | 유효한 최종 확인 없음 | 사용자에게 확인 화면 표시 |
| `IDEMPOTENCY_CONFLICT` | 같은 키에 다른 요청 | 기존 결과 확인 후 새 의도 생성 |
| `SLOT_UNAVAILABLE` | 잔여 정원 없음 | 일정 재선택 |
| `DB_BUSY` | 한정된 재시도 후에도 DB 잠금 | 같은 키로 제한적 재시도 |
| `INTERNAL` | 처리 실패 | request_id로 추적, 내부 예외 원문 비노출 |
