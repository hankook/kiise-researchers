# 한국정보과학회 신진연구자 프로필 브로셔 (웹)

기존 PPT/PDF 템플릿(`정보과학회 프로필.pptx`)의 항목과 디자인을 그대로 웹으로 옮긴
정적(static) 사이트입니다. 서버·데이터베이스·빌드 도구 없이 **HTML/CSS/JS 파일만으로** 동작합니다.

* **모바일** — 1단 세로 배치, 큰 터치 영역
* **PC** — 좌측 고정 프로필 + 우측 본문 2단 배치
* **인쇄/PDF** — 브라우저의 `인쇄 / PDF 저장` 버튼 한 번으로 기존 브로셔와 동일한 **A4 세로 1면** PDF 생성
* **검색** — 이름·소속·키워드·학회·연구내용 전문 검색, 초성 검색(`ㄱㅈㅂ`), 키워드 다중 필터,
  소사이어티·연구회 필터
* **운영** — 서버/DB 없이 메일로 받은 양식을 `inbox/` 에 올리면 Actions 가 반영 → Pages 배포 (→ 저장소 루트의 `OPERATIONS.md`)

---

## 1. 폴더 구성

```
profiles-web/
├── index.html              검색 가능한 연구자 목록 (브로셔 표지 역할)
├── profile.html            연구자 1인 프로필 (?id=연구자ID)
├── submit.html             프로필 등록 안내 / 양식 항목 설명
├── data/
│   ├── researchers.json    ★ 원본 데이터 (여기만 고치면 됩니다)
│   ├── societies.json      소사이어티·연구회 공식 목록 (표기 검증용)
│   └── researchers.js      자동 생성 — file:// 로 열 때 쓰는 폴백
├── photos/                 연구자 사진 (세로 3:4 권장)
├── figures/                연구내용 그림
├── assets/css, assets/js   디자인·동작
├── assets/profile-form.xlsx  자동 생성 — 교수님용 등록 양식 (submit.html 에서 내려받기)
└── tools/
    ├── build.py            inbox 반영(ingest), 동기화(sync), 점검(check)
    └── xlsx.py             xlsx 읽기·쓰기 (표준 라이브러리만)
```

## 2. 실행 방법

### 가장 간단한 방법 — 파일을 그대로 열기
`index.html` 을 더블클릭하면 바로 열립니다. (`data/researchers.js` 폴백 덕분에 동작)

### 권장 — 로컬 서버로 확인
```bash
cd profiles-web
python3 -m http.server 8765
# 브라우저에서 http://localhost:8765 접속
```

### 배포
GitHub Pages, 학회 웹서버 등 **정적 호스팅 어디에나** 폴더째 올리면 됩니다.
별도의 서버 구성이 필요 없습니다.

## 3. 연구자 추가·수정하기

### 방법 A — 등록 양식을 inbox 에 올리기 (평소)
교수님이 메일로 보낸 양식(xlsx)과 사진을 저장소 루트의 `inbox/` 에 올리면 GitHub Actions 가
`build.py ingest` 로 반영하고 배포합니다. 이 폴더의 파일을 손댈 일이 없습니다.
담당자용 안내는 `inbox/README.md`, 운영 절차는 `OPERATIONS.md` 2장.

로컬에서 미리 돌려 보려면:
```bash
pip install pillow            # 사진 축소용 (없으면 원본을 그대로 복사)
python3 tools/build.py ingest ../inbox --dry-run   # 검사만
python3 tools/build.py ingest ../inbox             # 반영 (처리한 파일은 inbox 에서 지움)
```

* 양식은 **세로형**입니다. A열 항목 이름 / B열 내용, A열이 빈 행은 바로 위 항목에 이어 붙습니다.
  항목 정의는 `tools/build.py` 의 `FORM` 하나뿐이고, 양식 파일(`assets/profile-form.xlsx`)은
  `sync` 가 이 정의와 `societies.json` 으로 만듭니다. 항목 이름을 바꾸면 이미 나간 양식을 못 읽으므로
  예전 이름을 `FORM_ALIASES` 에 남기세요.
* 누구의 프로필인지는 양식의 **E-mail** 로 찾습니다 (같으면 수정, 없으면 신규). 양식의 '프로필 id' 칸이
  채워져 있으면 그 id 를 씁니다.
* 사진은 `photos/<id>.jpg`(긴 변 1000px), 그림은 `figures/<id>-1.png|jpg`(긴 변 1600px)로 저장됩니다.
  양식에 사진·그림이 없으면 기존 파일을 유지합니다.
* 하나라도 문제가 있으면 아무것도 바꾸지 않고 종료 코드 1 로 끝납니다.

### 방법 C — JSON 직접 편집
`data/researchers.json` 에 아래 형식으로 항목을 추가한 뒤, **반드시** 동기화 명령을 실행합니다.
(GitHub 웹에서 고쳐 main 에 커밋한 경우에는 배포 때 자동으로 동기화됩니다)
```bash
python3 tools/build.py sync
```

```json
{
  "id": "kim-jeongbo",                       // 주소에 쓰이는 고유 ID (영문/숫자/하이픈)
  "name": "김정보",
  "nameEn": "Jeongbo Kim",
  "affiliation": "○○대학교",
  "department": "컴퓨터공학과",
  "position": "조교수",
  "photo": "photos/kim-jeongbo.jpg",         // 없으면 "" (이름 첫 글자가 표시됨)
  "degree": "○○대학교 공학박사 (인공지능)",
  "appointedAt": "2024-03",
  "email": "abcde123@xxx.ac.kr",
  "homepage": "https://example.ac.kr/~jbkim",
  "links": [{ "label": "Google Scholar", "url": "https://scholar.google.com/" }],
  "message": "데이터는 있는데 정답이 없다면 언제든 연락 주세요.",   // 한마디 (120자 이내)
  "keywords": ["기계학습", "표현학습", "..."],   // 5~10개 권장
  "societies": ["인공지능 소사이어티"],          // 정보과학회 소사이어티·연구회
  "conferences": ["NeurIPS", "ICML"],         // 주로 참석하는 학회
  "career": ["항목1", "항목2"],                // 주요 경력 — 이력 중심 (불릿)
  "achievements": ["항목1", "항목2"],           // 대표 논문 및 수행과제 — 실적 중심 (불릿)
  "goals": ["항목1", "항목2"],                 // 연구목표 (불릿)
  "research": {
    "body": ["문단1", "문단2"],                // 연구내용 (문단)
    "figures": [{ "src": "figures/x.png", "caption": "설명" }]
  },
  "collaboration": ["항목1", "항목2"],          // 공동연구 희망분야 (불릿)
  "visible": true,                            // false 로 두면 즉시 비공개 (데이터는 보존)
  "updatedAt": "2026-09-01"                   // 최근 업데이트일
}
```

`societies` 에 쓸 수 있는 값은 `data/societies.json` 에 정리되어 있습니다.
**이 파일은 예시 목록이므로 학회 공식 목록으로 교체한 뒤 운영하세요.**
목록에 없는 이름을 쓰면 `check` 가 경고합니다.

> `researchers.json` 이 원본이고 `researchers.js` 는 그 복사본입니다.
> JSON만 고치고 `sync` 를 잊으면, 파일을 직접 열었을 때 예전 내용이 보입니다.

### 데이터 점검
```bash
python3 tools/build.py check          # 사람이 보기 위한 점검
python3 tools/build.py check --strict # 문제가 있으면 종료 코드 1 (GitHub Actions 용)
```
필수 항목 누락, ID 중복, 키워드 개수(5~10개 권장), 한마디 길이, 소사이어티 표기,
사진·그림 파일 존재 여부, `researchers.js`·등록 양식 동기화 여부를 확인합니다.

### 특정 프로필만 임시로 내리기
평소에는 `inbox/요청.txt` 에 `비공개 프로필id` 라고 적어 올리면 됩니다.
직접 고칠 때는 삭제하지 말고 해당 항목에 `"visible": false` 를 넣은 뒤 `sync` 하세요.
목록·검색·상세에서 즉시 사라지고, 내용은 저장소에 남습니다.

## 4. PDF 브로셔 만들기

* **개인 1장** : 프로필 페이지 → `인쇄 / PDF 저장` → 대상 "PDF로 저장", 용지 A4, 배율 100%,
  여백 "기본", **배경 그래픽 인쇄 켜기** (네이비 제목 바가 인쇄되도록).
* 그림을 2장 넣거나 본문이 길면 2면으로 넘어갑니다. 1면에 맞추려면 각 항목을 3~5줄로 유지하고
  그림은 1장만 넣어 주세요. (섹션은 중간에서 잘리지 않고 통째로 다음 면으로 넘어갑니다.)
* **전체 브로셔** : 각 프로필을 PDF로 저장한 뒤 합치거나, 아래처럼 일괄 생성할 수 있습니다.
  ```bash
  # 예: Chrome 헤드리스로 전체 PDF 일괄 생성 (macOS)
  python3 -m http.server 8765 &
  for id in $(python3 -c "import json;print(' '.join(r['id'] for r in json.load(open('data/researchers.json'))))"); do
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
      --headless --disable-gpu --no-pdf-header-footer \
      --print-to-pdf="pdf/$id.pdf" "http://localhost:8765/profile.html?id=$id"
  done
  ```
  생성된 PDF들은 `Preview`, `pdfunite`, `qpdf` 등으로 한 권으로 병합합니다.

## 5. 디자인 규칙

| 항목 | 값 |
|---|---|
| 기준 색 | 네이비 `#002060` (원본 템플릿 RGB 0, 32, 96) |
| 본문 글꼴 | KoPub Dotum (설치되어 있으면 우선 적용) → Pretendard → 시스템 고딕 |
| 인쇄 용지 | A4 세로, 여백 11mm |
| 섹션 | 연구 키워드 / 학회 활동 / 주요 경력 / 대표 논문 및 수행과제 / 연구목표 / 연구내용 / 공동연구 희망분야 |

* KoPub 돋움은 웹폰트 CDN이 없어 링크하지 않았습니다. 학회 서버에 폰트 파일을 올려 사용하려면
  `assets/css/main.css` 상단에 `@font-face` 를 추가하면 됩니다.
  (다운로드: https://www.kopus.org/biz-electronic-font2-2/)
* 색을 바꾸려면 `assets/css/main.css` 의 `:root` 변수만 수정하면 전체에 반영됩니다.

## 6. 현재 데이터에 대해

`data/researchers.json` 에 들어 있는 6명은 **레이아웃 확인용 가상 예시**입니다.
실제 데이터를 넣기 전에 삭제하거나 덮어써 주세요.


## 7. 운영 (등록 → 검증 → 승인 → 배포)

저장소 루트의 **`OPERATIONS.md`** 에 정리되어 있습니다. 요약하면:

1. 교수님은 **등록 양식(xlsx) + 사진**을 소속 기관 메일로 제출 (GitHub 계정 불필요)
2. 담당자가 본인 확인 후 GitHub 웹에서 `inbox/` 에 끌어다 놓고 Commit
3. GitHub Actions 가 양식 검사·사진 축소 후 `researchers.json` 에 반영하고 커밋
4. `check --strict` 통과 시 GitHub Pages 로 자동 배포

관련 파일: `inbox/README.md`(담당자 안내), `.github/workflows/deploy.yml`(반영·검증·배포),
`.github/workflows/validate.yml`(PR 검증), `.github/pull_request_template.md`.
