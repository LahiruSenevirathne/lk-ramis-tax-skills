"""Nations Trust Bank PLC: monthly AIT certificate and consolidated yearly certificate.

Layout notes: ../references/bank-formats.md. Synthetic fixtures: tests/fixtures/wht/ntb/.
"""
import re

from ._common import FIXED, SAVINGS, iso, money

PROVIDER = {
    "id": "ntb",
    "name": "Nations Trust Bank PLC",
    "documents": ["Monthly Certificate of Advance Income Tax (AIT) Deduction",
                  "Consolidated yearly WHT certificate (cross-check only)"],
    "tested": "Y/A 2025/26",
}


def detect(text):
    return "Nations Trust Bank" in text


NTB_ROW = re.compile(
    r"^\s*(Savings|Saving|Fixed)\s+(\d{6,})\s+.*?([\d,]+\.\d{2})\s+(\d+(?:\.\d+)?)%\s+"
    r"([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*$", re.M)
NTB_RECEIPT = re.compile(r"^\s*(\d{10,})\s+(\d{2}-[A-Za-z]{3}-\d{2,4})\s*$", re.M)


def parse(text, name):
    cert = re.search(r"Certificate No\s*:?/?\s*Serial No\s*:-?\s*(\S+)", text)
    cert = cert.group(1) if cert else None
    tin = re.search(r"Withholding Agent TIN\s*:\s*(\d+)", text)
    period = re.search(r"from\s*:\s*(\S+)\s+to\s*:?\s*(\S+)", text)
    gross = re.search(r"Gross amount of Interest/Discount\s*(?:\(LKR\))?\s*:\s*(?:LKR\s*)?([\d,]+\.\d{2})", text)
    consolidated = bool(cert and cert.upper().startswith("BC/"))
    receipts = NTB_RECEIPT.findall(text)
    ird_date = iso(receipts[0][1]) if len(receipts) == 1 else None
    rows = []
    if not consolidated:
        for kind, acc, amt, rate, ait, net in NTB_ROW.findall(text):
            rows.append({
                "source_type": SAVINGS if kind.startswith("Sav") else FIXED,
                "agent_tin": tin.group(1) if tin else None,
                "agent_name": "Nations Trust Bank",
                "certificate_no": cert,
                "account": acc,
                "amount_received": money(amt),
                "ait": money(ait),
                "ait_rate_pct": float(rate),
                "net_paid": money(net),
                "interest_date": None,  # NTB monthly certificates show a period only
                "ird_paid_date": ird_date,
                "ird_receipt_no": receipts[0][0] if len(receipts) == 1 else None,
                "period_from": iso(period.group(1)) if period else None,
                "period_to": iso(period.group(2)) if period else None,
                "file": name,
            })
    else:
        # Consolidated rows wrap account numbers over two lines; capture totals only.
        for m in re.finditer(r"LKR\s+([\d,]+\.\d{2})\s+(\d+)%\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})", text):
            rows.append({
                "source_type": None, "agent_tin": tin.group(1) if tin else None,
                "agent_name": "Nations Trust Bank", "certificate_no": cert, "account": None,
                "amount_received": money(m.group(1)), "ait": money(m.group(3)),
                "ait_rate_pct": float(m.group(2)), "net_paid": money(m.group(4)),
                "interest_date": None, "ird_paid_date": None, "ird_receipt_no": None,
                "period_from": iso(period.group(1)) if period else None,
                "period_to": iso(period.group(2)) if period else None, "file": name,
            })
    checks = {}
    if gross:
        checks["printed_gross"] = money(gross.group(1))
        checks["rows_gross"] = round(sum(r["amount_received"] for r in rows), 2)
        checks["gross_matches"] = abs(checks["printed_gross"] - checks["rows_gross"]) < 0.005
    return {"bank": "NTB", "kind": "consolidated" if consolidated else "monthly",
            "file": name, "rows": rows, "checks": checks}


