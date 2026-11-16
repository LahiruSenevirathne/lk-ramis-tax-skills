"""Capital TRUST Securities (Private) Limited: the worked broker example.

Documents: trade confirmation, portfolio valuation as at DD/MM/YYYY.
Layout notes: ../references/cse-formats.md. Synthetic fixtures: tests/fixtures/cse/capital_trust/.
"""
import re

from ._common import NUM, ddmmyyyy, num

PROVIDER = {
    "id": "capital_trust",
    "name": "Capital TRUST Securities (Private) Limited",
    "family": "broker",
    "documents": ["Trade Confirmation", "Portfolio Valuation as at 31 March"],
    "tested": "Y/A 2025/26",
}


def parse_valuation(t, name):
    m = re.search(r"Portfolio Valuation as at (\d\d/\d\d/\d{4})", t)
    if not m:
        return None
    doc = {"kind": "portfolio_valuation", "file": name, "as_at": ddmmyyyy(m.group(1)), "holdings": []}
    row = re.compile(r"(?m)^\s*([A-Z0-9]+\.[A-Z]\d{4})\s+(.+?)\s+(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")\s+("
                     + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")\s*$")
    for r in row.finditer(t):
        code, sname, ub, us, cleared, bal, pledged, vwa, value = r.groups()
        doc["holdings"].append({
            "code": code, "name": " ".join(sname.split()),
            "unsettled_buy": int(num(ub)), "unsettled_sell": int(num(us)),
            "cleared": int(num(cleared)), "quantity": int(num(bal)), "pledged": int(num(pledged)),
            "vwa_price": num(vwa), "market_value": num(value), "as_at": doc["as_at"], "file": name,
        })
    tot = re.search(r"(?m)^\s*Total\s+(" + NUM + r")\s*$", t)
    s = round(sum(h["market_value"] for h in doc["holdings"]), 2)
    doc["total_market_value"] = num(tot.group(1)) if tot else None
    doc["checks"] = {
        "rows_value_eq_qty_x_price": all(abs(h["quantity"] * h["vwa_price"] - h["market_value"]) < 0.01
                                         for h in doc["holdings"]),
        "total_matches": tot is not None and abs(num(tot.group(1)) - s) < 0.01,
        "has_rows": bool(doc["holdings"]),
        "no_unsettled": all(h["unsettled_buy"] == 0 and h["unsettled_sell"] == 0 for h in doc["holdings"]),
    }
    return doc


def parse_trade_confirmation(t, name):
    if "TRADE CONFIRMATION" not in t:
        return None
    doc = {"kind": "trade_confirmation", "file": name, "trades": [], "checks": {}}
    m = re.search(r"Transaction Date\s*:\s*(\d\d/\d\d/\d{4})", t)
    doc["transaction_date"] = ddmmyyyy(m.group(1)) if m else None
    pat = re.compile(
        r"(Purchase|Sale)s? of (.+?) \( ?([A-Z0-9]+\.[A-Z]\d{4}) ?/ ?([A-Z0-9]+) ?\)(.*?)\n\s*Total ([^\n]+)",
        re.S)
    for m in pat.finditer(t):
        side, sec_name, code, isin, body, tot = m.groups()
        tk = re.findall(NUM, tot)
        dates = re.findall(r"(?m)^\s*(\d\d/\d\d/\d{4}) (\d{6,})", body)
        if len(tk) < 4 or not dates:
            doc.setdefault("unparsed", []).append(code)
            continue
        doc["trades"].append({
            "date": ddmmyyyy(dates[0][0]),
            "side": "buy" if side == "Purchase" else "sell",
            "code": code, "isin": isin, "name": " ".join(sec_name.split()),
            "qty": int(num(tk[0])), "avg_price": num(tk[1]),
            "gross": num(tk[2]),
            "net": num(tk[-2]),  # last column is "Foreign Brokerage"
            "contracts": [c for _, c in dates],
            "file": name,
        })
    pt = re.search(r"Purchase Total\s+(" + NUM + ")", t)
    st = re.search(r"Sales Total\s+(" + NUM + ")", t)
    buys = round(sum(x["net"] for x in doc["trades"] if x["side"] == "buy"), 2)
    sells = round(sum(x["net"] for x in doc["trades"] if x["side"] == "sell"), 2)
    doc["checks"] = {
        "purchase_total_matches": bool(pt) and abs(num(pt.group(1)) - buys) < 0.01,
        "sales_total_matches": bool(st) and abs(num(st.group(1)) - sells) < 0.01,
        "has_trades": bool(doc["trades"]) and not doc.get("unparsed"),
    }
    return doc



DOCUMENTS = [parse_valuation, parse_trade_confirmation]
