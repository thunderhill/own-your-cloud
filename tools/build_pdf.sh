#!/usr/bin/env bash
# Render the whole book to a single PDF.
#
#   ./tools/build_pdf.sh [out.pdf]
#
# Assembles every chapter into one self-contained HTML document
# (tools/build_pdf.py, figures inlined as data URIs), then prints it with
# headless Chrome — the same renderer the companion repo uses for its demo
# frames. Requires Python 3 with `markdown`, and google-chrome or chromium.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="${1:-own-your-cloud.pdf}"
TMP_HTML="html/own-your-cloud.html"

CHROME="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)"
[[ -z "$CHROME" ]] && { echo "ERROR: no chrome/chromium found" >&2; exit 1; }

echo "==> Assembling single-document HTML"
python3 tools/build_pdf.py "$TMP_HTML"

echo "==> Rendering PDF with $(basename "$CHROME")"
PROFILE="$(mktemp -d)"
trap 'rm -rf "$PROFILE"' EXIT

"$CHROME" \
  --headless \
  --disable-gpu \
  --no-sandbox \
  --user-data-dir="$PROFILE" \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT" \
  --virtual-time-budget=20000 \
  "file://$(pwd)/$TMP_HTML" 2>/dev/null

[[ -f "$OUT" ]] || { echo "ERROR: Chrome produced no PDF" >&2; exit 1; }

# Chrome cannot number pages or write bookmarks (CSS paged-media margin boxes
# are unimplemented), so add both with Ghostscript if it is available.
if command -v gs >/dev/null && command -v pdftotext >/dev/null; then
  echo "==> Adding page numbers and bookmarks"
  python3 tools/pdf_extras.py "$OUT" "$PROFILE/extras.ps"
  gs -q -dBATCH -dNOPAUSE -dSAFER -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress \
     -sOutputFile="$PROFILE/final.pdf" "$PROFILE/extras.ps" "$OUT" 2>/dev/null
  # Only accept the result if it kept every page.
  before=$(pdfinfo "$OUT" 2>/dev/null | awk '/^Pages:/{print $2}')
  after=$(pdfinfo "$PROFILE/final.pdf" 2>/dev/null | awk '/^Pages:/{print $2}')
  if [[ -n "$after" && "$before" == "$after" ]]; then
    mv "$PROFILE/final.pdf" "$OUT"
  else
    echo "    WARNING: Ghostscript pass changed the page count ($before -> $after); keeping the unnumbered PDF" >&2
  fi
else
  echo "==> Skipping page numbers and bookmarks (needs gs and pdftotext)"
fi

echo "==> Wrote $OUT ($(du -h "$OUT" | cut -f1), $(pdfinfo "$OUT" 2>/dev/null | awk '/^Pages:/{print $2}') pages)"
