/* 개인 프로필 페이지 */
(function () {
  "use strict";
  var K = window.KIISE;
  var root = document.getElementById("profile");
  var toolbar = document.getElementById("toolbar-extra");

  function param(name) {
    return new URLSearchParams(location.search).get(name);
  }

  /* 내용이 없으면 빈 문자열 → 그 섹션은 그리지 않음 */
  function bullets(items) {
    if (!items || !items.length) return "";
    return '<ul class="pf-list">' + items.map(function (t) {
      return "<li>" + K.escape(t) + "</li>";
    }).join("") + "</ul>";
  }

  function section(title, bodyHTML) {
    if (!bodyHTML) return "";
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
    var fig = r.figure && r.figure.src
      ? '<figure class="pf-fig"><img src="' + K.escape(r.figure.src) + '" alt="' +
          K.escape(r.figure.caption || "연구 내용 그림") + '">' +
          (r.figure.caption ? "<figcaption>" + K.escape(r.figure.caption) + "</figcaption>" : "") + "</figure>"
      : "";
    return fig + bullets(r.research);   /* 그림을 먼저 두어 글이 그림 옆으로 흐르게 */
  }

  /* 키워드·소사이어티 칩. 누르면 그 조건으로 걸러진 목록으로 이동 */
  function chips(items, filterKey) {
    if (!items || !items.length) return "";
    return '<div class="pf-kws">' + items.map(function (k) {
      return '<a class="kw" href="index.html#' + filterKey + "=" + encodeURIComponent(k) + '">' + K.escape(k) + "</a>";
    }).join("") + "</div>";
  }

  function render(r, all) {
    document.title = r.name + " · " + r.affilFull + " — 한국정보과학회 신진연구자 프로필";

    root.innerHTML =
      '<div class="pf-aside">' +
        headHTML(r) +
        '<div class="pf-kwsec">' + section("연구 키워드", chips(r.keywords, "kw")) + "</div>" +
        section("소사이어티 · 연구회", chips(r.societies, "soc")) +
      "</div>" +
      '<div class="pf-main">' +
        section("주요 경력", bullets(r.career)) +
        section("대표 논문", bullets(r.papers)) +
        section("수행 과제", bullets(r.projects)) +
        section("연구 목표 및 내용", researchHTML(r)) +
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
