#!/usr/bin/env bash
# Unlock password-protected PDFs (CDS eStatements, dividend e-warrants, bank
# certificates) into a separate folder.
#
# Usage: unlock_pdfs.sh OUT_DIR FILE.pdf [FILE.pdf ...]
#
# The password is read from the PDF_PASSWORD environment variable, or prompted
# for without echo, and handed to qpdf through a temporary file, so it is never a
# command-line argument (which other processes could see). Originals are never
# modified.
# Files that are not encrypted are copied as-is. Requires qpdf.
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 OUT_DIR FILE.pdf [FILE.pdf ...]" >&2
  exit 2
fi
out="$1"; shift
mkdir -p "$out"

if [ -z "${PDF_PASSWORD:-}" ]; then
  read -r -s -p "PDF password: " PDF_PASSWORD; echo >&2
fi
pwfile="$(mktemp)"; trap 'rm -f "$pwfile"' EXIT
printf '%s' "$PDF_PASSWORD" > "$pwfile"

status=0
for f in "$@"; do
  name="$(basename "$f")"
  if qpdf --is-encrypted "$f" >/dev/null 2>&1; then
    if qpdf --password-file="$pwfile" --decrypt "$f" "$out/$name" 2>/dev/null; then
      echo "unlocked  $name"
    else
      echo "FAILED    $name (wrong password?)" >&2; status=1
    fi
  else
    cp "$f" "$out/$name"; echo "copied    $name (not encrypted)"
  fi
done

for f in "$out"/*.pdf; do
  if qpdf --is-encrypted "$f" >/dev/null 2>&1; then
    echo "STILL ENCRYPTED: $(basename "$f")" >&2; status=1
  fi
done
exit $status
