# data-research

LG AX 부트캠프 실전프로젝트 팀의 자료조사 저장소입니다.
고객 문제 근거, 공개 데이터, 리뷰·커뮤니티 조사 결과를 모아 기획서와 발표의 근거로 사용합니다.

## 폴더 구조

| 폴더 | 용도 | 병합 방식 |
|---|---|---|
| `research/` | 개인·팀별 조사 문서 및 데이터 | 검사 통과 시 자동 병합 |
| `decisions/` | 최종 아이디어 선정, 주요 결론 문서 | 팀장 승인 후 병합 |
| `templates/` | 조사 문서 템플릿 | 검사 통과 시 자동 병합 |
| `.github/` | 자동 검사·병합 설정 | 팀장 승인 후 병합 |

## 작업 순서

1. `main`에서 새 브랜치 생성: `research/주제명` (예: `research/air-purifier-reviews`)
2. `templates/research-template.md`를 복사해 `research/` 아래에 작성
3. 커밋 후 push
4. GitHub에서 `main` 대상으로 **Pull Request 생성** (push만으로는 병합되지 않음)
5. 자동 검사 통과 시 자동 Squash Merge, 작업 브랜치 자동 삭제
6. 검사 실패 시 Actions 로그 확인 → 수정 → 같은 브랜치에 다시 push (PR 새로 만들 필요 없음)

## PR 제목 규칙

Squash Merge 시 PR 제목이 `main`의 커밋 메시지가 됩니다.

- `docs:` 문서 및 조사 결과 추가
- `data:` 수집 데이터 추가 및 수정
- `fix:` 잘못된 자료 수정
- `chore:` 폴더 구조 및 설정 변경

예: `docs: 공기청정기 고객 리뷰 조사`

## 자동 검사 항목

- PR 제목 형식
- 허용 확장자: md, txt, csv, json, pdf, xlsx, png, jpg, jpeg
- 파일당 20MB 이하
- `research/`의 Markdown 문서에 `출처:`, `조사일:` 기재

## 금지 사항

- `main` 직접 push
- 개인정보, 인증정보(API 키, 비밀번호), 재배포가 제한된 원본 데이터 업로드
- 대용량 데이터 업로드 → 외부 저장소에 보관하고 링크와 수집 방법만 기록

## 사람 검토가 필요한 경우

- `decisions/`, `.github/` 변경은 팀장 승인 후 병합됩니다.
- 그 밖에 검토가 필요한 PR에는 `needs-review` 라벨을 붙이면 자동 병합에서 제외됩니다.