# LG Move Care 데이터 리서치

이사를 앞둔 LG 워시타워 구독 고객에게 **계약 확인 → 규정 검색 → 해지·이전 비용 비교 → 데모 이전설치 예약**을 제공하는 프로젝트의 데이터 모음입니다.

수집·가상 데이터 기준일: **2026-10-12, 한국 시간**. 작업 브랜치: `khh`.

## 먼저 읽기

- **[고객 계약·이전 견적·기사 일정·예약 정보 설명](docs/mcp/BUSINESS_DATA_GUIDE.md)** — 파일별 필드·실제 예시·MCP 연결·현재 데이터의 한계
- **[MCP 담당자 구현 참고자료](docs/mcp/README.md)** — 공식 자료 14개, 도구별 입출력, 연동 예시, 예약·테스트 설계
- [기획 요약 및 정정 사항](docs/PROJECT_SUMMARY.md)
- [데이터 설명서](docs/DATA_DICTIONARY.md)
- [분석 방법과 활용 한계](docs/ANALYSIS_NOTES.md)
- [출처·다운로드 URL·해시 목록](sources.json)
- [파일 및 데이터 검증 결과](docs/validation.json)

## MCP 구현을 위한 추가 자료

MCP 서버·도구 구현 담당자가 사용할 자료를 `docs/mcp/`에 정리했습니다. 공식 원문 링크, 한국어 요약, 기존 Mock 데이터에 연결하는 방법을 제공합니다.

| 파일 | 내용 |
| --- | --- |
| [읽는 순서와 공식 자료](docs/mcp/README.md) | 담당 범위, 우선순위, 버전 주의점, 데이터 연결표 |
| [도구 계약 제안](docs/mcp/TOOL_CONTRACTS.md) | 기획안 5개 도구의 입력·응답·오류·근거 설계 |
| [연동 참고](docs/mcp/INTEGRATION.md) | FastMCP 서버·Client 예시, stdio/HTTP, Inspector, 선택적 LangChain 연동 |
| [예약과 검증](docs/mcp/BOOKING_AND_TESTING.md) | 최종 확인, idempotency, SQLite 동시 예약, 테스트 18개 |
| [기술 출처 목록](docs/mcp/sources.json) | 공식 출처 14개의 URL·확인일·적용 이유 |

설계·코드 예시는 참고자료이며 MCP 서버 구현이나 실행 테스트 완료를 의미하지 않습니다. 소비자 통계와 LG 공개 안내의 출처는 기존 루트 `sources.json`에 따로 있습니다.

## 확보한 데이터

| 자료 | 파일 | 용도와 범위 |
| --- | --- | --- |
| 한국소비자원 실태조사 원문, 36쪽 | `raw/kca_subscription_report_202604.pdf` | 계약 문제의 근거. 피해구제 2022.1~2025.6, 별도 설문 500명 |
| PDF 추출 텍스트 | `raw/kca_subscription_report_202604.txt` | 검색 보조. 표 수치는 원문 페이지와 대조 |
| 공공데이터포털 피해구제 원본 CSV | `raw/kca_relief_20260630.csv` | **2026년 2분기 12,834건**, CP949 인코딩, 8개 컬럼 |
| LG 구독 FAQ 원문 HTML | `raw/lg_subscription_faq.html` | 위약금·회수비·추가 정산 기준 |
| LG 재설치 혜택 원문 HTML | `raw/lg_reinstallation_benefit.html` | 1회 무상 철거·재설치와 운송 제외 조건 |
| LG 설치 체크리스트 원문 HTML | `raw/lg_installation_checklist.html` | 설치 환경 사전 확인 |
| 보고서 및 CSV 출처 페이지 HTML | `raw/kca_report_landing.html`, `raw/kca_relief_portal.html` | 발간일·컬럼·이용조건 확인 |

`raw/`에는 실제 다운로드한 파일을 로컬 보관했습니다. **LG 원문 HTML은 Git 추적에서 제외되어 새로 clone한 저장소에는 없습니다.** 공개 저장소에는 출처와 요약을 제공합니다. HTML은 정적 응답 스냅샷이며 완전한 오프라인 복제본은 아닙니다. 다운로드 당시 FAQ의 111,000원, 재설치 조건, 설치 안내를 확인했습니다.

## 바로 사용할 가공 데이터

| 파일 | 내용 |
| --- | --- |
| `processed/kca_report_statistics.json` | 보고서의 연도별·유형별·계약유형별·일부 품목별 집계 및 설문 통계. 분모·기간·PDF 쪽수 포함 |
| `processed/kca_selected_appliances.jsonl` | 공개 CSV에서 세탁기·건조기·냉장고·에어컨·정수기 관련 **10개 품목명을 정확히 일치**시켜 291건 추출. 원본 행 번호 포함 |
| `processed/kca_public_profile.json` | 전체 행 수, 결측치, 실제 관측 기간, 선정 품목·청구이유·연령 분포 |
| `processed/kca_product_reason_age.json` | 선정 품목 × 청구이유 × 연령 집계 |
| `processed/product_filter.json` | 선정한 원본 품목명과 프로젝트 분류의 매핑 |
| `processed/rag_rules.jsonl` | 출처가 연결된 LG 공개 안내 요약 9개. RAG 시드용이며 **서명된 계약 약관이 아님** |
| `processed/installation_reference.json` | 수도꼭지 위치별 설치공간 예시. 실제 모델·현장 판정에는 추가 확인 필요 |

JSON·JSONL은 UTF-8입니다. `.jsonl`은 한 줄에 레코드 하나입니다. 원본 CSV를 Excel에서 열 때는 **데이터 → 텍스트/CSV 가져오기 → 한국어 CP949**를 선택하세요.

## Mock 내부 시스템 데이터

`mock/` 데이터는 모두 합성 데이터입니다. 실고객·실주소·실제 LG 견적·기사 일정이 아닙니다. 실제 소비자 문제의 발생 비율을 입증하는 데 사용할 수 없습니다.

| 파일 | 규모 / 역할 |
| --- | --- |
| `customers.json` | 가상 고객 100명. 식별자 C001~C100, 가상 이사 주소 |
| `contracts.json` | 가상 계약 100건. 기본요금과 납부요금, 의무·총기간, 혜택 이력, 추가 정산 |
| `quotes.json` | 가상 견적 100건. 철거·운송·재설치 분리, 설치 상태 포함 |
| `products.json` | 워시타워 제품군 1개. 실판매 모델번호는 미지정 |
| `terms.json` | 가상 약관 버전 1개. 공식 FAQ에서 참고한 규칙과 데모 경계 처리 |
| `slots.json` | 지역 3곳 × 14일 × 철거/재설치 = 84개 가상 슬롯 |
| `bookings.json` | 초기 예약 0건 |
| `lg_move_care.sqlite` | 위 업무 데이터를 넣은 SQLite DB. 관계 키와 JSON payload 사용 |
| `assumptions.json` | 가정, 고정 난수 시드, 날짜·가격·설치 판정 생성 규칙 |
| `evaluation_cases.json` | 정상 비용 비교 15개, 정보 부족 5개, 예외 5개, 위험 5개. **평가 입력과 기대값만 생성했으며 Agent 평가는 미실행** |

대표 C001의 데모 계산은 `59,000원 × 잔여 18개월 × 20% + 회수비 111,000원 = 323,400원`입니다. 이전 견적은 80,000원이며 일회성 차이는 243,400원입니다. 향후 월 구독료와 대체가전 비용은 이 차이에 포함되지 않습니다.

요금·견적은 가정입니다. 회수비 숫자는 공식 FAQ를 참고했지만 C001에 적용된다는 사실까지 검증된 것은 아닙니다. `MOCK-20261012-V1`은 LG의 실제 약관 버전이 아닙니다.

## 실행 방법

Python 3.10 이상과 표준 라이브러리만으로 **다운로드된 원본에서 가공 JSON·가상 DB를 재생성**할 수 있습니다.

```powershell
python scripts/build_dataset.py
```

이 명령은 `processed/`, `mock/`, `sources.json`, `docs/validation.json`을 다시 씁니다. **가상 DB의 예약도 초기화하므로 운영 중인 예약 DB에 사용하지 마세요.** PDF 재추출은 실행 과정에 필요하지 않습니다. 최초 수집 때만 pypdf로 텍스트를 추출했고 핵심 표 3쪽은 이미지로 대조했습니다.

Git에 포함된 CSV와 출처 manifest만으로 재생성할 수 있습니다. 배포하지 않는 LG HTML이 없으면 수집 당시 저장된 해시를 유지하며, 현재 파일을 다시 검증한 것으로 간주하지 않습니다. `sources.json`의 `distribution=local_only`로 구분합니다.

고객 계약 조회 예시:

```python
import json, sqlite3
db = sqlite3.connect('mock/lg_move_care.sqlite')
row = db.execute('SELECT payload FROM contracts WHERE customer_id = ?', ('C001',)).fetchone()
contract = json.loads(row[0])
print(contract['monthly_base_fee'])
```

## 아직 확보하지 못한 데이터

| 항목 | 현재 상태 / 필요한 이유 |
| --- | --- |
| 가입 시점별 실제 LG 구독 계약서와 약관 원문 | 미확보. 공식 홈페이지 회원 서비스 약관은 구독 계약서 대체 불가. 과거 계약에 현재 FAQ를 자동 적용하면 안 됨 |
| 실제 운송·철거·재설치 견적 | 미확보. 주소·설치환경·서비스 범위별 견적 필요. 현재는 Mock |
| 모델별 확정 사양과 설치 판정 | 제품군 공용 안내만 확보. 실모델 선정 후 설명서와 현장 확인 필요 |
| 실제 기사 일정·예약 API | 비공개 내부 데이터. 현재는 Mock |
| 워시타워 구독 고객의 이사·해지 연계 데이터 | 미확보. 이사가 최대 분쟁 원인이라고 주장할 근거 없음 |
| 소비자상담 별도 원자료와 피해구제 과거 분기 파일 | 이번 묶음에 미포함. 상담 건수와 피해구제 건수는 서로 다른 지표 |
| 품목별 피해구제 사례 XML | 목록만 확인. `sources.json`의 `catalog_only_not_downloaded` 항목 |

## 출처와 사용 조건

- [한국소비자원 실태조사](https://www.kca.go.kr/smartconsumer/sub.do?menukey=7301&mode=view&no=1004452389): 게시물은 공공누리 제1유형(출처표시). 첨부 내 제3자 이미지·자료는 별도 확인이 필요합니다.
- [공공데이터포털 피해구제 자료](https://www.data.go.kr/data/3040720/fileData.do): 포털에 이용허락범위 제한 없음으로 표시되어 있습니다.
- [LG FAQ](https://www.lge.co.kr/support/usage-guide-faq), [재설치 안내](https://bestshop.lge.co.kr/story/insight/detail/IN10009002), [설치 체크리스트](https://www.lge.co.kr/support/solutions-20151615505398): LG 저작권 고지가 있습니다. 원문 HTML은 로컬 조사용으로 수집했으며, 공개 저장소 재배포 전 사용 조건을 확인해야 합니다. `.gitignore`에서 LG 원문 HTML의 기본 추적을 제외했습니다.

수집 원본의 URL·SHA-256·바이트 크기는 `sources.json`에 있습니다. 최신 안내가 바뀌면 원본을 새로 수집하고 적용일·계약 매칭을 재검토하세요. 파일 기준일은 계약상 시행일과 다릅니다.
