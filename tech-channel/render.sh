#!/usr/bin/env bash
# Render one episode folder -> slides.pdf + png/slide-XX.png + narration PDFs.
# Uses Chrome headless (HTML->PDF) and PyMuPDF (PDF->PNG). No WeasyPrint/GTK.
#
#   ./render.sh episodes/ep01_how-does-ai-work
#
# Override Chrome path with: CHROME="/path/to/chrome.exe" ./render.sh <ep>
set -euo pipefail

EP="${1:?usage: ./render.sh episodes/<folder>}"
EP="${EP%/}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
[ -x "$CHROME" ] || CHROME="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"

PROFILE="$(mktemp -d)"
trap 'rm -rf "$PROFILE"' EXIT

html2pdf() {  # $1=input.html  $2=output.pdf
  local in out
  in="$(cygpath -m "$(realpath "$1")")"
  out="$(cygpath -w "$(realpath -m "$2")")"
  "$CHROME" --headless=new --disable-gpu --no-sandbox \
    --user-data-dir="$(cygpath -w "$PROFILE")" \
    --no-pdf-header-footer --print-to-pdf="$out" "file:///$in" >/dev/null 2>&1
}

echo "[render] $EP"

# 1) slides -> PDF -> PNGs
if [ -f "$EP/slides.html" ]; then
  html2pdf "$EP/slides.html" "$EP/slides.pdf"
  python "$ROOT/core/pdf2png.py" "$EP/slides.pdf" "$EP/png"
  echo "  slides.pdf + png/ done"
fi

# 2) narration scripts -> PDF (English + Hinglish, whichever exist)
for n in narration-en narration-hi narration; do
  if [ -f "$EP/$n.html" ]; then
    html2pdf "$EP/$n.html" "$EP/$n.pdf"
    echo "  $n.pdf done"
  fi
done

echo "[render] complete: $EP"
