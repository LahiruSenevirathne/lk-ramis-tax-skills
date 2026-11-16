#!/usr/bin/env python3
"""Extract CSE share data from CDS and broker documents into JSON.

Usage:
    extract_cse.py FILE_OR_DIR [...] > extracted.json

Inputs (mix freely):
  * unlocked PDFs (see unlock_pdfs.sh), or .txt from ``pdftotext -layout``
  * .json files in the canonical shape (references/data-model.md), written by
    Claude (or anyone) for documents no parser below understands, e.g. another
    broker's contract notes. They are validated and merged like parsed data.

Parsers live in ./cse_parsers/, one module per document provider, found
automatically (run with --list-providers):
  cds             CDS dividend e-warrants and monthly eStatements: the same for
                  every CSE investor, whatever the broker
  capital_trust   Capital TRUST Securities trade confirmation and portfolio
                  valuation: the worked broker example
**Brokers tested so far: Capital TRUST only.** Other brokers' documents come
back "unrecognised". Read them and write canonical JSON, or add a parser
(see CONTRIBUTING.md).

Output: {"documents": [...], "trades": [...], "dividends": [...],
         "holdings": [...], "movements": [...], "problems": [...]}

Every document is self-checked (printed totals, required fields); anything that
does not reconcile, or is not recognised, is listed in "problems". Treat every
problem as a stop: read that file yourself and, if needed, write its rows as
canonical JSON.

Text extraction uses ``pdftotext -layout`` when available, otherwise pypdf.
PDFs must already be unlocked (pypdf also tries PDF_PASSWORD if set).
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

def squash(t):
    """Collapse runs of spaces/tabs; keep line breaks."""
    return re.sub(r"[ \t ]+", " ", t.replace("­", "-"))


# --------------------------------------------------------------------------
# text extraction
# --------------------------------------------------------------------------
def pdf_text(path):
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                             capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout
    try:
        import pypdf  # optional fallback
    except ImportError:
        raise RuntimeError("needs pdftotext (poppler) or the pypdf package")
    r = pypdf.PdfReader(str(path))
    if r.is_encrypted:
        pw = os.environ.get("PDF_PASSWORD", "")
        if not pw or not r.decrypt(pw):
            raise RuntimeError("PDF is encrypted; unlock it first (unlock_pdfs.sh)")
    text = "\n".join(p.extract_text(extraction_mode="layout") or "" for p in r.pages)
    if len(text.strip()) < 50:  # some e-warrants only extract in plain mode
        text = "\n".join(p.extract_text() or "" for p in r.pages)
    return text


def read_any(path):
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        return pdf_text(p)
    return p.read_text(errors="replace")


sys.path.insert(0, str(Path(__file__).resolve().parent))  # also works with python -I
import cse_parsers as parsers  # noqa: E402


def parse(text, name):
    return parsers.parse(squash(text), name)


# --------------------------------------------------------------------------
# canonical JSON input (hand-written rows for documents without a parser)
# --------------------------------------------------------------------------
DATE_RE = re.compile(r"^\d{4}-\d\d-\d\d$")
CODE_RE = re.compile(r"^[A-Z0-9]+\.[A-Z]\d{4}$")
REQUIRED = {
    "trades": {"date": "date", "side": ("buy", "sell"), "code": "code", "name": str, "qty": int, "net": float},
    "holdings": {"as_at": "date", "code": "code", "name": str, "quantity": int, "vwa_price": float,
                 "market_value": float},
    "dividends": {"date": "date", "company": str, "code_root": str, "gross": float, "ait": float, "net": float},
    "movements": {"date": "date", "code": "code", "kind": ("deposit", "withdrawal"), "qty": int},
}


def _bad(v, rule):
    if rule == "date":
        return not (isinstance(v, str) and DATE_RE.match(v))
    if rule == "code":
        return not (isinstance(v, str) and CODE_RE.match(v))
    if isinstance(rule, tuple):
        return v not in rule
    if rule is float:
        return not isinstance(v, (int, float)) or isinstance(v, bool)
    if rule is int:
        return not (isinstance(v, int) and not isinstance(v, bool))
    return not isinstance(v, rule) or not v


def load_canonical(path):
    """Validate a hand-written canonical JSON file; return (sections, problems)."""
    data = json.loads(Path(path).read_text())
    name = Path(path).name
    out, problems = {}, []
    unknown = set(data) - set(REQUIRED) - {"source", "note", "documents"}
    if unknown:
        problems.append("unknown keys %s" % sorted(unknown))
    for key, rules in REQUIRED.items():
        rows = data.get(key, [])
        for i, r in enumerate(rows):
            bad = [f for f, rule in rules.items() if f not in r or _bad(r[f], rule)]
            if bad:
                problems.append("%s[%d]: missing/invalid %s" % (key, i, bad))
            r.setdefault("file", name)
            r.setdefault("source", data.get("source", "manual"))
        for r in rows if key == "dividends" else []:
            if all(isinstance(r.get(k), (int, float)) for k in ("gross", "ait", "net")) \
                    and abs(r["gross"] - r["ait"] - r["net"]) > 0.01:
                problems.append("dividends: gross - ait != net for %s" % r.get("company"))
        out[key] = rows
    return out, problems


def collect(paths):
    files = []
    for a in paths:
        p = Path(a)
        if p.is_dir():
            files += sorted(x for x in p.rglob("*") if x.suffix.lower() in (".pdf", ".txt", ".json"))
        else:
            files.append(p)
    return files


def main(argv):
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    if argv == ["--list-providers"]:
        json.dump(parsers.providers(), sys.stdout, indent=1)
        print()
        return 0
    out = {"documents": [], "trades": [], "dividends": [], "holdings": [], "movements": [], "problems": []}
    for f in collect(argv):
        if f.suffix.lower() == ".json":
            try:
                rows, probs = load_canonical(f)
            except Exception as e:
                out["problems"].append({"file": f.name, "problem": "bad JSON: %s" % e})
                continue
            for k, v in rows.items():
                out[k] += v
            out["documents"].append({"kind": "canonical_json", "file": f.name,
                                     "counts": {k: len(v) for k, v in rows.items()}})
            if probs:
                out["problems"].append({"file": f.name, "kind": "canonical_json", "failed_checks": probs})
            continue
        try:
            d = parse(read_any(f), f.name)
        except Exception as e:  # report, don't guess
            out["problems"].append({"file": f.name, "problem": str(e)})
            continue
        out["documents"].append({k: v for k, v in d.items() if k not in ("trades", "holdings", "movements")})
        out["trades"] += d.get("trades", [])
        out["holdings"] += d.get("holdings", [])
        out["movements"] += d.get("movements", [])
        if d["kind"] == "dividend_warrant":
            out["dividends"].append({k: d[k] for k in ("file", "source", "warrant_no", "code_root", "date",
                                                       "company", "title", "shares", "gross", "ait", "net")})
        failed = [k for k, v in d.get("checks", {}).items() if not v]
        if failed:
            out["problems"].append({"file": f.name, "kind": d["kind"], "failed_checks": failed})
    json.dump(out, sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
