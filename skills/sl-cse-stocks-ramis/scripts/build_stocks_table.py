#!/usr/bin/env python3
"""Build the RAMIS shares (assets) and disposals tables from extract_cse.py output.

Usage:
    build_stocks_table.py extracted.json --fy 2025 --out Shares_FY2025-26.xlsx \
        [--ramis-json ramis_rows.json] [--sold-dividends zero-row|omit] \
        [--names names.json]

--fy 2025 means year of assessment 2025/26 (1 April 2025 to 31 March 2026).

RAMIS sections (Statement of assets & liabilities tab):
  shares     Part 1 iii. "Shares/stocks/securities as at 31.03.YYYY"
             Type | Name of company | No. of shares | Date of acquisition |
             Cost of acquisition/market value if not acquired | Net dividend income
  disposals  Part 2 B. "Disposal of assets including shares during the year"
             Type | Description | Date of disposal | Sales proceed | Date acquired | Cost

Rules (the defaults the skill confirms with the user at Stage 0):
  * Lots = broker purchases (net amount incl. fees) + CDS direct deposits
    without a matching withdrawal (scrip dividend / bonus) at NIL cost.
  * A same-day "withdraw all + deposit N" on the CDS statement is a share
    subdivision/consolidation: earlier lots' quantities are scaled, cost kept.
  * Sales consume lots first-in-first-out. Disposal cost = cost of the lots
    consumed; "Date acquired" = the earliest lot consumed; proceeds = net
    amount after fees; dates are trade dates.
  * Holdings at year end: lots bought inside the year -> one row at cost (date
    = first purchase in the year); lots from before the year -> one row at
    31 March market value (VWA) from the portfolio valuation (date = first
    such lot). Quantities are reconciled to the valuation.
  * Net dividends paid inside the year (e-warrant date) go on the company's
    first holding row; companies no longer held get a 0-share row
    (--sold-dividends zero-row, default) or are left out (omit).

Everything that needs a human decision is listed in "needs_confirmation";
anything that does not reconcile is listed in "problems".
"""
import argparse
import json
import sys
from collections import defaultdict
from datetime import date


def d(s):
    return date.fromisoformat(s)


def r2(x):
    return round(x + 0.0, 2)


def build(ex, fy, sold_dividends="zero-row", names=None):
    start, end = date(fy, 4, 1), date(fy + 1, 3, 31)
    names = dict(names or {})
    problems, confirm = [], []

    for t in ex["trades"]:
        names.setdefault(t["code"], t["name"])
    vals = [h for h in ex["holdings"] if d(h["as_at"]) == end]
    if not vals:
        problems.append("no portfolio valuation as at %s" % end)
    val = {h["code"]: h for h in vals}
    for h in vals:
        names[h["code"]] = names.get(h["code"]) or h["name"]

    # ---- events per security, in date order --------------------------------
    events = defaultdict(list)
    for t in ex["trades"]:
        events[t["code"]].append((t["date"], 1 if t["side"] == "buy" else 2, t))
    moves = defaultdict(list)
    for m in ex["movements"]:
        if m["kind"] in ("deposit", "withdrawal"):
            moves[(m["code"], m["date"])].append(m)
        else:
            confirm.append("CDS statement %s: unclassified movement for %s on %s: %s"
                           % (m["file"], m["code"], m["date"], m.get("text")))
    for (code, day), ms in moves.items():
        w = [m for m in ms if m["kind"] == "withdrawal"]
        dep = [m for m in ms if m["kind"] == "deposit"]
        if w and dep and dep[0]["qty"] != w[0]["qty"]:
            ratio = dep[0]["qty"] / w[0]["qty"]
            events[code].append((day, 0, {"type": "split", "ratio": ratio, "from": w[0]["qty"], "to": dep[0]["qty"]}))
            confirm.append("%s: %d shares became %d on %s (treated as a 1:%g subdivision; cost unchanged)"
                           % (code, w[0]["qty"], dep[0]["qty"], day, ratio))
        elif dep and not w:
            for m in dep:
                events[code].append((day, 1, {"type": "scrip", "qty": m["qty"], "date": day, "ref": m["ref"]}))
                confirm.append("%s: %d shares deposited on %s with no purchase (ref %s), treated as scrip/bonus at nil cost"
                               % (code, m["qty"], day, m["ref"]))
        elif w and not dep:
            confirm.append("%s: %d shares withdrawn on %s with no matching deposit; check (transfer out?)"
                           % (code, w[0]["qty"], day))

    disposals, held = [], {}
    for code, evs in events.items():
        lots = []  # [date, qty, cost]
        for day, _, e in sorted(evs, key=lambda x: (x[0], x[1])):
            if e.get("type") == "split":
                for lot in lots:
                    lot[1] = lot[1] * e["ratio"]
            elif e.get("type") == "scrip":
                lots.append([day, e["qty"], 0.0])
            elif e["side"] == "buy":
                lots.append([day, e["qty"], e["net"]])
            else:  # sell, FIFO
                need, cost, first = e["qty"], 0.0, None
                while need > 1e-9 and lots:
                    lot = lots[0]
                    take = min(need, lot[1])
                    cost += lot[2] * take / lot[1]
                    first = first or lot[0]
                    lot[2] -= lot[2] * take / lot[1]
                    lot[1] -= take
                    need -= take
                    if lot[1] <= 1e-9:
                        lots.pop(0)
                if need > 1e-9:
                    problems.append("%s: sold %d on %s but only %d accounted for by known purchases"
                                    % (code, e["qty"], day, e["qty"] - need))
                if start <= d(day) <= end:
                    disposals.append({
                        "code": code, "name": names.get(code, code), "qty": e["qty"],
                        "disposal_date": day, "proceeds": r2(e["net"]),
                        "acquired": first, "cost": r2(cost),
                    })
        held[code] = [lot for lot in lots if d(lot[0]) <= end]

    # ---- holdings at year end ------------------------------------------------
    shares = []
    for code in sorted(set(val) | {c for c, ls in held.items() if sum(l[1] for l in ls) > 1e-9}):
        lots = held.get(code, [])
        v = val.get(code)
        inside = [l for l in lots if d(l[0]) >= start]
        before = [l for l in lots if d(l[0]) < start]
        q_in = round(sum(l[1] for l in inside))
        q_before = round(sum(l[1] for l in before))
        q_val = v["quantity"] if v else 0
        if v is None:
            problems.append("%s: %d shares by trade history but not in the valuation" % (code, q_in + q_before))
            continue
        if q_in + q_before != q_val:
            gap = q_val - q_in - q_before
            if gap > 0:
                confirm.append("%s: valuation shows %d shares, trade history explains %d; %d older shares valued at market value with no date"
                               % (code, q_val, q_in + q_before, gap))
                q_before += gap
                before.append(["", gap, 0.0])
            else:
                problems.append("%s: trade history gives %d shares but valuation shows %d" % (code, q_in + q_before, q_val))
                continue
        if q_in:
            shares.append({"code": code, "company": v["name"], "shares": q_in,
                           "date": min(l[0] for l in inside), "value": r2(sum(l[2] for l in inside)),
                           "dividend": None, "basis": "cost (acquired in the year)"})
        if q_before:
            dated = [l[0] for l in before if l[0]]
            shares.append({"code": code, "company": v["name"], "shares": q_before,
                           "date": min(dated) if dated else None, "value": r2(q_before * v["vwa_price"]),
                           "dividend": None, "basis": "market value at %s (held before the year)" % end})

    # ---- dividends -------------------------------------------------------------
    codes = set(names) | set(val)
    per_code = defaultdict(float)
    for w in ex["dividends"]:
        if not w.get("date") or not (start <= d(w["date"]) <= end):
            continue
        cands = sorted(c for c in codes if w.get("code_root") and c.split(".")[0] == w["code_root"])
        cands = [c for c in cands if c.endswith(".N0000")] or cands
        if not cands:
            confirm.append("dividend %s (%s) could not be matched to a security" % (w.get("warrant_no"), w.get("company")))
            continue
        per_code[cands[0]] += w["net"]
        names.setdefault(cands[0], w.get("company") or cands[0])
    for code, amt in sorted(per_code.items()):
        row = next((s for s in shares if s["code"] == code), None)
        if row:
            row["dividend"] = r2((row["dividend"] or 0) + amt)
        elif sold_dividends == "zero-row":
            shares.append({"code": code, "company": names.get(code, code), "shares": 0, "date": None,
                           "value": None, "dividend": r2(amt), "basis": "not held at year end; dividend only"})

    val_total = sum(h["market_value"] for h in vals)
    return {
        "year_of_assessment": "%d/%02d" % (fy, (fy + 1) % 100),
        "as_at": str(end),
        "shares": shares,
        "disposals": disposals,
        "totals": {
            "shares_value": r2(sum(s["value"] or 0 for s in shares)),
            "shares_dividend": r2(sum(s["dividend"] or 0 for s in shares)),
            "disposal_proceeds": r2(sum(x["proceeds"] for x in disposals)),
            "disposal_cost": r2(sum(x["cost"] for x in disposals)),
            "valuation_market_value": r2(val_total),
        },
        "needs_confirmation": confirm,
        "problems": problems,
    }


def ramis_rows(res):
    return {
        "shares": [{"type": "A", "company": s["company"], "shares": s["shares"], "date": s["date"],
                    "value": s["value"], "dividend": s["dividend"]} for s in res["shares"]],
        "disposals": [{"type": "A",
                       "description": "Shares - %s (%s) - %s shares" % (x["name"], x["code"], format(x["qty"], ",")),
                       "disposal_date": x["disposal_date"], "proceeds": x["proceeds"],
                       "acquired": x["acquired"], "cost": x["cost"]} for x in res["disposals"]],
    }


def write_xlsx(res, rows, path):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Shares %s" % res["as_at"]
    ws.append(["S/N", "Type", "Code", "Name of company/institution", "No. of shares/stocks etc.",
               "Date of acquisition", "Cost of acquisition/market value if not acquired (Rs.)",
               "Net dividend income (Rs.)", "Basis"])
    for i, (s, r) in enumerate(zip(res["shares"], rows["shares"]), 1):
        ws.append([i, r["type"], s["code"], r["company"], r["shares"], r["date"], r["value"], r["dividend"], s["basis"]])
    ws.append([])
    ws.append(["", "", "", "TOTAL", "", "", res["totals"]["shares_value"], res["totals"]["shares_dividend"]])
    ws2 = wb.create_sheet("Disposals")
    ws2.append(["S/N", "Type", "Description", "Date of disposal", "Sales proceed (Rs.)", "Date acquired", "Cost (Rs.)"])
    for i, r in enumerate(rows["disposals"], 1):
        ws2.append([i, r["type"], r["description"], r["disposal_date"], r["proceeds"], r["acquired"], r["cost"]])
    ws2.append([])
    ws2.append(["", "", "TOTAL", "", res["totals"]["disposal_proceeds"], "", res["totals"]["disposal_cost"]])
    for sheet in (ws, ws2):
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = min(60, max(10, max(len(str(c.value or "")) for c in col) + 2))
    wb.save(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("extracted")
    ap.add_argument("--fy", type=int, required=True, help="start year of the year of assessment, e.g. 2025")
    ap.add_argument("--out", help="write an .xlsx here")
    ap.add_argument("--ramis-json", help="write the rows ramis_stocks_fill.js takes")
    ap.add_argument("--sold-dividends", choices=["zero-row", "omit"], default="zero-row")
    ap.add_argument("--names", help="JSON {code: company name} overrides")
    a = ap.parse_args(argv)
    ex = json.load(open(a.extracted))
    names = json.load(open(a.names)) if a.names else None
    res = build(ex, a.fy, a.sold_dividends, names)
    rows = ramis_rows(res)
    if a.out:
        write_xlsx(res, rows, a.out)
    if a.ramis_json:
        json.dump(rows, open(a.ramis_json, "w"), indent=1)
    json.dump(res, sys.stdout, indent=1)
    print()
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
