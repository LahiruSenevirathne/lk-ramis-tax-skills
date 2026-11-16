"""Sampath Bank PLC: yearly Certificate of Advance Income Tax Deduction, one per account.

Layout notes: ../references/bank-formats.md. Synthetic fixtures: tests/fixtures/wht/sampath/.
"""
import re

from ._common import iso, money

PROVIDER = {
    "id": "sampath",
    "name": "Sampath Bank PLC",
    "documents": ["Certificate of Advance Income Tax Deduction (yearly, per account)"],
    "tested": "Y/A 2025/26",
}


def detect(text):
    return "Sampath Bank" in text


SAMPATH_ROW = re.compile(
    r"^\s*(\d{2}-\d{2}-\d{4})\s+(\d+(?:\.\d+)?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+"
    r"([\d,]+\.\d{2})\s+(\S+)\s+(\d{2}-\d{2}-\d{4})\s+(\d{10,})\s*$", re.M)
SAMPATH_TOTAL = re.compile(r"^\s*Total\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})", re.M)


def parse(text, name, source_type=None):
    tin = re.search(r"Withholding Agent TIN:\s*(\d+)", text)
    acc = re.search(r"Account Number:\s*(\d+)", text)
    period = re.search(r"From\s+(\d{2}-\d{2}-\d{4})\s+to\s+(\d{2}-\d{2}-\d{4})", text)
    rows = []
    for tdate, rate, gross, ait, net, chq, paid, cert in SAMPATH_ROW.findall(text):
        rows.append({
            "source_type": source_type,  # the certificate does not say savings vs FD
            "agent_tin": tin.group(1) if tin else None,
            "agent_name": "Sampath Bank PLC",
            "certificate_no": cert,
            "account": acc.group(1) if acc else None,
            "amount_received": money(gross),
            "ait": money(ait),
            "ait_rate_pct": float(rate),
            "net_paid": money(net),
            "interest_date": iso(tdate),
            "ird_paid_date": iso(paid),
            "ird_receipt_no": chq,
            "period_from": iso(period.group(1)) if period else None,
            "period_to": iso(period.group(2)) if period else None,
            "file": name,
        })
    checks = {}
    tot = SAMPATH_TOTAL.search(text)
    if tot:
        checks["printed_gross"], checks["printed_ait"] = money(tot.group(1)), money(tot.group(2))
        checks["rows_gross"] = round(sum(r["amount_received"] for r in rows), 2)
        checks["rows_ait"] = round(sum(r["ait"] for r in rows), 2)
        checks["gross_matches"] = abs(checks["printed_gross"] - checks["rows_gross"]) < 0.005
        checks["ait_matches"] = abs(checks["printed_ait"] - checks["rows_ait"]) < 0.005
    return {"bank": "Sampath", "kind": "yearly-per-account", "file": name,
            "rows": rows, "checks": checks}


