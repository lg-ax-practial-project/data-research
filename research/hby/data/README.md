# hby 조사 근거 데이터와 원자료 보관 안내

- 조사자: hby
- 조사일: 2026-11-09 — 기존 검증 결과 작성일 기준
- 출처:
  - [기존 hby 원자료 커밋](https://github.com/lg-ax-practial-project/data-research/tree/a28352d33c1e1c593139f6fb8397acbdbb3aa1dc/hby/Data) — 기존 자료 보관 위치
  - [기존 검증 작업기록](../topic-discovery/작업기록_v2.md) — 수행 범위와 오류 수정 이력
  - [파일별 무결성 목록](manifest.json) — 원본과 Git 저장본 각각의 파일 경로·크기·SHA-256
- 표본 수 (전체): 기존 검증 대상별로 다름. 통계·라벨·사례를 별도 표본으로 해석
- 유효 건수 (분석에 사용): 각 CSV/JSON 및 조사 문서 본문 참조
- 보관 경로 정리일: 2026-11-18

## 조사 목적

기존 자료에서 만든 집계·검증 결과를 조사 문서와 함께 공유하고 원자료를 추적할 수 있게 한다.

## 주요 발견 (관찰한 사실)

이 폴더에는 기존 CSV/JSON 결과 **32개**의 수치·본문·내부 경로 문자열을 유지했다. Git이 파일을 저장하면서 CRLF 줄바꿈을 LF로 정규화한 경우 외에는 원본 바이트와 동일하며 분석 스크립트를 재실행하지 않았다. `manifest.json`과 이 안내는 이번 정리에서 추가했다.

| 위치 | 역할 | 우선 참조 |
|---|---|---|
| `검증_v3/` | 통계·수치·원자료 목록 대조 결과 | 통계 검증 최종 참조본 |
| `검증_v1/`, `검증_v2/` | 이전·부분 검증 결과 | 오류 수정 이력 확인용 |
| `정성검토_v1/` | 기존 라벨 재집계와 최소화된 사례 발췌 | 전체 오류율·모집단 추정에 사용하지 않음 |
| `추적검증_v2/` | 가공본·수집본 행 연결 | 완전일치와 400자 접두사 일치를 구분 |
| `추적검증_v1/` | 초기 행 연결 결과 | 이전본 |
| 루트 CSV 3개 | 인사이트 근거표·15사례 판정·비율 계산 | 해당 조사 문서와 함께 확인 |

`manifest.json`의 `bytes`·`sha256`은 Git에 저장된 파일 기준이고, `original_bytes`·`original_sha256`은 로컬 백업 원본 기준이다. `git_line_endings_normalized`가 참인 32개는 CRLF → LF 변경만 있는지 바이트 단위로 확인했다.

## 팀 가설 (관찰과 구분)

자료 수와 라벨 집계는 고객 수요, 고장률, 서비스 효과나 팀의 주제 확정을 입증하지 않는다.

## 프로젝트 반영 포인트

공유 문서는 [topic-discovery 안내](../topic-discovery/README.md)부터 읽고 근거표의 확인 위치로 추적한다. 기존에 병합된 [토론 자료](../../debate-lab/README.md)는 그대로 참조한다.

### 과거 경로와 현재 위치

| 기존 기록의 경로 | 현재 공유·보관 위치 |
|---|---|
| `Analysis/topic_discovery/` 또는 `research/topic-discovery/`의 Markdown | `research/hby/topic-discovery/` |
| 같은 위치의 CSV/JSON 집계·검증 결과 | `research/hby/data/` — 하위 폴더명 유지 |
| `Data/통합자료/...` | 위 링크의 기존 hby 원자료 커밋 또는 로컬 `.local/original/data/통합자료/...` |
| `Data/drive-download-20261109T000429Z-1-001/...` | 기존 hby 커밋의 같은 경로 또는 로컬 `.local/original/data/drive-export/...` |
| 기존 Python 보조 코드 4개 | 로컬 `.local/original/research/topic-discovery/` |
| 최근 기획서·실전프로젝트 자료 | 로컬 `.local/original/data/기획서/`, `.local/original/data/실전프로젝트-자료/` |

로컬 전체 백업은 `.local/backups/before-data-cleanup-*/working-tree.zip`과 파일별 해시 목록에 보존한다. 기존 `hby` 브랜치와 정리 전 작업의 stash도 유지한다. `.local/`은 각 컴퓨터의 로컬 보관 공간이므로 다른 팀원의 clone에 자동으로 생기지 않는다.

### 커밋에서 제외한 자료

원자료 전체 사본, 20MB를 넘는 `standardized_redress.csv`(41,715,640바이트), 보조 코드·HTML/XML/JSONL·압축 파일·Office 원본·로컬 DB는 재업로드하지 않았다. 원자료의 공개 범위·재배포 조건을 검토한 뒤 필요한 자료만 별도 작업으로 공유한다. `.gitignore`는 로컬 보관 폴더, 인증정보 파일, 캐시·OS·편집기 임시 파일·로컬 DB를 제외한다. CSV/JSON/PDF 등 조사에 쓰는 정상 자료 확장자는 일괄 제외하지 않는다.

## 한계 및 추가 조사 필요

이 목록은 기존 결과의 보존과 경로 추적을 위한 것이다. 원자료 전수 검토, 외부 출처 최신성 확인, 개인정보 비식별 처리의 완전성, 집계 수치 재검산을 새로 수행한 결과가 아니다. 근거표와 파일 목록 안의 과거 경로는 추적용 식별자로 유지했다.
