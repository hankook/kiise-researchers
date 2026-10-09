#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국정보과학회 신진연구자 프로필 브로셔 — 데이터 빌드 도구

사용법
  python3 tools/build.py sync
      data/researchers.json 을 읽어 data/researchers.js 를 다시 생성합니다.
      (researchers.js 는 file:// 로 직접 열었을 때를 위한 폴백 파일입니다.
       JSON 을 손으로 고친 뒤에는 반드시 이 명령을 한 번 실행하세요.)

  python3 tools/build.py import <응답.csv> [--merge]
      구글 폼 응답 CSV 를 data/researchers.json 형식으로 변환합니다.
      --merge 를 주면 기존 JSON 에 같은 id 는 덮어쓰고 새 id 는 추가합니다.
      (미지정 시 기존 파일을 백업한 뒤 전체 교체)

  python3 tools/build.py check [--strict]
      데이터 무결성을 점검합니다. 필수 항목 누락, id 중복, 연구 키워드 개수,
      소사이어티 표기, 사진·그림 파일 존재 여부, researchers.js 동기화 여부를 확인합니다.
      --strict 를 주면 문제가 있을 때 종료 코드 1 을 반환합니다 (GitHub Actions 용).
"""
import csv
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "data", "researchers.json")
JS_PATH = os.path.join(ROOT, "data", "researchers.js")

# 구글 폼 문항 제목 → 내부 필드. 헤더에 아래 문자열이 '포함'되면 매칭됩니다.
FIELD_HINTS = [
    ("name",          ["성명(국문)", "성명 (국문)", "국문 성명", "이름"]),
    ("nameEn",        ["성명(영문)", "성명 (영문)", "영문 성명", "영문명"]),
    ("affiliation",   ["소속 기관", "소속기관", "소속 대학"]),
    ("department",    ["학과", "학부", "전공"]),
    ("position",      ["직위"]),
    ("degree",        ["최종 학위", "최종학위"]),
    ("appointedAt",   ["최초 임용일", "최초임용일", "임용일"]),
    ("email",         ["이메일", "e-mail", "email"]),
    ("homepage",      ["연구실 홈페이지", "홈페이지"]),
    ("links",         ["추가 링크", "연구자 url", "scholar"]),
    ("keywords",      ["연구 키워드", "연구키워드", "키워드"]),
    ("societies",     ["소사이어티", "연구회"]),
    ("conferences",   ["참석하는 학회", "주요 학회", "참여 학회"]),
    ("message",       ["한마디", "하고 싶은 말", "소개 문구"]),
    ("career",        ["주요 경력", "주요 연구 경력", "경력 및 역량", "역량"]),
    ("achievements",  ["대표 논문", "논문 및 수행과제", "수행과제", "업적"]),
    ("goals",         ["연구목표", "연구 목표"]),
    ("research",      ["연구내용", "연구 내용"]),
    ("collaboration", ["공동연구", "희망분야"]),
    ("photo",         ["사진"]),
    ("updatedAt",     ["타임스탬프", "timestamp"]),
]


def log(msg):
    print(msg)


# ------------------------------------------------------------------ 공통 유틸
def slugify(name_en, name_ko, used):
    base = (name_en or "").strip().lower()
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    if not base:
        base = "researcher-" + re.sub(r"\W+", "", name_ko or "")[:8] or "researcher"
    slug, n = base, 2
    while slug in used:
        slug, n = "%s-%d" % (base, n), n + 1
    used.add(slug)
    return slug


def split_lines(text):
    """여러 줄/불릿 입력을 항목 리스트로 분리."""
    if not text:
        return []
    out = []
    for line in re.split(r"[\r\n]+", str(text)):
        line = re.sub(r"^\s*[-•·*▪●○\d]+[.)]?\s*", "", line).strip()
        if line:
            out.append(line)
    return out


def split_keywords(text):
    if not text:
        return []
    parts = re.split(r"[,、/|\n\r]+", str(text))
    return [p.strip().lstrip("#").strip() for p in parts if p.strip()]


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


# ------------------------------------------------------------- JSON -> JS 동기화
def render_js():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    body = json.dumps(data, ensure_ascii=False, indent=2)
    text = ("/* 자동 생성 파일 — 직접 수정하지 마세요.\n"
            "   data/researchers.json 을 고친 뒤 `python3 tools/build.py sync` 를 실행하면 갱신됩니다.\n"
            "   file:// 로 페이지를 직접 열었을 때(fetch 불가) 사용되는 폴백 데이터입니다. */\n"
            "window.RESEARCHERS = " + body + ";\n")
    return data, text


def cmd_sync():
    data, text = render_js()
    with open(JS_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    log("✓ data/researchers.js 생성 완료 (%d명)" % len(data))


# ------------------------------------------------------------------ CSV 가져오기
def map_headers(headers):
    mapping = {}
    for idx, h in enumerate(headers):
        hl = (h or "").strip().lower()
        for field, hints in FIELD_HINTS:
            if field in mapping.values():
                continue
            if any(hint.lower() in hl for hint in hints):
                mapping[idx] = field
                break
    return mapping


def cmd_import(csv_path, merge=False):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        sys.exit("CSV 가 비어 있습니다.")

    headers, body = rows[0], rows[1:]
    mapping = map_headers(headers)
    matched = sorted(set(mapping.values()))
    log("· 인식된 항목: " + ", ".join(matched))
    missing = [f for f, _ in FIELD_HINTS if f not in matched]
    if missing:
        log("· 인식되지 않은 항목(비워 둡니다): " + ", ".join(missing))

    used = set()
    records = []
    for row in body:
        get = lambda field: next((row[i].strip() for i, f in mapping.items()
                                  if f == field and i < len(row) and row[i]), "")
        name = get("name")
        if not name:
            continue
        rec = {
            "id": slugify(get("nameEn"), name, used),
            "name": name,
            "nameEn": get("nameEn"),
            "affiliation": get("affiliation"),
            "department": get("department"),
            "position": get("position"),
            "photo": get("photo"),
            "degree": get("degree"),
            "appointedAt": norm_date(get("appointedAt")),
            "email": get("email"),
            "homepage": get("homepage"),
            "links": parse_links(get("links")),
            "message": get("message"),
            "keywords": split_keywords(get("keywords")),
            "societies": split_keywords(get("societies")),
            "conferences": split_keywords(get("conferences")),
            "career": split_lines(get("career")),
            "achievements": split_lines(get("achievements")),
            "goals": split_lines(get("goals")),
            "research": {"body": split_lines(get("research")), "figures": []},
            "collaboration": split_lines(get("collaboration")),
            "visible": True,
            "updatedAt": norm_date(get("updatedAt")) or datetime.now().strftime("%Y-%m-%d"),
        }
        records.append(rec)

    if merge and os.path.exists(JSON_PATH):
        with open(JSON_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        by_id = {r["id"]: r for r in existing}
        for r in records:
            by_id[r["id"]] = r
        records = list(by_id.values())

    if os.path.exists(JSON_PATH):
        backup = JSON_PATH + "." + datetime.now().strftime("%Y%m%d%H%M%S") + ".bak"
        shutil.copy2(JSON_PATH, backup)
        log("· 기존 데이터 백업: " + os.path.relpath(backup, ROOT))

    records.sort(key=lambda r: r["name"])
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log("✓ data/researchers.json 저장 완료 (%d명)" % len(records))
    cmd_sync()


def load_societies():
    """data/societies.json 의 공식 목록(소사이어티 + 연구회). 없으면 빈 집합."""
    path = os.path.join(ROOT, "data", "societies.json")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return set(d.get("societies", [])) | set(d.get("sigs", []))


# --------------------------------------------------------------------- 점검
def cmd_check(strict=False):
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    problems = []

    # researchers.js 가 researchers.json 과 어긋나 있는지 (sync 실행 누락)
    _, expected = render_js()
    current = open(JS_PATH, encoding="utf-8").read() if os.path.exists(JS_PATH) else ""
    if current != expected:
        problems.append("data/researchers.js 가 최신이 아닙니다. "
                        "`python3 tools/build.py sync` 를 실행하고 함께 커밋하세요.")

    seen = {}
    for r in data:
        rid = r.get("id", "")
        who = "%s(%s)" % (r.get("name", "?"), rid or "id 없음")
        if not rid:
            problems.append(who + ": id 가 없습니다.")
        elif rid in seen:
            problems.append(who + ": id 가 중복됩니다.")
        seen[rid] = True
        for field, label in [("name", "성명"), ("affiliation", "소속"), ("position", "직위")]:
            if not r.get(field):
                problems.append("%s: %s 누락" % (who, label))
        if not r.get("keywords"):
            problems.append(who + ": 연구 키워드 없음")
        elif not (5 <= len(r["keywords"]) <= 10):
            problems.append("%s: 연구 키워드 %d개 (권장 5~10개)" % (who, len(r["keywords"])))
        known = load_societies()
        if known:
            for soc in r.get("societies", []):
                if soc not in known:
                    problems.append("%s: 공식 목록에 없는 소사이어티/연구회 표기 → %s" % (who, soc))
        if len(r.get("message", "")) > 120:
            problems.append("%s: 한마디가 %d자 (120자 이내 권장)" % (who, len(r["message"])))
        if r.get("visible") is False:
            log("  · %s 는 visible:false 로 비공개 상태입니다." % who)
        photo = r.get("photo")
        if photo and not os.path.exists(os.path.join(ROOT, photo)):
            problems.append("%s: 사진 파일 없음 → %s" % (who, photo))
        for f_ in r.get("research", {}).get("figures", []):
            if not os.path.exists(os.path.join(ROOT, f_.get("src", ""))):
                problems.append("%s: 그림 파일 없음 → %s" % (who, f_.get("src")))

    log("총 %d명 점검" % len(data))
    if problems:
        log("⚠ 확인이 필요한 항목 %d건" % len(problems))
        for p in problems:
            log("  - " + p)
        if strict:
            sys.exit(1)
    else:
        log("✓ 문제 없음")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
    elif args[0] == "sync":
        cmd_sync()
    elif args[0] == "import":
        if len(args) < 2:
            sys.exit("CSV 경로를 지정하세요.")
        cmd_import(args[1], merge="--merge" in args)
    elif args[0] == "check":
        cmd_check(strict="--strict" in args)
    else:
        sys.exit("알 수 없는 명령: " + args[0])
