# data-research

LG AX 부트캠프 실전프로젝트 팀의 자료조사 저장소입니다.
고객 문제 근거, 공개 데이터, 리뷰·커뮤니티 조사 결과를 모아 기획서와 발표의 근거로 사용합니다.

## 한눈에 보는 흐름

```
main 최신화 → 새 브랜치 → research/에 작성 → commit → push → PR 생성
                                                         ↓ (여기부터 자동)
                                     자동 검사 → 통과 시 자동 병합 → 브랜치 자동 삭제
```

- 내가 하는 일: **PR 생성까지**
- push만 하면 아무 일도 일어나지 않습니다. 반드시 PR을 만들어야 합니다.
- 작업 하나 = 브랜치 하나 = PR 하나. 병합된 브랜치는 다시 쓰지 않습니다.

## 폴더 구조

| 폴더 | 용도 | 병합 방식 |
|---|---|---|
| `research/` | 개인·팀별 조사 문서 및 데이터 | 검사 통과 시 자동 병합 |
| `decisions/` | 최종 아이디어 선정, 주요 결론 문서 | 팀장 승인 후 병합 |
| `templates/` | 조사 문서 템플릿 | 검사 통과 시 자동 병합 |
| `.github/` | 자동 검사·병합 설정 | 팀장 승인 후 병합 |

⚠️ `research/`는 **레포 최상위 폴더**입니다. `.github/research/`처럼 다른 폴더 안에 만들지 마세요.

## 처음 한 번만

```bash
git clone https://github.com/lg-ax-practial-project/data-research.git
cd data-research
```

## 작업할 때마다

### 1. main 최신화 후 새 브랜치 만들기

```bash
git switch main
git pull
git switch -c research/주제명
```

브랜치 이름 예: `research/air-purifier-reviews`, `research/fridge-community`

### 2. 템플릿 복사해서 작성

`templates/research-template.md`를 `research/` 폴더에 복사한 뒤 이름을 바꿔 작성합니다.

```powershell
# Windows PowerShell
Copy-Item templates\research-template.md research\air-purifier-reviews.md
```

```bash
# Mac / Git Bash
cp templates/research-template.md research/air-purifier-reviews.md
```

- `조사일:`, `출처:` 항목은 **반드시 실제 값으로 채웁니다.** (없으면 검사 실패)
- 데이터 파일(csv, xlsx, 이미지 등)도 `research/` 아래에 둡니다.

### 3. 올라갈 파일 확인 후 commit, push

```bash
git status
```

`research/...` 경로의 내 파일만 보이는지 확인합니다. 모르는 파일(`desktop.ini`, `~$파일.xlsx` 등)이 보이면 올리지 마세요.

```bash
git add research/
git commit -m "docs: 공기청정기 고객 리뷰 조사"
git push -u origin research/주제명
```

### 4. GitHub에서 PR 만들기

1. 레포 페이지 상단의 노란 배너 **Compare & pull request** 클릭
2. `base: main` ← `compare: research/주제명` 확인
3. 제목 확인 (아래 제목 규칙)
4. **Create pull request** 클릭 (▼ 눌러서 Draft로 만들지 않기)

### 5. 기다리기

- 1분 안에 보라색 **Merged**로 바뀌면 끝입니다. 브랜치도 자동으로 삭제됩니다.
- 빨간 ❌가 뜨면 아래 "검사 실패 시"를 보세요.

### 6. 내 컴퓨터 정리

```bash
git switch main
git pull
git fetch --prune
git branch -D research/주제명
```

다음 작업은 다시 1번부터 새 브랜치로 시작합니다.

## PR 제목 규칙

Squash Merge 시 PR 제목이 `main`의 커밋 메시지가 됩니다.

형식: **`종류: 내용`** — 콜론(`:`) 뒤에 **한 칸 띄우기 필수**

| 종류 | 용도 |
|---|---|
| `docs:` | 문서 및 조사 결과 추가 |
| `data:` | 수집 데이터 추가 및 수정 |
| `fix:` | 잘못된 자료 수정 |
| `chore:` | 폴더 구조 및 설정 변경 |

- ✅ `docs: 공기청정기 고객 리뷰 조사`
- ❌ `docs:공기청정기 고객 리뷰 조사` (띄어쓰기 없음)
- ❌ `공기청정기 리뷰 조사` (종류 없음)

## 자동 검사 항목

- PR 제목 형식
- 허용 확장자: md, txt, csv, json, pdf, xlsx, png, jpg, jpeg
- 파일당 20MB 이하
- `research/`의 Markdown 문서에 `출처:`, `조사일:` 기재

## 검사 실패 시

1. PR 화면의 ❌ `validate-research` 클릭 → 로그에서 `Error:` 줄 확인
2. 원인별 해결

| 로그 메시지 | 해결 |
|---|---|
| `PR 제목 형식 오류` | PR 제목 옆 ✏️ 눌러 수정 (push 필요 없음, 자동 재검사) |
| `허용되지 않은 파일` | 해당 파일 `git rm` 후 commit, push |
| `출처: 누락` / `조사일: 누락` | 문서에 항목 추가 후 commit, push |
| `20MB 초과` | 파일 삭제 후 외부 저장소 링크로 대체 |

3. **같은 브랜치에 다시 push**하면 기존 PR이 자동으로 재검사됩니다. PR을 새로 만들지 마세요.

## 사람 검토가 필요한 경우

- `decisions/`, `.github/` 변경은 검사를 통과해도 **팀장 승인 후 병합**됩니다. PR을 올려두고 기다리면 됩니다.
- 그 밖에 검토가 필요한 PR에는 `needs-review` 라벨을 붙이면 자동 병합에서 제외됩니다.

## 금지 사항

- `main` 직접 push (막혀 있음)
- 다른 사람의 브랜치 수정·삭제
- 개인정보, 인증정보(API 키, 비밀번호), 재배포가 제한된 원본 데이터 업로드
- 대용량 데이터 업로드 → 외부 저장소에 보관하고 링크와 수집 방법만 기록