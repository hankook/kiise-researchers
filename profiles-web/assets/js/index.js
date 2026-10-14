/* 목록/검색 페이지 */
(function () {
  "use strict";
  var K = window.KIISE;

  var el = {
    q: document.getElementById("q"),
    clear: document.getElementById("q-clear"),
    kwfilter: document.getElementById("kwfilter"),
    kwmore: document.getElementById("kwmore"),
    affil: document.getElementById("affil"),
    soc: document.getElementById("soc"),
    sort: document.getElementById("sort"),
    count: document.getElementById("count"),
    reset: document.getElementById("reset"),
    cards: document.getElementById("cards"),
    total: document.getElementById("total")
  };

  var ALL = [];
  var state = { q: "", kws: [], affil: "", soc: "", sort: "name" };

  /* ------------------------------------------------------- URL(해시) 동기화 */
  function readHash() {
    var h = (location.hash || "").replace(/^#/, "");
    if (!h) return;
    var p = new URLSearchParams(h);
    state.q = p.get("q") || "";
    state.kws = (p.get("kw") || "").split(",").filter(Boolean);
    state.affil = p.get("affil") || "";
    state.soc = p.get("soc") || "";
    state.sort = p.get("sort") || "name";
  }
  function writeHash() {
    var p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    if (state.kws.length) p.set("kw", state.kws.join(","));
    if (state.affil) p.set("affil", state.affil);
    if (state.soc) p.set("soc", state.soc);
    if (state.sort !== "name") p.set("sort", state.sort);
    var s = p.toString();
    history.replaceState(null, "", s ? "#" + s : location.pathname + location.search);
  }

  /* ------------------------------------------------------------- 필터 로직 */
  function terms() {
    return K.fold(state.q).split(" ").filter(Boolean);
  }

  function match(r) {
    if (state.affil && r.affiliation !== state.affil) return false;
    if (state.soc && r.societies.indexOf(state.soc) === -1) return false;
    for (var i = 0; i < state.kws.length; i++) {
      if (r.keywords.indexOf(state.kws[i]) === -1) return false;   // 선택 키워드 AND 조건
    }
    var ts = terms();
    for (var j = 0; j < ts.length; j++) {
      if (r.searchText.indexOf(ts[j]) === -1) return false;
    }
    return true;
  }

  function sorted(list) {
    var c = list.slice();
    if (state.sort === "updated") {
      c.sort(function (a, b) { return String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")); });
    } else if (state.sort === "affil") {
      c.sort(function (a, b) { return a.affilFull.localeCompare(b.affilFull, "ko") || a.name.localeCompare(b.name, "ko"); });
    } else {
      c.sort(function (a, b) { return a.name.localeCompare(b.name, "ko"); });
    }
    return c;
  }

  /* --------------------------------------------------------------- 렌더링 */
  function renderKeywordFilter() {
    var counts = {};
    ALL.forEach(function (r) {
      r.keywords.forEach(function (k) { counts[k] = (counts[k] || 0) + 1; });
    });
    var keys = Object.keys(counts).sort(function (a, b) {
      return counts[b] - counts[a] || a.localeCompare(b, "ko");
    });
    el.kwfilter.innerHTML = keys.map(function (k) {
      var on = state.kws.indexOf(k) !== -1;
      return '<button type="button" class="kwchip" aria-pressed="' + on + '" data-kw="' +
        K.escape(k) + '">' + K.escape(k) + "<small>" + counts[k] + "</small></button>";
    }).join("");
    el.kwmore.hidden = keys.length < 18;
  }

  function renderAffilFilter() {
    var set = {};
    ALL.forEach(function (r) { if (r.affiliation) set[r.affiliation] = 1; });
    var keys = Object.keys(set).sort(function (a, b) { return a.localeCompare(b, "ko"); });
    el.affil.innerHTML =
      '<option value="">소속 전체</option>' +
      keys.map(function (k) {
        return '<option value="' + K.escape(k) + '"' + (state.affil === k ? " selected" : "") +
          ">" + K.escape(k) + "</option>";
      }).join("");
  }

  function renderSocFilter() {
    var counts = {};
    ALL.forEach(function (r) {
      r.societies.forEach(function (k) { counts[k] = (counts[k] || 0) + 1; });
    });
    var keys = Object.keys(counts).sort(function (a, b) { return a.localeCompare(b, "ko"); });
    el.soc.innerHTML =
      '<option value="">소사이어티 · 연구회 전체</option>' +
      keys.map(function (k) {
        return '<option value="' + K.escape(k) + '"' + (state.soc === k ? " selected" : "") +
          ">" + K.escape(k) + " (" + counts[k] + ")</option>";
      }).join("");
    el.soc.hidden = keys.length === 0;
  }

  /* 카드 요약문은 '인사말'을 우선 사용 */
  function summaryOf(r) {
    return (r.message || r.research[0] || r.career[0] || "");
  }

  function cardHTML(r, ts) {
    var hl = function (s) { return K.highlight(K.escape(s), ts); };
    var photo = r.photo
      ? '<img class="card__photo" src="' + K.escape(r.photo) + '" alt="' + K.escape(r.name) + ' 사진" loading="lazy">'
      : '<div class="card__photo card__photo--ph" aria-hidden="true">' + K.escape(K.initial(r.name)) + "</div>";

    return (
      '<a class="card" href="profile.html?id=' + encodeURIComponent(r.id) + '">' +
        '<div class="card__top">' + photo +
          "<div>" +
            '<h3 class="card__name">' + hl(r.name) +
              (r.nameEn ? "<span>" + hl(r.nameEn) + "</span>" : "") + "</h3>" +
            '<p class="card__affil">' + hl(r.affilFull) + "</p>" +
            '<p class="card__pos">' + hl(r.position || "") + "</p>" +
            (r.societies.length
              ? '<p class="card__soc" title="' + K.escape(r.societies.join(", ")) + '">' +
                  hl(r.societies.join(" · ")) + "</p>"
              : "") +
          "</div>" +
        "</div>" +
        '<p class="card__desc">' + hl(summaryOf(r)) + "</p>" +
        '<div class="card__kw">' +
          r.keywords.map(function (k) {
            var on = state.kws.indexOf(k) !== -1;
            return '<span class="kw' + (on ? "" : " kw--muted") + '">' + hl(k) + "</span>";
          }).join("") +
        "</div>" +
      "</a>"
    );
  }

  function render() {
    var ts = terms();
    var list = sorted(ALL.filter(match));

    el.count.innerHTML = "<strong>" + list.length + "</strong>명";
    var filtered = state.q || state.kws.length || state.affil || state.soc;
    el.reset.hidden = !filtered;

    el.cards.innerHTML = list.length
      ? list.map(function (r) { return cardHTML(r, ts); }).join("")
      : '<div class="empty"><strong>검색 결과가 없습니다.</strong>' +
        "검색어나 선택한 키워드를 바꾸어 다시 시도해 보세요.</div>";

    Array.prototype.forEach.call(el.kwfilter.querySelectorAll(".kwchip"), function (b) {
      b.setAttribute("aria-pressed", state.kws.indexOf(b.dataset.kw) !== -1);
    });
    el.clear.hidden = !state.q;
    writeHash();
  }

  /* ----------------------------------------------------------- 이벤트 연결 */
  var timer;
  el.q.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { state.q = el.q.value; render(); }, 120);
  });
  el.clear.addEventListener("click", function () {
    el.q.value = ""; state.q = ""; el.q.focus(); render();
  });
  el.kwfilter.addEventListener("click", function (e) {
    var b = e.target.closest(".kwchip");
    if (!b) return;
    var k = b.dataset.kw, i = state.kws.indexOf(k);
    if (i === -1) state.kws.push(k); else state.kws.splice(i, 1);
    render();
  });
  el.kwmore.addEventListener("click", function () {
    var col = el.kwfilter.classList.toggle("is-collapsed");
    el.kwmore.textContent = col ? "키워드 모두 보기" : "키워드 접기";
  });
  el.affil.addEventListener("change", function () { state.affil = el.affil.value; render(); });
  el.soc.addEventListener("change", function () { state.soc = el.soc.value; render(); });
  el.sort.addEventListener("change", function () { state.sort = el.sort.value; render(); });
  el.reset.addEventListener("click", function () {
    state = { q: "", kws: [], affil: "", soc: "", sort: state.sort };
    el.q.value = ""; el.affil.value = ""; el.soc.value = "";
    render();
  });
  /* 단축키: "/" 로 검색창 포커스 */
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== el.q) { e.preventDefault(); el.q.focus(); }
  });

  /* -------------------------------------------------------------- 시작 */
  K.load().then(function (list) {
    ALL = list;
    readHash();
    el.q.value = state.q;
    el.sort.value = state.sort;
    el.total.textContent = ALL.length;
    renderKeywordFilter();
    renderAffilFilter();
    renderSocFilter();
    el.kwfilter.classList.add("is-collapsed");
    render();
  }).catch(function (err) {
    el.cards.innerHTML = '<div class="empty"><strong>데이터를 불러오지 못했습니다.</strong>' +
      K.escape(err.message) + "</div>";
  });
})();
