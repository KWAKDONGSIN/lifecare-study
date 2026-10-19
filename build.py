# content/의 쉬운 본문·문제·낱말을 읽어 GitHub Pages용 정적 사이트를 docs/에 만든다 (장마다 한 페이지)
import hashlib, html, json, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "content")
OUT = os.path.join(HERE, "docs")
# 폰 브라우저가 예전 CSS/JS를 붙잡지 않게, 파일 내용이 바뀌면 주소 뒤 버전도 바뀐다
VER = hashlib.md5(b"".join(open(os.path.join(HERE, "assets", f), "rb").read() for f in ("style.css", "app.js"))
                  + open(os.path.join(HERE, "content", "easy", "easy_data.json"), "rb").read()).hexdigest()[:8]

CHS = [  # (id, 제목, 한 줄 설명, 문제 그룹, 자료 출처 — 바탕화면 '라이프케어' 폴더 파일 이름 기준)
    ("c0", "왕초보 생명 기초", "세포 · DNA · 유전자 · 단백질 — 생물 처음이면 여기부터", ["basic"], "2주차 · 2. 기본생물학.pdf · 라이프02"),
    ("c1", "큰 그림 — 파이프라인", "설계도 책에서 오타 찾기 이야기", ["big", "etc"], "4·7주차 · 5. DNA variant 분석_수정.pdf · 라이프05·08"),
    ("c2", "바이오 기초", "센트럴 도그마 · 코돈 · 메틸화 · 돌연변이", ["bio"], "2주차 · 2. 기본생물학.pdf · 라이프02"),
    ("c3", "NGS", "Sanger vs NGS · SBS · Illumina가 이긴 이유", ["ngs"], "3주차 · 3. NGS 기술소개_리눅스환경.pdf · 라이프03"),
    ("c4", "FASTQ와 품질 점수", "4줄 구조 · Phred Q30", ["fastq"], "3주차 · 3. NGS 기술소개_리눅스환경.pdf · 라이프03"),
    ("c5", "Depth · 어디를 읽을까", "depth/coverage · WGS/WES/Targeted · 페어드엔드", ["depth"], "3·6주차 · 3. NGS · 5. DNA variant 분석 · 라이프03·07"),
    ("c6", "QC → 얼라인먼트 → BAM", "FastQC · 트리밍 · BWA · SAM/CIGAR · IGV", ["qc", "align", "sam", "linux"], "4·6·7주차 · 3. NGS(리눅스) · 5. DNA variant 분석 · 라이프05·07·08"),
    ("c7", "진짜 변이 골라내기", "MarkDuplicates · BQSR · HaplotypeCaller · VCF", ["post", "variant"], "7주차 · 5. DNA variant 분석_수정.pdf · 라이프08"),
    ("c8", "Annotation", "ANNOVAR · dbSNP · ClinVar", ["annot"], "7주차 · 5. DNA variant 분석_수정.pdf · 라이프08"),
    ("c9", "실습 따라가기", "명령 하나하나가 파이프라인의 어디인지", ["practice"], "3·6·7주차 실습 · read_fastq.ipynb · 5. DNA variant_실습_수정.pdf"),
]
GROUPS = {g for c in CHS for g in c[3]}
NAV = [("index.html", "보드"), ("b.html", "B코스"), ("bplus.html", "B+코스"), ("quiz.html", "퀴즈"), ("essay.html", "서술형"),
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
<link rel="stylesheet" href="assets/style.css?v={VER}">
</head>
<body>
<header class="top"><div class="top-in">
<a class="brand" href="index.html"><span class="bases"><i class="a">A</i><i class="t">T</i><i class="g">G</i><i class="c">C</i></span>라이프케어 시험공부</a>
<nav class="nav" aria-label="메뉴">{nav}</nav>
</div></header>
<main>
{body}
</main>
{scripts}<script src="assets/app.js?v={VER}"></script>
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


def plain(h, n=70):
    t = html.unescape(re.sub(r"<[^>]+>", "", h)).strip()
    t = re.sub(r"\s+", " ", t)
    return t if len(t) <= n else t[:n].rstrip() + "…"


def split_posts(body):
    """장 본문을 소단원(h3)마다 카드 한 장으로 자른다. 맨 끝 '이 장 3줄 요약'도 따로 한 장."""
    summ = ""
    m = re.search(r'<div class="box tip"><span class="t">이 장 3줄 요약</span>.*?</div>\s*$', body, re.S)
    if m:
        summ, body = m.group(0), body[:m.start()]
    parts = re.split(r"<h3>(.*?)</h3>", body, flags=re.S)
    posts = []
    for i in range(1, len(parts), 2):
        title = re.sub(r"^\s*(\d+-)?\d+\.\s*", "", html.unescape(re.sub(r"<[^>]+>", "", parts[i]))).strip()
        posts.append((title, parts[i + 1]))
    if summ:
        posts.append(("이 장 3줄 요약", summ))
    return parts[0], posts


def preview(h):
    m = re.search(r'<div class="box def">.*?<p>(.*?)</p>', h, re.S) or re.search(r"<p>(.*?)</p>", h, re.S)
    return plain(m.group(1)) if m else ""


def tags(h):
    out = []
    if 'class="box exam"' in h:
        out.append("✍ 시험 문장")
    if 'class="slide"' in h or "<svg" in h or 'class="seq"' in h:
        out.append("그림")
    if '<details class="check"' in h:
        out.append("확인 문제")
    return out


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
    wscript = f'<script src="assets/words.js?v={VER}"></script>\n'

    def write(fname, title, body, active, scripts=""):
        open(os.path.join(OUT, fname), "w", encoding="utf-8").write(page(fname, title, body, active, scripts))

    # 장 페이지
    for n, (cid, title, sub, groups, srcs) in enumerate(CHS):
        body = open(os.path.join(C, "easy", cid + ".html"), encoding="utf-8").read()
        body = re.sub(r"^\s*<!--.*?-->\s*", "", body, flags=re.S)
        body = link_words(webify(body), rx, idx)
        prev = f'<a href="{CHS[n - 1][0]}.html"><b>← 이전</b>{html.escape(CHS[n - 1][1])}</a>' if n else '<a href="index.html"><b>← 처음으로</b>홈</a>'
        nxt = f'<a class="next" href="{CHS[n + 1][0]}.html"><b>다음 →</b>{html.escape(CHS[n + 1][1])}</a>' if n + 1 < len(CHS) else '<a class="next" href="cheat.html"><b>다음 →</b>시험 전 1장</a>'
        head = f'<div class="chhead"><span>{n} / {len(CHS) - 1}장</span><a href="index.html">목차</a></div>'
        foot = (f'<div class="done"><button class="go ghost" id="markread" data-ch="{cid}" type="button">다 읽었어요 ✓</button>'
                f'<a class="go" href="quiz.html#{cid}">이 장 문제 풀기</a><div class="pn">{prev}{nxt}</div></div>')
        write(f"{cid}.html", title, head + body + foot, "c0.html", wscript)

    # 카드 페이지 + 보드 (패들렛처럼: 장마다 세로 칸, 소단원마다 카드)
    cols = []
    for n, (cid, title, sub, groups, srcs) in enumerate(CHS):
        body = open(os.path.join(C, "easy", cid + ".html"), encoding="utf-8").read()
        body = webify(re.sub(r"^\s*<!--.*?-->\s*", "", body, flags=re.S))
        intro, posts = split_posts(body)
        cards = []
        for k, (pt, ph) in enumerate(posts):
            fname = f"{cid}-{k + 1:02d}.html"
            prev = f"{cid}-{k:02d}.html" if k else "index.html#" + cid
            if k + 1 < len(posts):
                nxt, nxt_t = f"{cid}-{k + 2:02d}.html", posts[k + 1][0]
            elif n + 1 < len(CHS):
                nxt, nxt_t = f"{CHS[n + 1][0]}-01.html", f"{n + 1}장 {CHS[n + 1][1]} 시작"
            else:
                nxt, nxt_t = "cheat.html", "시험 전 1장"
            head = (f'<div class="crumb k{n}"><a href="index.html#{cid}">← 보드</a><span>{n}장 {html.escape(title)} · {k + 1}/{len(posts)}</span></div>'
                    f'<h1>{html.escape(pt)}</h1>')
            foot = (f'<div class="done"><a class="go" href="{nxt}">다음 카드 → {html.escape(nxt_t)}</a>'
                    f'<div class="pn"><a href="{prev}"><b>← 이전</b>{"이전 카드" if k else "보드로"}</a>'
                    f'<a class="next" href="quiz.html#{cid}"><b>연습</b>이 장 문제 풀기</a></div>'
                    f'<p class="muted small">자료: {html.escape(srcs)}</p></div>')
            write(fname, pt, head + link_words(ph, rx, idx) + foot, "index.html", wscript)
            img = re.search(r'<img src="(slides/[^"]+)"', ph)
            cards.append(f'<a class="post" href="{fname}">' + (f'<img src="{img.group(1)}" alt="" loading="lazy">' if img else "")
                         + f'<b>{html.escape(pt)}</b><span>{html.escape(preview(ph))}</span>'
                         + "".join(f"<i>{t}</i>" for t in tags(ph)) + "</a>")
        cols.append(f'<section class="col k{n}" id="{cid}"><div class="colhead"><b>{n}장 · {html.escape(title)}</b>'
                    f'<small>{html.escape(srcs)}</small><span class="cnt">카드 {len(posts)}장</span></div>'
                    + "".join(cards)
                    + f'<a class="post quiz" href="quiz.html#{cid}"><b>✓ 이 장 문제 풀기</b><span>읽은 다음 바로 확인</span></a></section>')

    files = [("라이프02.txt", "2주차", "2. 기본생물학.pdf"),
             ("라이프03.txt", "3주차", "3. NGS 기술소개_리눅스환경.pdf, read_fastq.ipynb, S1_S13 fastq 2개"),
             ("라이프05.txt", "4주차", "4. 팀별조사발표 안내 (시험 범위 아님) + 리눅스 실습"),
             ("라이프06.txt", "5주차", "학생 회사 발표 (시험 범위 아님)"),
             ("라이프07.txt", "6주차", "5. DNA variant 분석.pdf, 5. DNA variant_실습.pdf"),
             ("라이프08.txt", "7주차", "5. DNA variant 분석_수정.pdf, 실습_수정.pdf, 6. 암 조기진단(수업에서 안 나감)")]
    ftab = "".join(f"<tr><td>{a}</td><td><b>{b}</b></td><td>{c}</td></tr>" for a, b, c in files)
    start = f"""<section class="col kS" id="start"><div class="colhead"><b>시작하기</b><small>먼저 이 칸부터</small></div>
<div class="post note"><b>10/20(화) 12:30 중간고사</b><span id="dday">종이 시험 · 서술형+단답형</span><span>범위: 기본생물학 → NGS → FASTQ부터 variant calling까지. 코딩 문제 없음.</span></div>
<div class="post note"><b>쓰는 법</b><span>① 카드를 누르면 크게 열려요 ② 밑줄 친 낱말을 누르면 쉬운 뜻 ③ 옆으로 밀면 다음 장 칸 ④ 장 끝에서 "문제 풀기"</span></div>
<a class="post bplus" href="b.html"><b>★ 오늘 이것만: B 코스 (약 1시간)</b><span>제일 쉬운 설명 · 핵심 12개 · 약어 10 · 숫자 5 · 서술형 4</span></a>
<a class="post note" href="bplus.html"><b>★ 시간 없으면 여기만: B+ 최단 코스</b><span>약 2시간 · 핵심 카드 21장 · 약어 15 · 서술형 6 · 핵심 문제</span></a>
<a class="post go2" href="c0-01.html"><b>▶ 0장 첫 카드부터 시작</b><span>생물 처음이면 여기부터 순서대로</span></a>
<details class="post note"><summary><b>교수님 시험 힌트 (7주차)</b></summary><ul><li>"NGS가 뭔가" 같은 개념 설명</li><li>"GATK가 이니셜이 뭔가" — 약어 풀네임</li><li>디테일은 빼고 자주 나온 쉬운 개념</li><li>바이오 기초 · 파이프라인 순서와 이유 · NGS 개념</li></ul></details>
<details class="post note"><summary><b>자료 확인 — 바탕화면 파일과 주차</b></summary><p class="small">바탕화면 '라이프케어' 폴더 18개 파일이 이 사이트에 쓴 자료와 내용까지 같아요. 녹취 번호는 03 다음부터 하나씩 밀려 있어요.</p><div class="tw"><table><tr><th>파일</th><th>실제</th><th>같이 본 자료</th></tr>{ftab}</table></div><p class="small muted">1주차(오리엔테이션) 녹취는 이 폴더엔 없어요. 수업계획서는 평가 비율(중간 25%)만 썼어요.</p></details>
<p class="swipe">옆으로 밀면 0장 →</p></section>"""
    practice = """<section class="col kP" id="practice"><div class="colhead"><b>연습하기</b><small>읽고 나서 여기서 확인</small></div>
<a class="post" href="quiz.html"><b>퀴즈</b><span>객관식·OX·단답 114문제, 틀린 것만 다시</span></a>
<a class="post" href="essay.html"><b>서술형 27</b><span>쉬운 풀이 + 시험지에 쓸 모범답안</span></a>
<a class="post" href="cards.html"><b>암기카드</b><span>약어 풀네임 31 · 외울 숫자 20</span></a>
<a class="post" href="words.html"><b>낱말사전 167</b><span>모르는 말 찾기</span></a>
<a class="post go2" href="cheat.html"><b>시험 전 1장</b><span>암기표 · 헷갈리는 숫자 · 시험장에서 할 일</span></a></section>"""
    jump = "".join(f'<a href="#{c[0]}">{i}장</a>' for i, c in enumerate(CHS))
    home = (f'<div class="jump"><a href="#start">시작</a>{jump}<a href="#practice">연습</a></div>'
            f'<div class="board">{start}{"".join(cols)}{practice}</div>')
    write("index.html", "보드", home, "index.html")

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
    core_kw = ["NGS", "Sanger", "Illumina", "Roche", "Phred", "Q30", "FASTQ", "depth", "Depth", "coverage", "WGS", "WES", "Targeted",
               "페어드", "CIGAR", "MarkDuplicates", "BQSR", "GT", "VCF", "GATK", "HaplotypeCaller", "전사", "번역", "침묵", "넌센스",
               "미스센스", "메틸화", "풀네임", "ClinVar", "얼라인", "BWA", "트리밍", "어댑터", "Sequencing by Synthesis"]
    core = [q["id"] for q in uq if any(k in q["q"] for k in core_kw)]
    qjs = json.dumps([{k: q[k] for k in keep if k in q} for q in uq], ensure_ascii=False).replace("</", "<\\/")
    cjs = json.dumps([{"id": c[0], "title": c[1], "groups": c[3]} for c in CHS], ensure_ascii=False)
    write("quiz.html", "퀴즈", '<h1>퀴즈</h1><div id="quiz"><noscript><p>퀴즈는 자바스크립트가 필요해요. 서술형·암기카드 페이지는 없이도 돼요.</p></noscript></div>',
          "quiz.html", f"<script>window.QUIZ={qjs};window.CHS={cjs};window.CORE={json.dumps(core)};</script>\n")

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

    # B 코스 (시험 당일, 가장 쉬운 한 페이지)
    bb = open(os.path.join(C, "b.html"), encoding="utf-8").read()
    bb = link_words(webify(re.sub(r"^\s*<!--.*?-->\s*", "", bb, flags=re.S)), rx, idx)
    write("b.html", "B 코스", bb, "b.html", wscript)

    # B+ 최단 코스
    bp = open(os.path.join(C, "bplus.html"), encoding="utf-8").read()
    bp = link_words(webify(re.sub(r"^\s*<!--.*?-->\s*", "", bp, flags=re.S)), rx, idx)
    write("bplus.html", "B+ 최단 코스", bp, "bplus.html", wscript)

    print(f"장 {len(CHS)} · 핵심문제 {len(core)} · 문제 {len(uq)} · 서술형 {len(essays)} · 낱말 {len(words)} · 약어 {len(base['abbr'])} → {OUT}")


if __name__ == "__main__":
    main()
