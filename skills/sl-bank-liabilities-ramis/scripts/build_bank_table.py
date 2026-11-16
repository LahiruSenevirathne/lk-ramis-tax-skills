#!/usr/bin/env python3
"""Build the RAMIS bank-balance, liability and property rows from canonical JSON.

Usage:
    build_bank_table.py LETTER.json [...] --fy 2025 [--out FILE.xlsx]
        [--ramis-json rows.json] [--wht wht_rows.json]
        [--savings-invested blank|balance] [--include-zero-balance]
        [--ait-rate 10]

Input: one canonical JSON file per document (balance confirmation letter, loan
statement, property papers), usually written by Claude after reading a scanned
letter. Shape: references/data-model.md. Several files are merged.

Output (stdout): {"rows": {"bank": [...], "liabilities": [...], "property": [...],
"acquired": [...]}, "totals", "needs_confirmation", "problems"}. The "rows"
part is exactly what ramis_statement_fill.js takes.

Checks:
  * AIT ≈ --ait-rate % of interest (warns; foreign currency accounts are often 0)
  * foreign currency amounts need fx_rate (and fx_source) to be converted to LKR
  * loans: (released or granted) - principal repaid == outstanding, else a
    needs_confirmation item (partial release, prepayment, typo?)
  * with --wht (sl-wht-ramis extract JSON): each account's interest and AIT must
    match the certificates' totals for that account
  * balances are as at 31 March of the year of assessment
Exit code 1 when "problems" is not empty.
"""
import argparse
import json
import sys
from collections import defaultdict
from datetime import date

KIND_LABEL = {"savings": "savings", "current": "current", "fixed": "fixed/term deposit",
              "term": "fixed/term deposit", "foreign_currency": "foreign currency"}


def r2(x):
    return None if x is None else round(float(x) + 0.0, 2)


def lkr(amount, acct, problems):
    if amount is None:
        return None
    cur = (acct.get("currency") or "LKR").upper()
    if cur == "LKR":
        return r2(amount)
    rate = acct.get("fx_rate")
    if not rate:
        problems.append("%s %s: %s amount needs fx_rate (and fx_source)" % (acct.get("institution"), _tail(acct.get("account")), cur))
        return None
    return r2(float(amount) * float(rate))


def _amt(x):
    return "{:,.2f}".format(float(x)) if x is not None else "?"


def _tail(s):
    s = str(s or "")
    return "…" + s[-4:] if len(s) > 4 else s


def build(docs, fy, savings_invested="blank", include_zero=False, ait_rate=10.0, wht=None):
    end = date(fy + 1, 3, 31)
    problems, confirm = [], []
    bank, liabilities, prop, acquired = [], [], [], []

    for doc in docs:
        as_at = doc.get("as_at")
        if as_at and as_at != str(end):
            problems.append("%s: balances are as at %s, not %s" % (doc.get("file") or doc.get("source"), as_at, end))

        for a in doc.get("deposits", []):
            if a.get("include") is False:
                continue
            bal = lkr(a.get("balance"), a, problems)
            if not include_zero and (bal or 0) == 0 and not a.get("interest"):
                confirm.append("%s %s: zero balance and no interest, left out (use --include-zero-balance to keep)"
                               % (a["institution"], _tail(a.get("account"))))
                continue
            interest = lkr(a.get("interest"), a, problems)
            kind = a.get("kind", "savings")
            invested = a.get("amount_invested")
            if invested is None and kind in ("fixed", "term"):
                confirm.append("%s %s: term deposit without amount_invested (principal)" % (a["institution"], _tail(a.get("account"))))
            if invested is None and kind not in ("fixed", "term") and savings_invested == "balance":
                invested = a.get("balance")
            invested = lkr(invested, a, problems)
            ait = a.get("ait")
            if a.get("interest") and ait is not None:
                expected = round(float(a["interest"]) * ait_rate / 100, 2)
                if abs(expected - float(ait)) > 0.011:
                    confirm.append("%s %s: AIT %s is not %s%% of interest %s (exempt account, self-declaration, or rate change?)"
                                   % (a["institution"], _tail(a.get("account")), ait, ait_rate, a["interest"]))
            name = a["institution"]
            cur = (a.get("currency") or "LKR").upper()
            if cur != "LKR":
                name += " (%s, %s %s; interest %s %s; converted at %s %s on %s)" % (
                    a.get("product") or cur, cur, _amt(a.get("balance")), cur, _amt(a.get("interest")),
                    a.get("fx_source") or "rate", a.get("fx_rate"), end.strftime("%d-%b-%Y"))
            bank.append({"type": a.get("type", "A"), "institution": name, "account": str(a.get("account") or ""),
                         "invested": invested, "interest": interest, "balance": bal,
                         "_kind": KIND_LABEL.get(kind, kind), "_ait": ait, "_currency": cur})

        for l in doc.get("loans", []):
            granted = l.get("amount_granted")
            released = l.get("amount_released", granted)
            repaid = l.get("principal_repaid")
            out = l.get("outstanding")
            if None not in (released, repaid, out) and abs(float(released) - float(repaid) - float(out)) > 0.01:
                confirm.append("%s loan %s: released %s - principal repaid %s = %s, but outstanding is %s (partial release? prepayment? typo?)"
                               % (l["institution"], _tail(l.get("loan_no")), released, repaid,
                                  r2(float(released) - float(repaid)), out))
            desc = l.get("description") or "%s %s %s" % (l["institution"], l.get("loan_type", "loan"), l.get("loan_no", ""))
            liabilities.append({"type": l.get("type", "A"), "description": desc.strip(),
                                "security": l.get("security") or "None",
                                "commenced": l.get("date_granted"), "original": r2(granted),
                                "outstanding": r2(out),
                                "repaid": r2(repaid if l.get("repaid_basis", "principal") == "principal"
                                             else (repaid or 0) + (l.get("interest_paid") or 0))})

        for p in doc.get("properties", []):
            prop.append({"type": p.get("type", "A"), "situation": p["situation"], "date": p.get("date"),
                         "cost": r2(p.get("cost")), "market_value": r2(p.get("market_value"))})
            if p.get("acquired_in_year"):
                acquired.append({"type": p.get("type", "A"), "description": p.get("short_description") or p["situation"],
                                 "how": p.get("how", "Purchase"), "date": p.get("date"), "value": r2(p.get("cost"))})

    if wht is not None:
        by = defaultdict(lambda: [0.0, 0.0])
        for r in wht.get("rows", []):
            by[str(r.get("account"))][0] += r.get("amount_received") or 0
            by[str(r.get("account"))][1] += r.get("ait") or 0
        for b in bank:
            if b["_currency"] != "LKR" or not b["account"] or b["account"] not in by:
                continue
            gi, ga = by[b["account"]]
            if abs(gi - (b["interest"] or 0)) > 0.01 or (b["_ait"] is not None and abs(ga - b["_ait"]) > 0.01):
                problems.append("%s %s: letter interest/AIT %s/%s but Schedule 7A certificates total %s/%s"
                                % (b["institution"], _tail(b["account"]), b["interest"], b["_ait"], r2(gi), r2(ga)))
        for b in bank:
            if b["_currency"] == "LKR" and b["_ait"] and b["account"] not in by:
                confirm.append("%s %s: AIT %s deducted but no Schedule 7A certificate rows for this account"
                               % (b["institution"], _tail(b["account"]), b["_ait"]))

    clean = lambda rows: [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    return {
        "year_of_assessment": "%d/%02d" % (fy, (fy + 1) % 100),
        "as_at": str(end),
        "rows": {"bank": clean(bank), "liabilities": liabilities, "property": prop, "acquired": acquired},
        "totals": {
            "bank_interest": r2(sum(b["interest"] or 0 for b in bank)),
            "bank_balance": r2(sum(b["balance"] or 0 for b in bank)),
            "liabilities_outstanding": r2(sum(l["outstanding"] or 0 for l in liabilities)),
            "property_cost": r2(sum(p["cost"] or 0 for p in prop)),
        },
        "needs_confirmation": confirm,
        "problems": problems,
    }


def write_xlsx(res, path):
    from openpyxl import Workbook
    wb = Workbook()
    sheets = [
        ("Bank balances", "bank", ["Type", "Name of bank/financial institution", "Account No.", "Amount invested (Rs.)", "Interest (Rs.)", "Balance (Rs.)"],
         ["type", "institution", "account", "invested", "interest", "balance"]),
        ("Liabilities", "liabilities", ["Type", "Description of liability", "Security on liability", "Date of commencement",
                                        "Original amount (Rs.)", "Amount as at 31 March (Rs.)", "Amount repaid during the Y/A (Rs.)"],
         ["type", "description", "security", "commenced", "original", "outstanding", "repaid"]),
        ("Immovable properties", "property", ["Type", "Situation of property", "Date of acquisition", "Cost (Rs.)", "Market value (Rs.)"],
         ["type", "situation", "date", "cost", "market_value"]),
        ("Assets acquired", "acquired", ["Type", "Description of asset", "Gift/exchange/purchase", "Date of acquisition/receipt", "Cost/market value (Rs.)"],
         ["type", "description", "how", "date", "value"]),
    ]
    first = True
    for title, key, header, fields in sheets:
        ws = wb.active if first else wb.create_sheet()
        first = False
        ws.title = title
        ws.append(header)
        for r in res["rows"][key]:
            ws.append([r.get(f) for f in fields])
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(60, max(10, max(len(str(c.value or "")) for c in col) + 2))
    wb.save(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--fy", type=int, required=True)
    ap.add_argument("--out")
    ap.add_argument("--ramis-json")
    ap.add_argument("--wht", help="sl-wht-ramis extract_certificates.py output, for the interest/AIT cross-check")
    ap.add_argument("--savings-invested", choices=["blank", "balance"], default="blank")
    ap.add_argument("--include-zero-balance", action="store_true")
    ap.add_argument("--ait-rate", type=float, default=10.0)
    a = ap.parse_args(argv)
    docs = []
    for f in a.files:
        d = json.load(open(f))
        d.setdefault("file", f)
        docs.append(d)
    wht = json.load(open(a.wht)) if a.wht else None
    res = build(docs, a.fy, a.savings_invested, a.include_zero_balance, a.ait_rate, wht)
    if a.out:
        write_xlsx(res, a.out)
    if a.ramis_json:
        json.dump(res["rows"], open(a.ramis_json, "w"), indent=1)
    json.dump(res, sys.stdout, indent=1)
    print()
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
