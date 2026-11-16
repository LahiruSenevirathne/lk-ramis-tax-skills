"""Helpers shared by bank parsers."""
from datetime import datetime

SAVINGS = "Savings interest"
FIXED = "Fixed deposit interest"


def money(s):
    return round(float(s.replace(",", "")), 2)


def iso(s):
    """Convert 15-May-2025, 15-MAY-25, 15-05-2025 or 01/04/2025 to YYYY-MM-DD."""
    s = s.strip()
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.title() if "b" in fmt else s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError(f"unrecognised date: {s!r}")
