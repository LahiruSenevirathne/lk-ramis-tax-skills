"""Tests for sl-cse-stocks-ramis (extract_cse.py, build_stocks_table.py).

All fixture data is invented. Run with:  python -m pytest -q
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "sl-cse-stocks-ramis" / "scripts"
FIX = Path(__file__).parent / "fixtures" / "cse"

sys.path.insert(0, str(SCRIPTS))
import build_stocks_table as bt  # noqa: E402
import extract_cse as ex  # noqa: E402

GOOD = [
    "tc_2025-01-15.txt", "tc_2025-05-10.txt", "tc_2025-06-01.txt", "tc_2025-07-02.txt",
    "tc_2026-01-22.txt", "valuation_2026-03-31.txt", "warrant_xyz.txt", "warrant_mno.txt",
    "warrant_next_year.txt", "estatement_2025-03.txt", "estatement_2026-01.txt",
]


def fx(name):
    return next(FIX.rglob(name))


def doc(name):
    return ex.parse(fx(name).read_text(), name)


def extracted(files=GOOD):
    out = {"documents": [], "trades": [], "dividends": [], "holdings": [], "movements": [], "problems": []}
    for f in files:
        d = doc(f)
        out["trades"] += d.get("trades", [])
        out["holdings"] += d.get("holdings", [])
        out["movements"] += d.get("movements", [])
        if d["kind"] == "dividend_warrant":
            out["dividends"].append(d)
    return out


# ---- extraction --------------------------------------------------------------
def test_trade_confirmation_old_layout_two_securities():
    d = doc("tc_2025-01-15.txt")
    assert d["kind"] == "trade_confirmation"
    assert all(d["checks"].values())
    xyz, abc = d["trades"]
    assert (xyz["code"], xyz["side"], xyz["qty"], xyz["net"]) == ("XYZ.N0000", "buy", 100, 1011.20)
    assert (abc["code"], abc["qty"], abc["net"], abc["date"]) == ("ABC.N0000", 50, 5056.00, "2025-01-15")
    assert abc["contracts"] == ["20250100002", "20250100003"]


def test_trade_confirmation_new_layout_with_clearing_fee():
    d = doc("tc_2025-05-10.txt")
    assert all(d["checks"].values())
    assert d["trades"][0]["net"] == 2225.17  # not the clearing-fee column


def test_trade_confirmation_sale():
    t = doc("tc_2025-07-02.txt")["trades"][0]
    assert (t["side"], t["qty"], t["net"]) == ("sell", 52, 6170.11)


def test_trade_confirmation_bad_total_is_flagged():
    d = doc("tc_bad_total.txt")
    assert d["checks"]["purchase_total_matches"] is False


def test_valuation():
    d = doc("valuation_2026-03-31.txt")
    assert d["kind"] == "portfolio_valuation" and d["as_at"] == "2026-03-31"
    assert all(d["checks"].values())
    h = d["holdings"][0]
    assert (h["code"], h["quantity"], h["vwa_price"], h["market_value"]) == ("XYZ.N0000", 300, 12.0, 3600.0)


def test_dividend_warrants():
    d = doc("warrant_xyz.txt")
    assert d["kind"] == "dividend_warrant" and all(d["checks"].values())
    assert (d["code_root"], d["date"], d["gross"], d["ait"], d["net"]) == ("XYZ", "2025-09-10", 35.29, 5.29, 30.0)
    assert d["company"] == "EXAMPLE HOLDINGS PLC"
    m = doc("warrant_mno.txt")
    assert (m["net"], m["shares"]) == (85.0, 10)


def test_estatement_movements():
    mv = doc("estatement_2026-01.txt")["movements"]
    assert [(m["kind"], m["qty"]) for m in mv] == [("withdrawal", 10), ("deposit", 100)]
    scrip = doc("estatement_2025-03.txt")["movements"]
    assert scrip == [{"date": "2025-03-18", "code": "ABC.N0000", "kind": "deposit", "ref": "ABC250001S2",
                      "qty": 2, "balance_after": 52, "file": "estatement_2025-03.txt"}]


def test_unrecognised():
    assert doc("unrelated.txt")["kind"] == "unrecognised"


# ---- building ------------------------------------------------------------------
def test_build_shares_and_disposals():
    res = bt.build(extracted(), 2025)
    assert res["problems"] == []
    shares = [(s["code"], s["shares"], s["date"], s["value"], s["dividend"]) for s in res["shares"]]
    assert shares == [
        ("XYZ.N0000", 200, "2025-05-10", 2225.17, 30.0),       # bought in the year: cost; dividend on first row
        ("XYZ.N0000", 100, "2025-01-15", 1200.0, None),        # held before the year: 100 x 12.00 market value
        ("MNO.N0000", 0, None, None, 85.0),                    # sold, but paid a dividend in the year
    ]
    disp = [(x["code"], x["qty"], x["disposal_date"], x["proceeds"], x["acquired"], x["cost"]) for x in res["disposals"]]
    assert sorted(disp) == [
        ("ABC.N0000", 52, "2025-07-02", 6170.11, "2025-01-15", 5056.0),   # 50 bought + 2 scrip at nil cost
        ("MNO.N0000", 100, "2026-01-22", 1482.84, "2025-06-01", 1112.31),  # 10 became 100 (1:10 subdivision)
    ]
    assert res["totals"]["shares_dividend"] == 115.0  # next-year warrant ignored
    assert any("scrip" in c for c in res["needs_confirmation"])
    assert any("subdivision" in c for c in res["needs_confirmation"])


def test_sold_dividends_omit():
    res = bt.build(extracted(), 2025, sold_dividends="omit")
    assert [s["code"] for s in res["shares"]] == ["XYZ.N0000", "XYZ.N0000"]


def test_missing_purchase_history_is_a_problem():
    files = [f for f in GOOD if f != "tc_2025-01-15.txt"]
    res = bt.build(extracted(files), 2025)
    assert any("ABC.N0000" in p for p in res["problems"])          # sale with no purchases
    assert any("XYZ.N0000" in c for c in res["needs_confirmation"])  # 100 shares unexplained -> MV, no date


def test_ramis_rows_shape():
    rows = bt.ramis_rows(bt.build(extracted(), 2025))
    assert set(rows) == {"shares", "disposals"}
    assert set(rows["shares"][0]) == {"type", "company", "shares", "date", "value", "dividend"}
    assert set(rows["disposals"][0]) == {"type", "description", "disposal_date", "proceeds", "acquired", "cost"}
    assert rows["disposals"][0]["description"] == "Shares - ALPHA BANK PLC (ABC.N0000) - 52 shares"


# ---- broker-agnostic input -----------------------------------------------------------
def test_sources_are_tagged():
    assert doc("tc_2025-01-15.txt")["source"] == "capital_trust"
    assert doc("warrant_xyz.txt")["source"] == "cds"
    assert doc("estatement_2025-03.txt")["source"] == "cds"


def test_canonical_json_from_another_broker_merges():
    rows, probs = ex.load_canonical(fx("other_broker_canonical.json"))
    assert probs == []
    data = extracted()
    for k, v in rows.items():
        data[k] += v
    res = bt.build(data, 2025)
    assert res["problems"] == []
    qrs = [x for x in res["disposals"] if x["code"] == "QRS.N0000"][0]
    assert (qrs["proceeds"], qrs["cost"], qrs["acquired"]) == (2500.0, 2024.0, "2025-08-01")
    assert [s for s in res["shares"] if s["code"] == "QRS.N0000"][0]["dividend"] == 17.0


def test_canonical_json_is_validated():
    _, probs = ex.load_canonical(fx("bad_canonical.json"))
    text = " ".join(probs)
    assert "trades[0]" in text and "date" in text and "side" in text and "code" in text and "qty" in text
    assert "gross - ait != net" in text


def test_cli_reads_mixed_folder(tmp_path, capsys):
    import shutil
    for f in GOOD + ["other_broker_canonical.json"]:
        shutil.copy(fx(f), tmp_path / f)
    assert ex.main([str(tmp_path)]) == 0
    import json
    out = json.loads(capsys.readouterr().out)
    assert out["problems"] == []
    assert any(d["kind"] == "canonical_json" for d in out["documents"])


def test_registry_order_and_tested_providers():
    ids = [p["id"] for p in ex.parsers.providers()]
    assert ids == ["capital_trust", "cds"]  # brokers first, CDS last
