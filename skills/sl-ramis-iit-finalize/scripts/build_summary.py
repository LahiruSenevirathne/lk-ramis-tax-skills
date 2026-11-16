#!/usr/bin/env python3
"""Summarise a RAMIS IIT return snapshot (from ramis_snapshot.js) section by section.

Usage:
    build_summary.py snapshot.json [--out summary.md] [--json checks.json]

Writes a Markdown summary: header, the tax computation (cages, with arithmetic
checks), every section in the order of the return with row counts, rows and
column totals, then cross-checks between sections:

  * Main return:  total income - reliefs = taxable income; tax - credits = balance
  * Schedule 7A interest/AIT per institution vs. the Interest column of bank
    balances (Part 01 B ii)
  * institutions that paid interest (Schedule 7A) but have no bank-balance row
  * bank interest with no AIT/WHT row (e.g. foreign-currency accounts): is it
    declared or exempt?
  * liabilities whose security refers to a property not in Part 01 A
  * the "A. Local / B. Foreign" assets checkboxes, and documents uploaded

Amounts are printed with thousands separators. The snapshot is already masked
(long numbers show only their last 4 digits).
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finalize_lib import CAGES, bank_key, col_index, numeric_cols, section_of  # noqa: E402


def fmt(v):
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (int, float)):
        return "{:,.2f}".format(v)
    return "" if v is None else str(v)


def cage_name(field_id):
    for k, v in CAGES.items():
        if field_id.endswith(k):
            return v
    return None


def cage_value(snap, suffix):
    for tab, fid, label, val in snap.get("fields", []):
        if fid.endswith(suffix):
            return val
    return None


def checks(snap):
    out = []  # (level, message)   level: ok | warn | info
    c = {k: cage_value(snap, k) for k in ("Cage50", "Cage80", "Cage120", "Cage170", "Cage180", "Cage210")}
    if None not in (c["Cage50"], c["Cage80"], c["Cage120"]):
        d = round(max(0.0, c["Cage50"] - c["Cage80"]) - c["Cage120"], 2)  # taxable income can't go below 0
        out.append(("ok" if abs(d) < 0.01 else "warn",
                    "Total income %s − reliefs %s = taxable income %s%s" % (fmt(c["Cage50"]), fmt(c["Cage80"]), fmt(c["Cage120"]),
                                                                           "" if abs(d) < 0.01 else " (difference %s)" % fmt(d))))
    if None not in (c["Cage170"], c["Cage180"], c["Cage210"]):
        d = round(c["Cage170"] - c["Cage180"] - c["Cage210"], 2)
        out.append(("ok" if abs(d) < 0.01 else "warn",
                    "Tax %s − credits %s = balance %s %s" % (fmt(c["Cage170"]), fmt(c["Cage180"]), fmt(c["Cage210"]),
                                                           "payable" if c["Cage210"] > 0 else "refundable/nil")))

    grids = {section_of(g["id"])["key"]: g for g in snap["grids"] if section_of(g["id"])}
    wht, bank = grids.get("interest_wht"), grids.get("bank")
    w_by = defaultdict(lambda: [0.0, 0.0, 0])
    if wht:
        ia, ir, it = (col_index(wht, ["name of the withholding agent"]), col_index(wht, ["amount received"]),
                      col_index(wht, ["deducted"]))
        for r in wht["rows"]:
            k = bank_key(r[ia])
            w_by[k][0] += r[ir] or 0
            w_by[k][1] += r[it] or 0
            w_by[k][2] += 1
    b_by = defaultdict(lambda: [0.0, []])
    if bank:
        ib, ii = col_index(bank, ["name of bank"]), col_index(bank, ["interest"])
        for r in bank["rows"]:
            k = bank_key(r[ib])
            b_by[k][0] += r[ii] or 0
            b_by[k][1].append(r)
    for k in sorted(set(w_by) | set(b_by)):
        wi = round(w_by[k][0], 2) if k in w_by else None
        bi = round(b_by[k][0], 2) if k in b_by else None
        if k in w_by and k not in b_by:
            out.append(("warn", "%s: Schedule 7A interest %s (AIT %s, %d rows) but no bank-balance row in Part 01 B ii "
                                "(balance confirmation pending, or account omitted?)" % (k, fmt(wi), fmt(w_by[k][1]), w_by[k][2])))
        elif k in b_by and k not in w_by:
            out.append(("warn" if bi else "info", "%s: bank interest %s but no Schedule 7A row (no AIT deducted? exempt? "
                                                  "declared elsewhere?)" % (k, fmt(bi))))
        else:
            # rows whose name carries a note (e.g. foreign currency) usually have no AIT/7A row
            plain = sum((r[ii] or 0) for r in b_by[k][1] if "(" not in str(r[ib]))
            noted = round(bi - plain, 2)
            d = round(plain - wi, 2)
            if abs(d) < 0.01:
                out.append(("ok", "%s: bank interest %s matches Schedule 7A %s" % (k, fmt(plain), fmt(wi))))
            else:
                out.append(("warn", "%s: bank interest %s vs Schedule 7A %s (difference %s)" % (k, fmt(plain), fmt(wi), fmt(d))))
            if noted:
                out.append(("warn", "%s: further interest %s on a noted account (e.g. foreign currency) has no Schedule 7A "
                                    "row: confirm whether it is exempt or must be declared" % (k, fmt(noted))))

    liab, prop = grids.get("liabilities"), grids.get("property")
    if liab and liab["rows"]:
        isec = col_index(liab, ["security"])
        props = " ".join(str(r[col_index(prop, ['situation'])]) for r in (prop["rows"] if prop else []))
        for r in liab["rows"]:
            sec = str(r[isec] or "")
            if "MORTGAGE" in sec.upper() and not any(w in props for w in sec.upper().replace(",", " ").split() if len(w) > 5):
                out.append(("warn", "Liability secured by '%s' but no matching property in Part 01 A" % sec))
    for tab, label, checked in snap.get("checkboxes", []):
        if label.startswith(("A. Local", "B. Foreign")):
            has_rows = any(g["rows"] for g in snap["grids"] if g["id"].startswith("gridStatement"))
            if label.startswith("A. Local") and has_rows and not checked:
                out.append(("warn", "'A. Local' is not ticked in 'Assets as at 31 March' although local assets are declared"))
    up = grids.get("uploaded")
    if up is not None:
        out.append(("info" if up["rows"] else "warn",
                    "Document Details: %d document(s) uploaded to RAMIS" % len(up["rows"])))
    return out


def render(snap):
    L = []
    h = snap.get("header", {})
    L.append("# RAMIS IIT return summary – Y/A %s" % h.get("Year of assessment", "?"))
    L.append("")
    L.append("- Taxpayer: %s (TIN %s)" % (h.get("Name of taxpayer", "?"), h.get("Taxpayer Identification Number", "?")))
    L.append("- Return: %s · snapshot taken %s (read-only; long numbers masked)" % (snap.get("page", ""), snap.get("captured", "")))
    L.append("- Tabs: %s" % " → ".join(snap.get("tabs", [])))
    L.append("")
    L.append("## Tax computation (Main Return)")
    L.append("")
    L.append("| Cage | Meaning | Amount (Rs.) |")
    L.append("|---|---|---|")
    for tab, fid, label, val in snap.get("fields", []):
        L.append("| %s | %s | %s |" % (fid.split("_")[-1], cage_name(fid) or label or "", fmt(val)))
    L.append("")
    cs = checks(snap)
    L.append("## Checks")
    L.append("")
    icon = {"ok": "✅", "warn": "⚠️", "info": "ℹ️"}
    for lvl, msg in cs:
        L.append("- %s %s" % (icon[lvl], msg))
    L.append("")
    L.append("## Sections")
    for g in snap["grids"]:
        s = section_of(g["id"])
        L.append("")
        L.append("### %s" % (s["name"] if s else g["title"] or g["id"]))
        L.append("")
        if not g["rows"]:
            L.append("_No rows._")
            continue
        cols = [c[1] for c in g["columns"]]
        keep = [i for i, c in enumerate(cols) if not (i > 0 and cols[i] == cols[i - 1])]
        L.append("| # | " + " | ".join(cols[i] for i in keep) + " |")
        L.append("|---|" + "---|" * len(keep))
        for n, r in enumerate(g["rows"], 1):
            L.append("| %d | " % n + " | ".join(fmt(r[i]).replace("|", "/") for i in keep) + " |")
        nums = numeric_cols(g)
        if nums:
            tot = {i: round(sum((r[i] or 0) for r in g["rows"] if isinstance(r[i], (int, float))), 2) for i in nums}
            L.append("| **Total** | " + " | ".join("**%s**" % fmt(tot[i]) if i in tot and "TIN" not in cols[i] else ""
                                                   for i in keep) + " |")
        L.append("")
        L.append("Rows: %d" % len(g["rows"]))
    return "\n".join(L) + "\n", cs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snapshot")
    ap.add_argument("--out")
    ap.add_argument("--json", help="write the checks as JSON")
    a = ap.parse_args(argv)
    snap = json.load(open(a.snapshot))
    md, cs = render(snap)
    if a.out:
        Path(a.out).write_text(md)
    else:
        sys.stdout.write(md)
    if a.json:
        json.dump([{"level": l, "message": m} for l, m in cs], open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
