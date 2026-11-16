"""Tests for sl-bank-liabilities-ramis (build_bank_table.py). All data is synthetic."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "sl-bank-liabilities-ramis" / "scripts"))
import build_bank_table as bb  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "bank" / "canonical"


def docs():
    return [json.loads((FIX / f).read_text()) for f in ("example_bank_a.json", "example_bank_b.json")]


def test_rows_and_conventions():
    res = bb.build(docs(), 2025)
    assert res["problems"] == []
    bank = {r["account"]: r for r in res["rows"]["bank"]}
    assert "100000000002" not in bank                     # zero-balance current account left out
    assert bank["100000000001"] == {"type": "A", "institution": "Example Bank PLC", "account": "100000000001",
                                    "invested": None, "interest": 500.0, "balance": 100000.0}
    assert bank["200000000001"]["invested"] == 500000.0    # term deposit: principal
    usd = bank["200000000002"]
    assert (usd["balance"], usd["interest"]) == (30000.0, 3000.0)   # USD x 300
    assert usd["institution"] == ("Sample Finance PLC (PFCA, USD 100.00; interest USD 10.00; "
                                  "converted at CBSL TT buying 300.0 on 31-Mar-2026)")
    assert res["totals"]["bank_balance"] == 630000.0


def test_loans_property_and_acquired():
    res = bb.build(docs(), 2025)
    home, personal = res["rows"]["liabilities"]
    assert (home["original"], home["outstanding"], home["repaid"]) == (1000000.0, 880000.0, 20000.0)
    assert home["security"] == "Mortgage of 1 Sample Road, Colombo"
    # 1,000,000 granted but 900,000 released: 900,000 - 20,000 = 880,000 reconciles, no flag
    assert not any("400000000001"[-4:] in c and "outstanding" in c for c in res["needs_confirmation"])
    # personal: 500,000 - 150,000 = 350,000 but outstanding 300,000 -> flagged
    assert any("…0002" in c and "outstanding is 300000" in c for c in res["needs_confirmation"])
    assert res["rows"]["property"][0]["cost"] == 1200000.0
    assert res["rows"]["acquired"] == [{"type": "A", "description": "House, 1 Sample Road", "how": "Purchase",
                                        "date": "2026-01-20", "value": 1200000.0}]


def test_repaid_basis_principal_plus_interest():
    d = docs()
    d[0]["loans"][1]["repaid_basis"] = "principal_plus_interest"
    res = bb.build(d, 2025)
    assert res["rows"]["liabilities"][1]["repaid"] == 190000.0


def test_foreign_currency_without_rate_is_a_problem():
    d = docs()
    del d[1]["deposits"][1]["fx_rate"]
    assert any("needs fx_rate" in p for p in bb.build(d, 2025)["problems"])


def test_wrong_year_is_a_problem():
    d = docs()
    d[0]["as_at"] = "2025-03-31"
    assert any("not 2026-03-31" in p for p in bb.build(d, 2025)["problems"])


def test_wht_cross_check():
    wht = json.loads((FIX / "wht_rows.json").read_text())
    res = bb.build(docs(), 2025, wht=wht)
    # term deposit matches its two certificates (30,000 / 3,000); savings letter says 500/50 vs 400/40
    assert len(res["problems"]) == 1 and "…0001" in res["problems"][0] and "400.0/40.0" in res["problems"][0]


def test_ait_rate_warning():
    res = bb.build(docs(), 2025)
    assert any("…0002" in c and "AIT 0" in c for c in res["needs_confirmation"])  # USD account, no AIT


def test_cli(tmp_path):
    out = tmp_path / "rows.json"
    rc = bb.main([str(FIX / "example_bank_a.json"), str(FIX / "example_bank_b.json"), "--fy", "2025",
                  "--out", str(tmp_path / "t.xlsx"), "--ramis-json", str(out)])
    assert rc == 0
    assert set(json.loads(out.read_text())) == {"bank", "liabilities", "property", "acquired"}
