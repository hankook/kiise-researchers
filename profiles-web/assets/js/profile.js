/* 개인 프로필 페이지 */
(function () {
  "use strict";
  var K = window.KIISE;
  var root = document.getElementById("profile");
  var toolbar = document.getElementById("toolbar-extra");

  function param(name) {
    return new URLSearchParams(location.search).get(name);
  }

  function bullets(items) {
    if (!items || !items.length) return '<p class="pf-none">준비 중입니다.</p>';
    return '<ul class="pf-list">' + items.map(function (t) {
      return "<li>" + K.escape(t) + "</li>";
    }).join("") + "</ul>";
  }

  function section(title, bodyHTML) {
    return (
      '<section class="pf-sec">' +
        '<h2 class="pf-sec__title">' + K.escape(title) + "</h2>" +
        '<div class="pf-sec__body">' + bodyHTML + "</div>" +
      "</section>"
    );
  }

  function factRow(k, vHTML) {
    if (!vHTML) return "";
    return '<li><span class="k">' + K.escape(k) + '</span><span class="v">' + vHTML + "</span></li>";
  }

  function headHTML(r) {
    var photo = r.photo
      ? '<img class="pf-photo" src="' + K.escape(r.photo) + '" alt="' + K.escape(r.name) + ' 사진">'
      : '<div class="pf-photo--ph" aria-hidden="true">' + K.escape(K.initial(r.name)) + "</div>";

    var facts =
      factRow("최종 학위", K.escape(r.degree)) +
      factRow("최초 임용일", K.escape(K.fmtDate(r.appointedAt))) +
      factRow("E-mail", r.email ? '<a href="mailto:' + K.escape(r.email) + '">' + K.escape(r.email) + "</a>" : "") +
      factRow("연구실", r.homepage
        ? '<a href="' + K.escape(r.homepage) + '" target="_blank" rel="noopener">' + K.escape(r.homepage) + "</a>"
        : "");

    var message = r.message
      ? '<blockquote class="pf-quote">' + K.escape(r.message) + "</blockquote>"
      : "";

    var links = (r.links && r.links.length)
      ? '<div class="pf-links">' + r.links.map(function (l) {
          return '<a href="' + K.escape(l.url) + '" target="_blank" rel="noopener">' + K.escape(l.label) + " ↗</a>";
        }).join("") + "</div>"
      : "";

    return (
      '<header class="pf-head">' +
        '<div class="pf-head__bar">' +
          '<span class="pf-head__brand">한국정보과학회 신진연구자 프로필</span>' +
          '<span class="pf-updated">최근 업데이트일: ' + K.escape(K.fmtDate(r.updatedAt) || "-") + "</span>" +
        "</div>" +
        '<div class="pf-head__body">' +
          photo +
          '<div class="pf-idblock">' +
            '<div class="pf-nameline">' +
              '<h1 class="pf-name">' + K.escape(r.name) +
                (r.nameEn ? '<span class="pf-name-en">' + K.escape(r.nameEn) + "</span>" : "") +
              "</h1>" +
              '<p class="pf-pos">' + K.escape(r.posLine) + "</p>" +
            "</div>" +
          "</div>" +
          '<div class="pf-head__facts">' +
            '<ul class="pf-facts">' + facts + "</ul>" + links + message +
          "</div>" +
        "</div>" +
      "</header>"
    );
  }

  function researchHTML(r) {
    var body = r.research.body.length
      ? r.research.body.map(function (p) { return "<p>" + K.escape(p) + "</p>"; }).join("")
      : '<p class="pf-none">준비 중입니다.</p>';
    var figs = r.research.figures.length
      ? '<div class="pf-figs">' + r.research.figures.map(function (f) {
          return '<figure class="pf-fig"><img src="' + K.escape(f.src) + '" alt="' +
            K.escape(f.caption || "연구 내용 그림") + '">' +
            (f.caption ? "<figcaption>" + K.escape(f.caption) + "</figcaption>" : "") + "</figure>";
        }).join("") + "</div>"
      : "";
    return body + figs;
  }

  function chips(items, filterKey, muted) {
    if (!items || !items.length) return '<p class="pf-none">등록된 내용이 없습니다.</p>';
    return '<div class="pf-kws">' + items.map(function (k) {
      var cls = "kw" + (muted ? " kw--muted" : "");
      return filterKey
        ? '<a class="' + cls + '" href="index.html#' + filterKey + "=" + encodeURIComponent(k) + '">' + K.escape(k) + "</a>"
        : '<span class="' + cls + '">' + K.escape(k) + "</span>";
    }).join("") + "</div>";
  }

  function kwHTML(r) {
    if (!r.keywords.length) return '<p class="pf-none">등록된 키워드가 없습니다.</p>';
    return chips(r.keywords, "kw");
  }

  /* 학회 활동 — 소사이어티·연구회 / 주로 참석하는 학회를 한 섹션에 */
  function activityHTML(r) {
    if (!r.societies.length && !r.conferences.length) return "";
    var rows = "";
    if (r.societies.length) {
      rows += '<div class="pf-row"><span class="pf-row__label">소사이어티 · 연구회</span>' +
        '<div class="pf-row__body">' + chips(r.societies, "soc") + "</div></div>";
    }
    if (r.conferences.length) {
      rows += '<div class="pf-row"><span class="pf-row__label">주로 참석하는 학회</span>' +
        '<div class="pf-row__body">' + chips(r.conferences, null, true) + "</div></div>";
    }
    return section("학회 활동", rows);
  }

  function render(r, all) {
    document.title = r.name + " · " + r.affilFull + " — 한국정보과학회 신진연구자 프로필";

    root.innerHTML =
      '<div class="pf-aside">' +
        headHTML(r) +
        '<div class="pf-kwsec">' + section("연구 키워드", kwHTML(r)) + "</div>" +
        '<div class="pf-actsec">' + activityHTML(r) + "</div>" +
      "</div>" +
      '<div class="pf-main">' +
        section("주요 경력", bullets(r.career)) +
        section("대표 논문 및 수행과제", bullets(r.achievements)) +
        section("연구목표", bullets(r.goals)) +
        section("연구내용", researchHTML(r)) +
        section("공동연구 희망분야", bullets(r.collaboration)) +
        '<div class="pf-printfoot print-only">' +
          "<span>한국정보과학회 신진연구자 프로필</span>" +
          "<span>" + K.escape(r.name) + " · " + K.escape(r.affilFull) + "</span>" +
        "</div>" +
      "</div>";

    /* 이전/다음 연구자 이동 */
    var sorted = all.slice().sort(function (a, b) { return a.name.localeCompare(b.name, "ko"); });
    var i = sorted.findIndex(function (x) { return x.id === r.id; });
    var prev = sorted[(i - 1 + sorted.length) % sorted.length];
    var next = sorted[(i + 1) % sorted.length];
    if (sorted.length > 1) {
      toolbar.insertAdjacentHTML("afterbegin",
        '<a class="btn btn--ghost" href="profile.html?id=' + encodeURIComponent(prev.id) + '">← ' + K.escape(prev.name) + "</a>" +
        '<a class="btn btn--ghost" href="profile.html?id=' + encodeURIComponent(next.id) + '">' + K.escape(next.name) + " →</a>");
    }
  }

  function notFound(id) {
    root.innerHTML = '<div class="empty" style="width:100%">' +
      "<strong>해당 연구자를 찾을 수 없습니다.</strong>" +
      (id ? "요청한 ID: " + K.escape(id) + "<br>" : "") +
      '<a href="index.html">목록으로 돌아가기</a></div>';
  }

  /* ------------------------------------------------------------------ 시작 */
  var id = param("id");
  K.load().then(function (all) {
    var r = all.filter(function (x) { return x.id === id; })[0];
    if (!r) return notFound(id);
    render(r, all);
  }).catch(function (err) {
    root.innerHTML = '<div class="empty" style="width:100%"><strong>데이터를 불러오지 못했습니다.</strong>' +
      K.escape(err.message) + "</div>";
  });

  /* 인쇄 / 링크 복사 */
  document.getElementById("btn-print").addEventListener("click", function () { window.print(); });
  var copy = document.getElementById("btn-copy");
  copy.addEventListener("click", function () {
    var done = function () {
      var t = copy.textContent; copy.textContent = "복사됨 ✓";
      setTimeout(function () { copy.textContent = t; }, 1500);
    };
    if (navigator.clipboard) navigator.clipboard.writeText(location.href).then(done, done);
    else { window.prompt("아래 주소를 복사하세요", location.href); }
  });
})();
