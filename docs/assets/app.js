// 시험공부 사이트 공용 기능 — 낱말 뜻 창, 읽음 표시, 퀴즈 (구형 폰 브라우저도 돌도록 단순한 문법만 쓴다)
(function () {
  var KEY = 'lc-study-v2';
  var S = { read: {}, wrong: {}, right: {} };
  try { var v = JSON.parse(localStorage.getItem(KEY) || 'null'); if (v) { S.read = v.read || {}; S.wrong = v.wrong || {}; S.right = v.right || {}; } } catch (e) {}
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  function $(s) { return document.querySelector(s); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }

  // D-day
  var dd = $('#dday');
  if (dd) {
    var ms = new Date('2026-10-20T12:30:00+09:00') - new Date();
    dd.textContent = ms <= 0 ? '시험 날' : (ms >= 864e5 ? 'D-' + Math.floor(ms / 864e5) + ' · ' : '') + Math.floor(ms % 864e5 / 36e5) + '시간 남음';
  }

  // 낱말 뜻 창 (JS가 없으면 링크대로 낱말 페이지로 이동)
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a.w') : null;
    if (!a || !window.WORDS) return;
    var w = window.WORDS[+a.getAttribute('data-w')];
    if (!w) return;
    e.preventDefault();
    var sh = $('#sheet');
    if (!sh) { sh = document.createElement('div'); sh.id = 'sheet'; sh.className = 'sheet'; sh.setAttribute('role', 'dialog'); document.body.appendChild(sh); }
    sh.innerHTML = '<b>' + esc(w.term) + '</b>' + (w.en ? '<span class="en">' + esc(w.en) + '</span>' : '') +
      '<p>' + esc(w.easy) + '</p><button class="go" type="button" id="shx">알겠어요</button>';
    sh.hidden = false;
    $('#shx').onclick = function () { sh.hidden = true; };
  });

  // 장 읽음 표시
  var doneBtn = $('#markread');
  if (doneBtn) {
    var cid = doneBtn.getAttribute('data-ch');
    var paint = function () { doneBtn.textContent = S.read[cid] ? '✓ 다 읽었어요 (취소하려면 누르기)' : '다 읽었어요 ✓'; };
    paint();
    doneBtn.onclick = function () { if (S.read[cid]) delete S.read[cid]; else S.read[cid] = 1; save(); paint(); };
  }
  var marks = document.querySelectorAll('[data-readmark]');
  for (var i = 0; i < marks.length; i++) if (S.read[marks[i].getAttribute('data-readmark')]) marks[i].textContent = '✓ 읽음';
  var stat = $('#stat');
  if (stat) {
    var r = Object.keys(S.right).length, w = Object.keys(S.wrong).length;
    stat.textContent = '읽은 장 ' + Object.keys(S.read).length + '개 · 퀴즈 ' + (r + w) + '문제 풀이 · 오답 ' + w + '개';
  }

  // 낱말 페이지 검색
  var sb = $('#wsearch');
  if (sb) sb.oninput = function () {
    var q = sb.value.trim().toLowerCase(), dts = document.querySelectorAll('.words dt');
    for (var i = 0; i < dts.length; i++) { var hit = !q || dts[i].textContent.toLowerCase().indexOf(q) >= 0 || dts[i].nextElementSibling.textContent.toLowerCase().indexOf(q) >= 0; dts[i].hidden = !hit; dts[i].nextElementSibling.hidden = !hit; }
  };

  // ---------- 퀴즈 ----------
  var box = $('#quiz');
  if (!box || !window.QUIZ) return;
  var Q = null;
  function name(id) { for (var i = 0; i < window.CHS.length; i++) if (window.CHS[i].id === id) return window.CHS[i].title; return ''; }
  function inCh(q, id) { for (var i = 0; i < window.CHS.length; i++) if (window.CHS[i].id === id) return window.CHS[i].groups.indexOf(q.ch) >= 0; return false; }
  function menu(msg) {
    var wn = window.QUIZ.filter(function (q) { return S.wrong[q.id]; }).length;
    var chips = window.CHS.map(function (c) { var n = window.QUIZ.filter(function (q) { return inCh(q, c.id); }).length; return n ? '<button class="chip" data-c="' + c.id + '">' + esc(c.title) + ' ' + n + '</button>' : ''; }).join('');
    box.innerHTML = (msg ? '<div class="fb ok">' + msg + '</div>' : '') +
      '<button class="go" data-m="10">랜덤 10문제</button><button class="go ghost" data-m="30">실전처럼 30문제</button>' +
      '<button class="go ghost" data-m="w">틀린 문제만 다시 (' + wn + ')</button>' +
      '<h3>장별로 풀기</h3><div class="chips">' + chips + '</div>' +
      '<p class="muted small">전체 ' + window.QUIZ.length + '문제 · 객관식, O/X, 단답형. 단답형은 써 보고 "확인", 표기만 달라 틀렸다고 나오면 "맞은 걸로"를 누르세요.</p>';
    var bs = box.querySelectorAll('[data-m]');
    for (var i = 0; i < bs.length; i++) bs[i].onclick = function () {
      var m = this.getAttribute('data-m');
      if (m === 'w') { var l = window.QUIZ.filter(function (q) { return S.wrong[q.id]; }); if (!l.length) return menu('틀린 문제가 없어요. 먼저 풀어 보세요.'); start(shuffle(l), '틀린 문제 다시'); }
      else start(shuffle(window.QUIZ).slice(0, +m), m === '10' ? '랜덤 10문제' : '실전 30문제');
    };
    var cs = box.querySelectorAll('[data-c]');
    for (var j = 0; j < cs.length; j++) cs[j].onclick = function () { var id = this.getAttribute('data-c'); start(shuffle(window.QUIZ.filter(function (q) { return inCh(q, id); })), name(id) + ' 문제'); };
  }
  function start(list, title) { Q = { list: list, i: 0, score: 0, title: title, missed: [] }; show(); }
  function norm(s) { return String(s).toLowerCase().replace(/[\s.,·\-_()'"~→]/g, ''); }
  function mark(q, ok) {
    if (ok) { Q.score++; S.right[q.id] = 1; delete S.wrong[q.id]; } else { S.wrong[q.id] = 1; delete S.right[q.id]; Q.missed.push(q); }
    save();
  }
  function answerText(q) { return q.type === 'mc' ? q.choices[q.answer] : q.type === 'ox' ? (q.answer ? 'O' : 'X') : q.answer; }
  function show() {
    window.scrollTo(0, 0);
    if (Q.i >= Q.list.length) return result();
    var q = Q.list[Q.i], body = '';
    if (q.type === 'mc') body = q.choices.map(function (c, k) { return '<button class="opt" data-k="' + k + '"><span class="k">' + '①②③④⑤'.charAt(k) + '</span><span>' + esc(c) + '</span></button>'; }).join('');
    if (q.type === 'ox') body = '<div class="ox"><button class="opt" data-k="1">O</button><button class="opt" data-k="0">X</button></div>';
    if (q.type === 'short') body = '<input class="ans" id="sa" autocomplete="off" placeholder="답을 써 보세요"><button class="go" id="sc">확인</button><button class="go ghost" id="ss">모르겠어요</button>';
    box.innerHTML = '<div class="qmeta"><span>' + esc(Q.title) + '</span><span>' + (Q.i + 1) + ' / ' + Q.list.length + '</span></div>' +
      '<div class="bar"><i style="width:' + (Q.i / Q.list.length * 100) + '%"></i></div>' +
      '<div class="qtext">' + esc(q.q) + '</div>' + body + '<div id="fb"></div>';
    function feedback(ok, extra) {
      $('#fb').innerHTML = '<div class="fb ' + (ok ? 'ok' : 'no') + '"><div class="v">' + (ok ? '정답!' : '아쉬워요 — 정답: ' + esc(answerText(q))) + '</div><p>' + esc(q.explain || '') + '</p>' +
        (q.src ? '<div class="src">출처: ' + esc(q.src) + '</div>' : '') + (extra || '') + '</div>' +
        '<button class="go" id="nx">' + (Q.i + 1 < Q.list.length ? '다음 문제 →' : '결과 보기') + '</button>';
      $('#nx').onclick = function () { Q.i++; show(); };
      if ($('#fix')) $('#fix').onclick = function () { Q.missed.pop(); delete S.wrong[q.id]; mark(q, true); Q.i++; show(); };
    }
    if (q.type !== 'short') {
      var os = box.querySelectorAll('.opt');
      for (var i = 0; i < os.length; i++) os[i].onclick = function () {
        var right = q.type === 'mc' ? q.answer : (q.answer ? 1 : 0), k = +this.getAttribute('data-k'), ok = k === right;
        for (var j = 0; j < os.length; j++) { os[j].disabled = true; if (+os[j].getAttribute('data-k') === right) os[j].className += ' ok'; }
        if (!ok) this.className += ' no';
        mark(q, ok); feedback(ok);
      };
    } else {
      var check = function (given) {
        var g = norm(given), cands = [q.answer].concat(q.alts || []).map(norm).filter(Boolean);
        var ok = !!g && cands.some(function (c) { return g === c || (c.length >= 2 && g.indexOf(c) >= 0) || (g.length >= 3 && c.indexOf(g) >= 0); });
        $('#sa').disabled = true; $('#sc').disabled = true; $('#ss').disabled = true;
        mark(q, ok);
        feedback(ok, ok ? '' : '<button class="chip" id="fix" style="margin-top:8px">맞은 걸로 (표기만 달랐어요)</button>');
      };
      $('#sc').onclick = function () { check($('#sa').value); };
      $('#ss').onclick = function () { check(''); };
      $('#sa').onkeydown = function (e) { if (e.key === 'Enter') check($('#sa').value); };
    }
  }
  function result() {
    var n = Q.list.length, p = Math.round(Q.score / n * 100);
    box.innerHTML = '<div class="score">' + Q.score + ' / ' + n + '</div><p class="big">' +
      (p >= 80 ? '좋아요! 이 정도면 B+ 충분해요.' : p >= 60 ? '절반 넘었어요. 틀린 것만 한 번 더!' : '괜찮아요. 해설 읽고 틀린 것만 다시 풀면 금방 올라요.') + '</p>' +
      (Q.missed.length ? '<button class="go" id="rw">틀린 ' + Q.missed.length + '문제 다시</button>' : '') + '<button class="go ghost" id="rm">퀴즈 처음으로</button>' +
      (Q.missed.length ? '<h3>틀린 문제</h3><ul>' + Q.missed.map(function (q) { return '<li>' + esc(q.q) + '<br><span class="muted">→ ' + esc(answerText(q)) + '</span></li>'; }).join('') + '</ul>' : '');
    if ($('#rw')) $('#rw').onclick = function () { start(shuffle(Q.missed), '틀린 문제 다시'); };
    $('#rm').onclick = function () { menu(); };
    window.scrollTo(0, 0);
  }
  var h = location.hash.slice(1);
  var hc = window.CHS.filter(function (c) { return c.id === h; })[0];
  if (hc) start(shuffle(window.QUIZ.filter(function (q) { return inCh(q, hc.id); })), hc.title + ' 문제'); else menu();
})();
