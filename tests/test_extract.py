"""Tests for extract_certificates.py and build_table.py using synthetic fixtures.

All fixture data is invented. Run with:  python -m pytest -q
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "sl-wht-ramis" / "scripts"
FIX = Path(__file__).parent / "fixtures" / "wht"

sys.path.insert(0, str(SCRIPTS))
import extract_certificates as ex  # noqa: E402


def text(name):
    return next(FIX.rglob(name)).read_text()


def test_ntb_monthly():
    doc = ex.parse(text("ntb_monthly_example.txt"), "ntb.txt")
    assert doc["bank"] == "NTB" and doc["kind"] == "monthly"
    assert doc["checks"]["gross_matches"]
    rows = {r["account"]: r for r in doc["rows"]}
    assert set(rows) == {"300000000001", "200000000001"}
    fd, sav = rows["300000000001"], rows["200000000001"]
    assert fd["source_type"] == "Fixed deposit interest"
    assert sav["source_type"] == "Savings interest"
    assert fd["amount_received"] == 10000.00 and fd["ait"] == 1000.00
    assert sav["amount_received"] == 2345.67 and sav["ait"] == 234.57
    assert fd["certificate_no"] == "WHT/2025/SEP/99999999"
    assert fd["agent_tin"] == "134008059"
    assert fd["ird_paid_date"] == "2025-10-14"
    assert fd["interest_date"] is None
    assert (fd["period_from"], fd["period_to"]) == ("2025-09-01", "2025-09-30")


def test_ntb_consolidated_is_flagged():
    doc = ex.parse(text("ntb_consolidated_example.txt"), "cons.txt")
    assert doc["kind"] == "consolidated"
    assert doc["checks"]["gross_matches"]
    assert round(sum(r["amount_received"] for r in doc["rows"]), 2) == 12345.67


def test_sampath():
    doc = ex.parse(text("sampath_example.txt"), "sampath.txt")
    assert doc["bank"] == "Sampath"
    assert doc["checks"]["gross_matches"] and doc["checks"]["ait_matches"]
    assert len(doc["rows"]) == 3
    first = doc["rows"][0]
    assert first["certificate_no"] == "310000000000000000001"
    assert first["interest_date"] == "2025-04-20"
    assert first["ird_paid_date"] == "2025-05-15"
    assert first["agent_tin"] == "134001194"
    assert first["source_type"] is None  # certificate does not say savings or FD


def test_unrecognised():
    assert ex.parse("Some other bank letter", "x.txt")["kind"] == "unrecognised"


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def test_cli_and_build_table(tmp_path):
    out = run(SCRIPTS / "extract_certificates.py", FIX / "ntb", FIX / "sampath")
    assert out.returncode == 0, out.stdout + out.stderr
    data = json.loads(out.stdout)
    assert data["problems"] == []
    # consolidated rows are excluded by default
    assert len(data["rows"]) == 5
    rows_json = tmp_path / "rows.json"
    rows_json.write_text(out.stdout)

    xlsx, csvf, ramis = tmp_path / "t.xlsx", tmp_path / "t.csv", tmp_path / "r.json"
    b = run(SCRIPTS / "build_table.py", rows_json, "--fy", "2025", "--date-mode", "ird",
            "--out", xlsx, "--csv", csvf, "--ramis-json", ramis,
            "--account-type", "100000000001=savings")
    assert b.returncode == 0, b.stderr
    summary = json.loads(b.stdout)
    assert summary["rows"] == 5
    assert summary["missing_source_type"] == 0
    assert summary["total_amount_received"] == round(12345.67 + 1400.49, 2)
    assert summary["total_ait"] == round(1234.57 + 140.05, 2)
    header = csvf.read_text().splitlines()[0]
    assert header.startswith("Source/type,TIN of the Withholding Agent,Name of the Withholding Agent")
    r = json.loads(ramis.read_text())
    assert {x["agent"] for x in r} == {"NATIONS TRUST BANK", "SAMPATH BANK PLC"}
    assert all(x["source"] == "I-INTEREST" for x in r)


def test_interest_date_mode_leaves_ntb_empty(tmp_path):
    out = run(SCRIPTS / "extract_certificates.py", FIX / "ntb", FIX / "sampath")
    rows_json = tmp_path / "rows.json"
    rows_json.write_text(out.stdout)
    ramis = tmp_path / "r.json"
    b = run(SCRIPTS / "build_table.py", rows_json, "--fy", "2025", "--date-mode", "interest",
            "--out", tmp_path / "t.xlsx", "--ramis-json", ramis)
    assert b.returncode == 0, b.stderr
    r = json.loads(ramis.read_text())
    assert all(x["date"] == "" for x in r if x["agent"] == "NATIONS TRUST BANK")
    assert all(x["date"] for x in r if x["agent"] == "SAMPATH BANK PLC")


# ---- registry and banks without a parser --------------------------------------------
def test_registry_lists_the_tested_banks():
    ids = [p["id"] for p in ex.parsers.providers()]
    assert ids == ["ntb", "sampath"]


def test_canonical_rows_for_another_bank(tmp_path):
    out = run(SCRIPTS / "extract_certificates.py", FIX / "canonical" / "other_bank_example.json")
    assert out.returncode == 0, out.stdout
    data = json.loads(out.stdout)
    assert data["problems"] == []
    assert data["rows"][0]["agent_name"] == "Example Finance PLC" and data["rows"][0]["ait"] == 500.0


def test_canonical_rows_are_validated():
    out = run(SCRIPTS / "extract_certificates.py", FIX / "canonical" / "bad_example.json")
    assert out.returncode == 1
    err = json.dumps(json.loads(out.stdout)["problems"])
    for field in ("agent_tin", "certificate_no", "amount_received", "ait", "interest_date"):
        assert field in err


def test_unrecognised_names_tested_banks(tmp_path):
    f = tmp_path / "other.txt"
    f.write_text("Certificate of AIT deduction - Some Other Bank PLC")
    out = run(SCRIPTS / "extract_certificates.py", f)
    assert out.returncode == 1
    assert "Nations Trust Bank PLC, Sampath Bank PLC" in out.stdout
