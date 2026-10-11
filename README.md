# 신진연구자 프로필 브로셔 — 운영 안내

한국정보과학회 신진연구자 프로필을 모은 웹 브로셔입니다. 검색되는 목록과 1인 1페이지 프로필이 있고,
프로필 페이지에서 인쇄하면 A4 1면 PDF가 나옵니다.

- 사이트: https://hankook.github.io/kiise-researchers/
- 등록 안내 (교수님용): https://hankook.github.io/kiise-researchers/submit.html

```
교수님   등록 안내에서 양식(xlsx)을 받아 작성 → 양식 + 사진을 소속 기관 메일로 제출
관리자   본인 확인 → 이 저장소의 inbox/ 에 첨부 파일을 올리고 Commit
자동     GitHub Actions 가 양식 검사 · 사진 축소 · 데이터 반영 · 사이트 배포 (1~2분)
```

**inbox 에 올리는 것이 곧 게시 승인입니다.** 공개 저장소라 올리는 순간 누구나 볼 수 있으니,
확인이 끝난 첨부만 올리세요.

---

## 1. 등록 메일 처리

### 확인할 것
- 메일이 **소속 기관 도메인**(`@*.ac.kr`, `@*.re.kr` 등)에서 왔다
- 성명·소속·직위가 **학과 홈페이지 교원 목록**과 맞다
- 신진연구자 등록 기준에 맞다
- 비방·광고·정치적 주장, 제3자의 개인정보가 없다. 사진이 본인 사진이다

양식에 '필수'로 표시된 항목, 키워드 개수(3~5개), 대표 논문·수행과제·연구목표 및 내용 개수(각 최대 5개),
인사말 길이(120자), 소사이어티 표기, 공개 동의, 사진 형식은 자동으로 검사합니다.

### 올리기
1. 메일의 양식과 사진(그림)을 내려받습니다.
2. 저장소의 **`inbox` 폴더 → Add file → Upload files** → 파일을 끌어다 놓고 **Commit changes**
3. **Actions** 탭에서 `프로필 반영 및 배포` 가 초록색 ✓ 이 되면 사이트에서 확인하고 교수님께 회신합니다.

**한 번에 한 분씩** 올리면 양식과 사진을 자동으로 짝짓습니다.
여러 분을 한꺼번에 올리려면 사람별 폴더에 넣어 폴더째 올리거나, 각 양식의 '사진 파일명' 칸이
첨부 파일 이름과 맞아야 합니다.

## 2. 수정 요청

고친 양식을 1번과 똑같이 올립니다. 양식의 **E-mail 이 같은 프로필**을 찾아 고치므로 주소는 바뀌지 않습니다.
사진을 다시 보내지 않으셨으면 양식에 사진 파일명이 적혀 있어도 기존 사진이 유지됩니다 (그림도 같음).

## 3. 비공개 · 공개 · 삭제

`inbox` 에서 **Add file → Create new file** 로 `요청.txt` 를 만들고 한 줄에 하나씩 적어 Commit 합니다.

```
비공개 kim-jeongbo
공개 kim-jeongbo
삭제 kim-jeongbo
```

프로필 id 는 사이트 주소 `profile.html?id=…` 의 값입니다 (성명으로 적어도 되지만 동명이인이 있으면 id).

- **비공개** — 사이트에서만 내리고 내용은 남깁니다. 신고가 들어오면 먼저 비공개 → 사실 확인 → 공개 또는 삭제.
- **삭제** — 데이터와 사진을 지웁니다 (게시 동의 철회 등). git 이력에는 남습니다.

## 4. 실패했을 때

Actions 가 빨간색 ✗ 이면 **아무것도 바뀌지 않은** 상태입니다. 실패한 실행의 **Summary** 에 파일별 이유가 나옵니다.
고친 파일을 **같은 이름으로** 다시 올리면 자동으로 다시 시도합니다.
실패한 파일이 inbox 에 남아 있으면 다음 업로드도 함께 막히니, 필요 없는 파일은 지웁니다 (파일 열기 → ⋯ → Delete file).

| 메시지 | 조치 |
|---|---|
| 연구 키워드 N개 / 대표 논문 N개 / 인사말 N자 / ○○ 없음 | 양식 보완 요청 |
| 공식 목록에 없는 소사이어티·연구회 | 양식의 '소사이어티 목록' 시트에 있는 이름 그대로 |
| '공개 동의' 칸에 '동의'가 없습니다 | 동의 없이는 게시하지 않음. 교수님께 확인 |
| 어느 양식의 이미지인지 알 수 없습니다 | 한 분씩 올리거나 사람별 폴더에, 또는 '사진 파일명' 칸 확인 |
| 이미지를 열 수 없습니다 | JPG·PNG 로 다시 요청 |
| 이름·소속이 같은 프로필(○○)이 이미 있는데 E-mail 이 다릅니다 | 같은 분이면 양식의 '프로필 id' 칸에 그 id, 다른 분이면 새 id 를 적어 다시 올림 |
| 예전 엑셀 형식(.xls) | xlsx 로 저장해서 다시 |

## 5. 가끔 하는 일

아래는 저장소 파일을 고치는 일입니다. 고친 뒤 `main` 에 올리면 배포 때 양식도 자동으로 다시 만들어집니다.

| 할 일 | 고칠 곳 |
|---|---|
| 접수 메일 주소 변경 | `tools/build.py` 의 `SUBMIT_EMAIL` (양식 안내문), `profiles-web/submit.html` 의 메일 주소 |
| 소사이어티·연구회 목록 변경 | `profiles-web/data/societies.json` (양식의 목록 시트와 표기 검사에 쓰임) |
| 키워드 개수 기준 변경 | `tools/build.py` 의 `KEYWORDS_MIN, KEYWORDS_MAX` 와 `submit.html` 안내 |
| 양식 항목·필수 여부 변경 | `tools/build.py` 의 `FORM` 과 `submit.html` 의 항목 표 |
| 관리자 교체 | 저장소 Settings → Collaborators 에서 쓰기 권한 추가·회수 |

로컬에서 확인하려면 (Python 3, 저장소 루트에서):

```bash
python3 tools/build.py ingest --dry-run      # inbox 검사만
python3 tools/build.py check                 # 데이터 점검
python3 -m http.server -d profiles-web 8765  # http://localhost:8765
```

## 6. 저장소 설정 (처음 한 번)

- Settings → Pages → Source: **GitHub Actions**
- Settings → Rules → Rulesets → `main`: *Restrict deletions*, *Block force pushes* 만 켭니다.
  **PR 필수·상태 체크 필수는 켜지 마세요.** 업로드와 Actions 의 반영 커밋이 `main` 에 바로 들어가야 합니다.
- Settings → General → Features 에서 **Issues 끄기** (등록은 메일로만 받습니다)
- 쓰기 권한은 담당자에게만

### 운영 전에 남은 일
- [ ] 접수 메일 주소 확정 (5장)
- [ ] `societies.json` 을 학회 공식 소사이어티·연구회 목록으로 교체 (지금은 예시)
- [ ] 예시 프로필 6명(가상대학교 등) 삭제 — `요청.txt` 에 `삭제 kim-jeongbo` 등
- [ ] 신진연구자 등록 기준 확정 (예: 임용 7년 이내 — 위원회 의결)

## 폴더

```
inbox/          관리자가 양식·사진·요청.txt 를 올리는 곳 (처리 후 비워짐)
profiles-web/   사이트 (이 폴더만 배포됨)
  data/         researchers.json (프로필 데이터), societies.json (소사이어티 목록)
  photos/ figures/   사진·그림 (자동 저장)
  assets/       CSS·JS, profile-form.xlsx (등록 양식, 자동 생성 — 직접 수정 금지)
tools/          build.py (inbox 반영·양식 생성·점검), xlsx.py
.github/workflows/deploy.yml   반영 → 점검 → 커밋 → 배포
```
