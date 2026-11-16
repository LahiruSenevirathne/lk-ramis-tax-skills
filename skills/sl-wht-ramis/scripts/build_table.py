#!/usr/bin/env python3
"""Turn extract_certificates.py output into the RAMIS Schedule 7 interest table.

Writes an .xlsx (and optionally .csv) with exactly these columns, in this order:

  Source/type | TIN of the Withholding Agent | Name of the Withholding Agent |
  AIT/WHT certificate No. | Amount received (Rs.) | Date of payment |
  AIT/ WHT deducted by the withholding agent (Rs.)

followed by reference-only columns (account, interest period, IRD remittance date,
source file) and a totals row that uses SUM formulas.

Usage:
  build_table.py rows.json --fy 2025 --date-mode ird --out WHT_FY2025-26.xlsx \
      [--csv WHT_FY2025-26.csv] [--ramis-json ramis_rows.json] \
      [--account-type 1234567890=savings ...]

  --fy 2025         year of assessment starting 1 April 2025 (ends 31 March 2026)
  --date-mode ird   Date of payment = date the bank paid the AIT to the IRD
  --date-mode interest  Date of payment = date the interest was credited
                    (left empty when a certificate does not show it)
  --account-type    set Source/type for accounts whose certificate does not say
                    (savings | fd)

Requires openpyxl.
"""
import argparse
import csv
import json
import sys
from datetime import date

HEADERS = [
    "Source/type",
    "TIN of the Withholding Agent",
    "Name of the Withholding Agent",
    "AIT/WHT certificate No.",
    "Amount received (Rs.)",
    "Date of payment",
    "AIT/ WHT deducted by the withholding agent (Rs.)",
]
REF_HEADERS = ["Account No. (ref)", "Interest period (ref)", "AIT remitted to IRD on (ref)", "Source file (ref)"]
TYPES = {"savings": "Savings interest", "fd": "Fixed deposit interest"}


def in_fy(row, start, end):
    """Keep a row when its interest date, or else its period end, is inside the year."""
    d = row.get("interest_date") or row.get("period_to")
    if not d:
        return True  # cannot tell; keep it and let the person decide
    return start <= date.fromisoformat(d) <= end


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rows_json")
    ap.add_argument("--fy", type=int, required=True, help="first calendar year of the year of assessment, e.g. 2025")
    ap.add_argument("--date-mode", choices=["ird", "interest"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv")
    ap.add_argument("--ramis-json", help="also write rows in the shape ramis_fill.js expects")
    ap.add_argument("--account-type", action="append", default=[], metavar="ACCOUNT=savings|fd")
    args = ap.parse_args()

    data = json.load(open(args.rows_json))
    rows = data["rows"] if isinstance(data, dict) else data
    overrides = {}
    for item in args.account_type:
        acc, kind = item.split("=", 1)
        overrides[acc.strip()] = TYPES[kind.strip().lower()]

    start, end = date(args.fy, 4, 1), date(args.fy + 1, 3, 31)
    kept, dropped = [], []
    for r in rows:
        (kept if in_fy(r, start, end) else dropped).append(r)
    kept.sort(key=lambda r: (r["agent_name"] or "", r.get("period_from") or "", r.get("interest_date") or "",
                             0 if r.get("source_type") == TYPES["savings"] else 1))

    table = []
    for r in kept:
        src = overrides.get(r.get("account") or "", r.get("source_type")) or ""
        when = r.get("ird_paid_date") if args.date_mode == "ird" else r.get("interest_date")
        period = " to ".join(x for x in (r.get("period_from"), r.get("period_to")) if x)
        table.append([src, r.get("agent_tin") or "", r.get("agent_name") or "", r.get("certificate_no") or "",
                      r["amount_received"], when or "", r["ait"],
                      r.get("account") or "", period, r.get("ird_paid_date") or "", r.get("file") or ""])

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = f"WHT FY{args.fy}-{str(args.fy + 1)[2:]}"
    ws.append(HEADERS + REF_HEADERS)
    for t in table:
        ws.append([date.fromisoformat(v) if i in (5, 9) and v else v for i, v in enumerate(t)])
    last = len(table) + 1
    ws.append(["Total", "", "", "", f"=SUM(E2:E{last})", "", f"=SUM(G2:G{last})"])

    base, bold = Font(name="Arial", size=10), Font(name="Arial", size=10, bold=True)
    thin = Side(style="thin", color="BFBFBF")
    for row in ws.iter_rows():
        for c in row:
            c.font = bold if c.row in (1, last + 1) else base
            c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
            c.alignment = Alignment(vertical="top", wrap_text=c.row == 1)
    for c in ws[1]:
        c.fill = PatternFill("solid", fgColor="D9E1F2")
    for i in range(2, last + 2):
        ws[f"E{i}"].number_format = ws[f"G{i}"].number_format = "#,##0.00"
        ws[f"F{i}"].number_format = ws[f"J{i}"].number_format = "yyyy-mm-dd"
        for col in "BDH":
            ws[f"{col}{i}"].number_format = "@"
    for i, w in enumerate([24, 14, 22, 26, 14, 14, 18, 16, 26, 16, 30], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 45
    ws.freeze_panes = "A2"

    notes = [
        "Amount received = gross interest before AIT, as printed on each certificate.",
        "Date of payment = " + ("date the bank remitted the AIT to the IRD." if args.date_mode == "ird"
                                else "date the interest was credited; empty where the certificate does not show it."),
        "Columns H-K are reference only and are not entered into RAMIS.",
    ]
    ws.cell(row=last + 3, column=1, value="Notes").font = bold
    for k, t in enumerate(notes):
        ws.cell(row=last + 4 + k, column=1, value=t).font = base
    wb.save(args.out)

    if args.ramis_json:
        with open(args.ramis_json, "w") as f:
            json.dump([{"tin": t[1], "agent": t[2].upper(), "cert": t[3], "amount": t[4],
                        "date": t[5], "ait": t[6], "source": "I-INTEREST"} for t in table], f, indent=1)

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(HEADERS)
            for t in table:
                w.writerow(t[:7])

    summary = {
        "rows": len(table),
        "dropped_outside_year": len(dropped),
        "missing_source_type": sum(1 for t in table if not t[0]),
        "total_amount_received": round(sum(t[4] for t in table), 2),
        "total_ait": round(sum(t[6] for t in table), 2),
        "by_agent": {},
    }
    for t in table:
        a = summary["by_agent"].setdefault(t[2], {"rows": 0, "amount_received": 0.0, "ait": 0.0})
        a["rows"] += 1
        a["amount_received"] = round(a["amount_received"] + t[4], 2)
        a["ait"] = round(a["ait"] + t[6], 2)
    json.dump(summary, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
