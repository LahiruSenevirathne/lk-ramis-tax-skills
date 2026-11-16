"""<Broker name>: <documents>.   (copy to cse_parsers/<id>.py)

Layout notes: add a section to ../references/cse-formats.md.
Synthetic fixtures: tests/fixtures/cse/<id>/  (never real documents).
"""
import re

from ._common import NUM, ddmmyyyy, num  # noqa: F401

PROVIDER = {
    "id": "<id>",                    # short, lowercase; matches the fixtures folder
    "name": "<Broker (Private) Limited>",
    "family": "broker",              # or "registrar" for dividend warrants from a registrar
    "documents": ["<contract note title>", "<holdings statement title>"],
    "tested": "<Y/A you tested on>",
}


def parse_contract_note(t, name):
    """t is whitespace-squashed text. Return None if this isn't the document."""
    if "<phrase only this broker's contract notes contain>" not in t:
        return None
    trades = []
    # trades.append({"date": "YYYY-MM-DD" (trade date), "side": "buy"|"sell",
    #                "code": "ABC.N0000", "isin": ..., "name": ..., "qty": int,
    #                "avg_price": float, "gross": float, "net": float (incl. all fees),
    #                "contracts": [...], "file": name})
    checks = {
        "has_trades": bool(trades),
        # "purchase_total_matches": ..., compare with any printed total
    }
    return {"kind": "trade_confirmation", "file": name, "trades": trades, "checks": checks}


def parse_holdings(t, name):
    if "<phrase only the holdings statement contains>" not in t:
        return None
    holdings = []
    # holdings.append({"code", "name", "quantity": int, "vwa_price": float,
    #                  "market_value": float, "as_at": "YYYY-MM-DD", "file": name})
    checks = {"has_rows": bool(holdings)}
    return {"kind": "portfolio_valuation", "file": name, "holdings": holdings, "checks": checks}


DOCUMENTS = [parse_holdings, parse_contract_note]
