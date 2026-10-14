/* 공통 데이터 로더 & 유틸 (index / profile 공용) */
(function () {
  "use strict";
  var KIISE = (window.KIISE = window.KIISE || {});

  /* -------------------------------------------------- 데이터 로드
     fetch 를 쓰므로 파일을 더블클릭(file://)해서는 열리지 않습니다. 로컬 서버로 확인하세요. */
  KIISE.load = function () {
    return fetch("data/researchers.json", { cache: "no-cache" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (list) {
        return (list || [])
          .filter(function (r) { return r && r.visible !== false; })  /* 비공개 처리된 프로필 제외 */
          .map(KIISE.normalize);
      });
  };

  /* -------------------------------------------------- 레코드 정규화 */
  KIISE.normalize = function (r) {
    var o = Object.assign({}, r);
    o.keywords = o.keywords || [];
    o.societies = o.societies || [];        /* 정보과학회 내 소사이어티·연구회 */
    o.career = o.career || [];              /* 주요 경력 */
    o.papers = o.papers || [];              /* 대표 논문 */
    o.projects = o.projects || [];          /* 수행 과제 */
    o.research = o.research || [];          /* 연구 목표 및 내용 */
    o.message = o.message || "";            /* 인사말 */
    o.links = o.links || [];
    o.affilFull = [o.affiliation, o.department].filter(Boolean).join(" ");
    o.posLine = [o.affilFull, o.position].filter(Boolean).join(" ");
    o.searchText = KIISE.fold(
      [
        o.name, o.nameEn, o.affiliation, o.department, o.position, o.degree,
        o.keywords.join(" "), o.societies.join(" "), o.message,
        o.career.join(" "), o.papers.join(" "), o.projects.join(" "), o.research.join(" ")
      ].join(" ")
    );
    return o;
  };

  /* -------------------------------------------------- 문자열 유틸 */
  KIISE.fold = function (s) {
    return String(s || "").toLowerCase().replace(/\s+/g, " ").trim();
  };

  KIISE.escape = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (m) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m];
    });
  };

  /* 검색어 하이라이트 (이미 escape 된 문자열에 적용) */
  KIISE.highlight = function (escaped, terms) {
    if (!terms || !terms.length) return escaped;
    var pat = terms
      .filter(function (t) { return t.length > 0; })
      .map(function (t) { return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); })
      .join("|");
    if (!pat) return escaped;
    return escaped.replace(new RegExp("(" + pat + ")", "gi"), "<mark>$1</mark>");
  };

  /* 날짜 표기: 2026-09-01 → 2026. 09. 01. */
  KIISE.fmtDate = function (s) {
    if (!s) return "";
    var m = String(s).match(/^(\d{4})[-.\/]?(\d{2})?[-.\/]?(\d{2})?/);
    if (!m) return s;
    return [m[1], m[2], m[3]].filter(Boolean).join(". ") + ".";
  };

  /* 사진이 없을 때 쓰는 이니셜 (성 한 글자) */
  KIISE.initial = function (name) {
    return String(name || "?").trim().charAt(0);
  };
})();
