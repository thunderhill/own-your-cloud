#!/usr/bin/env python3
"""Generate a Ghostscript pdfmark prologue: chapter bookmarks + page numbers.

Usage:  python3 tools/pdf_extras.py <book.pdf> <out.ps>

Titles come from the source markdown (headings wrap in the rendered page, so
reading them back out of the text layer truncates them). Page numbers come from
the PDF's own text layer, so a bookmark points where the chapter actually
landed rather than where we guessed it would.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])

PARTS = {
    "01": "Part I — The Bill",
    "05": "Part II — The Factory",
    "10": "Part III — The Fabric",
    "13": "Part IV — The Brain",
    "17": "Part V — The Dividend",
}

text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"],
                      capture_output=True, text=True, check=True).stdout
pages = [re.sub(r"\s+", " ", p).strip() for p in text.split("\f")]
n_pages = text.count("\f")   # pdftotext ends every page with a form feed

# Page layout: 1 front cover, 2 title page, 3 contents, chapters..., last = back cover.
# The covers and the title page carry no page number; every other page shows its
# position in the file, so the number on the page matches the viewer's page counter.
UNNUMBERED_FRONT = 2
FIRST_CHAPTER_SEARCH = 4


def find_page(needle, start=1, loose=False):
    """First page (1-based, at or after `start`) whose text contains `needle`.

    loose=True ignores all whitespace: Chrome's wide letter-spacing makes pdftotext read
    the divider kicker "PART II" as "PA RT I I"."""
    squash = (lambda t: re.sub(r"\s+", "", t)) if loose else (lambda t: re.sub(r"\s+", " ", t).strip())
    probe = squash(needle)
    for n in range(start, len(pages) + 1):
        if probe in squash(pages[n - 1]):
            return n
    return None


entries = []   # (level, title, page)
cursor = FIRST_CHAPTER_SEARCH   # skip front cover, title page and contents

for path in sorted((ROOT / "chapters").glob("*.md")):
    first = path.read_text().split("\n", 1)[0]
    title = first.lstrip("# ").strip()

    key = path.stem[:2]
    if key in PARTS:
        part = PARTS[key]
        # The divider page reads "PART II The Factory ..." (the kicker is set in caps). Match the
        # kicker and name together: the name alone also turns up in earlier body text.
        kicker, name = part.split(" — ")
        p = find_page(f"{kicker.upper()} {name}", cursor, loose=True) or find_page(name, cursor)
        if p:
            entries.append((0, part, p))
            cursor = p

    p = find_page(title, cursor)
    if p is None:
        print(f"  WARNING: could not locate '{title}'", file=sys.stderr)
        continue
    entries.append((1, title, p))
    cursor = p

if not entries:
    sys.exit("ERROR: no headings located")

# Children per part, so parts render as collapsible parents.
counts = []
for i, (lvl, _, _) in enumerate(entries):
    if lvl != 0:
        counts.append(0)
        continue
    k = 0
    for lvl2, _, _ in entries[i + 1:]:
        if lvl2 == 0:
            break
        k += 1
    counts.append(k)


def pdf_text(s):
    """A PDF text string: UTF-16BE with a byte-order mark, so characters such as the em dash survive.
    (A plain (...) string is read as PDFDocEncoding, which turns UTF-8 bytes into mojibake.)"""
    return "<FEFF" + s.encode("utf-16-be").hex().upper() + ">"


ps = [
    "%!PS",
    f"% Page numbers, centred in the bottom margin. The front cover and title page (pages 1-{UNNUMBERED_FRONT})",
    "% and the back cover (last page) are skipped.",
    "<< /EndPage {",
    "  2 dict begin",
    "  /Reason exch def /PageCount exch def",  # Reason is on top of the stack
    "  Reason 0 eq {",
    f"    PageCount {UNNUMBERED_FRONT} ge PageCount {n_pages - 1} lt and {{",
    "      gsave",
    "      /Helvetica findfont 8 scalefont setfont",
    "      0.45 setgray",
    "      PageCount 1 add 5 string cvs",
    "      dup stringwidth pop 2 div 297.5 exch sub 28 moveto",
    "      show",
    "      grestore",
    "    } if",
    "    true",
    "  } { false } ifelse",
    "  end",
    "} bind >> setpagedevice",
    "",
    "% Outline (bookmarks).",
]
for (lvl, title, page), kids in zip(entries, counts):
    count = f"/Count {kids} " if lvl == 0 and kids else ""
    ps.append(f"[ {count}/Page {page} /View [/XYZ null null null] /Title {pdf_text(title)} /OUT pdfmark")

OUT.write_text("\n".join(ps) + "\n")
parts = sum(1 for e in entries if e[0] == 0)
print(f"wrote {OUT}: {len(entries)} bookmarks ({parts} parts, {len(entries) - parts} chapters)")
