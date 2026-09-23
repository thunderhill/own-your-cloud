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

    # Datelines, as in the per-chapter build.
    body = re.sub(r"<p><em>(Meridian · .*?)</em></p>", r'<p class="dateline dateline-fiction">\1</p>', body)
    body = re.sub(r"<p><em>(Build log · .*?)</em></p>", r'<p class="dateline dateline-record">\1</p>', body)
    body = re.sub(r"<p><em>((?:Public record|Briefing|Design guidance|Not independently verified) · .*?)</em></p>",
                  r'<p class="dateline dateline-public">\1</p>', body)
    body = body.replace("<hr />", '<hr class="scene-break" />')
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return body


def main():
    chapters = sorted(p for p in (ROOT / "chapters").glob("*.md"))
    pieces, toc = [], []

    for path in chapters:
        stem = path.stem
        key = stem[:2]
        if key in PARTS:
            part = PARTS[key]
            pieces.append(
                f'<section class="part-page"><p class="part-kicker">{part.split(" — ")[0]}</p>'
                f'<h1 class="part-title">{part.split(" — ")[1]}</h1>'
                f'<p class="part-epigraph">{PART_EPIGRAPH[part]}</p></section>'
            )
            toc.append(f'<li class="toc-part">{part}</li>')

        body = render(path)
        m = re.match(r'\s*<h1 id="([^"]*)">(.*?)</h1>', body, re.S)
        anchor, heading = (m.group(1), m.group(2)) if m else (stem, stem)
        body = body[m.end():] if m else body

        pieces.append(
            f'<section class="chapter" id="{anchor}">'
            f'<header class="ch-head"><h1>{heading}</h1></header>{body}</section>'
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
