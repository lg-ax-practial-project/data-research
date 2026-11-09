# LG TV FAQ and Self-help Collection

최종 갱신: 2026-10-05. 현재 담당 업무는 **LG TV 공식 FAQ·스스로 해결 수집과 정제**다. 소비자원 사례는 이전 업무이며 Agent 평가·개발은 이번 수집 완료 조건이 아니다.

## 현재 범위

- [공식 TV FAQ](https://www.lge.co.kr/story/faq/tvs-faq): 독립 FAQ 페이지. 제품·설치·구매·배송·고객지원 질문이 혼재하므로 원문의 category를 보존한다. 모든 질문을 고장/A/S 문의라고 해석하지 않는다.
- [스스로 해결](https://www.lge.co.kr/support/solutions): TV 관련 선별 상세 글과 공식 FAQ에서 관찰한 상세 글 링크를 수집한다.
- 목록 페이지는 제품 선택이 필요한 동적 화면이다. 정적 조회만으로 TV 전체 목록·페이지 수를 확정하지 못했다. 따라서 **사이트 전체 수집 완료나 완료율을 주장하지 않는다.**
- collection_sources.json으로 추가 후보 URL과 실행당 상한(30개, 코드 안전 상한 40개)을 관리한다. FAQ 페이지 링크를 새로 발견해도 상한 초과분은 discovery.json에 남긴다. 검색 결과는 후보이며 실제 제목·본문 확인 후 정제한다.

## 가장 먼저 볼 자료

최신 실제 실행 경로와 건수는 [수정·검증 기록](repair_20261005/RESULTS.md)을 참고한다.

| 경로 | 내용 |
| --- | --- |
| runs/<실행시각>/raw/ | 수정하지 않은 HTTP HTML 바이트 원본·robots.txt |
| runs/<실행시각>/processed/articles.jsonl | 본문, 단계/표 블록, 이미지 설명, FAQ, 출처·원본 해시 |
| runs/<실행시각>/processed/faqs.jsonl | 전체 Q/A. source_type으로 독립 FAQ/자가점검 글을 구분 |
| runs/<실행시각>/processed/faq_catalog.jsonl | 독립 TV FAQ의 Q/A, 공식 카테고리 포함 |
| runs/<실행시각>/processed/self_help_faqs.jsonl | 스스로 해결 본문에 포함된 Q/A |
| runs/<실행시각>/manifest.json | 시도한 주소, 성공/검토 필요, 원본 경로·해시 |
| runs/<실행시각>/discovery.json | 후보 주소, 발견 출처, 미시도 주소, 전체 범위 미확인 표시 |
| runs/<실행시각>/validation.json | 실행 건수와 해시 검증 결과. 의미·전체 범위 검증은 아님 |
| discovery_20261005.firecrawl.json | 공식 검색·목록·TV FAQ 확인 기록. Firecrawl 변환본이며 HTTP 원본과 구분 |
| lg_tv_crawler.py / collection_sources.json | 수집기와 수집 범위 설정 |
| test_lg_tv_crawler.py / verify_collection.py | 추출 시험과 원본 해시·재추출 검증 |
| lg_tv_workflow.json | 기존 수동 n8n 워크플로우 가져오기 파일 |

## 정제 방식과 검증

1. 공개 공식 페이지만 robots 허용 여부 확인 후 2초 간격으로 요청한다. 문서 ID/정규 URL로 실행 내 중복을 방지한다.
2. HTTP 원본은 새 실행 폴더에 저장하고 SHA-256을 기록한다. 이전 실행과 원본은 수정하지 않는다.
3. 스스로 해결은 본문 컨테이너, 독립 FAQ는 machine-faq 컨테이너를 선택한다. 메뉴/스크립트는 제외한다.
4. 실제 dt/dd 질문을 순서대로 모두 연결한다. 독립 FAQ는 각 질문/답변 항목과 공식 category를 연결한다. 미짝 질문은 extraction_issues로 남긴다. 생성형 모델로 질문·답변을 만들지 않는다.
5. text에 이미지 alt를 포함하고 content_blocks에 문단·제목·목록·표 행/셀을 보존한다. image_alts는 별도 필드로도 보존한다. 이미지·영상 자체는 다운로드하거나 시각 검수하지 않았다.
6. 날짜는 head-infos에서만 후보로 추출한다. 날짜 의미(게시/수정)는 수동 확인 필요이며 없으면 빈 배열이다. 전역 템플릿 날짜를 게시일로 쓰지 않는다.
7. 시험 10개는 추출 기능 검증이지 전체 수집률이나 Agent 정확도가 아니다. 실제 원본을 재추출해 본문·FAQ·블록·alt·날짜를 비교하고 원본 해시를 검사한다.

## 실행 방법

n8n: http://localhost:5678/workflow/We1WireffIYDxQtj

Python 3 표준 라이브러리만 사용한다. 패키지 설치는 불필요하다. Python 실행 파일 위치는 각 PC 환경에 맞게 지정한다.

폴더 안에서 PowerShell 실행:

```powershell
python -B .\lg_tv_crawler.py --output . --serve
```

이 PC에서 python 명령이 없다면 다음 실행 파일로 대체한다:

`C:\Users\HanBuyong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

- 도우미가 켜져 있는 상태에서 n8n Execute workflow를 누른다. n8n은 실행/결과 검증을 맡고 실제 조회·정제·저장은 Python 도우미가 수행한다. n8n 단독 실행 구조는 아니다.
- 도우미는 127.0.0.1:8766에 바인딩하고 Docker n8n은 host.docker.internal:8766으로 요청한다. 재부팅 후 도우미를 다시 시작해야 한다. 자동 시작·예약 실행은 구성하지 않았다.
- 직접 일회 수집은 `python -B .\lg_tv_crawler.py --output .`이다.
- 검증: `python -B .\verify_collection.py .\runs\<실행시각> .\runs`
- 새 실행은 새 폴더에 저장한다. 과거 실행 건수를 합산해 고유 문서 수로 표현하지 않는다.

## 현재 업무 밖의 과거 보조 산출물

review_20261004/, recheck_20261005/, common_scenarios_20261005/, execution_handoff_20261005/는 삭제하지 않고 보존한다. **이전 원본 기준 수동 스냅샷이며 최신 수집 때 자동 갱신되지 않는다.** 가상 평가 질문은 공식 FAQ 건수에 포함하지 않는다. 팀 모델/Agent 주소 미정은 현재 수집 작업의 장애물이 아니다.

위 보조 폴더와 생성 스크립트는 로컬 보관 자료이며 이번 수집 PR에는 포함하지 않는다. 과거 README의 이들 경로는 당시 로컬 기록으로만 읽는다.

수집기 수정 전 파일은 repair_20261005/pre_repair/에 보존했다. 이전 상세 README도 같은 곳에 보존한다. 짧은 작업 기록과 최신 건수는 repair_20261005/RESULTS.md에 기록한다.

## 인계 시 주의

공식 원문에 있는 안내와 고객 발생 빈도·실제 사례를 구분한다. 정책 관련 답변은 적용 조건과 현행 원문을 확인한 뒤 사용한다. 문서 보존이 모든 모델 적용, 최종 고장 진단 또는 교환/환급 승인을 의미하지 않는다. 사용자 요청에 따라 비공개 팀 저장소에 수집 PR로 제출한다. 공개 재배포 허락을 확인하지 않았으므로 공개 저장소 게시나 머지는 수행하지 않는다.
