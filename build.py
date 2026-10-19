# content/의 쉬운 본문·문제·낱말을 읽어 GitHub Pages용 정적 사이트를 docs/에 만든다 (장마다 한 페이지)
import hashlib, html, json, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "content")
OUT = os.path.join(HERE, "docs")

CHS = [  # (id, 제목, 한 줄 설명, 문제 그룹)
    ("c0", "왕초보 생명 기초", "세포 · DNA · 유전자 · 단백질 — 생물 처음이면 여기부터", ["basic"]),
    ("c1", "큰 그림 — 파이프라인", "설계도 책에서 오타 찾기 이야기", ["big", "etc"]),
    ("c2", "바이오 기초", "센트럴 도그마 · 코돈 · 메틸화 · 돌연변이", ["bio"]),
    ("c3", "NGS", "Sanger vs NGS · SBS · Illumina가 이긴 이유", ["ngs"]),
    ("c4", "FASTQ와 품질 점수", "4줄 구조 · Phred Q30", ["fastq"]),
    ("c5", "Depth · 어디를 읽을까", "depth/coverage · WGS/WES/Targeted · 페어드엔드", ["depth"]),
    ("c6", "QC → 얼라인먼트 → BAM", "FastQC · 트리밍 · BWA · SAM/CIGAR · IGV", ["qc", "align", "sam", "linux"]),
    ("c7", "진짜 변이 골라내기", "MarkDuplicates · BQSR · HaplotypeCaller · VCF", ["post", "variant"]),
    ("c8", "Annotation", "ANNOVAR · dbSNP · ClinVar", ["annot"]),
    ("c9", "실습 따라가기", "명령 하나하나가 파이프라인의 어디인지", ["practice"]),
]
GROUPS = {g for c in CHS for g in c[3]}
NAV = [("index.html", "홈"), ("c0.html", "공부"), ("quiz.html", "퀴즈"), ("essay.html", "서술형"),
       ("cards.html", "암기카드"), ("words.html", "낱말사전"), ("cheat.html", "시험 전 1장")]
VOID = {"br", "img", "meta", "link", "hr", "input", "source", "wbr", "col", "area", "base", "embed", "param", "track"}
SKIP = {"svg", "code", "h1", "h2", "h3", "summary", "figcaption", "a", "button", "script", "style", "th"}


def load(name):
    return json.load(open(os.path.join(C, name), encoding="utf-8"))


def page(fname, title, body, active, scripts=""):
    nav = "".join(f'<a href="{h}"{" class=on" if h == active else ""}>{t}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)} · 라이프케어 시험공부</title>
<meta name="description" content="라이프케어빅데이터분석 중간고사를 생물 처음인 사람도 이해하게 정리한 공부 사이트">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top"><div class="top-in">
<a class="brand" href="index.html"><span class="bases"><i class="a">A</i><i class="t">T</i><i class="g">G</i><i class="c">C</i></span>라이프케어 시험공부</a>
<nav class="nav" aria-label="메뉴">{nav}</nav>
</div></header>
<main>
{body}
</main>
{scripts}<script src="assets/app.js"></script>
</body>
</html>
"""


def webify(s):
    s = re.sub(r'(<svg\b.*?</svg>)', r'<div class="paper">\1</div>', s, flags=re.S)
    s = re.sub(r'(<svg[^>]*?)\s+width="\d+mm"', r"\1", s)
    s = re.sub(r'(<table\b.*?</table>)', r'<div class="tw">\1</div>', s, flags=re.S)
    return s


def glossary_regex(words):
    idx, keys = {}, []
    for i, w in enumerate(words):
        for k in [w["term"]] + w.get("aka", []):
            k = (k or "").strip()
            if len(k) >= 2 and k.lower() not in idx:
                idx[k.lower()] = i
                keys.append(k)
    keys.sort(key=len, reverse=True)
    return re.compile("|".join(re.escape(k) for k in keys), re.I), idx


def link_words(s, rx, idx):
    """본문 글자 속 낱말을 처음 한 번만 a.w 링크로 바꾼다. 제목·그림·코드·링크 안은 건드리지 않는다."""
    seen, out, stack = set(), [], []

    def repl(text):
        res, last = [], 0
        for m in rx.finditer(text):
            k = m.group(0)
            if k[0].isascii() and k[0].isalnum():  # 영어 약어는 단어 중간에서 잡지 않는다
                b = text[m.start() - 1] if m.start() else ""
                a = text[m.end()] if m.end() < len(text) else ""
                if (b.isascii() and b.isalnum()) or (a.isascii() and a.isalnum()):
                    continue
            i = idx[k.lower()]
            if i in seen:
                continue
            seen.add(i)
            res.append(text[last:m.start()])
            res.append(f'<a class="w" href="words.html#w{i}" data-w="{i}">{k}</a>')
            last = m.end()
        res.append(text[last:])
        return "".join(res)

    for tok in re.split(r"(<[^>]+>)", s):
        if tok.startswith("<"):
            m = re.match(r"<\s*(/)?\s*([a-zA-Z][a-zA-Z0-9]*)([^>]*)>", tok)
            if m:
                close, name, attrs = m.group(1), m.group(2).lower(), m.group(3)
                if close:
                    while stack:
                        if stack.pop()[0] == name:
                            break
                elif name not in VOID and not attrs.rstrip().endswith("/"):
                    skip = name in SKIP or bool(re.search(r'class="[^"]*\b(t|seq|flow|code)\b', attrs))
                    stack.append((name, skip))
            out.append(tok)
        elif tok.strip() and not any(sk for _, sk in stack):
            out.append(repl(tok))
        else:
            out.append(tok)
    return "".join(out)


def pdf_section(no):
    src = open(os.path.join(C, "시험대비_쉬운설명.html"), encoding="utf-8").read()
    for s in re.findall(r'<section class="ch">(.*?)</section>', src, re.S):
        if f'<span class="chno">{no}장</span>' in s:
            return re.sub(r'<span class="chno">.*?</span>\s*', "", s)
    raise KeyError(no)


def qid(q):
    return hashlib.md5(re.sub(r"\s+", "", q["q"]).encode()).hexdigest()[:8]


def check(q):
    assert q["type"] in ("mc", "ox", "short") and q["q"].strip(), q
    if q["type"] == "mc":
        assert 2 <= len(q["choices"]) <= 5 and 0 <= q["answer"] < len(q["choices"]), q
    elif q["type"] == "ox":
        assert isinstance(q["answer"], bool), q
    else:
        assert isinstance(q["answer"], str) and q["answer"].strip(), q


def main():
    base, easy = load("base_data.json"), load("easy/easy_data.json")
    ex = [load(n) for n in ("extract_w1_4.json", "extract_w5_7.json", "extract_notes.json")]
    words = easy["glossary"]
    rx, idx = glossary_regex(words)

    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(OUT, "assets"))
    shutil.copytree(os.path.join(C, "slides"), os.path.join(OUT, "slides"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    wjs = json.dumps([{"term": w["term"], "en": w.get("en", ""), "easy": w["easy"]} for w in words], ensure_ascii=False)
    open(os.path.join(OUT, "assets", "words.js"), "w", encoding="utf-8").write("window.WORDS=" + wjs + ";\n")
    wscript = '<script src="assets/words.js"></script>\n'

    def write(fname, title, body, active, scripts=""):
        open(os.path.join(OUT, fname), "w", encoding="utf-8").write(page(fname, title, body, active, scripts))

    # 장 페이지
    for n, (cid, title, sub, groups) in enumerate(CHS):
        body = open(os.path.join(C, "easy", cid + ".html"), encoding="utf-8").read()
        body = re.sub(r"^\s*<!--.*?-->\s*", "", body, flags=re.S)
        body = link_words(webify(body), rx, idx)
        prev = f'<a href="{CHS[n - 1][0]}.html"><b>← 이전</b>{html.escape(CHS[n - 1][1])}</a>' if n else '<a href="index.html"><b>← 처음으로</b>홈</a>'
        nxt = f'<a class="next" href="{CHS[n + 1][0]}.html"><b>다음 →</b>{html.escape(CHS[n + 1][1])}</a>' if n + 1 < len(CHS) else '<a class="next" href="cheat.html"><b>다음 →</b>시험 전 1장</a>'
        head = f'<div class="chhead"><span>{n} / {len(CHS) - 1}장</span><a href="index.html">목차</a></div>'
        foot = (f'<div class="done"><button class="go ghost" id="markread" data-ch="{cid}" type="button">다 읽었어요 ✓</button>'
                f'<a class="go" href="quiz.html#{cid}">이 장 문제 풀기</a><div class="pn">{prev}{nxt}</div></div>')
        write(f"{cid}.html", title, head + body + foot, "c0.html", wscript)

    # 홈
    path = "".join(f'<li><a href="{c}.html"><span class="no">{i}</span><span class="tt">{html.escape(t)}<small>{html.escape(s)}</small></span>'
                   f'<span class="ok" data-readmark="{c}"></span></a></li>' for i, (c, t, s, g) in enumerate(CHS))
    home = f"""<section class="hero">
<span class="dday" id="dday">10/20(화) 12:30</span>
<h1>라이프케어빅데이터분석<br>중간고사 공부</h1>
<p>종이 시험 · 서술형과 단답형 · 범위는 <b>기본생물학 → NGS → FASTQ부터 variant calling까지</b>. 코딩 문제는 없어요.</p>
<a class="go" href="c0.html">생물 처음이면 0장부터 시작</a>
<p class="muted small" id="stat">밑줄 친 낱말을 누르면 쉬운 뜻이 나와요.</p>
</section>
<div class="box pro"><span class="t">교수님이 직접 말한 시험 힌트 (7주차)</span>
<ul><li>"NGS가 뭔가" 같은 <b>개념 설명</b>을 많이 물어봐요</li><li>"GATK가 이니셜이 뭔가" — <b>약어 풀네임</b></li>
<li>디테일은 빼고 <b>수업에 자주 나온 쉬운 개념</b> 위주</li><li>중요한 3가지 — 바이오 기초 · 파이프라인 순서와 이유 · NGS 개념</li></ul></div>
<h2>순서대로 읽기</h2>
<ol class="path">{path}<li><a href="cheat.html"><span class="no">★</span><span class="tt">시험 전 1장<small>암기표 · 헷갈리는 숫자 · 시험장에서 할 일</small></span></a></li></ol>
<h2 style="margin-top:28px">연습하기</h2>
<div class="grid2">
<a href="quiz.html">퀴즈<small>객관식·OX·단답 문제</small></a>
<a href="essay.html">서술형<small>모범답안 + 쉬운 풀이</small></a>
<a href="cards.html">암기카드<small>약어 풀네임 · 숫자</small></a>
<a href="words.html">낱말사전<small>모르는 말 찾기</small></a>
</div>
<div class="box tip"><span class="t">오늘 공부 순서</span><ul>
<li>0장 → 9장을 순서대로 읽고, 장마다 <b>"이 장 문제 풀기"</b></li>
<li>저녁엔 서술형 10개를 <b>종이에 직접</b> 써 보기</li>
<li>시험 날 아침엔 <b>암기카드 + 틀린 문제만 다시 + 시험 전 1장</b></li></ul></div>
<p class="muted small">근거 — 1~7주차 수업 녹취, 교수님 강의자료(기본생물학 · NGS · DNA variant 분석), 실습자료. 진도는 이 폰 브라우저에만 저장돼요.</p>"""
    write("index.html", "홈", home, "index.html")

    # 퀴즈
    quiz = list(base["quiz"])
    for x in ex:
        quiz += x.get("quiz", [])
    uq, seen = [], set()
    for q in quiz:
        check(q)
        if q.get("ch") not in GROUPS:
            q["ch"] = "etc"
        q["id"] = qid(q)
        q["explain"] = easy["explain"].get(q["id"], q.get("explain", ""))
        if q["id"] not in seen:
            seen.add(q["id"]); uq.append(q)
    keep = ("id", "ch", "type", "q", "choices", "answer", "alts", "explain", "src")
    qjs = json.dumps([{k: q[k] for k in keep if k in q} for q in uq], ensure_ascii=False).replace("</", "<\\/")
    cjs = json.dumps([{"id": c[0], "title": c[1], "groups": c[3]} for c in CHS], ensure_ascii=False)
    write("quiz.html", "퀴즈", '<h1>퀴즈</h1><div id="quiz"><noscript><p>퀴즈는 자바스크립트가 필요해요. 서술형·암기카드 페이지는 없이도 돼요.</p></noscript></div>',
          "quiz.html", f"<script>window.QUIZ={qjs};window.CHS={cjs};</script>\n")

    # 서술형
    essays = list(base["essay"])
    for x in ex:
        essays += x.get("essay", [])
    items = []
    for i, e in enumerate(essays):
        assert e["q"].strip() and e["a"].strip() and e["keys"], e
        ez = easy["essay_easy"].get("e%02d" % i, "")
        items.append(f'<details class="card"><summary>{i + 1}. {html.escape(e["q"])}</summary><div class="in">'
                     + (f'<div class="easy"><b>쉽게 말하면</b><p>{html.escape(ez)}</p></div>' if ez else "")
                     + f'<div class="model"><b>시험지엔 이렇게 써요</b><p>{html.escape(e["a"])}</p></div>'
                     + '<div class="keys">' + "".join(f"<span>{html.escape(k)}</span>" for k in e["keys"]) + "</div></div></details>")
    write("essay.html", "서술형", '<h1>서술형 연습</h1><p class="muted">문제를 먼저 종이에 써 보고, 눌러서 답을 확인하세요. '
          '공식은 <b>정의 → 왜(목적) → 예시·숫자</b>. 노란 칸은 꼭 들어가야 할 키워드예요.</p>' + "".join(items), "essay.html")

    # 암기카드
    ab = "".join(f'<details class="card"><summary><span class="abbr">{html.escape(a)}</span></summary><div class="in"><b>{html.escape(f)}</b><p>{html.escape(m)}</p></div></details>' for a, f, m in base["abbr"])
    nb = "".join(f'<details class="card"><summary>{html.escape(a)}</summary><div class="in"><b>{html.escape(v)}</b></div></details>' for a, v in base["numbers"])
    write("cards.html", "암기카드", '<h1>암기카드</h1><p class="muted">눌러서 뒷면 보기. 교수님이 "GATK가 이니셜이 뭔가" 같은 문제를 낸다고 했어요.</p>'
          f'<h2>약어 풀네임 ({len(base["abbr"])})</h2>{ab}<h2 style="margin-top:28px">외울 숫자 ({len(base["numbers"])})</h2>{nb}', "cards.html")

    # 낱말사전
    dl = "".join(f'<dt id="w{i}">{html.escape(w["term"])}' + (f'<small>{html.escape(w["en"])}</small>' if w.get("en") else "")
                 + f'</dt><dd>{html.escape(w["easy"])}</dd>' for i, w in enumerate(words))
    write("words.html", "낱말사전", f'<h1>낱말사전</h1><p class="muted">{len(words)}개 · 본문에서 밑줄 친 말을 누르면 여기 뜻이 떠요.</p>'
          f'<input class="search" id="wsearch" placeholder="찾을 낱말 (예: 전사, CIGAR)"><dl class="words">{dl}</dl>', "words.html")

    # 시험 전 1장
    memo = "".join(f'<div class="box gray"><span class="t">{html.escape(c["title"])}</span><p>{c["body"]}</p></div>' for c in ex[2]["concepts"])
    cheat = link_words(webify(pdf_section(9)) + '<h2 style="margin-top:30px">헷갈리는 숫자</h2>' + memo + webify(pdf_section(11)), rx, idx)
    write("cheat.html", "시험 전 1장", cheat, "cheat.html", wscript)

    print(f"장 {len(CHS)} · 문제 {len(uq)} · 서술형 {len(essays)} · 낱말 {len(words)} · 약어 {len(base['abbr'])} → {OUT}")


if __name__ == "__main__":
    main()
