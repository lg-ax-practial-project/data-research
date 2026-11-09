# 부용 자료조사 - LG Move Care 자료 위치와 진행 상태

최종 갱신: **2026-10-12 추가 조사 2차 및 DataResearch 로컬 반영 (한국 시간)**. 이 README는 이번 워시타워 구독 조사의 범위, 자료 위치, 검증 결과, 남은 작업을 안내한다.

**공식 근거 자료:** [자료 모음](evidence/README.md) · [핵심정책 근거표](evidence/핵심정책_공식근거표.md) · [4쪽 근거 자료집](evidence/공식근거_자료집.pdf). 기관 발행 원본 PDF 2종을 별도 보존 사본으로 제공하며, 편집 자료와 공식 원본을 구분했다. 출처별 URL·원문 위치·날짜·적용 한계·파일 지문을 연결했다.

**저장 위치:** 사용자 요청에 따라 조사 묶음을 `D:\lg-ax-core-project\DataResearch\부용 자료 조사\move-care-research-20261012\`에 반영했다. 개인 폴더의 상위 README가 자료 안내 입구다. 작성에 사용한 ChatGPT 프로젝트의 `output/move-care-research-20261012/`도 보존했으며, 두 위치는 자동 동기화되지 않는다. 후속 자료는 실제 DataResearch 개인 폴더를 우선 확인한다.

**추가 확보:** 일반 유상 워시타워 이전설치 요금표·설치 조건·요청 사전답사 비용, 과거 LG 공지 연결 약관 전문, KCA 실태조사 원본을 확보했다. 현행 약관 버전과 과거 계약의 무상 혜택 적용은 여전히 추가 확인이 필요하다.

## 현재 담당 업무와 작업 단계

- 프로젝트: LG Move Care. 이사를 앞둔 LG 워시타워 구독 고객의 해지·이전 선택을 지원하는 Agent.
- 담당: **공식 계약 자료조사와 RAG 검색 기능 구축**. 현재는 자료조사·공식 원문 대조 단계다.
- 이번 작업: 현재 워크스페이스와 Git 상태 확인, 기존 확보 자료 점검, FAQ·구독 안내·이전설치 관련 공식 근거 수집, 적용 날짜 및 미확정 사항 기록.
- 기준: 워크스페이스의 `sources/진짜 찐최종_기획안.pdf`를 직접 읽었다. PC의 동명 파일로 대체하지 않았다.
- 개발 상태: Move Care 검색 기능·임베딩·ChromaDB 색인은 아직 구축하거나 평가하지 않았다. 원문 확보와 검색 기능 완성은 구분한다.

React/UI, 계산 Tool, 예약 Tool은 이번 작업 범위에 포함하지 않았다. 공식 정책과 Mock 고객·견적·예약 데이터는 분리한다.

**추가 조사 2차:** [최신 보고서](reports/추가조사_20261012_02.md)에 구독 대상 조회 경로·온라인 접수 제한·출장비 문구 충돌을 기록했다. 현행 약관과 과거 계약 적용은 미확정이며 [공식 확인 질문지](reports/공식확인_질문지_20261012.md)를 준비했다.

## 가장 먼저 볼 자료

1. [추가 조사 2차](reports/추가조사_20261012_02.md): 최신 조사 결과·충돌 문구·미확정 항목과 다음 확인 경로.
2. [추가 조사 1차](reports/추가조사_20261012_01.md): 새 약관 근거·일반 요금표·설치 조건·KCA 통계와 현재 남은 확인 사항.
3. [초기 조사현황](reports/조사현황_20261012.md): 기준 기획안, 실제 폴더와 Git 상태, 작업 시작 당시 확보 자료, 핵심 원문 대조.
4. [공식 출처 및 적용 조건 목록](metadata/source_manifest.json): 문서명·기관·URL·날짜·제품·계약 유형·원문 위치·조건·검증 상태.
5. 아래 ‘현재까지 확인한 핵심 조건’과 ‘남은 작업과 다음 순서’: 확인한 내용과 아직 확정하지 않은 내용.

## 어디에서 무엇을 보면 되는가

아래 링크는 이 README가 있는 폴더를 기준으로 한다. 폴더 전체를 함께 옮기면 내부 자료 링크를 유지할 수 있다.

| 폴더 / 문서 | 내용 | 먼저 볼 파일 |
| --- | --- | --- |
| [reports](reports/추가조사_20261012_02.md) | 초기 점검과 후속 조사 결과 | 최신 `추가조사_20261012_02.md` |
| [metadata/source_manifest.json](metadata/source_manifest.json) | 공식 및 공식 연결 출처 16개와 핵심 조건, 계약 적용 미확정 사항 | `sources`, `policy_findings`, `remaining_after_additional_research` |
| [raw/LG-FAQ-001.firecrawl.md](raw/LG-FAQ-001.firecrawl.md) | 회수비·위약금·2026-03-24 기준일을 확인한 LG FAQ 수집본 | ‘가전 구독 월 요금 외 발생 비용이 있나요?’ |
| [raw/LG-WASHTOWER-001.firecrawl.md](raw/LG-WASHTOWER-001.firecrawl.md) | 워시타워 제품의 무상 철거·재설치·운송비 안내 | ‘무상 철거/재설치’, ‘구독 확인사항’ |
| [metadata/planning_review.json](metadata/planning_review.json) | 기준 기획안 11쪽의 추출 텍스트, 원문 링크, 파일 지문 | `source`, `sha256`, `pages`, `links` |
| [references/진짜 찐최종_기획안.pdf](references/진짜%20찐최종_기획안.pdf) | 실제 기준으로 읽은 기획안의 보존 사본. 공식 계약 정책과 구분 | 서비스 범위와 Mock 설계 |
| [raw/reference/소비자분쟁해결기준_2025.pdf](raw/reference/소비자분쟁해결기준_2025.pdf) | 기존 확보 원본의 보존 사본 | PDF 69~71쪽 장기 물품대여서비스업 |
| [metadata/local_reference_copies.json](metadata/local_reference_copies.json) | 두 PDF의 원래 위치·사본 상대 경로·SHA-256 | 원본과 사본의 동일성 |
| [metadata/workspace_inventory.json](metadata/workspace_inventory.json) | 조사 시점의 기존 파일 목록 | `inventory_at_review_excluding_new_research` |
| [metadata/existing_reference_review.json](metadata/existing_reference_review.json) | 기존 KCA 정수기 렌탈 답변의 관련성 및 사용 범위 | `scope`, `records` |
| [metadata/search_log.json](metadata/search_log.json) | 추가 검색에서 사용한 결과와 탐색 기록 | `results` |
| [metadata/additional_sources_01.json](metadata/additional_sources_01.json) | 추가 출처 8개와 조건·통계·남은 확인 사항 | `sources`, `findings`, `remaining` |
| [raw/LX-RELOCATION-PRICE-001.browser-observation.json](raw/LX-RELOCATION-PRICE-001.browser-observation.json) | 비용표의 세탁기&건조기 탭에서 직접 확인한 워시타워 행 | `headers`, `visible_rows`, `transport_notices` |
| [raw/cx/KCA-SUBSCRIPTION-REPORT-2026.pdf](raw/cx/KCA-SUBSCRIPTION-REPORT-2026.pdf) | KCA 실태조사 다운로드 원본 36쪽. CX 분석용 | PDF 3·14·22·25쪽 |
| [metadata/kca_subscription_report_text.json](metadata/kca_subscription_report_text.json) | KCA 원본 지문·전체 추출 텍스트·PDF 페이지 번호 | `sha256`, `pages` |
| [metadata/additional_search_log_01.json](metadata/additional_search_log_01.json) | 추가 조사 탐색·접근 한계·정책 원문으로 제외한 자료 | `results`, `excluded_policy_sources` |
| [metadata/additional_sources_02.json](metadata/additional_sources_02.json) | 추가 출처 2개·재검토·충돌·남은 확인 사항 | 최신 조사 기록 |
| [metadata/booking_html_observations_02.json](metadata/booking_html_observations_02.json) | 접수 수집본의 구독 조회 양식과 출장비 문구 위치 | 원문 위치와 실제 노출 미확인 한계 |
| [metadata/additional_search_log_02.json](metadata/additional_search_log_02.json) | 추가 검색 및 직접 화면 열람 제한 | 검색 결과·제외 이유·접근 기록 |

검토 대상 출처는 **초기 6개 + 추가 1차 8개 + 추가 2차 2개 = 16개**다. LG가 공식적으로 연결한 LX판토스 가격표와 LG계정 약관을 포함한다. 같은 문서의 JSON·Markdown·PDF 또는 기본 탭·제품별 탭 관찰을 별도 정책으로 합산하지 않는다. 탐색 목록·부적합한 사이트 약관·버전 불일치 비교표는 `metadata/discovery/`에 별도로 보존했다. 전체 사이트 수집률과 전체 프로젝트 진행률은 산정하지 않았다.

**2차 조사 보완:** 구독 대상 조회 양식에서 철거·설치별 무상 잔여 횟수 등 항목을 확인했다. 개별 계약 조회 결과는 아니며 과거 계약 자격은 여전히 추가 확인이 필요하다. 방문 후 취소 출장비는 접수 본문 25,000원과 희망일 레이어 20,000원 문구가 공존하므로 실제 적용액을 확정하지 않는다. 요청 사전답사 25,000원과도 구분한다.

## 기존 확보 자료와 이번에 확보한 자료

| 조사 대상 | 작업 시작 전 | 이번 결과 | 남은 확인 |
| --- | --- | --- | --- |
| R1 LG 구독 FAQ | 독립 원문 수집본 미발견 | 회수비 111,000원·안내 기준일·위약금 안내 확보 | 적용 계약 및 약관 버전 |
| R2 구독 약관·이용 가이드 | 약관 전문 미확보 | 구독 안내·가이드, 2021년 개정 공지와 연결된 비매장용 전문 확보 | 현행 전문·계약 채널·고객확인사항·일반항목·개정 이력 |
| R3 워시타워 이전설치 | 독립 원문 수집본 미발견 | 무상 혜택 시작일·횟수·운송비 제외, 일반 요금표·설치 조건·사전답사 비용 확보 | 과거 계약 적용·무료 혜택 후 운송·추가비 정산 |
| R4 소비자분쟁해결기준 | 기존 원본 PDF·출처 기록 있음 | 기존 PDF 69~71쪽 장기 물품대여서비스업 확인, 공식 본문 시행일 대조 | LG 계약과의 적용 관계 |
| R5 KCA 구독 관련 자료 | 기존 A/S 자료와 과거 정수기 렌탈 답변 일부 있음 | 가전 구독·렌탈 실태조사 공식 원본 36쪽과 통계·약관 쟁점 확인 | 워시타워/이사에 직접 맞는 공식 답변·사례 필요 시 추가 조사 |

기존 자료는 작성 당시 ChatGPT 워크스페이스의 `resources/raw/`와 `resources/processed/`, TV 조사 기록은 `output/`, `outputs/`, `tv_crawl_repair/`, `recheck_20261005/` 등에 남아 있다. 이 경로들은 DataResearch 개인 폴더 내부 경로가 아니다. 이번 대조에 사용한 분쟁해결기준 PDF만 사본으로 포함했고, 기존 TV 자료 전체를 옮기거나 워시타워 정책으로 취급하지 않았다.

## 현재까지 확인한 핵심 조건

| 항목 | 공식 원문에서 확인한 내용 | 아직 확정하지 않은 내용 |
| --- | --- | --- |
| 워시타워 회수비 | 111,000원. **2026-03-24는 안내 기준일**이며 실제 회수비는 계약서 명기 금액을 따름 | 모든 계약에 111,000원이 적용된다는 판단, 이 날짜 이후 계약만 해당한다는 판단 |
| 중도해지 위약금 | 할인 전 기본요금·잔여 의무사용기간 총 요금 기준. 일반 안내는 사용기간별 30%·20%·10%, 2년 계약 상품 예외 있음 | 약관 버전·계약 시점별 적용, 1년/2년 경계 및 일할 계산 |
| 무상 철거·재설치 | 확인한 W2420WHNR 안내는 **2025-03-01부터**, 가전 구독 고객에게 계약기간 내 1회 | 과거 계약 포함·소급 여부, 계약일/설치일 중 자격 판정 기준 |
| 운송 및 추가 비용 | 무료 혜택에 운송비 제외. 일반 유상 요금표 및 거리별 운송 안내 확보 | 구독 무료 혜택 고객의 실제 운송·추가비 정산. 기획안의 80,000원은 Mock 견적 |

추가 확인한 일반 유상 표는 **워시타워 철거 97,000원 / 설치 134,000원 / 기본 운송 포함 이전설치 271,000원**이며 컴팩트는 별도 행이다. 운송 0km 이상 10km 미만은 40,000원으로 안내한다. 이 값을 구독 무료 혜택 적용 후 실제 청구액이나 해지 회수비로 사용하지 않는다.

워시타워 설치가이드에는 **이전설치를 위한 고객 요청 사전답사 25,000원**이 명시돼 있다. 구매 전 최초 무료 사전답사, 컴팩트 예외, 작업 불가 출장비는 조건이 달라 구분한다.

위 내용은 **공식 안내 원문 확인** 상태다. 개별 고객 계약에 대한 확정 정책이나 계산 규칙으로 승인한 상태는 아니다. W2420WHNR은 검증용 예시 모델이며 팀의 최종 대상 모델로 확정하지 않았다.

### 자료 사이 차이와 주의 사항

- 같은 공식 페이지에도 현재 회수비 표와 2021-11-05 계약부터라는 과거 FAQ 금액이 함께 남아 있다. 수집일이 최신이어도 본문의 모든 항목이 현행 정책인 것은 아니다.
- 다른 제품인 에어컨·STEM 냉장고의 ‘2026-01-05 이후 설치’ 철거 조건을 워시타워에 적용하지 않는다.
- 제품 구독과 서비스만 제공하는 케어십의 위약금 조건을 구분한다. 가이드의 ‘케어십 위약금 없음’을 워시타워 제품 구독에 전용하지 않는다.
- LG FAQ의 사용경과기간별 위약금 안내와 분쟁해결기준의 의무사용기간 길이별 기준은 구분이 다르다. 양쪽 원문을 검색할 수 있게 보존하되, 적용 관계 확인 없이 계산 규칙을 합치거나 감면을 보장하지 않는다.
- 해지 회수비에 포함되는 운송과 이사할 때의 이전 운송은 별도 상황이다. 무료 이전설치 혜택을 무료 해지 회수로 해석하지 않는다.
- 과거 공지 연결 약관은 ‘비매장용’이고 본문 시행일이 없다. 위약금 조문도 KCA의 2025년 인용본과 달라 현행 버전으로 확정하지 않는다. 개정 공지와 링크된 상세 비교표의 날짜 차이도 추가 조사 보고서에 기록했다.

### CX 분석용 KCA 근거

공식 게시 페이지의 발간일은 **2026-04-09**, PDF 표지는 **2025-12**다. 피해구제 2022-01~2025-06 총 2,624건 중 계약 관련 1,446건(55.1%), 품질·AS 관련 908건(34.6%)을 확인했다. 2025-11-12~11-21의 설문 500명 중 위약금이 없는 것으로 인지한 사람은 157명(31.4%), 위약금 외 추가비 발생을 몰랐던 사람은 139명(27.8%)이다.

31.4%를 단순한 ‘위약금 수준 미인지’로 넓혀 표현하지 않는다. 전체 가전 구독·렌탈 자료를 LG 워시타워·이사 고객의 통계로 일반화하지 않고, 피해구제와 설문 분모를 구분한다. KCA 조사 보고서는 `raw/cx/`에 보관하며 현재 LG 계약 정책 원문과 동일한 기본 검색 묶음으로 취급하지 않는다.

## 공식 출처와 수집본

수집일은 모두 **2026-10-12 (한국 시간)**이다. 새 출처 2개는 [LG 케어 소개 수집본](raw/LG-CARE-ABOUT-001.firecrawl.md)과 [LG 연결 LX판토스 접수 수집본](raw/LG-RELOCATION-BOOKING-001.firecrawl.md)이다. 상품 재수집은 같은 출처 ID로 관리한다. 게시일·수정일·약관 시행일이 확인되지 않은 경우 `원문 미기재`로 기록했다. 안내 기준일, 서비스 제공 시작일, 약관 시행일을 서로 대체하지 않았다.

| ID | 문서 | 공식 원문 | 보관 수집본 |
| --- | --- | --- | --- |
| LG-FAQ-001 | LG 구독 추가 비용 FAQ | [LG FAQ](https://www.lge.co.kr/support/usage-guide-faq) | [Markdown](raw/LG-FAQ-001.firecrawl.md) / [JSON](raw/LG-FAQ-001.firecrawl.json) |
| LG-SERVICE-001 | 가전 구독 서비스 안내 | [LG 서비스 안내](https://www.lge.co.kr/care-solutions/rentalService) | [Markdown](raw/LG-SERVICE-001.firecrawl.md) / [JSON](raw/LG-SERVICE-001.firecrawl.json) |
| LG-GUIDE-001 | 세탁/의류 관리 구독 가이드 | [LG 구독 가이드](https://www.lge.co.kr/story/buying-guide/care-solutions-guide2) | [Markdown](raw/LG-GUIDE-001.firecrawl.md) / [JSON](raw/LG-GUIDE-001.firecrawl.json) |
| LG-WASHTOWER-001 | W2420WHNR 무상 혜택·구독 확인사항 | [LG 워시타워](https://www.lge.co.kr/product/care-solutions/wash-tower/w2420whnr) | [Markdown](raw/LG-WASHTOWER-001.firecrawl.md) / [JSON](raw/LG-WASHTOWER-001.firecrawl.json) |
| KCA-CRITERIA-001 | 분쟁해결기준 적용 성격 안내 | [KCA 기준 안내](https://www.kca.go.kr/odr/cm/in/rsltnCrtral.do) | [Markdown](raw/KCA-CRITERIA-001.firecrawl.md) / [JSON](raw/KCA-CRITERIA-001.firecrawl.json) |
| FTC-LAW-001 | 분쟁해결기준 제2025-14호 본문·부칙 | [국가법령정보센터](https://www.law.go.kr/admRulInfoP.do?admRulSeq=2100000270136) | [Markdown](raw/FTC-LAW-001.firecrawl.md) / [JSON](raw/FTC-LAW-001.firecrawl.json) |
| LG-RELOCATION-001 | 일반 이전설치 범위·현장 추가비 | [LG 베스트 케어](https://www.lge.co.kr/lg-best-care/service-installation-removal) | [Markdown](raw/LG-RELOCATION-001.firecrawl.md) / [JSON](raw/LG-RELOCATION-001.firecrawl.json) |
| LG-RELOCATION-FAQ-001 | 이전설치 비용·접수 안내 | [LG 비용 안내](https://www.lge.co.kr/support/solutions-20154362473191?category=CT50019274&subCategory=CT50019275&sort=update&page=1&cstFlag=Y&productCode=CLDRR&seq=161) | [Markdown](raw/LG-RELOCATION-FAQ-001.firecrawl.md) / [JSON](raw/LG-RELOCATION-FAQ-001.firecrawl.json) |
| LX-RELOCATION-PRICE-001 | 일반 요금표·워시타워 행 | [LX판토스 비용표](https://move.lxpantos.com/mvinst/priceTable.jsp) | [기본 탭 수집본](raw/LX-RELOCATION-PRICE-001.firecrawl.md) / [워시타워 탭 관찰](raw/LX-RELOCATION-PRICE-001.browser-observation.json) |
| LG-INSTALLATION-001 | 모델별 설치 조건·요청 사전답사 | [LG 설치가이드](https://www.lge.co.kr/story/setup-guide/washer-installation-guide) | [Markdown](raw/LG-INSTALLATION-001.firecrawl.md) / [JSON](raw/LG-INSTALLATION-001.firecrawl.json) |
| LG-WASHTOWER-FAQ-002 | 워시타워 설치 FAQ | [LG 워시타워 FAQ](https://www.lge.co.kr/story/useful-tip/wash-tower-faq) | [Markdown](raw/LG-WASHTOWER-FAQ-002.firecrawl.md) / [JSON](raw/LG-WASHTOWER-FAQ-002.firecrawl.json) |
| LG-TERMS-NOTICE-2021-001 | 과거 개정 공지·신규 이용자 범위 | [LG 과거 공지](https://bestshop.lge.co.kr/footer/notice/detail-267) | [Markdown](raw/LG-TERMS-NOTICE-2021-001.firecrawl.md) / [JSON](raw/LG-TERMS-NOTICE-2021-001.firecrawl.json) |
| LG-RENTAL-TERMS-LINKED-001 | 공지 연결 비매장용 전문·버전 미확정 | [LG계정 연결본](https://qt-kr.m.lgaccount.com/membership-spx-webapp/customer/terms_attachment1) | [Markdown](raw/LG-RENTAL-TERMS-LINKED-001.firecrawl.md) / [JSON](raw/LG-RENTAL-TERMS-LINKED-001.firecrawl.json) |
| KCA-SUBSCRIPTION-REPORT-001 | 실태조사·CX 통계·약관 쟁점 | [KCA 공식 게시 페이지](https://www.kca.go.kr/smartconsumer/sub.do?menukey=7301&mode=view&no=1004452389&page=1&cate=00000057) | [원본 PDF](raw/cx/KCA-SUBSCRIPTION-REPORT-2026.pdf) / [게시 페이지 수집본](raw/KCA-SUBSCRIPTION-REPORT-001.firecrawl.md) |
| LG-CARE-ABOUT-001 | 워시타워 케어 소개·무상 혜택 범위 | [LG 케어 소개](https://www.lge.co.kr/care-solutions/rentalService-aboutcare) | [Markdown](raw/LG-CARE-ABOUT-001.firecrawl.md) / [JSON](raw/LG-CARE-ABOUT-001.firecrawl.json) |
| LG-RELOCATION-BOOKING-001 | 구독 대상 조회 양식·온라인 접수 제한·출장비 상충 | [LG 연결 접수](https://www.lge.co.kr/lg-best-care/service-installation-removal/reservation) | [Markdown](raw/LG-RELOCATION-BOOKING-001.firecrawl.md) / [JSON](raw/LG-RELOCATION-BOOKING-001.firecrawl.json) |

`raw` 파일은 Firecrawl이 반환한 수집본이다. Markdown은 변환된 본문이고, JSON에는 메타데이터와 지원되는 경우 HTML이 포함돼 있다. 원 서버 HTTP 응답 바이트와 동일한 원본 파일을 뜻하지 않는다. `maxAge: 0`으로 요청했고, 관련 항목을 읽어 대조했다.

수집본에는 과거 정책·타제품·케어십·메뉴가 함께 포함될 수 있으므로 전체 내용을 곧바로 검색 색인에 넣지 않는다. 표의 금액·적용 날짜·예외 조항은 정제할 때 함께 유지해야 한다.

## 검증한 것과 검증 범위

- 공식 출처 6개의 URL, 수집본의 응답 상태, JSON/Markdown 보관 파일, 필수 메타데이터를 확인했다.
- 회수비 111,000원·2026-03-24 기준일·계약서 우선 문구, 무상 혜택 시작일·1회·운송비 제외 문구를 수집본에서 확인했다.
- 기준 PDF 텍스트와 링크를 추출하고 핵심 1·6쪽, 기존 분쟁해결기준의 관련 69·70쪽 표와 비고를 이미지로 확인했다. 기준 PDF의 파일 지문은 최초 확인값과 일치했다.
- 기존 자료의 파일 목록·README·출처 기록·관련 텍스트 검색과 관련 원문을 검토했다. KCA 사례집·연보 전체 페이지 전수 검토는 하지 않았다.
- 이번 README 보완에서는 파일 링크와 출처 ID의 연결, 기록한 상태와 출처 목록의 일치를 확인했다.
- 추가 조사: 비용표 제품 탭과 열 제목을 직접 대조했고, KCA 원본 PDF를 저장·지문 확인·텍스트 추출한 뒤 관련 PDF 3·14·22·25쪽의 표·분모·조사기간을 시각 검토했다.

자료 검증이 검색 정확도·계산 정확도·Agent 평가 통과를 의미하지 않는다. 개발 테스트와 검색 성능 테스트는 실행하지 않았다.

추가 조사 2차에서는 공개 접수 양식과 HTML 문구 위치를 대조했다. 직접 브라우저 열람은 자동 승인 검토의 429 오류로 미실행했다. 이에 따른 제한과 출처별 검증 상태는 최신 보고서를 따른다.

## 남은 작업과 다음 순서

1. **최우선:** 과거 연결 전문과 구분하여 LG 구독의 현행 매장용·비매장용 약관, 청약 전 고객확인사항/일반항목, 개정 이력을 확보한다. 시행일·버전과 계약 시점별 적용을 확인한다.
2. **최우선:** 워시타워 무상 철거·재설치의 과거 계약 포함 여부, 소급 적용, 계약일/설치일 판정 기준을 확인한다.
3. 확보한 일반 이전설치 표와 구분하여 무료 혜택 고객의 운송 단독 요금·추가비·요청 사전답사 면제 여부·혜택 소진 후 정산을 확인한다. 최초 배송 안내를 이전설치 조건으로 대체하지 않는다.
4. LG 계약·FAQ와 장기 물품대여서비스업 분쟁해결기준의 적용 차이를 대조하고, 예외의 해당 조건을 기록한다.
5. 확보한 KCA 실태조사를 CX 근거로 활용하고, 워시타워/이사에 직접 맞는 공식 답변·사례가 필요하면 보완한다. 통계와 계약 적용 규정을 분리한다.
6. 원문과 적용 조건 확인 후 문서 정제·청크 분할·임베딩·ChromaDB 색인·`search_contract_terms` 구축·대표 질문 검증으로 진행한다. 정확한 입력/출력 형식은 Agent 담당자와 합의한다.

2차 조사에서 추가된 우선 확인: 접수 본문과 희망일 레이어의 출장비 25,000원/20,000원 적용 버전, 철거·설치별 무상 잔여 횟수의 차감 규칙. [공식 확인 질문지](reports/공식확인_질문지_20261012.md)에 정리했다.

약관 전문을 검색에서 찾지 못한 것은 공개 문서가 없다는 뜻이 아니다. 사이트 이용약관·개인정보처리방침을 구독 계약 약관으로 대체하지 않는다. 아직 확정되지 않은 자료는 `원문 미기재`, `추가 확인 필요` 상태를 유지한다.

## 실제 작업 위치와 Git 반영 상태

Git 확인 기준일: 2026-10-12. 로컬 추적 정보 기준이며 원격 상태를 새로 Fetch한 결과는 아니다.

| 위치 | 확인 결과 | 이번 자료 반영 상태 |
| --- | --- | --- |
| 현재 ChatGPT 프로젝트 워크스페이스 | Git 저장소가 아님 | 작성본은 `output/move-care-research-20261012/`에 보존 |
| `D:\lg-ax-core-project\DataResearch` | 브랜치 `hby`, 개인 폴더 README 수정 및 조사 폴더 추가 | `부용 자료 조사/move-care-research-20261012/`에 로컬 반영. 커밋·Push 미실행 |
| `D:\core-project\cx-agent` | 기존 TV 개발 저장소. `hby`, 변경 없음, 로컬 `origin/hby`보다 16커밋 앞섬 | 이번 워시타워 조사 반영 없음 |

목표 조사 저장소는 `https://github.com/lg-ax-core-project/DataResearch.git`이다. 이번 반영은 로컬 `hby` 작업 폴더에 자료를 저장한 단계이며 GitHub 업로드를 뜻하지 않는다. 커밋·Push·Merge는 실행하지 않았다. 초기 보고서의 빈 README·변경 없음 표기는 조사 시작 당시의 상태다.

## 원본 보존과 README 갱신 원칙

- `sources/`의 동기화된 기준 자료와 기존 TV 조사 원본은 수정·삭제하지 않는다.
- 새 조사 수집본은 이 폴더에 보존한다. 후속 정제 자료·검색 평가용 정답·Mock 데이터는 역할에 맞게 분리한다.
- 자료 추가·검증 때 이 README와 출처 목록에 날짜, 위치, 결과, 한계, 남은 작업을 함께 갱신한다. 자동으로 갱신되는 기능은 아니다.
- `metadata/source_manifest.json`은 조사 기록이며 공통 API·검색 반환 스키마·계산 Tool 규칙을 변경하는 파일이 아니다.
- 이번 README의 구성은 기존 `D:\core-project\cx-agent-planning\부용자료조사\README.md`와 해당 폴더의 TV 수집 README를 참고했다. 과거 TV 작업 결과·수치·완료 상태를 이번 프로젝트의 실적으로 옮기지 않았다.
- 2026-10-12 README 점검: 출처 목록 중심의 안내를 현재 범위·자료 위치·확보 현황·검증 결과·추가 조사 순서·Git 반영 상태까지 포함하도록 보완했다.
- 2026-10-12 추가 조사 1차: 출처 8개와 KCA PDF 원본을 추가하고, 약관의 버전 한계·일반 유상 요금·설치 조건·CX 분모 및 날짜·남은 확인 사항을 갱신했다. 이 조사 완료 당시에는 DataResearch 폴더로 복사하기 전이었다.
- 2026-10-12 로컬 반영: 사용자 요청으로 DataResearch 개인 폴더에 조사 묶음과 기준 PDF 사본을 추가하고, 상위 README와 현재 저장 위치를 갱신했다. 기존 원본은 보존했다.

- 2026-10-12 추가 조사 2차: 공식 및 공식 연결 출처 2개 추가(총 16개), 상품 확인사항 재검토, 구독 대상 조회 경로·온라인 접수 제한·출장비 상충 기록 및 공식 확인 질문지 작성. 실제 개인 폴더에 로컬 반영했으며 개발·커밋·Push는 진행하지 않았다.

- 2026-10-12 공식 근거 정리: 기존 출처 16개를 유지하면서 원문 근거표·4쪽 편집 자료집·기관 발행 PDF 사본 2종과 지문 기록을 추가했다.
