#!/usr/bin/env python3
"""Extract AIT/WHT interest certificate data from Sri Lankan bank documents.

Reads unlocked (decrypted) PDFs, .txt files produced by `pdftotext -layout`, and
canonical .json files, and writes one JSON object per account-and-certificate row.

Bank layouts are parsed by modules in ./wht_parsers/, one per institution, found
automatically. **Tested so far with two banks only:** Nations Trust Bank and
Sampath Bank (run with --list-providers). Every other bank or financial
institution is reported as "unrecognised". Claude (or the user) then reads that
certificate and writes its rows as canonical JSON:

    {"source": "<institution>", "rows": [ {<row fields>}, ... ]}

with the row fields listed in references/bank-formats.md. Such a file is
validated and merged like parsed data. The script never guesses missing
values: they are left as null.

Usage:
  extract_certificates.py [--include-consolidated] FILE_OR_DIR [...] > rows.json
  extract_certificates.py --list-providers

Uses `pdftotext -layout` (poppler) for PDFs, or pypdf if poppler is missing.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # also works with python -I
import wht_parsers as parsers  # noqa: E402

REQUIRED = {"agent_name": str, "agent_tin": str, "certificate_no": str,
            "amount_received": float, "ait": float}
DATE_FIELDS = ("interest_date", "ird_paid_date", "period_from", "period_to")
ALL_FIELDS = ("source_type", "agent_tin", "agent_name", "certificate_no", "account", "amount_received",
              "ait", "ait_rate_pct", "net_paid", "interest_date", "ird_paid_date", "ird_receipt_no",
              "period_from", "period_to", "file")


def parse(text, name):
    """Dispatch to the first registered bank parser that recognises the text."""
    return parsers.parse(text, name)


def pdf_text(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                             capture_output=True, text=True)
        if out.returncode != 0:
            raise RuntimeError(f"pdftotext failed on {path.name}: {out.stderr.strip()} "
                               "(is the PDF still password protected? unlock it first)")
        return out.stdout
    try:
        import pypdf  # fallback when poppler isn't installed
    except ImportError:
        raise RuntimeError("needs pdftotext (poppler) or the pypdf package")
    r = pypdf.PdfReader(str(path))
    if r.is_encrypted:
        raise RuntimeError(f"{path.name} is password protected; unlock it first (unlock_pdfs.sh)")
    return "\n".join(p.extract_text(extraction_mode="layout") or "" for p in r.pages)


def load_canonical(path: Path):
    """Validate hand-written rows for a bank without a parser. Returns a document dict."""
    data = json.loads(path.read_text())
    rows, problems = [], []
    for i, r in enumerate(data.get("rows", [])):
        bad = [k for k, t in REQUIRED.items()
               if k not in r or r[k] in (None, "") or (t is float and not isinstance(r[k], (int, float)))]
        bad += [k for k in DATE_FIELDS if r.get(k) and not re.match(r"^\d{4}-\d\d-\d\d$", str(r[k]))]
        if bad:
            problems.append(f"rows[{i}]: missing/invalid {bad}")
        row = {k: r.get(k) for k in ALL_FIELDS}
        row["file"] = r.get("file") or path.name
        rows.append(row)
    return {"bank": data.get("source", "manual"), "provider": "canonical_json", "kind": "canonical",
            "file": path.name, "rows": rows, "checks": {}, "problems": problems}


def collect(paths):
    files = []
    for p in paths:
        if p.is_dir():
            files += sorted(x for x in p.rglob("*") if x.suffix.lower() in (".pdf", ".txt", ".json"))
        else:
            files.append(p)
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--include-consolidated", action="store_true",
                    help="also emit rows from consolidated yearly certificates (normally cross-check only)")
    ap.add_argument("--list-providers", action="store_true", help="print the banks with a parser and exit")
    args = ap.parse_args()
    if args.list_providers:
        json.dump(parsers.providers(), sys.stdout, indent=2)
        print()
        return 0
    if not args.paths:
        ap.error("give at least one file or folder")

    docs, rows, problems = [], [], []
    for f in collect(args.paths):
        try:
            doc = load_canonical(f) if f.suffix.lower() == ".json" else parse(pdf_text(f), f.name)
        except Exception as e:  # report and keep going
            problems.append({"file": f.name, "error": str(e)})
            continue
        for p in doc.pop("problems", []):
            problems.append({"file": f.name, "error": p})
        for r in doc["rows"]:
            if r.get("ait_rate_pct") and abs(round(r["amount_received"] * r["ait_rate_pct"] / 100, 2) - r["ait"]) > 0.011:
                problems.append({"file": f.name, "error": f"AIT {r['ait']} is not {r['ait_rate_pct']}% of {r['amount_received']}"})
        if doc["kind"] == "unrecognised":
            problems.append({"file": f.name, "error": "no parser for this layout (tested banks: "
                             + ", ".join(p["name"] for p in parsers.providers())
                             + "); read it and write canonical JSON rows"})
        for k, v in doc["checks"].items():
            if k.endswith("_matches") and not v:
                problems.append({"file": f.name, "error": f"{k} failed: {doc['checks']}"})
        docs.append({k: doc.get(k) for k in ("bank", "provider", "kind", "file", "checks")} | {"row_count": len(doc["rows"])})
        if doc["kind"] != "consolidated" or args.include_consolidated:
            rows += doc["rows"]

    json.dump({"documents": docs, "rows": rows, "problems": problems}, sys.stdout, indent=2)
    print()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
