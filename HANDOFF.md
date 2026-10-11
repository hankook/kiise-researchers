# 인수인계 메모 — 신진연구자 프로필 브로셔

> 이 문서는 작업 내용을 **새 git 저장소로 옮기고 이어서 작업**하기 위한 기록입니다.
> 이전이 끝나면 이 파일은 새 저장소 루트에 두거나, 내용을 `README.md` / `OPERATIONS.md` 로
> 흡수시킨 뒤 삭제해도 됩니다.
>
> 작성: 2026-10-09 / 대상: 한국정보과학회 미디어홍보위원회

---

## 1. 프로젝트 개요

**목적** — 한국정보과학회 "신진연구자 커뮤니티 활성화" 사업. 신진연구자 프로필을 모아
브로셔를 만들되, **모바일 열람과 키워드 검색이 가능하도록 웹으로 구축**한다.

**출발점** — 원래는 구글 폼(또는 PPT)으로 수집 → 1인 1페이지 PDF → 묶어서 브로셔.
이 방식은 모바일 열람과 검색이 불가능해 웹으로 전환했다.
**PDF를 버린 것이 아니라**, 웹 페이지에서 인쇄하면 기존 템플릿과 같은 A4 1면 PDF가
그대로 나오도록 만들어 두 요구를 모두 충족시켰다.

**원본 디자인 기준** — `정보과학회 프로필.pptx` / `.pdf` (A4 세로, 네이비 `#002060`,
KoPub Dotum). 이 두 파일은 새 저장소에도 `reference/` 등으로 함께 옮기는 것을 권장한다.

---

## 2. 현재 구현 상태 (모두 동작 확인 완료)

```
2026 정보과학회 미디어홍보위원회/
├── 정보과학회 프로필.pdf / .pptx     원본 템플릿 (디자인 기준)
├── OPERATIONS.md                     운영 가이드 ★ 위원회 공유용
├── HANDOFF.md                        이 문서
├── .gitignore                        CSV·bak 제외 (개인정보 보호)
├── inbox/                            ★ 담당자가 양식·사진을 올리는 곳 (README.md = 담당자 안내)
├── .github/
│   ├── workflows/deploy.yml          main 변경 시 inbox 반영 → 검증 → 커밋 → Pages 배포
│   ├── workflows/validate.yml        PR 검증 (inbox 는 --dry-run)
│   ├── pull_request_template.md      PR 체크리스트
│   └── ISSUE_TEMPLATE/config.yml     이슈 대신 등록 안내·메일로 안내
└── profiles-web/                     ★ 사이트 본체 (Pages 배포 대상)
    ├── index.html                    검색 가능한 목록
    ├── profile.html                  개인 프로필 (?id=슬러그)
    ├── submit.html                   등록 안내 + 양식 내려받기 + 항목 설명
    ├── README.md                     개발·데이터 관리 문서
    ├── assets/css/{main,index,profile}.css
    ├── assets/js/{data,index,profile}.js
    ├── data/researchers.json         ★ 원본 데이터
    ├── data/researchers.js           자동 생성 폴백 (직접 수정 금지)
    ├── data/societies.json           소사이어티·연구회 목록 (※ 예시, 교체 필요)
    ├── assets/profile-form.xlsx      교수님용 등록 양식 (자동 생성 — 직접 수정 금지)
    ├── photos/ figures/              사진·그림
    └── tools/build.py, xlsx.py       inbox 반영 / 동기화 / 검증, 표준 라이브러리 xlsx 읽기·쓰기
```

의존성 없음. Node·번들러 불필요. Python 3 표준 라이브러리만 사용.
사진 축소에만 Pillow 를 쓰며, GitHub Actions 에서 설치한다 (로컬에 없으면 원본을 그대로 복사).

### 구현된 기능
- **목록**: 전문 검색(이름·소속·키워드·학회·연구내용), 초성 검색(`ㄱㅈㅂ`),
  키워드 다중 필터(AND), 소사이어티 필터, 소속 필터, 정렬 3종, URL 해시 상태 공유
- **프로필**: 모바일 1단 / PC 2단(좌측 고정) / 인쇄 A4 1단, 인쇄·링크복사 버튼,
  이전·다음 이동, 키워드 클릭 시 필터된 목록으로 이동
- **도구**: inbox 반영(`ingest`), 동기화(`sync` — researchers.js + 등록 양식), 데이터 검증(`check --strict`)
- **운영**: 교수님이 양식(xlsx)+사진을 기관 메일로 제출 → 담당자가 본인 확인 후 GitHub 웹에서 `inbox/` 에 업로드
  → Actions 가 양식 검사·사진 축소·`researchers.json` 반영·커밋 → Pages 배포.
  수정은 같은 E-mail 로 다시 보낸 양식을 올리면 되고, 비공개·삭제는 `inbox/요청.txt`.
  (`ingest` 는 openpyxl 로 엑셀처럼 저장한 양식, CP949 CSV, 실제 이미지로 시험함.
  GitHub Actions 위에서는 아직 돌려 보지 않음 — 저장소를 만든 뒤 7장 마지막 항목으로 확인)

---

## 3. 데이터 스키마

`data/researchers.json` 은 아래 객체의 배열이다. 필드 순서도 이 순서로 유지 중.

| 필드 | 설명 |
|---|---|
| `id` | 주소에 쓰이는 고유 슬러그 (영문·숫자·하이픈). 영문명에서 생성 |
| `name` / `nameEn` | 성명 국문 / 영문 |
| `affiliation` / `department` / `position` | 소속 기관 / 학과 / 직위 |
| `photo` | `photos/*.jpg` 경로. `""` 이면 이름 첫 글자 표시 |
| `degree` / `appointedAt` | 최종 학위 / 최초 임용일 (`YYYY-MM`) |
| `email` / `homepage` / `links[]` | 연락처. `links` 는 `{label, url}` |
| `message` | **한마디** (120자 이내). 헤더 인용구 + 목록 카드 소개문 |
| `keywords[]` | 연구 키워드 5~10개 |
| `societies[]` | **정보과학회 소사이어티·연구회** |
| `conferences[]` | **주로 참석하는 학회** |
| `career[]` | **주요 경력** — 이력 중심 |
| `achievements[]` | **대표 논문 및 수행과제** — 실적 중심 |
| `goals[]` | 연구목표 |
| `research.body[]` / `research.figures[]` | 연구내용 문단 / 그림 `{src, caption}` |
| `collaboration[]` | 공동연구 희망분야 |
| `visible` | `false` 면 목록·검색·상세에서 즉시 제외 (데이터는 보존) |
| `updatedAt` | 최근 업데이트일 |

> `message` / `societies` / `conferences` / `achievements` / `visible` 는 위원회 피드백으로
> 2차에 추가된 필드다. 원본 PPT 템플릿에는 없다.

---

## 4. 설계 결정과 이유 (되돌리기 전에 읽을 것)

| 결정 | 이유 |
|---|---|
| **정적 사이트, 빌드 도구 없음** | 담당 간사가 매년 바뀌어도 유지보수 가능해야 함. npm 의존성은 몇 년 뒤 설치조차 안 되는 경우가 많다 |
| **서버·DB 없음** | 로그인이 없으면 계정 탈취·DB 유출·스팸 가입이 구조적으로 불가능. 학회 소규모 운영에 서버 유지보수는 과함 |
| **JSON 원본 + JS 폴백 이중화** | `file://` 로 열면 브라우저가 `fetch`를 막는다. 담당자가 파일을 더블클릭해도 동작해야 해서 `researchers.js`(= `window.RESEARCHERS`)를 자동 생성해 둠 |
| **제출은 메일(양식 xlsx + 사진), 반영은 inbox 업로드 + Actions** | 교수님께 GitHub·웹 폼 로그인을 요구하지 않고, 기관 메일로 오는 것 자체가 본인 확인이 된다. 담당 간사가 매년 바뀌므로 반영도 터미널·git 없이 웹 업로드로 끝나야 하고, 구글 쪽 스크립트·토큰·트리거처럼 저장소 밖에서 관리할 것이 없어야 한다. (처음엔 구글 폼 + 담당자 CSV 변환·PR, 이어서 구글 시트 + Apps Script 를 검토했고 2026-10 에 이 방식으로 확정) |
| **inbox 업로드 = 게시 승인, `main` 직접 커밋 (1인 승인)** | 위원회가 2026-10 에 PR 리뷰 단계를 빼기로 결정. 잘못된 양식은 `ingest` 가 거르고 `check --strict` 가 한 번 더 막는다. 2차 확인이 필요해지면 업로드를 PR 로 받으면 된다 (validate.yml 이 inbox 를 --dry-run) |
| **세로형 양식 (A열 항목 / B열 내용)** | 가로 한 줄 25칸은 작성하기 어렵고, 여러 줄 항목에 셀 안 줄바꿈(Alt+Enter)을 요구하게 된다. 세로형은 칸 하나에 항목 하나, 모자라면 행 삽입 |
| **양식은 `FORM` 정의에서 자동 생성** | 양식 파일과 읽는 코드가 어긋나지 않도록 항목 정의를 한 곳(`build.py` 의 `FORM`)에만 둔다. 소사이어티 목록 시트도 `societies.json` 에서 만든다 |
| **누구의 프로필인지는 E-mail 로 판단** | 수정본을 보내면 새 프로필이 아니라 기존 프로필이 고쳐져야 한다. 영문 이름은 표기가 흔들려서 열쇠로 쓰기 어렵다. 이름·소속이 같은데 E-mail 이 다르면 막고 '프로필 id' 칸으로 해결 |
| **문제가 하나라도 있으면 아무것도 바꾸지 않음** | 일부만 반영되면 담당자가 무엇이 됐고 안 됐는지 추적해야 한다. 전부 아니면 전무로 두고, 고친 파일을 다시 올리면 처음부터 다시 처리 |
| **`visible: false` 로 비공개** | 신고 접수 시 삭제가 아니라 즉시 내리고 소명 후 복구. 이력이 git에 남음 |
| **인쇄를 별도 PDF가 아닌 `@media print` 로** | 데이터 한 벌로 웹·인쇄를 모두 커버. 내용 수정 시 PDF를 따로 다시 만들 필요가 없음 |

---

## 5. 함정 모음 (모르면 반드시 다시 밟는다)

1. **인쇄할 때 모바일 미디어쿼리가 같이 적용된다.**
   A4 인쇄 폭이 약 794px이라 `@media (max-width: 960px)` 규칙이 인쇄에도 걸린다.
   `profile.css` 의 `@media print` 블록에서 해당 속성들을 명시적으로 되돌리고 있다
   (`.pf-head__facts { border-top: 0; padding-top: 0; ... }`). 모바일 규칙을 손대면
   **반드시 인쇄 레이아웃도 다시 확인**할 것.

2. **A4 1면 한계는 약 1035px** (96dpi, 여백 11/12mm 기준).
   현재 예시 6명은 962~1015px로 간신히 들어간다. 섹션이나 그림을 추가하면 넘친다.
   확인 방법: 브라우저에서 `profile.css` 의 `@media print` 블록을 `@media screen` 으로
   바꿔 주입하고 `body` 를 794px로 고정한 뒤 `document.body` 높이를 재면 된다.

3. **`researchers.json` 을 고치면 반드시 `python3 tools/build.py sync`.**
   잊으면 `file://` 로 열었을 때만 옛 내용이 보여서 원인을 찾기 어렵다.
   `check` 가 이 불일치를 잡아 주고, CI에서도 막는다.

4. **KoPub 돋움은 쓸 만한 웹폰트 CDN이 없다.**
   jsDelivr의 알려진 경로 3곳을 확인했으나 모두 404. 현재는
   "로컬에 설치돼 있으면 사용 → Pretendard(CDN) → 시스템 고딕" 순으로 폴백한다.
   원본과 완전히 같게 하려면 학회 서버에 폰트를 올리고 `main.css` 에 `@font-face` 추가.

5. **인쇄 시 "배경 그래픽" 옵션을 켜야** 네이비 섹션 바가 나온다. 안내문에 명시해 둠.

6. **개발 중 브라우저 캐시에 반복적으로 속는다.** CSS·JS를 고쳤는데 반영이 안 보이면
   하드 리로드(⌘⇧R). 실제로 이 작업 중 두 번 "안 고쳐졌다"고 오판했다.

7. **키워드 칩 2줄 접기는 픽셀 계산에 의존한다.**
   칩 높이 32px + 간격 6px = `max-height: 70px`. 칩 폰트·패딩을 바꾸면 이 값도 같이 고쳐야
   칩이 반으로 잘리지 않는다.

8. **`file://` 에서 `history.replaceState` 가 막히는 브라우저가 있다.** try/catch로 감싸 둠.

9. **양식 항목 이름이 곧 열쇠다.** `ingest` 는 A열 항목 이름(글자·숫자만 비교)으로 칸을 찾는다.
   `FORM` 의 항목 이름을 바꾸면 이미 교수님들께 나간 양식을 못 읽으므로, 예전 이름을 `FORM_ALIASES` 에 남길 것.
   항목을 바꾼 뒤에는 `sync` 로 양식을 다시 만들고 `submit.html` 의 항목 표도 맞출 것.

10. **양식(`profile-form.xlsx`)은 바이트 단위로 비교된다.** `check` 가 `sync` 결과와 같은지 본다.
    그래서 zip 을 압축 없이·시각 고정으로 만든다. 엑셀로 열어 저장하면 달라지므로 직접 고치지 말 것.

11. **한국어 엑셀의 CSV 는 CP949 이고, 못 쓰는 글자는 '?' 가 된다.** `ingest` 는 UTF-8 → CP949 순으로
    읽고, 항목 이름의 특수문자는 무시한다. 그래도 내용 속 특수문자(—, 이모지)는 깨지므로 xlsx 를 권장.

12. **엑셀은 '2024-03' 을 날짜로 바꾼다.** 양식의 입력 칸은 텍스트 서식이라 괜찮지만, 다른 프로그램을
    거치면 날짜 일련번호(45352)로 올 수 있다. `norm_month` 가 되돌린다.

13. **`main` 에 "PR 필수"·"상태 체크 필수" 규칙을 켜면 반영이 멈춘다.** 담당자 업로드와 Actions 의
    반영 커밋이 `main` 에 바로 들어가야 하기 때문.

14. **Actions 의 반영 커밋은 다른 워크플로를 깨우지 않는다** (GITHUB_TOKEN 커밋의 성질). 그래서 반영·검증·
    배포를 한 워크플로(`deploy.yml`) 안에서 차례로 한다. 반영 단계를 다른 워크플로로 떼면 배포가 안 된다.

15. **inbox 에 실패한 파일이 남아 있으면 다음 업로드도 같이 실패한다.** 전부 아니면 전무이기 때문.
    담당자 안내(`inbox/README.md`)에 "필요 없는 파일은 지울 것"을 적어 둠.

16. **공개 저장소라 inbox 에 올린 양식과 원본 사진은 git 이력에 남는다.** 공개용 내용만 든 양식이라
    문제는 아니지만, 큰 사진이 쌓이면 저장소가 커진다. 사진은 1MB 안팎으로 받는 것이 좋다.

---

## 6. 위원회 피드백 반영 이력

| 피드백 | 처리 |
|---|---|
| 주로 참석하는 학회 칸 추가 | ✅ `conferences` — "학회 활동" 섹션, 검색 대상 포함 |
| 한마디 칸 추가 | ✅ `message` — 헤더 인용구 + 카드 소개문 |
| 소사이어티·연구회 정보 | ✅ `societies` — 섹션 표시 + 목록 페이지 전용 필터 |
| "주요 연구 경력 및 역량"이 너무 길어짐 | ✅ `career`(경력) / `achievements`(논문·과제)로 분리 |
| 검증 후 승인된 프로필만 게시 | ✅ 담당자가 본인 확인 후 inbox 에 올린 양식만 게시 (처음엔 PR 머지 = 승인, 2026-10 에 1인 승인으로 변경). `OPERATIONS.md` 3장 |

---

## 7. 남은 일 (새 저장소에서 이어서)

**게시 전 필수**
- [ ] `data/societies.json` 을 **학회 공식 소사이어티·연구회 목록으로 교체**
      (현재 값은 양식 확인용 예시이며 공식 목록과 대조하지 않았음 — 파일 첫 줄에 경고 있음)
- [ ] `data/researchers.json` 의 **예시 6명 삭제** (가상대학교·김정보 등)
- [ ] 접수 메일 주소 확정 → `tools/build.py` 의 `SUBMIT_EMAIL`, `submit.html` 의 `example@kiise.or.kr` 교체 후 `sync`
- [ ] `.github/ISSUE_TEMPLATE/config.yml` 의 `EXAMPLE` 주소 교체 (등록 안내 페이지, 담당자 메일)
- [ ] GitHub 에서 처음 돌려 보기: 본인 정보로 양식을 채워 `inbox/` 에 올림 → Actions ✓ → 사이트 확인
      → `inbox/요청.txt` 에 `삭제 id` 로 지움. 일부러 키워드 4개짜리를 올려 실패 Summary 도 확인
- [ ] `index.html` / `submit.html` 푸터의 문의처 교체
- [ ] 신진연구자 **자격 기준 확정** (예: 임용 7년 이내 / 만 45세 이하 — 위원회 의결 필요)

**검토 사항**
- [ ] KoPub 돋움 자체 호스팅 여부 (원본과 완전 일치 원할 경우)
- [ ] 전체 브로셔 PDF 일괄 생성 — `README.md` 5장에 Chrome 헤드리스 명령만 있고
      스크립트화는 안 되어 있음. 인원이 늘면 `tools/export_pdf.py` 로 만들 것
- [ ] 사진 규격 안내 강화 (세로 3:4, 600×800px 이상)
- [ ] 검토위원 2차 확인이 다시 필요해지면: 업로드를 PR 로 받도록 운영을 바꾼다 (`OPERATIONS.md` 3장 승인 단계).
      단 ruleset 에서 PR 필수를 켜면 Actions 의 반영 커밋도 막히므로, 그때는 `deploy.yml` 의 커밋 단계를
      ruleset 예외(bypass)로 두거나 PR 안에서 반영하도록 바꿔야 한다

---

## 8. 새 저장소로 옮기는 절차

아래는 제안 명령이다. **직접 실행해 주세요** (이 폴더 밖으로의 이동이라 대신 하지 않았습니다).

> 1)~3) 은 완료. 이후 폴더 이름을 `~/Codes/kiise-researchers` 로 바꿨고, GitHub 저장소 이름도
> `kiise-researchers` 로 한다 (Pages 주소: `https://계정.github.io/kiise-researchers/`). 남은 것은 4) 뿐.

```bash
# 1) 새 프로젝트 폴더 생성 후 내용 복사
mkdir -p ~/Codes/kiise-junior-researchers
cd "/Users/hankook/Library/CloudStorage/Dropbox/SKKU/기타/2026 정보과학회 미디어홍보위원회"
cp -R profiles-web .github .gitignore OPERATIONS.md HANDOFF.md ~/Codes/kiise-junior-researchers/

# 2) 원본 템플릿도 참고용으로 함께 (권장)
mkdir -p ~/Codes/kiise-junior-researchers/reference
cp "정보과학회 프로필.pdf" "정보과학회 프로필.pptx" ~/Codes/kiise-junior-researchers/reference/

# 3) git 초기화 & 첫 커밋
cd ~/Codes/kiise-junior-researchers
git init -b main
git add -A
git commit -m "신진연구자 프로필 브로셔 웹사이트 초기 구축"

# 4) GitHub 저장소 연결 (공개 저장소)
gh repo create kiise-researchers --public --source=. --push
```

**옮기지 않아도 되는 것**: `.claude/launch.json` (로컬 미리보기 설정, `.gitignore`에 포함됨),
`data/*.bak` (예전 CSV 가져오기 백업).

### GitHub 저장소 설정 (최초 1회)
`OPERATIONS.md` 3장 끝을 따른다. 요약:
1. Settings → Pages → Source: **GitHub Actions**
2. `main` ruleset: 삭제·강제 푸시 금지. **PR 필수·상태 체크 필수는 켜지 않음** (업로드와 Actions 반영 커밋이 main 에 바로 들어감)
3. 쓰기 권한은 미디어홍보위원회 담당자에게만 부여

### 로컬 확인
```bash
cd profiles-web && python3 -m http.server 8765   # http://localhost:8765
```

---

## 9. 문서 안내

| 문서 | 대상 | 내용 |
|---|---|---|
| `OPERATIONS.md` | **위원회·담당 간사** | 등록 메일 처리·수정·비공개 절차, 승인 정책, 개인정보, 구축 체크리스트 |
| `inbox/README.md` | **담당 간사** | 업로드 방법, 요청.txt, 실패 메시지별 조치 (GitHub 에서 inbox 폴더를 열면 보임) |
| `profiles-web/README.md` | 개발·데이터 관리자 | 폴더 구조, 실행, 데이터 추가/수정, PDF 생성, 디자인 규칙 |
| `profiles-web/submit.html` | **제출자(교수님)** | 양식 내려받기, 등록 절차 3단계, 양식 항목 설명 |
| `HANDOFF.md` | 다음 작업자 | 이 문서 — 설계 의도, 함정, 남은 일 |
