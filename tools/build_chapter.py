import re
import pathlib
import markdown

import sys
SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
PART = sys.argv[3]

src = SRC.read_text()
prose = src.split("## Draft notes")[0]
words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.\-/%]*", prose))

body = markdown.markdown(src, extensions=["tables", "fenced_code", "toc"])

m = re.match(r'\s*<h1 id="[^"]*">(?:Chapter (\d+)|(Prologue|Epilogue|Appendices)) — (.*?)</h1>\s*<blockquote>\s*(.*?)</blockquote>', body, re.S)
num, bookend, title, epigraph = m.groups()
num = num or ""
body = body[m.end():]

body = re.sub(r"<p><em>(Meridian · .*?)</em></p>", r'<p class="dateline dateline-fiction">\1</p>', body)
body = re.sub(r"<p><em>(Build log · .*?)</em></p>", r'<p class="dateline dateline-record">\1</p>', body)
body = re.sub(r"<p><em>((?:Public record|Briefing) · .*?)</em></p>", r'<p class="dateline dateline-public">\1</p>', body)
has_public = "dateline-public" in body
body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
body = body.replace("<hr />", '<hr class="scene-break" />')
body = body.replace('<pre><code class="language-agent">', '<pre class="agent-reply"><code>')

starts = [body.find(f'<h2 id="{k}">') for k in ("the-ledger", "ask-your-team", "open-the-repo")]
starts = [x for x in starts if x >= 0]
j = body.index('<h2 id="draft-notes">')
i = min(starts) if starts else j
body = (
    body[:i]
    + (('<div class="endmatter">' + body[i:j] + "</div>") if i < j else "")
    + '<aside class="draft-notes">' + body[j:] + "</aside>"
)

CSS = r"""
:root {
  --bg: #F3F4F1;
  --surface: #FBFBF8;
  --ink: #1B2430;
  --ink-2: #4A5563;
  --ink-3: #737C86;
  --rule: #D6DAD3;
  --rule-strong: #B8BFB6;
  --accent: #1F5F4A;
  --accent-soft: #E3EDE7;
  --code-bg: #EAEEE8;
  --display: "Fraunces", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  --text: "Source Serif 4", "Iowan Old Style", Georgia, serif;
  --sans: "Public Sans", "Helvetica Neue", Arial, sans-serif;
  --mono: "IBM Plex Mono", "SFMono-Regular", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0F1720; --surface: #151F2A; --ink: #E6E8E3; --ink-2: #A9B2BA; --ink-3: #7E8892;
    --rule: #2A3642; --rule-strong: #3B4955; --accent: #6FB79A; --accent-soft: #17302A; --code-bg: #1B2732;
  }
}
:root[data-theme="dark"] {
  --bg: #0F1720; --surface: #151F2A; --ink: #E6E8E3; --ink-2: #A9B2BA; --ink-3: #7E8892;
  --rule: #2A3642; --rule-strong: #3B4955; --accent: #6FB79A; --accent-soft: #17302A; --code-bg: #1B2732;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--text);
  font-optical-sizing: auto;
  font-size: 19px;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }

.chapter {
  max-width: 760px;
  margin: 0 auto;
  padding: 64px 28px 104px;
}
.chapter > p, .chapter > ul, .chapter > ol { max-width: 66ch; }

/* header */
.masthead { margin: 0 0 56px; }
.eyebrow {
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin: 0 0 28px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
}
.eyebrow .sep { color: var(--rule-strong); }
.bookend-label {
  font-family: var(--display);
  font-variation-settings: "opsz" 144, "SOFT" 50;
  font-weight: 300;
  font-size: 44px;
  line-height: 1;
  color: var(--accent);
  margin: 0 0 14px;
}
.legend-public { color: var(--ink-2); font-weight: 600; }
.ch-number {
  font-family: var(--display);
  font-variation-settings: "opsz" 144, "SOFT" 50;
  font-weight: 300;
  font-size: 104px;
  line-height: 0.8;
  color: var(--accent);
  margin: 0 0 14px;
  font-variant-numeric: lining-nums;
}
h1 {
  font-family: var(--display);
  font-variation-settings: "opsz" 144, "SOFT" 50;
  font-weight: 700;
  font-size: clamp(40px, 6.4vw, 60px);
  line-height: 1.02;
  letter-spacing: -0.015em;
  margin: 0 0 34px;
  text-wrap: balance;
}
.epigraph {
  margin: 0 0 30px;
  padding: 0;
  max-width: 34em;
}
.epigraph p { margin: 0; }
.epigraph p:first-child {
  font-family: var(--display);
  font-variation-settings: "opsz" 36, "SOFT" 50;
  font-size: 23px;
  line-height: 1.35;
  color: var(--ink);
}
.epigraph p + p {
  margin-top: 10px;
  font-family: var(--sans);
  font-size: 14px;
  color: var(--ink-3);
}
.epigraph code { font-size: 13px; }
.meta {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 18px;
  border-top: 1px solid var(--rule-strong);
  border-bottom: 1px solid var(--rule);
  padding: 12px 0;
  font-family: var(--sans);
  font-size: 14px;
  color: var(--ink-2);
  line-height: 1.5;
}
.meta dt {
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-3);
  padding-top: 2px;
}
.meta dd { margin: 0; }
.legend-fiction { color: var(--accent); font-weight: 600; }
.legend-record { color: var(--ink); font-weight: 600; }

/* prose */
p { margin: 0 0 1.05em; }
h2 {
  font-family: var(--display);
  font-variation-settings: "opsz" 72, "SOFT" 50;
  font-weight: 600;
  font-size: 30px;
  line-height: 1.15;
  margin: 2.1em 0 0.7em;
  text-wrap: balance;
}
h3 {
  font-family: var(--display);
  font-variation-settings: "opsz" 36, "SOFT" 50;
  font-weight: 600;
  font-size: 22px;
  line-height: 1.25;
  margin: 1.8em 0 0.5em;
  text-wrap: balance;
}
strong { font-weight: 600; }
code {
  font-family: var(--mono);
  font-size: 0.8em;
  background: var(--code-bg);
  padding: 1px 5px;
  border-radius: 3px;
  overflow-wrap: anywhere;
}
pre {
  margin: 0 0 1.4em;
  padding: 16px 18px;
  background: var(--code-bg);
  border-radius: 4px;
  overflow-x: auto;
  line-height: 1.5;
}
pre code {
  background: transparent;
  padding: 0;
  font-size: 13.5px;
  overflow-wrap: normal;
  white-space: pre;
  color: var(--ink);
}

pre.agent-reply {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 4px;
  padding: 30px 20px 16px;
  position: relative;
}
pre.agent-reply::before {
  content: "agent reply";
  position: absolute;
  top: 9px;
  left: 20px;
  font-family: var(--mono);
  font-size: 10.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-3);
}
pre.agent-reply code {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 14px;
  line-height: 1.6;
}
.dateline {
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 1.6em;
}
.dateline::before {
  content: "";
  width: 28px;
  height: 1px;
  background: currentColor;
  flex: none;
}
.dateline-fiction { color: var(--accent); }
.dateline-record { color: var(--ink-3); }
.dateline-public { color: var(--ink-2); }

.scene-break {
  border: 0;
  height: auto;
  margin: 3em 0;
  text-align: center;
}
.scene-break::after {
  content: "*   *   *";
  white-space: pre;
  font-family: var(--display);
  font-size: 20px;
  color: var(--ink-3);
}

blockquote {
  margin: 1.8em 0 1.9em;
  padding: 0 0 0 2.2em;
  max-width: 34em;
}
blockquote p {
  font-family: var(--display);
  font-variation-settings: "opsz" 36, "SOFT" 50;
  font-style: italic;
  font-size: 24px;
  line-height: 1.35;
  color: var(--ink);
  margin: 0;
  text-wrap: balance;
}

/* tables */
.table-wrap {
  overflow-x: auto;
  margin: 0.4em 0 1.8em;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--sans);
  font-size: 15px;
  line-height: 1.45;
  font-variant-numeric: tabular-nums;
}
th, td {
  padding: 9px 12px;
  border-bottom: 1px solid var(--rule);
  vertical-align: top;
  text-align: left;
}
th:first-child, td:first-child { padding-left: 0; }
th:last-child, td:last-child { padding-right: 0; }
thead th {
  font-family: var(--mono);
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-3);
  border-bottom: 1px solid var(--rule-strong);
  white-space: nowrap;
}
td[style*="right"], th[style*="right"] { white-space: nowrap; }
tbody tr:last-child td { border-bottom: 1px solid var(--rule-strong); }
td code { font-size: 12.5px; }
td strong { color: var(--accent); font-weight: 600; }

/* end matter */
.endmatter {
  margin: 4em 0 0;
  background: var(--surface);
  border: 1px solid var(--rule-strong);
  padding: 8px 32px 20px;
}
.endmatter h2 {
  font-family: var(--mono);
  font-weight: 500;
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 24px 0 12px;
}
.endmatter h2 + ul, .endmatter h2 + ol { margin-top: 0; }
.endmatter h2 ~ h2 {
  border-top: 1px solid var(--rule);
  padding-top: 24px;
}
.endmatter ul, .endmatter ol {
  font-family: var(--sans);
  font-size: 16px;
  line-height: 1.55;
  margin: 0 0 8px;
  padding-left: 1.25em;
  color: var(--ink-2);
}
.endmatter li { padding-left: 4px; }
.endmatter li + li { margin-top: 8px; }
.endmatter li strong { color: var(--ink); }
.endmatter code { font-size: 13px; }

.draft-notes {
  margin: 40px 0 0;
  border: 1px dashed var(--rule-strong);
  padding: 8px 28px 20px;
  font-family: var(--sans);
  font-size: 14.5px;
  line-height: 1.55;
  color: var(--ink-2);
}
.draft-notes h2 {
  font-family: var(--mono);
  font-weight: 500;
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin: 20px 0 4px;
}
.draft-notes > p { font-size: 13.5px; color: var(--ink-3); margin: 0 0 14px; }
.draft-notes ul { margin: 0; padding-left: 1.2em; }
.draft-notes li + li { margin-top: 8px; }
.draft-notes li strong { color: var(--ink); }
.draft-notes code { font-size: 12.5px; }

@media (max-width: 640px) {
  body { font-size: 17.5px; }
  .chapter { padding: 40px 20px 72px; }
  .ch-number { font-size: 76px; }
  h2 { font-size: 26px; }
  blockquote { padding-left: 1.2em; }
  blockquote p { font-size: 21px; }
  .endmatter { padding: 4px 20px 16px; }
  .draft-notes { padding: 4px 18px 16px; }
  .meta { grid-template-columns: 1fr; gap: 2px; }
  .meta dd + dt { margin-top: 8px; }
}
"""

html = f"""<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT@9..144,300,50;9..144,600,50;9..144,700,50&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Public+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>

<article class="chapter">
  <header class="masthead">
    <p class="eyebrow"><span>Own Your Cloud</span><span class="sep">/</span><span>{PART}</span><span class="sep">/</span><span>Draft 1</span></p>
    {f'<p class="ch-number" aria-hidden="true">{num}</p>' if num else f'<p class="bookend-label">{bookend}</p>'}
    <h1><span class="visually-hidden" style="position:absolute;left:-9999px">{("Chapter " + num) if num else bookend}: </span>{title}</h1>
    <blockquote class="epigraph">{epigraph}</blockquote>
    <dl class="meta">
      <dt>Two voices</dt>
      <dd><span class="legend-fiction">Meridian</span> scenes are composite fiction. <span class="legend-record">Build log</span> sections, and every number in them, come from the repository.{' <span class="legend-public">Public record</span> and <span class="legend-public">Briefing</span> sections quote named sources — published reports, or the strategy deck behind this book.' if has_public else ''}</dd>
      <dt>Length</dt>
      <dd>About {round(words, -2):,} words · about {round(words / 230):d} minutes to read</dd>
    </dl>
  </header>
{body}
</article>
"""

OUT.write_text(html)
print(f"wrote {OUT} — {words} words")
