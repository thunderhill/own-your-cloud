#!/usr/bin/env bash
# Render every manuscript file in chapters/ to html/, with its part label.
# Requires Python 3 and the `markdown` package (pip install markdown).
set -euo pipefail
cd "$(dirname "$0")/.."
part_for() {
  case "$1" in
    00-*) echo "Before Part I" ;;
    0[1-4]-*) echo "Part I — The Bill" ;;
    0[5-9]-*) echo "Part II — The Factory" ;;
    1[0-2]-*) echo "Part III — The Fabric" ;;
    1[3-6]-*) echo "Part IV — The Brain" ;;
    1[7-9]-*) echo "Part V — The Dividend" ;;
    99-*) echo "After Part V" ;;
    appendices*) echo "Reference" ;;
    *) echo "Draft" ;;
  esac
}
for src in chapters/*.md; do
  name=$(basename "$src" .md)
  python3 tools/build_chapter.py "$src" "html/${name}.html" "$(part_for "$name")"
done
