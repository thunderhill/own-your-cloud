#!/usr/bin/env python3
"""Assemble the whole manuscript into one print-ready HTML document.

Usage:  python3 tools/build_pdf.py [out.html]

Everything is inlined — figures, and the cover's fonts and logos, become base64
data URIs — so the result is a single self-contained file. The front cover is its
first page and the back cover its last (both from cover/cover.html, A4 like the
interior, on a named CSS page with no margins). tools/build_pdf.sh then renders it with headless
Chrome, the same renderer the companion repo already uses.
"""
import base64
import pathlib
import re
import sys

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "html" / "own-your-cloud.html"

PARTS = {
    "01": "Part I — The Bill",
    "05": "Part II — The Factory",
    "10": "Part III — The Fabric",
    "13": "Part IV — The Brain",
    "17": "Part V — The Dividend",
}
PART_EPIGRAPH = {
    "Part I — The Bill": "Why. Business first; the machinery arrives only at the end.",
    "Part II — The Factory": "The cluster-provisioning story. Every number in this Part was measured.",
    "Part III — The Fabric": "The mesh. The confession, then the fix.",
    "Part IV — The Brain": "Agentic operations.",
    "Part V — The Dividend": "Back to the boardroom.",
}


def inline_figures(html: str) -> str:
    """Replace <img src="../figures/x.svg"> with a base64 data URI."""
    def repl(m):
        src = m.group(1)
        path = (ROOT / src.replace("../", "")).resolve()
        if not path.exists():
            print(f"  WARNING: figure not found: {src}", file=sys.stderr)
            return m.group(0)
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return m.group(0).replace(src, f"data:image/svg+xml;base64,{data}")

    return re.sub(r'<img [^>]*src="([^"]+)"', repl, html)


# ── illustrated styling: source badges, part colours, part-opener art ──────────
ICONS = {
    "meridian": '<svg viewBox="0 0 12 12"><circle cx="6" cy="4" r="2.2"/><path d="M1.8 10.8c.4-2.4 2.2-3.6 4.2-3.6s3.8 1.2 4.2 3.6z"/></svg>',
    "buildlog": '<svg viewBox="0 0 12 12"><rect x="1" y="2" width="10" height="8" rx="1.4" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M3 5l1.8 1.3L3 7.6" fill="none" stroke="currentColor" stroke-width="1.1"/><path d="M6.4 8h2.6" stroke="currentColor" stroke-width="1.1"/></svg>',
    "public": '<svg viewBox="0 0 12 12"><path d="M2.5 1.2h5l2.3 2.3v7.3h-7.3z" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M4 6h4M4 8h4" stroke="currentColor" stroke-width="1"/></svg>',
    "briefing": '<svg viewBox="0 0 12 12"><rect x="1" y="1.6" width="10" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M3 7l2-2 1.6 1.4L9 4M4 10.6h4" fill="none" stroke="currentColor" stroke-width="1.1"/></svg>',
}

def style_datelines(body: str) -> str:
    def badge(kind, label, rest):
        rest = f'<span class="badge-date">{rest}</span>' if rest else ""
        return (f'<p class="dateline dateline-{kind}"><span class="badge badge-{kind}">'
                f'{ICONS[kind]}{label}</span>{rest}</p>')

    def meridian(m):
        return badge("meridian", "Meridian", m.group(1))
    def buildlog(m):
        return badge("buildlog", "Build log", m.group(1))
    def public(m):
        label, rest = m.group(1), m.group(2)
        kind = "briefing" if label == "Briefing" else "public"
        return badge(kind, label, rest)

    body = re.sub(r"<p><em>Meridian · (.*?)</em></p>", meridian, body)
    body = re.sub(r"<p><em>Build log · (.*?)</em></p>", buildlog, body)
    body = re.sub(r"<p><em>(Public record|Briefing|Design guidance|Not independently verified) · (.*?)</em></p>",
                  public, body)
    return body


def wrap_records(body: str) -> str:
    """Give each dated source block a coloured rule down its left edge, ending at the next heading or scene break."""
    stop = re.compile(r'<h[12][ >]|<hr class="scene-break"|<p class="dateline|<div class="bookend')
    out, pos = [], 0
    for m in re.finditer(r'<p class="dateline dateline-(\w+)">', body):
        if m.start() < pos:
            continue
        nxt = stop.search(body, m.end())
        end = nxt.start() if nxt else len(body)
        out.append(body[pos:m.start()])
        out.append(f'<div class="rec rec-{m.group(1)}">{body[m.start():end]}</div>')
        pos = end
    out.append(body[pos:])
    return "".join(out)


def wrap_bookends(body: str) -> str:
    """The ledger / ask-your-team / open-the-repo sections become cards."""
    pat = re.compile(r'<h2 id="(the-ledger|ask-your-team|open-the-repo)">(.*?)</h2>')
    ms = list(pat.finditer(body))
    if not ms:
        return body
    out = [body[:ms[0].start()]]
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(body)
        out.append(f'<div class="bookend bookend-{m.group(1)}"><p class="bookend-title">{m.group(2)}</p>'
                   f'{body[m.end():end]}</div>')
    return "".join(out)


def part_class(num: int) -> str:
    for hi, cls in ((4, "part-1"), (9, "part-2"), (12, "part-3"), (16, "part-4"), (20, "part-5")):
        if num <= hi:
            return cls
    return ""


PART_CLASS = {"Part I": "part-1", "Part II": "part-2", "Part III": "part-3", "Part IV": "part-4", "Part V": "part-5"}

_S = 'viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"'
PART_ART = {
    "Part I": f'<svg {_S}><rect x="14" y="4" width="92" height="112" rx="4"/>'
              + "".join(f'<rect x="28" y="{y}" width="{w}" height="4" rx="2" fill="currentColor" stroke="none" opacity=".22"/>'
                        for y, w in ((20, 62), (30, 48), (40, 56), (50, 40), (60, 30)))
              + '<path d="M14 112C50 108 80 90 106 32" stroke-width="2"/><circle cx="106" cy="32" r="3.2" fill="currentColor"/></svg>',
    "Part II": f'<svg {_S}>' + "".join(
        f'<rect x="{i*7}" y="{i*7}" width="{120-i*14}" height="{120-i*14}" rx="{14-i*2}"/>' for i in range(6)) + '</svg>',
    "Part III": f'<svg viewBox="0 0 160 80" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="38" cy="40" r="34"/><circle cx="122" cy="40" r="34"/>'
                '<path d="M60 44h40" stroke-dasharray="3 3"/><circle cx="60" cy="44" r="2.6" fill="currentColor"/><circle cx="100" cy="44" r="2.6" fill="currentColor"/>'
                '<circle cx="26" cy="28" r="2.6" fill="currentColor"/><circle cx="26" cy="58" r="2.6" fill="currentColor"/>'
                '<circle cx="136" cy="28" r="2.6" fill="currentColor"/><circle cx="136" cy="58" r="2.6" fill="currentColor"/></svg>',
    "Part IV": f'<svg {_S}>' + "".join(
        f'<path d="M62 62L{x} {y}" opacity=".6"/><circle cx="{x}" cy="{y}" r="4.2" fill="#fff"/>'
        for x, y in ((14, 38), (46, 8), (100, 22), (112, 66), (84, 106), (24, 100)))
              + '<circle cx="62" cy="62" r="7" fill="currentColor" stroke="none"/></svg>',
    "Part V": f'<svg {_S}><path d="M2 20C40 30 66 84 118 112" stroke-width="2"/><path d="M2 112L118 8" opacity=".35" stroke-width="2"/>'
              '<circle cx="62" cy="62" r="3.4" fill="currentColor"/></svg>',
}


def data_uri(path: pathlib.Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def load_cover():
    """Return (css, front_cover_html, back_cover_html) from cover/cover.html, self-contained."""
    cover_dir = ROOT / "cover"
    src = (cover_dir / "cover.html").read_text()
    css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    body = re.search(r"<body>(.*?)</body>", src, re.S).group(1)

    css = re.sub(r"url\(([\w./-]+\.woff2)\)",
                 lambda m: f"url({data_uri(cover_dir / m.group(1), 'font/woff2')})", css)
    body = re.sub(r'src="([\w./-]+\.svg)"',
                  lambda m: f'src="{data_uri(cover_dir / m.group(1), "image/svg+xml")}"', body)

    sheets = re.findall(r"<section class=\"sheet\".*?</section>", body, re.S)
    if len(sheets) != 2:
        sys.exit(f"ERROR: expected front and back cover sections in cover/cover.html, found {len(sheets)}")
    return css, sheets[0], sheets[1]


def render(path: pathlib.Path) -> str:
    src = path.read_text()
    body = markdown.markdown(src, extensions=["tables", "fenced_code", "toc"])

    # Same figure/caption pairing as build_chapter.py.
    body = re.sub(
        r'<p>(<img [^>]*>)</p>\s*<p><em>(Figure [^<]*)</em></p>',
        r'<figure class="figure">\1<figcaption>\2</figcaption></figure>',
        body,
    )
    body = re.sub(r'<p>(<img [^>]*>)</p>', r'<figure class="figure">\1</figure>', body)
    body = inline_figures(body)

    body = style_datelines(body)
    body = wrap_records(body)
    body = wrap_bookends(body)
    body = body.replace("<hr />", '<hr class="scene-break" />')
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return body


def main():
    chapters = sorted(p for p in (ROOT / "chapters").glob("*.md"))
    pieces, toc = [], []
    titles = {}
    for p_ in chapters:
        t = (ROOT / "chapters" / p_.name).read_text().splitlines()[0]
        mt = re.match(r"# Chapter (\d+) — (.*)", t)
        if mt:
            titles[int(mt.group(1))] = mt.group(2)

    for path in chapters:
        stem = path.stem
        key = stem[:2]
        if key in PARTS:
            part = PARTS[key]
            roman, ptitle = part.split(" — ")
            cur_part = PART_CLASS[roman]
            first = int(key)
            last = {"01": 4, "05": 9, "10": 12, "13": 16, "17": 20}[key]
            chlist = "".join(
                f'<li>Chapter {n} — {titles[n]}</li>' for n in range(first, last + 1) if n in titles)
            pieces.append(
                f'<section class="part-page {cur_part}"><span class="part-bar"></span>'
                f'<div class="part-text"><span class="part-rule"></span><p class="part-kicker">{roman}</p>'
                f'<h1 class="part-title">{ptitle}</h1>'
                f'<p class="part-epigraph">{PART_EPIGRAPH[part]}</p></div>'
                f'<div class="part-art">{PART_ART[roman]}</div>'
                f'<ul class="part-chapters">{chlist}</ul></section>'
            )
            toc.append(f'<li class="toc-part">{part}</li>')

        body = render(path)
        m = re.match(r'\s*<h1 id="([^"]*)">(.*?)</h1>', body, re.S)
        anchor, heading = (m.group(1), m.group(2)) if m else (stem, stem)
        body = body[m.end():] if m else body

        mnum = re.match(r"Chapter (\d+) — (.*)", re.sub(r"<[^>]+>", "", heading))
        if mnum:
            cnum = int(mnum.group(1))
            cls = part_class(cnum)
            head = (f'<p class="ch-num">{cnum:02d}</p><p class="ch-kicker">Chapter {cnum}</p>'
                    f'<h1>{mnum.group(2)}</h1>')
        else:
            cls = "" if stem[:2] not in ("00", "99") else ""
            head = f'<h1>{heading}</h1>'
        pieces.append(
            f'<section class="chapter {cls}" id="{anchor}">'
            f'<header class="ch-head">{head}</header>{body}</section>'
        )
        toc.append(f'<li class="toc-ch"><a href="#{anchor}">{heading}</a></li>')

    cover_css, front_cover, back_cover = load_cover()
    html = (TEMPLATE
            .replace("{{COVER_CSS}}", cover_css)
            .replace("{{FRONT_COVER}}", front_cover)
            .replace("{{BACK_COVER}}", back_cover)
            .replace("{{TOC}}", "\n".join(toc))
            .replace("{{BODY}}", "\n".join(pieces)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"wrote {OUT}  ({len(html):,} bytes, {len(chapters)} sections)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Own Your Cloud</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT@9..144,400,50;9..144,600,50;9..144,700,50&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Public+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Print-only: one light palette. The screen build keeps the dark theme; a PDF
   is ink on paper, so the dark half is deliberately absent here. */
:root {
  color-scheme: light;
  --ink:#1B2430; --ink-2:#4A5563; --ink-3:#737C86;
  --rule:#D6DAD3; --rule-strong:#B8BFB6;
  --accent:#1F5F4A; --accent-soft:#E3EDE7; --code-bg:#F1F3EF;
  --display:"Fraunces","Iowan Old Style",Georgia,serif;
  --text:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --sans:"Public Sans","Helvetica Neue",Arial,sans-serif;
  --mono:"IBM Plex Mono",Menlo,Consolas,monospace;
}
@page { size: A4; margin: 20mm 18mm 20mm 18mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin:0; font-family:var(--text); font-size:10.5pt; line-height:1.55; color:var(--ink); background:#fff; }

/* ── title page ─────────────────────────────────────────── */
.title-page { height: 245mm; display:flex; flex-direction:column; justify-content:center; text-align:center; break-after:page; }
.title-page h1 { font-family:var(--display); font-size:40pt; line-height:1.05; margin:0 0 6mm; letter-spacing:-.01em; }
.title-page .sub { font-family:var(--sans); font-size:12pt; color:var(--ink-2); margin:0 0 18mm; }
.title-page .byline { font-family:var(--sans); font-size:11pt; color:var(--ink); }
.title-page .meta { font-family:var(--sans); font-size:9pt; color:var(--ink-3); margin-top:14mm; line-height:1.7; }
.rule-short { width:28mm; height:2px; background:var(--accent); margin:0 auto 10mm; }

/* ── contents ───────────────────────────────────────────── */
.contents { break-after:page; }
.contents h2 { font-family:var(--display); font-size:20pt; margin:0 0 8mm; }
.contents ol { list-style:none; padding:0; margin:0; }
.toc-part { font-family:var(--sans); font-weight:600; font-size:10pt; color:var(--accent);
            margin:7mm 0 2mm; text-transform:uppercase; letter-spacing:.06em; }
.toc-ch { margin:1.6mm 0; font-size:11pt; }
.toc-ch a { color:var(--ink); text-decoration:none; }

/* ── part dividers ──────────────────────────────────────── */
.part-page { break-before:page; break-after:page; height:230mm; display:flex; flex-direction:column; justify-content:center; text-align:center; }
.part-kicker { font-family:var(--sans); font-size:10pt; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); margin:0 0 4mm; }
.part-title { font-family:var(--display); font-size:30pt; margin:0 0 6mm; }
.part-epigraph { font-family:var(--sans); font-size:10.5pt; color:var(--ink-2); font-style:italic; margin:0 auto; max-width:110mm; }

/* ── chapters ───────────────────────────────────────────── */
.chapter { break-before:page; }
.ch-head h1 { font-family:var(--display); font-size:23pt; line-height:1.15; margin:0 0 7mm; }
.chapter h2 { font-family:var(--display); font-size:14.5pt; margin:8mm 0 3mm; break-after:avoid; }
.chapter h3 { font-family:var(--sans); font-weight:600; font-size:11.5pt; margin:6mm 0 2mm; break-after:avoid; }
p { margin:0 0 3.2mm; orphans:3; widows:3; }
strong { font-weight:600; }
a { color:var(--accent); }

blockquote { margin:0 0 6mm; padding-left:5mm; border-left:2px solid var(--accent);
             font-family:var(--sans); font-size:10pt; color:var(--ink-2); font-style:italic; }
blockquote p { margin:0 0 1.6mm; }

.dateline { font-family:var(--sans); font-size:8.5pt; letter-spacing:.06em; text-transform:uppercase;
            color:var(--ink-3); margin:6mm 0 2.5mm; break-after:avoid; }
.dateline-record { color:var(--accent); }
.scene-break { border:0; text-align:center; margin:6mm 0; }
.scene-break::after { content:"* * *"; color:var(--ink-3); letter-spacing:.5em; }

ul, ol { margin:0 0 3.5mm; padding-left:6mm; }
li { margin:0 0 1.4mm; }

.table-wrap { break-inside:avoid; margin:0 0 5mm; }
table { width:100%; border-collapse:collapse; font-family:var(--sans); font-size:8.6pt; }
th, td { border-bottom:1px solid var(--rule); padding:1.6mm 2mm; text-align:left; vertical-align:top; }
th { border-bottom:1.5px solid var(--rule-strong); font-weight:600; }

pre { background:var(--code-bg); border:1px solid var(--rule); border-radius:2mm;
      padding:3mm; margin:0 0 4mm; overflow:hidden; break-inside:avoid; }
pre code { font-family:var(--mono); font-size:8pt; line-height:1.45; white-space:pre-wrap; word-break:break-word; }
code { font-family:var(--mono); font-size:8.8pt; background:var(--code-bg); padding:.2mm 1mm; border-radius:1mm; }
pre code { background:none; padding:0; }

.figure { break-inside:avoid; margin:6mm 0; }
.figure img { width:100%; height:auto; border:1px solid var(--rule); border-radius:2mm; box-sizing:border-box; }
/* border-box matters: with the default box model the 1px border makes each image 2px wider than the
   text column, and Chrome then shrinks the whole printed document to fit (about 0.3%). */
.figure figcaption { font-family:var(--sans); font-size:8.5pt; color:var(--ink-3); margin-top:2mm; }

/* ── illustrated styling (palette and art from the illustrated edition) ── */
:root { --part:#1F5F4A; --meridian:#A8700E; --buildlog:#1F7A5A; --public:#2F5FBF; --briefing:#6D4BC4; }
.part-1 { --part:#B4432F; } .part-2 { --part:#0086A8; } .part-3 { --part:#2F5FBF; }
.part-4 { --part:#6D4BC4; } .part-5 { --part:#A8700E; }

@page part { size:A4; margin:0; }
.part-page { page:part; position:relative; text-align:left; justify-content:flex-start; height:297mm; padding:82mm 18mm 0 26mm; box-sizing:border-box; color:var(--ink); }
.part-bar { position:absolute; left:0; top:0; width:5mm; height:297mm; background:var(--part); }
.part-rule { display:block; width:11mm; height:2px; background:var(--part); margin-bottom:5mm; }
.part-kicker { color:var(--part); font-weight:600; font-size:8.5pt; letter-spacing:.3em; margin:0 0 3mm; }
.part-title { font-size:34pt; font-weight:400; margin:0 0 9mm; }
.part-epigraph { text-align:left; margin:0; max-width:100mm; font-family:var(--text); color:var(--ink-2); }
.part-art { position:absolute; right:18mm; bottom:62mm; width:52mm; color:var(--part); }
.part-art svg { width:100%; height:auto; display:block; }
.part-chapters { position:absolute; left:26mm; right:18mm; bottom:24mm; list-style:none; margin:0; padding:3mm 0 0;
                 border-top:1px solid var(--rule); font-family:var(--sans); font-size:8.5pt; color:var(--ink-2); }
.part-chapters li { margin:0 0 1mm; }

.chapter .ch-head { margin-bottom:8mm; }
.ch-num { font-family:var(--display); font-size:50pt; line-height:1; font-weight:400; color:var(--part); margin:6mm 0 0; }
.ch-kicker { font-family:var(--sans); font-weight:600; font-size:7.5pt; letter-spacing:.2em; text-transform:uppercase; color:var(--part); margin:1mm 0 3mm; }
.chapter h2 { font-family:var(--sans); font-weight:600; font-size:12.5pt; position:relative; padding-left:6.5mm; margin:9mm 0 3.5mm; }
.chapter h2::before { content:""; position:absolute; left:0; top:.32em; width:2.8mm; height:2.8mm; border-radius:.6mm; background:var(--part); }
.chapter ol { list-style:none; counter-reset:n; padding-left:0; }
.chapter ol > li { counter-increment:n; position:relative; padding-left:8mm; }
.chapter ol > li::before { content:counter(n); position:absolute; left:0; top:.2em; width:5mm; height:5mm; border-radius:50%;
  background:var(--part); color:#fff; font:600 7pt/5mm var(--sans); text-align:center; }
.chapter blockquote { border-left-color:var(--part); }
.chapter th { border-bottom-color:var(--part); }

.dateline { text-transform:none; letter-spacing:0; margin:5mm 0 3mm; display:flex; align-items:center; gap:2.5mm; }
.badge { display:inline-flex; align-items:center; gap:1.4mm; font-family:var(--sans); font-weight:600; font-size:6.8pt;
         letter-spacing:.14em; text-transform:uppercase; color:#fff; padding:.7mm 2mm .7mm 1.6mm; border-radius:1mm; }
.badge svg { width:2.9mm; height:2.9mm; fill:currentColor; }
.badge-date { font-family:var(--sans); font-size:7pt; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-3); }
.badge-meridian { background:var(--meridian); } .badge-buildlog { background:var(--buildlog); }
.badge-public { background:var(--public); } .badge-briefing { background:var(--briefing); }
.rec { border-left:2px solid; padding-left:4mm; margin-left:-1mm; }
.rec-meridian { border-color:#E3CF9F; } .rec-buildlog { border-color:#BFDCCF; }
.rec-public { border-color:#C5D3F0; } .rec-briefing { border-color:#D6CCF0; }

.bookend { border:1px solid var(--rule); border-top:2px solid var(--ink); border-radius:1.5mm; padding:2mm 5mm 1mm; margin:7mm 0; font-size:9.6pt; }
.bookend-ask-your-team { border-top-color:var(--part); }
.bookend-open-the-repo { border-top-color:var(--ink-3); background:#FAFAF7; }
.bookend-title { font-family:var(--sans); font-weight:600; font-size:8pt; letter-spacing:.2em; text-transform:uppercase; margin:2mm 0 3mm; }
.bookend ul, .bookend ol { margin-bottom:2.5mm; }

/* ── front and back cover (cover/cover.html) ───────────── */
{{COVER_CSS}}
</style>
</head><body>

{{FRONT_COVER}}

<section class="title-page">
  <div class="rule-short"></div>
  <h1>Own Your Cloud</h1>
  <p class="sub">From Cloud Tenant to Infrastructure Owner<br>a sovereign-Kubernetes story told in chapters</p>
  <p class="byline">Mahipal</p>
  <p class="meta">
    Second draft · September 2026<br>
    Meridian scenes are composite fiction. Build-log sections, and every number in them,<br>
    were measured on the companion platform repository.
  </p>
</section>

<section class="contents">
  <h2>Contents</h2>
  <ol>{{TOC}}</ol>
</section>

{{BODY}}

{{BACK_COVER}}
</body></html>
"""

if __name__ == "__main__":
    main()
