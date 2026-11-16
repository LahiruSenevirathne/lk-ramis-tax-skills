"""<Institution name>: <certificate name>.   (copy to wht_parsers/<id>.py)

Layout notes: add a section to ../references/bank-formats.md.
Synthetic fixtures: tests/fixtures/wht/<id>/  (never real documents).
"""
import re

from ._common import FIXED, SAVINGS, iso, money  # noqa: F401

PROVIDER = {
    "id": "<id>",                      # short, lowercase; matches the fixtures folder
    "name": "<Institution PLC>",       # as it should appear in RAMIS (agent name)
    "documents": ["<certificate title as printed>"],
    "tested": "<Y/A you tested on, e.g. 2025/26>",
}


def detect(text):
    # A phrase that only this institution's certificates contain.
    return "<Institution PLC>" in text


def parse(text, name):
    tin = re.search(r"Withholding Agent TIN\s*:?\s*(\d+)", text)
    rows = []
    # for each certificate row:
    #   rows.append({
    #     "source_type": SAVINGS | FIXED | None,   # None if the certificate doesn't say
    #     "agent_tin": tin.group(1) if tin else None,
    #     "agent_name": PROVIDER["name"],
    #     "certificate_no": ..., "account": ...,
    #     "amount_received": money(gross), "ait": money(ait), "ait_rate_pct": float(rate),
    #     "net_paid": money(net),
    #     "interest_date": iso(...) or None, "ird_paid_date": iso(...) or None,
    #     "ird_receipt_no": ... or None,
    #     "period_from": ..., "period_to": ..., "file": name,
    #   })
    checks = {}
    # Compare against any printed total, e.g.
    # checks["gross_matches"] = abs(printed_total - sum(r["amount_received"] for r in rows)) < 0.005
    return {"bank": PROVIDER["id"], "kind": "<monthly|yearly|...>", "file": name, "rows": rows, "checks": checks}
