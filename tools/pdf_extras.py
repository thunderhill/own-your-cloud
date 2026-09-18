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


def find_page(needle, start=1):
    """First page (1-based, at or after `start`) whose text contains `needle`."""
    probe = re.sub(r"\s+", " ", needle).strip()
    for n in range(start, len(pages) + 1):
        if probe in pages[n - 1]:
            return n
    return None


entries = []   # (level, title, page)
cursor = 3     # skip title page + contents

for path in sorted((ROOT / "chapters").glob("*.md")):
    first = path.read_text().split("\n", 1)[0]
    title = first.lstrip("# ").strip()

    key = path.stem[:2]
    if key in PARTS:
        part = PARTS[key]
        # The part divider renders its name in caps, before the chapter.
        p = find_page(part.split(" — ")[1].upper(), cursor) or find_page(part.split(" — ")[1], cursor)
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


def esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


ps = [
    "%!PS",
    "% Page numbers, centred in the bottom margin. Page 1 (the title page) is skipped.",
    "<< /EndPage {",
    "  2 dict begin",
    "  /Reason exch def /PageCount exch def",  # Reason is on top of the stack
    "  Reason 0 eq {",
    "    PageCount 0 gt {",
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
    ps.append(f"[ {count}/Page {page} /View [/XYZ null null null] /Title ({esc(title)}) /OUT pdfmark")

OUT.write_text("\n".join(ps) + "\n")
parts = sum(1 for e in entries if e[0] == 0)
print(f"wrote {OUT}: {len(entries)} bookmarks ({parts} parts, {len(entries) - parts} chapters)")
