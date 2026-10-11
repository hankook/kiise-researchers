#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국정보과학회 신진연구자 프로필 브로셔 — 데이터 도구 (저장소 루트에서 실행)

  python3 tools/build.py ingest [--dry-run]
      inbox/ 에 올라온 등록 양식(xlsx·csv)·사진·요청(txt)을 반영합니다.
        - 양식 → profiles-web/data/researchers.json 에 추가. E-mail 이 같은 프로필이 있으면 그 프로필을 고칩니다.
        - 사진·그림 → 크기를 줄여 photos/ , figures/ 에 저장 (Pillow 필요. 없으면 원본을 그대로 복사)
        - 요청 txt → 한 줄에 하나씩 "비공개 프로필id" / "공개 프로필id" / "삭제 프로필id"
      처리한 파일은 inbox 에서 지웁니다. 문제가 하나라도 있으면 아무것도 바꾸지 않고
      이유를 출력한 뒤 종료 코드 1 을 반환합니다. --dry-run 은 검사만 합니다.
      평소에는 GitHub Actions(deploy.yml)가 main 에 파일이 올라올 때마다 실행합니다.

  python3 tools/build.py sync
      아래 FORM 정의 + data/societies.json → assets/profile-form.xlsx (교수님용 등록 양식)

  python3 tools/build.py check [--strict]
      필수 항목, id 중복·형식, 키워드·논문·과제·연구내용 개수, 인사말 길이, 소사이어티 표기,
      사진·그림 파일, 등록 양식 최신 여부를 점검합니다. --strict 면 문제가 있을 때 종료 코드 1.
"""
import csv
import io
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsx  # noqa: E402  (같은 폴더의 표준 라이브러리 기반 xlsx 읽기·쓰기)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(REPO, "inbox")
ROOT = os.path.join(REPO, "profiles-web")      # 배포되는 사이트 폴더. 사진·그림 경로의 기준
JSON_PATH = os.path.join(ROOT, "data", "researchers.json")
SOCIETIES_PATH = os.path.join(ROOT, "data", "societies.json")
FORM_PATH = os.path.join(ROOT, "assets", "profile-form.xlsx")
KST = timezone(timedelta(hours=9))

# ※ 실제 접수 메일로 바꾼 뒤 `python3 tools/build.py sync` — 등록 양식 안내문에 들어갑니다.
SUBMIT_EMAIL = "example@kiise.or.kr"

KEYWORDS_MIN, KEYWORDS_MAX = 3, 5   # 연구 키워드 개수
MAX_ITEMS = 5        # 대표 논문 · 수행과제 · 연구목표 및 내용 최대 개수
MESSAGE_MAX = 120    # 인사말 글자 수
PHOTO_SIZE = 1000    # 사진 긴 변 최대 px
FIGURE_SIZE = 1600   # 연구내용 그림 긴 변 최대 px
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# 등록 양식(세로형). 양식 생성 · 읽기 · 필수 항목 검사가 모두 이 정의를 씁니다.
#   (키, 항목 이름, 구분, 입력 칸 수, 안내)   구분: 필수 / 선택 / 담당자
# 항목은 이름으로 찾으므로, 이름을 바꾸면 이미 나간 양식은 그 항목을 못 읽습니다.
FORM = [
    ("name",        "성명(국문)",        "필수", 1, "예) 김정보"),
    ("nameEn",      "성명(영문)",        "필수", 1, "예) Jeongbo Kim — 프로필 주소를 만드는 데 쓰입니다"),
    ("affiliation", "소속 기관",         "필수", 1, "예) ○○대학교"),
    ("department",  "소속 학과/학부",     "선택", 1, "예) 컴퓨터공학과"),
    ("position",    "직위",             "필수", 1, "목록에서 고르거나 직접 입력"),
    ("degree",      "최종 학위",         "필수", 1, "예) ○○대학교 공학박사 (인공지능)"),
    ("appointedAt", "최초 임용일",       "필수", 1, "예) 2024-03"),
    ("email",       "E-mail",          "필수", 1, "프로필에 공개되는 연락처. 수정 양식을 보내실 때도 같은 주소로 적어 주세요"),
    ("homepage",    "연구실 홈페이지",    "선택", 1, ""),
    ("links",       "추가 링크",         "선택", 3, "칸 하나에 하나, 라벨|주소  예) Google Scholar|https://scholar.google.com/…"),
    ("keywords",    "연구 키워드",       "필수", 1, "쉼표로 구분, %d~%d개  예) 기계학습, 표현학습, 멀티모달" % (KEYWORDS_MIN, KEYWORDS_MAX)),
    ("societies",   "소사이어티·연구회",  "선택", 1, "정보과학회 내 소속. '소사이어티 목록' 시트의 이름 그대로, 쉼표로 구분"),
    ("message",     "인사말",           "선택", 1, "동료 연구자들께 전하는 인사, %d자 이내" % MESSAGE_MAX),
    ("career",      "주요 경력",         "필수", 5, "현 직위, 이전 소속, 학위 등. 칸 하나에 하나, 모자라면 아래에 행 삽입"),
    ("papers",      "대표 논문",         "선택", MAX_ITEMS, "칸 하나에 한 편, 최대 %d편" % MAX_ITEMS),
    ("projects",    "수행과제",          "선택", MAX_ITEMS, "칸 하나에 한 건, 최대 %d건" % MAX_ITEMS),
    ("research",    "연구목표 및 내용",   "필수", MAX_ITEMS, "칸 하나에 한 문단, 최대 %d개" % MAX_ITEMS),
    ("photo",       "사진 파일명",       "필수", 1, "메일에 첨부한 사진의 파일 이름  예) kim.jpg — 세로 3:4, JPG·PNG"),
    ("figure",      "그림 파일명",       "선택", 1, "연구내용 그림 1장(가로형 권장)을 첨부했다면 그 파일 이름"),
    ("caption",     "그림 설명",         "선택", 1, "그림 아래에 붙는 한 줄 설명"),
    ("consent",     "공개 동의",         "필수", 1, "위 내용을 신진연구자 브로셔에 공개하는 데 동의하시면 '동의'라고 적어 주세요"),
    ("id",          "프로필 id",         "담당자", 1, "담당자용 — 비워 두세요"),
]
LABEL_OF = {key: label for key, label, _, _, _ in FORM}
REQUIRED = [key for key, _, need, _, _ in FORM if need == "필수"]
POSITIONS = ["조교수", "부교수", "교수", "연구교수", "선임연구원", "책임연구원"]
FORM_NOTE = ("노란 칸(C열)에 입력해 주세요. '필수' 항목은 꼭 채워 주시고, '선택' 항목은 비워 두셔도 됩니다.\n"
             "여러 줄 항목은 칸 하나에 하나씩 적어 주세요. 작성한 이 파일과 사진(그림)을 소속 기관 메일로 %s 에 보내 주세요.")

TABLE_EXT = {".xlsx", ".csv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
WEB_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
INBOX_IGNORE = {"readme.md", ".gitkeep"}


def log(msg=""):
    print(msg)


# ------------------------------------------------------------------ 공통 유틸
def slugify(name_en, taken):
    base = unicodedata.normalize("NFKD", (name_en or "").strip().lower()).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "researcher"
    slug, n = base, 2
    while slug in taken:
        slug, n = "%s-%d" % (base, n), n + 1
    taken.add(slug)
    return slug


def split_lines(text):
    """여러 줄/불릿 입력을 항목 리스트로 분리.
    앞에 붙은 불릿(-, •)이나 번호(1. 2))만 뗍니다. "2021.08 박사" 같은 내용은 그대로 둡니다."""
    if not text:
        return []
    out = []
    for line in re.split(r"[\r\n]+", str(text)):
        line = re.sub(r"^\s*(?:[-•·*▪●○]+\s*|\d{1,2}[.)](?!\d)\s*)", "", line).strip()
        if line:
            out.append(line)
    return out


def split_keywords(text):
    if not text:
        return []
    parts = re.split(r"[,、/|\n\r]+", str(text))
    return [p.strip().lstrip("#").strip() for p in parts if p.strip().lstrip("#").strip()]


def parse_links(text):
    """'라벨|URL' 또는 'URL' 형식을 한 줄에 하나씩."""
    links = []
    for line in split_lines(text):
        if "|" in line:
            label, url = line.split("|", 1)
        else:
            url = line
            label = "링크"
            m = re.search(r"scholar\.google|dblp|scopus|orcid|scholarworks|github", url, re.I)
            if m:
                label = {"scholar.google": "Google Scholar", "dblp": "DBLP", "scopus": "Scopus",
                         "orcid": "ORCID", "scholarworks": "Scholarworks",
                         "github": "GitHub"}[m.group(0).lower()]
        url = url.strip()
        if url.startswith("http"):
            links.append({"label": label.strip(), "url": url})
    return links


def norm_date(text):
    if not text:
        return ""
    s = str(text).strip()
    m = re.search(r"(\d{4})\D+(\d{1,2})(?:\D+(\d{1,2}))?", s)
    if not m:
        return s
    y, mo, d = m.group(1), m.group(2).zfill(2), (m.group(3) or "").zfill(2) if m.group(3) else ""
    return "-".join([p for p in (y, mo, d) if p])


def norm_month(text):
    """최초 임용일 → YYYY-MM. 엑셀이 날짜로 바꿔 버린 칸(일련번호 45352 등)도 되돌립니다."""
    s = str(text or "").strip()
    if re.fullmatch(r"\d{5}(\.0+)?", s):
        return (date(1899, 12, 30) + timedelta(days=int(float(s)))).strftime("%Y-%m")
    s = norm_date(s)
    return s[:7] if re.match(r"^\d{4}-\d{2}", s) else s


def is_local(path):
    return bool(path) and not re.match(r"^[a-z]+:", path, re.I)


def local_paths(rec):
    return [p for p in (rec.get("photo"), (rec.get("figure") or {}).get("src")) if is_local(p)]


def load_data():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def write_data(data):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def society_lists():
    if not os.path.exists(SOCIETIES_PATH):
        return [], []
    with open(SOCIETIES_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("societies", []), d.get("sigs", [])


def load_societies():
    """data/societies.json 의 공식 목록(소사이어티 + 연구회). 없으면 빈 집합."""
    societies, sigs = society_lists()
    return set(societies) | set(sigs)


def decode(raw):
    """한국어 엑셀이 저장한 CSV 는 UTF-8 이 아니라 CP949 인 경우가 많습니다."""
    for enc in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("글자 인코딩을 알 수 없습니다")


# ------------------------------------------------------------- 등록 양식 생성
def render_form():
    S = xlsx
    rows = [
        [("한국정보과학회 신진연구자 프로필 등록 양식", S.TITLE)] + [("", S.TITLE)] * 3,
        [(FORM_NOTE % SUBMIT_EMAIL, S.HINT)] + [("", S.HINT)] * 3,
        [("구분", S.HEADER), ("항목", S.HEADER), ("내용 (이 열에 입력)", S.HEADER), ("안내", S.HEADER)],
    ]
    validations = []
    for key, label, need, n, hint in FORM:
        first_row = len(rows) + 1
        mark = S.REQUIRED if need == "필수" else S.OPTIONAL
        for i in range(n):
            top = i == 0
            rows.append([(need if top else "", mark), (label if top else "", S.LABEL),
                         ("", S.INPUT), (hint if top else "", S.HINT)])
        if key == "position":
            validations.append(("C%d" % first_row, POSITIONS))
        elif key == "consent":
            validations.append(("C%d" % first_row, ["동의"]))
    profile = S.sheet_xml(rows, [7, 18, 60, 50], merges=["A1:D1", "A2:D2"], validations=validations,
                          freeze_rows=3, row_heights={1: 28, 2: 48}, input_col="C")

    societies, sigs = society_lists()
    soc_rows = [[("소사이어티", S.HEADER), ("연구회", S.HEADER)]]
    for i in range(max(len(societies), len(sigs))):
        soc_rows.append([(societies[i] if i < len(societies) else "", S.PLAIN),
                         (sigs[i] if i < len(sigs) else "", S.PLAIN)])
    soc = S.sheet_xml(soc_rows, [40, 40])
    return S.build([("프로필", profile), ("소사이어티 목록", soc)])


def cmd_sync():
    os.makedirs(os.path.dirname(FORM_PATH), exist_ok=True)
    with open(FORM_PATH, "wb") as f:
        f.write(render_form())
    log("✓ assets/profile-form.xlsx 생성 완료 (등록 양식)")


# ----------------------------------------------------------------- 점검 규칙
def record_problems(r, official):
    """레코드 한 건의 문제 목록. check 와 ingest 가 같은 기준을 씁니다.
    (사진 첨부와 공개 동의는 양식을 읽을 때만 확인)"""
    p = [LABEL_OF[k] + " 없음" for k in REQUIRED if k not in ("photo", "consent") and not r.get(k)]
    kw = r.get("keywords") or []
    if kw and not KEYWORDS_MIN <= len(kw) <= KEYWORDS_MAX:
        p.append("연구 키워드 %d개 (%d~%d개)" % (len(kw), KEYWORDS_MIN, KEYWORDS_MAX))
    for k in ("papers", "projects", "research"):
        n = len(r.get(k) or [])
        if n > MAX_ITEMS:
            p.append("%s %d개 (최대 %d개)" % (LABEL_OF[k], n, MAX_ITEMS))
    if official:
        p.extend("공식 목록에 없는 소사이어티·연구회: " + soc for soc in r.get("societies", []) if soc not in official)
    if len(r.get("message", "")) > MESSAGE_MAX:
        p.append("인사말 %d자 (%d자 이내)" % (len(r["message"]), MESSAGE_MAX))
    return p


def cmd_check(strict=False):
    data = load_data()
    problems = []

    form = open(FORM_PATH, "rb").read() if os.path.exists(FORM_PATH) else b""
    if form != render_form():
        problems.append("assets/profile-form.xlsx(등록 양식)가 최신이 아닙니다. "
                        "`python3 tools/build.py sync` 를 실행하고 함께 커밋하세요.")

    official = load_societies()
    seen = set()
    for r in data:
        rid = r.get("id", "")
        who = "%s(%s)" % (r.get("name", "?"), rid or "id 없음")
        if not rid:
            problems.append(who + ": id 가 없습니다.")
        elif rid in seen:
            problems.append(who + ": id 가 중복됩니다.")
        elif not ID_RE.match(rid):
            problems.append(who + ": id 는 영문 소문자·숫자·하이픈만 쓸 수 있습니다.")
        seen.add(rid)
        problems.extend("%s: %s" % (who, x) for x in record_problems(r, official))
        if r.get("visible") is False:
            log("  · %s 는 visible:false 로 비공개 상태입니다." % who)
        photo = r.get("photo")
        if photo and not os.path.exists(os.path.join(ROOT, photo)):
            problems.append("%s: 사진 파일 없음 → %s" % (who, photo))
        fig = (r.get("figure") or {}).get("src")
        if fig and not os.path.exists(os.path.join(ROOT, fig)):
            problems.append("%s: 그림 파일 없음 → %s" % (who, fig))

    log("총 %d명 점검" % len(data))
    if problems:
        log("⚠ 확인이 필요한 항목 %d건" % len(problems))
        for p in problems:
            log("  - " + p)
        if strict:
            sys.exit(1)
    else:
        log("✓ 문제 없음")


# ------------------------------------------------------------- 등록 양식 읽기
def norm_label(s):
    """항목 이름 비교용: 글자·숫자만 남김. 띄어쓰기·괄호·가운뎃점이 달라도, CP949 CSV 로 저장하면서
    특수문자가 '?' 로 바뀌어도 같은 항목으로 봅니다."""
    return re.sub(r"[\W_]+", "", str(s)).lower()


LABELS = {norm_label(label): key for key, label, _, _, _ in FORM}


def read_table(path):
    if path.lower().endswith(".xlsx"):
        return xlsx.read_rows(path, prefer_sheet="프로필")
    with open(path, "rb") as f:
        return list(csv.reader(io.StringIO(decode(f.read()))))


def parse_form(rows):
    """세로형 양식 → {키: [값, ...]}. 항목 이름이 있는 열을 찾아 바로 오른쪽 칸을 값으로 읽고,
    항목 칸이 빈 행은 바로 위 항목에 이어 붙입니다. 항목 이름이 거의 없으면 양식이 아니라고 보고 None."""
    col = next((i for row in rows for i, c in enumerate(row) if norm_label(c) in LABELS), None)
    if col is None:
        return None
    values, current, found = {}, None, 0
    for row in rows:
        a = str(row[col]).strip() if len(row) > col else ""
        b = str(row[col + 1]).strip() if len(row) > col + 1 else ""
        if a:
            current = LABELS.get(norm_label(a))
            found += current is not None
        if current and b:
            values.setdefault(current, []).append(b)
    return values if found >= 5 else None


def first(values, key):
    return " ".join(values.get(key, [])).strip()


def form_to_record(v, rid, today):
    every = lambda k: [x for cell in v.get(k, []) for x in split_lines(cell)]  # noqa: E731
    homepage = first(v, "homepage")
    if homepage and not re.match(r"^[a-z]+://", homepage, re.I):
        homepage = "https://" + homepage
    return {
        "id": rid,
        "name": first(v, "name"),
        "nameEn": first(v, "nameEn"),
        "affiliation": first(v, "affiliation"),
        "department": first(v, "department"),
        "position": first(v, "position"),
        "photo": "",
        "degree": first(v, "degree"),
        "appointedAt": norm_month(first(v, "appointedAt")),
        "email": first(v, "email"),
        "homepage": homepage,
        "links": [l for cell in v.get("links", []) for l in parse_links(cell)],
        "message": re.sub(r"\s+", " ", first(v, "message")),
        "keywords": split_keywords(",".join(v.get("keywords", []))),
        "societies": split_keywords(",".join(v.get("societies", []))),
        "career": every("career"),
        "papers": every("papers"),
        "projects": every("projects"),
        "research": every("research"),
        "figure": None,
        "visible": True,
        "updatedAt": today,
    }


# ------------------------------------------------------------------ 이미지
_PIL = []


def pillow():
    """Pillow 가 있으면 Image 모듈, 없으면 None. (iPhone HEIC 는 pillow-heif 가 있을 때만)"""
    if not _PIL:
        try:
            from PIL import Image
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass
            _PIL.append(Image)
        except ImportError:
            _PIL.append(None)
    return _PIL[0]


def plan_image(src, kind, rid):
    """저장할 경로(photos/… , figures/…)와 오류. 이미지는 실제로 열어 확인합니다."""
    ext = os.path.splitext(src)[1].lower()
    Image = pillow()
    if Image:
        try:
            with Image.open(src) as im:
                im.load()
                fmt = im.format
        except Exception:
            return None, "이미지를 열 수 없습니다. JPG·PNG 로 다시 보내 달라고 요청하세요"
        out_ext = ".png" if kind == "figure" and fmt == "PNG" else ".jpg"
    else:
        if ext not in WEB_IMAGE_EXT:
            return None, "Pillow 가 없어 %s 를 변환할 수 없습니다 (GitHub Actions 에서는 자동 설치됨)" % ext
        if os.path.getsize(src) > 3 * 1024 * 1024:
            return None, "Pillow 가 없어 3MB 넘는 이미지를 줄일 수 없습니다 (GitHub Actions 에서는 자동 설치됨)"
        out_ext = ".jpg" if ext == ".jpeg" else ext
    return "%s/%s%s" % ("photos" if kind == "photo" else "figures", rid, out_ext), None


def save_image(src, dest, kind):
    Image = pillow()
    if not Image:
        shutil.copyfile(src, dest)
        return
    from PIL import ImageOps
    size = PHOTO_SIZE if kind == "photo" else FIGURE_SIZE
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)   # 휴대폰 사진의 회전 정보 반영
        im.thumbnail((size, size))
        if dest.endswith(".png"):
            im.save(dest, "PNG", optimize=True)
            return
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            rgba = im.convert("RGBA")
            bg = Image.new("RGB", im.size, "white")
            bg.paste(rgba, mask=rgba.getchannel("A"))
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        im.save(dest, "JPEG", quality=85, optimize=True, progressive=True)


def match_images(people, images, errors, rel):
    """양식의 '사진 파일명'·'그림 파일명'으로 이미지를 짝짓습니다.

    사진(필수): 적힌 파일이 없거나 칸이 비어 있으면, 같은 폴더에 양식이 그것 하나뿐이고 남은 이미지도
          하나면 그것을 사진으로 봅니다. 그래도 없을 때 이미 게시된 프로필이면 기존 사진을 유지하고
          (예전 양식을 고쳐 보내면서 사진은 다시 첨부하지 않은 경우), 처음 등록이면 오류입니다.
    그림(선택): 적힌 파일이 없으면 기존 그림을 유지하고, 기존 그림도 없으면 오류. 자동으로 짝짓지 않습니다."""
    claimed = {}

    def find(p, name):
        folder = os.path.dirname(p["file"])
        cands = [i for i in images if os.path.dirname(i) == folder]
        n = name.strip().lower()
        hits = [i for i in cands if os.path.basename(i).lower() == n]
        if not hits:   # 확장자를 빼고 적은 경우
            hits = [i for i in cands if os.path.splitext(os.path.basename(i))[0].lower() == os.path.splitext(n)[0]]
        return hits[0] if len(hits) == 1 else None

    for p in people:
        old = p["old"] or {}
        p["photo_src"], p["photo_named"], p["figure_src"], p["keep_figure"] = None, "", None, ""
        for key in ("photo", "figure"):
            name = first(p["values"], key)
            if not name:
                continue
            hit = find(p, name)
            if hit and claimed.get(hit, p) is not p:
                errors.append((rel(hit), "두 양식이 같은 이미지 파일을 가리킵니다"))
                continue
            if hit:
                claimed[hit] = p
            if key == "photo":
                p["photo_named"], p["photo_src"] = name, hit
            elif hit:
                p["figure_src"] = hit
            elif is_local((old.get("figure") or {}).get("src")):
                p["keep_figure"] = name
            else:
                errors.append((rel(p["file"]), "그림 파일명 '%s' 에 해당하는 파일이 같은 폴더에 없습니다" % name))

    for p in people:
        if p["photo_src"]:
            continue
        folder = os.path.dirname(p["file"])
        tables_here = [q for q in people if os.path.dirname(q["file"]) == folder]
        rest = [i for i in images if os.path.dirname(i) == folder and i not in claimed]
        if len(tables_here) == 1 and len(rest) == 1:
            p["photo_src"] = rest[0]
            claimed[rest[0]] = p
            if p["photo_named"]:
                p["notes"].append("사진 파일명 '%s' 대신 함께 올라온 %s 를 사진으로 사용"
                                  % (p["photo_named"], os.path.basename(rest[0])))
        elif len(tables_here) == 1 and len(rest) > 1:
            errors.append((rel(p["file"]), "사진으로 볼 수 있는 이미지가 %d개입니다 (%s). 양식의 '사진 파일명' 칸에 어느 파일인지 적어 주세요"
                           % (len(rest), ", ".join(os.path.basename(i) for i in rest))))
            for i in rest:
                claimed[i] = p
        elif not is_local((p["old"] or {}).get("photo")):
            errors.append((rel(p["file"]), "사진 파일명 '%s' 에 해당하는 파일이 같은 폴더에 없습니다" % p["photo_named"]
                           if p["photo_named"] else "사진이 없습니다. 사진을 첨부해 달라고 요청하세요"))

    for i in images:
        if i not in claimed:
            errors.append((rel(i), "어느 양식의 이미지인지 알 수 없습니다. 한 분씩 올리거나 사람별 폴더에 넣거나, "
                                   "양식의 '사진 파일명' 칸에 이 파일 이름을 적어 주세요"))


def parse_requests(paths, errors, rel):
    out = []
    for path in paths:
        try:
            text = decode(open(path, "rb").read())
        except ValueError as e:
            errors.append((rel(path), str(e)))
            continue
        for n, line in enumerate(text.splitlines(), 1):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            m = re.match(r"^(비공개|공개|삭제)\s+(.+)$", line)
            if not m:
                errors.append((rel(path), "%d행 '%s' — '비공개 프로필id', '공개 프로필id', '삭제 프로필id' 중 하나로 적어 주세요"
                               % (n, line)))
                continue
            out.append({"file": rel(path), "line": n, "action": m.group(1), "target": m.group(2).strip()})
    return out


# ------------------------------------------------------------- inbox 반영
def inbox_files(inbox):
    out = []
    for dirpath, dirnames, filenames in os.walk(inbox):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.startswith(".") or name.lower() in INBOX_IGNORE:
                continue
            out.append(os.path.join(dirpath, name))
    return out


def cmd_ingest(dry_run=False, message_file=None):
    inbox = INBOX
    if not os.path.isdir(inbox):
        sys.exit("inbox 폴더가 없습니다: " + inbox)
    files = inbox_files(inbox)
    if not files:
        log("inbox 에 처리할 파일이 없습니다.")
        return

    base = os.path.dirname(inbox)
    rel = lambda p: os.path.relpath(p, base)  # noqa: E731
    errors = []    # (파일, 내용)
    tables, images, request_files = [], [], []
    for p in files:
        ext = os.path.splitext(p)[1].lower()
        if ext in TABLE_EXT:
            tables.append(p)
        elif ext in IMAGE_EXT:
            images.append(p)
        elif ext == ".txt":
            request_files.append(p)
        elif ext == ".xls":
            errors.append((rel(p), "예전 엑셀 형식(.xls)입니다. xlsx 로 저장해서 다시 보내 달라고 요청하세요"))
        else:
            errors.append((rel(p), "처리할 수 없는 파일입니다. 양식(xlsx·csv), 사진(jpg·png), 요청(txt)만 올려 주세요"))

    data = load_data()
    official = load_societies()
    by_id = {r["id"]: r for r in data}
    taken = set(by_id)
    today = datetime.now(KST).strftime("%Y-%m-%d")

    # 1) 양식 읽기 → 누구의 프로필인지 정하기 → 검사
    people, owner = [], {}
    for t in tables:
        try:
            values = parse_form(read_table(t))
        except Exception as e:  # 깨진 파일, 암호 걸린 파일 등
            errors.append((rel(t), "파일을 읽지 못했습니다 (%s)" % e))
            continue
        if values is None:
            errors.append((rel(t), "신진연구자 등록 양식이 아닙니다. '성명(국문)' 같은 항목 이름이 있는 양식으로 보내 달라고 요청하세요"))
            continue
        email = first(values, "email").lower()
        given = first(values, "id")
        if given:
            rid, old = given, by_id.get(given)
        else:
            old = next((r for r in data if email and str(r.get("email", "")).lower() == email), None)
            if old:
                rid = old["id"]
            else:
                twin = next((r for r in data if r.get("name") == first(values, "name")
                             and r.get("affiliation") == first(values, "affiliation")), None)
                if twin:
                    errors.append((rel(t), "이름·소속이 같은 프로필(%s)이 이미 있는데 E-mail 이 다릅니다. 같은 분이면 양식의 "
                                           "'프로필 id' 칸에 %s 를, 다른 분이면 새 id 를 적어 주세요" % (twin["id"], twin["id"])))
                rid = slugify(first(values, "nameEn"), taken)
        rec = form_to_record(values, rid, today)
        probs = record_problems(rec, official)
        consent = first(values, "consent")
        if "동의" not in consent or "않" in consent or "비동의" in consent:
            probs.append("'공개 동의' 칸에 '동의'가 없습니다")
        if not ID_RE.match(rid):
            probs.append("프로필 id 형식 오류: %s (영문 소문자·숫자·하이픈)" % rid)
        if rid in owner:
            probs.append("%s 와 같은 사람(프로필 id %s)입니다. 한 사람당 양식 하나만 올려 주세요" % (owner[rid], rid))
        owner.setdefault(rid, rel(t))
        errors.extend((rel(t), x) for x in probs)
        people.append({"file": t, "values": values, "id": rid, "old": old, "record": rec, "notes": []})

    # 2) 사진·그림 짝짓기와 확인
    match_images(people, images, errors, rel)
    jobs = []   # (원본, 저장 경로, 종류)
    for p in people:
        rec, old = p["record"], p["old"]
        if p["photo_src"]:
            dest, err = plan_image(p["photo_src"], "photo", p["id"])
            if err:
                errors.append((rel(p["photo_src"]), err))
            else:
                rec["photo"] = dest
                jobs.append((p["photo_src"], dest, "photo"))
                p["notes"].append("사진 " + os.path.basename(p["photo_src"]))
        elif old and is_local(old.get("photo")):
            rec["photo"] = old["photo"]
            p["notes"].append("사진 파일('%s')이 없어 기존 사진 유지" % p["photo_named"] if p["photo_named"]
                              else "사진은 기존 것 유지")
        old_fig = (old or {}).get("figure")
        caption = first(p["values"], "caption")
        if p["figure_src"]:
            dest, err = plan_image(p["figure_src"], "figure", p["id"])
            if err:
                errors.append((rel(p["figure_src"]), err))
            else:
                rec["figure"] = {"src": dest, "caption": caption}
                jobs.append((p["figure_src"], dest, "figure"))
        elif p["keep_figure"]:
            rec["figure"] = dict(old_fig, caption=caption or old_fig.get("caption", ""))
            p["notes"].append("그림 파일('%s')이 없어 기존 그림 유지" % p["keep_figure"])
        elif old and not first(p["values"], "figure"):
            rec["figure"] = old_fig     # 양식에 그림이 없으면 기존 그림 유지
        if old and old.get("visible") is False:
            rec["visible"] = False
            p["notes"].append("비공개 상태라 계속 비공개 (공개하려면 요청 txt 에 '공개 %s')" % p["id"])

    # 3) 새 데이터 만들기 (아직 파일에는 쓰지 않음)
    new = list(data)
    index = {r["id"]: i for i, r in enumerate(new)}
    done = []   # (구분, 성명, id, 비고)
    remove = []
    for p in people:
        rec = p["record"]
        if p["id"] in index:
            remove += local_paths(new[index[p["id"]]])
            new[index[p["id"]]] = rec
            done.append(("수정", rec["name"], rec["id"], " · ".join(p["notes"])))
        else:
            index[p["id"]] = len(new)
            new.append(rec)
            done.append(("신규", rec["name"], rec["id"], " · ".join(p["notes"])))

    for req in parse_requests(request_files, errors, rel):
        hits = [r for r in new if r["id"] == req["target"]] or [r for r in new if r.get("name") == req["target"]]
        where = "%s %d행" % (req["file"], req["line"])
        if len(hits) != 1:
            errors.append((where, "'%s' 에 해당하는 프로필이 %s" % (req["target"], "없습니다" if not hits else "여러 개입니다. 프로필 id 로 적어 주세요")))
            continue
        r = hits[0]
        i = new.index(r)
        if req["action"] == "삭제":
            remove += local_paths(r)
            new.pop(i)
        else:
            new[i] = dict(r, visible=req["action"] == "공개")
        done.append((req["action"], r.get("name", ""), r["id"], ""))

    in_use = {p for r in new for p in local_paths(r)}
    written = {dest for _, dest, _ in jobs}
    remove = sorted({p for p in remove if p not in in_use and p not in written})

    # 4) 결과
    if errors:
        report_errors(errors)
        sys.exit(1)
    if dry_run:
        report_done(done, dry_run=True)
        return

    for src, dest, kind in jobs:
        os.makedirs(os.path.dirname(os.path.join(ROOT, dest)), exist_ok=True)
        save_image(src, os.path.join(ROOT, dest), kind)
    for p in remove:
        if os.path.exists(os.path.join(ROOT, p)):
            os.remove(os.path.join(ROOT, p))
    write_data(new)
    for p in files:
        os.remove(p)
    for dirpath, _, _ in sorted(os.walk(inbox), key=lambda w: -len(w[0])):
        if dirpath != inbox and not os.listdir(dirpath):
            os.rmdir(dirpath)
    report_done(done)
    if message_file and done:
        with open(message_file, "w", encoding="utf-8") as f:
            f.write(commit_message(done))


def commit_message(done):
    order, groups = [], {}
    for kind, name, rid, _ in done:
        if kind not in groups:
            order.append(kind)
            groups[kind] = []
        groups[kind].append("%s(%s)" % (name, rid))
    title = "프로필 반영 — " + " · ".join("%s %d" % (k, len(groups[k])) for k in order)
    body = "\n".join("- %s: %s" % (k, ", ".join(groups[k])) for k in order)
    return title + "\n\n" + body + "\n\ninbox 에 올라온 파일을 GitHub Actions 가 반영했습니다.\n"


def _md(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def _summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def report_errors(errors):
    log("⚠ inbox 를 반영하지 못했습니다. 아무것도 바꾸지 않았습니다.")
    for where, msg in errors:
        log("  - %s: %s" % (where, msg))
    log("고친 파일을 같은 이름으로 inbox 에 다시 올리면(덮어쓰기) 자동으로 다시 시도합니다.")
    _summary("## ⚠ inbox 를 반영하지 못했습니다\n\n"
             "문제가 있어 **아무것도 바꾸지 않았습니다.** 사이트는 이전 상태 그대로입니다.\n\n"
             "| 파일 | 내용 |\n|---|---|\n" +
             "".join("| %s | %s |\n" % (_md(w), _md(m)) for w, m in errors) +
             "\n고친 파일을 **같은 이름으로** `inbox/` 에 다시 올리면(덮어쓰기) 자동으로 다시 시도합니다. "
             "필요 없는 파일은 `inbox/` 에서 지워 주세요.")


def report_done(done, dry_run=False):
    head = "검사 통과 — 반영하면 다음과 같이 바뀝니다" if dry_run else "반영 완료"
    log("✓ %s (%d건)" % (head, len(done)))
    for kind, name, rid, note in done:
        log("  - [%s] %s (%s)%s" % (kind, name, rid, " — " + note if note else ""))
    _summary("## ✓ %s\n\n| 구분 | 성명 | 프로필 id | 비고 |\n|---|---|---|---|\n" % head +
             "".join("| %s | %s | `%s` | %s |\n" % (k, _md(n), r, _md(note)) for k, n, r, note in done))


# ------------------------------------------------------------------ 진입점
if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
    elif args[0] == "sync":
        cmd_sync()
    elif args[0] == "check":
        cmd_check(strict="--strict" in args)
    elif args[0] == "ingest":
        msg = args[args.index("--message-file") + 1] if "--message-file" in args else None
        cmd_ingest(dry_run="--dry-run" in args, message_file=msg)
    else:
        sys.exit("알 수 없는 명령: " + args[0])
