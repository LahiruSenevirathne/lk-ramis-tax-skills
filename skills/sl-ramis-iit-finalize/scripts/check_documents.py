#!/usr/bin/env python3
"""Check supporting documents for every section of a RAMIS return, and assemble
the year's final folder.

Usage:
    check_documents.py snapshot.json --year-dir ~/Documents/Tax-Sri-Lanka/YA-2025-26
        [--search DIR ...] [--out missing-documents.md] [--json checklist.json]
        [--assemble [--include-outside]]

1. Derives the documents the return needs from its rows: an AIT/WHT certificate
   per withholding agent, a balance confirmation per bank, a loan confirmation
   per liability, a deed/agreement per property, the broker valuation, trade
   confirmations and dividend warrants for shares, an APIT/T-10 per employer,
   and so on (catalogue in finalize_lib.py).
2. Looks for each one in the year folder (originals/, unlocked/, work/,
   output/ of every skill folder) and, if given, in --search folders (e.g. an
   old Downloads folder). Matching is by the counterparty's name or alias in the
   folder/file name, plus document keywords. It's a heuristic, so review it.
3. Reports each requirement as FOUND (in the year folder), ELSEWHERE (only
   found outside it, so copy it in) or MISSING.
4. With --assemble, creates <year-dir>/final/ with one numbered sub-folder per
   section holding COPIES of the documents found (unlocked copies preferred),
   plus README.md (index), and copies of the summary and snapshot if present
   in <year-dir>/ramis/. Never moves or deletes anything. With
   --include-outside, documents found elsewhere are copied too.
"""
import argparse
import re
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finalize_lib import SECTIONS, bank_key, col_index, entity_tokens, section_of  # noqa: E402

DOC_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".csv", ".txt", ".json", ".docx", ".heic"}
SKIP_DIRS = {"final", "__pycache__", ".git", "node_modules"}
# working files are not evidence: inside the year folder only these count
NOT_EVIDENCE = {"work", "output", "ramis"}


def inventory(root, max_depth=6):
    out = []
    root = Path(root).expanduser()
    if not root.is_dir():
        return out
    base = len(root.parts)
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts[base:]):
            continue
        if len(p.parts) - base > max_depth:
            continue
        if any(part in NOT_EVIDENCE for part in p.parts[base:-1]):
            continue
        if p.is_file() and p.suffix.lower() in DOC_EXT and not p.name.startswith("."):
            out.append(p)
    return out


def requirements(snap):
    reqs = []
    seen = set()

    def add(sec, label, tokens, keywords, need_keyword=False):
        key = (sec["key"], label)
        if key in seen:
            return
        seen.add(key)
        reqs.append({"section": sec["key"], "section_name": sec["name"], "folder": sec["folder"],
                     "document": label, "tokens": tokens, "keywords": keywords, "need_keyword": need_keyword})

    grids = {}
    for g in snap["grids"]:
        s = section_of(g["id"])
        if s:
            grids[s["key"]] = (s, g)
    for key, (s, g) in grids.items():
        if not g["rows"] or not s["doc"]:
            continue
        if key in ("property", "acquired"):
            ic = col_index(g, ["situation", "description"])
            for r in g["rows"]:
                add(s, s["doc"].format(entity=str(r[ic])[:70]), [], s["keywords"], need_keyword=True)
        elif key == "shares":
            add(s, "Broker portfolio valuation / statement of holdings as at 31 March", [], ["valuation", "portfolio", "holding"], True)
            add(s, "Trade confirmations / contract notes for shares bought", [], ["trade_confirmation", "trade confirmation", "contract"], True)
            idv = col_index(g, ["dividend"])
            n = sum(1 for r in g["rows"] if (r[idv] or 0) > 0) if idv is not None else 0
            if n:
                add(s, "Dividend warrants / certificates of tax deduction (%d companies with net dividend income)" % n,
                    [], ["dividend", "warrant"], True)
        elif key == "disposals":
            add(s, s["doc"], [], ["trade_confirmation", "trade confirmation", "contract", "sale"], True)
        elif key == "liabilities":
            ic = col_index(g, s["entity_col"])
            for r in g["rows"]:
                lender = entity_tokens(str(r[ic]))[:1]
                add(s, s["doc"].format(entity=str(r[ic])[:70]), lender, s["keywords"])
        else:
            ic = col_index(g, s["entity_col"])
            for r in g["rows"]:
                ent = bank_key(r[ic]) if key in ("bank", "interest_wht") else str(r[ic])
                add(s, s["doc"].format(entity=ent.title()), entity_tokens(ent), s["keywords"])
    # institutions that paid interest but have no balance row
    if "interest_wht" in grids:
        s7, g7 = grids["interest_wht"]
        sb = next(x for x in SECTIONS if x["key"] == "bank")
        banks = set()
        if "bank" in grids:
            sbk, gb = grids["bank"]
            ib = col_index(gb, sbk["entity_col"])
            banks = {bank_key(r[ib]) for r in gb["rows"]}
        ia = col_index(g7, s7["entity_col"])
        for r in g7["rows"]:
            b = bank_key(r[ia])
            if b not in banks:
                add(sb, sb["doc"].format(entity=b.title()) + " (paid interest; no bank-balance row yet)",
                    entity_tokens(b), sb["keywords"])
    return reqs


def matches(req, path, root):
    p = str(path).lower().replace("-", "_")
    rel = str(path.relative_to(root)).lower() if root and path.is_relative_to(root) else p
    has_kw = any(k.replace("-", "_").replace(" ", "_") in p.replace(" ", "_") for k in req["keywords"])
    if req["tokens"]:
        # whole words of folder and file names (split on _ - . space), so "trust"
        # doesn't match inside "capital_trust" unless it's a word there too
        words = set(re.split(r"[^a-z0-9]+", rel.lower()))
        tok = any(t in words for t in req["tokens"])
        if not tok:
            return False
        if root and path.is_relative_to(root) and req["folder"]:
            # inside the year folder: the counterparty's folder in the right section is
            # enough; elsewhere in the year folder the file name must also fit
            return rel.startswith(req["folder"].lower()) or has_kw
        # outside the year folder the file name must say what the document is
        return has_kw
    return has_kw


def check(snap, year_dir, search=()):
    year = Path(year_dir).expanduser()
    inside = inventory(year)
    outside = [p for d in search for p in inventory(d, max_depth=3)]
    reqs = requirements(snap)
    for r in reqs:
        r["found"] = [str(p.relative_to(year)) for p in inside if matches(r, p, year)]
        r["elsewhere"] = [] if r["found"] else [str(p) for p in outside if matches(r, p, None)]
        r["status"] = "FOUND" if r["found"] else ("ELSEWHERE" if r["elsewhere"] else "MISSING")
    return reqs


def render(reqs):
    L = ["# Supporting documents checklist", ""]
    counts = {s: sum(1 for r in reqs if r["status"] == s) for s in ("FOUND", "ELSEWHERE", "MISSING")}
    L.append("FOUND %(FOUND)d · ELSEWHERE (copy into the year folder) %(ELSEWHERE)d · MISSING %(MISSING)d" % counts)
    icon = {"FOUND": "✅", "ELSEWHERE": "📁", "MISSING": "❌"}
    current = None
    for r in reqs:
        if r["section_name"] != current:
            current = r["section_name"]
            L += ["", "## " + current, ""]
        L.append("- %s **%s** %s" % (icon[r["status"]], r["status"], r["document"]))
        for f in (r["found"] or r["elsewhere"])[:6]:
            L.append("    - `%s`" % f)
        extra = len(r["found"] or r["elsewhere"]) - 6
        if extra > 0:
            L.append("    - … and %d more" % extra)
    return "\n".join(L) + "\n"


def assemble(reqs, year_dir, include_outside=False):
    year = Path(year_dir).expanduser()
    final = year / "final"
    final.mkdir(exist_ok=True)
    order = {s["key"]: i for i, s in enumerate(SECTIONS, 1)}
    copied = []
    index = ["# Final folder – supporting documents", "",
             "Copies only; originals stay where they are. Generated by check_documents.py.", ""]
    for r in reqs:
        sub = final / ("%02d-%s" % (order[r["section"]], r["section"].replace("_", "-")))
        files = [year / f for f in r["found"]] + ([Path(f) for f in r["elsewhere"]] if include_outside else [])
        index.append("- [%s] %s (%s)" % (r["status"], r["document"], r["section_name"]))
        for src in files:
            unlocked = src.parent.parent.parent / "unlocked" / src.name if "originals" in src.parts else None
            if unlocked and unlocked.exists():
                src = unlocked
            sub.mkdir(exist_ok=True)
            dst = sub / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
                copied.append(str(dst.relative_to(year)))
            index.append("    - `%s`" % dst.relative_to(final))
    for name in ("summary.md", "snapshot.json", "checks.json"):
        src = year / "ramis" / name
        if src.exists():
            shutil.copy2(src, final / name)
    (final / "README.md").write_text("\n".join(index) + "\n")
    (final / "missing-documents.md").write_text(render(reqs))
    return copied


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snapshot")
    ap.add_argument("--year-dir", required=True)
    ap.add_argument("--search", nargs="*", default=[])
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--include-outside", action="store_true")
    a = ap.parse_args(argv)
    snap = json.load(open(a.snapshot))
    reqs = check(snap, a.year_dir, a.search)
    md = render(reqs)
    if a.out:
        Path(a.out).write_text(md)
    else:
        sys.stdout.write(md)
    if a.json:
        json.dump(reqs, open(a.json, "w"), indent=1)
    if a.assemble:
        copied = assemble(reqs, a.year_dir, a.include_outside)
        print("assembled final/ (%d files copied)" % len(copied), file=sys.stderr)
    return 1 if any(r["status"] == "MISSING" for r in reqs) else 0


if __name__ == "__main__":
    sys.exit(main())
