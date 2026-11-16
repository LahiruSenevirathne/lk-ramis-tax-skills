"""Tests for sl-ramis-iit-finalize (build_summary.py, check_documents.py). Synthetic data only."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "sl-ramis-iit-finalize" / "scripts"))
import build_summary as bs  # noqa: E402
import check_documents as cd  # noqa: E402

SNAP = json.loads((Path(__file__).parent / "fixtures" / "finalize" / "snapshot_example.json").read_text())


def test_summary_sections_totals_and_cages():
    md, _ = bs.render(SNAP)
    assert "# RAMIS IIT return summary – Y/A 2025/2026" in md
    assert "Schedule 7A – AIT/WHT deducted by the Withholding Agent" in md
    assert "| **Total** |" in md and "**1,800.00**" in md          # Schedule 7A amount total
    assert "Balance tax payable" in md and "Taxable income" in md
    assert "_No rows._" in md                                         # disposals empty


def test_checks():
    cs = dict((m, l) for l, m in bs.checks(SNAP))
    text = "\n".join(cs)
    assert any(l == "ok" and "= taxable income" in m for m, l in cs.items())
    assert any(l == "ok" and "Tax 100.00 − credits 180.00 = balance -80.00 refundable" in m for m, l in cs.items())
    assert "EXAMPLE BANK: bank interest 800.00 matches Schedule 7A 800.00" in text
    assert "further interest 300.00 on a noted account" in text      # foreign-currency interest without 7A
    assert "OTHER BANK: Schedule 7A interest 1,000.00" in text and "no bank-balance row" in text
    assert "'A. Local' is not ticked" in text
    assert "0 document(s) uploaded" in text


def test_requirements_and_matching(tmp_path):
    year = tmp_path / "YA-2025-26"
    (year / "3-bank-liabilities" / "originals" / "example").mkdir(parents=True)
    (year / "3-bank-liabilities" / "originals" / "example" / "scan_0001.pdf").write_bytes(b"x")
    (year / "1-interest-wht" / "originals" / "example").mkdir(parents=True)
    (year / "1-interest-wht" / "originals" / "example" / "wht_cert_apr.pdf").write_bytes(b"x")
    other = tmp_path / "Downloads"
    other.mkdir()
    (other / "PortfolioValuation.pdf").write_bytes(b"x")
    reqs = cd.check(SNAP, year, [other])
    by = {r["document"]: r for r in reqs}
    bal = by["Balance confirmation letter as at 31 March from Example Bank"]
    assert bal["status"] == "FOUND" and bal["found"] == ["3-bank-liabilities/originals/example/scan_0001.pdf"]
    assert by["AIT/WHT certificate(s) from Example Bank"]["status"] == "FOUND"
    assert by["AIT/WHT certificate(s) from Other Bank"]["status"] == "MISSING"
    assert any("Other Bank" in d and "no bank-balance row" in d for d in by)
    val = by["Broker portfolio valuation / statement of holdings as at 31 March"]
    assert val["status"] == "ELSEWHERE"
    assert any(r["section"] == "property" and r["status"] == "MISSING" for r in reqs)
    loan = [r for r in reqs if r["section"] == "liabilities"][0]
    assert loan["status"] == "FOUND"                                  # lender folder in the right section
    assert any(r["section"] == "employment" and r["status"] == "MISSING" for r in reqs)


def test_assemble_copies_only(tmp_path):
    year = tmp_path / "YA"
    src = year / "3-bank-liabilities" / "originals" / "example" / "letter.pdf"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"x")
    (year / "ramis").mkdir()
    (year / "ramis" / "summary.md").write_text("# s\n")
    reqs = cd.check(SNAP, year)
    copied = cd.assemble(reqs, year)
    assert src.exists()                                               # original untouched
    assert any(c.endswith("letter.pdf") for c in copied)
    assert (year / "final" / "README.md").exists() and (year / "final" / "missing-documents.md").exists()
    assert (year / "final" / "summary.md").exists()
    assert "MISSING" in (year / "final" / "missing-documents.md").read_text()


def test_working_files_and_other_documents_are_not_evidence(tmp_path):
    year = tmp_path / "YA"
    (year / "3-bank-liabilities" / "work").mkdir(parents=True)
    (year / "3-bank-liabilities" / "work" / "example.json").write_text("{}")
    other = tmp_path / "old"
    other.mkdir()
    (other / "OTHER_WHT_2025-04.pdf").write_bytes(b"x")       # a certificate, not a balance letter
    reqs = cd.check(SNAP, year, [other])
    bal = [r for r in reqs if r["section"] == "bank" and "Example Bank" in r["document"]][0]
    assert bal["status"] == "MISSING"
    pending = [r for r in reqs if "Other Bank" in r["document"] and r["section"] == "bank"][0]
    assert pending["status"] == "MISSING"
    wht = [r for r in reqs if "AIT/WHT certificate(s) from Other Bank" == r["document"]][0]
    assert wht["status"] == "ELSEWHERE"


def test_counterparty_words_do_not_cross_match(tmp_path):
    year = tmp_path / "YA"
    f = year / "2-shares-cse" / "originals" / "capital_trust" / "Trade_Confirmation_as_at_02_04_2025.pdf"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"x")
    snap = json.loads(json.dumps(SNAP))
    snap["grids"][1]["rows"].append(["I-INTEREST", 300000000, "NATIONS TRUST BANK", "N/0001", 10.0, "2025-05-01", 1.0])
    reqs = cd.check(snap, year)
    ntb = [r for r in reqs if r["section"] == "bank" and "Nations Trust" in r["document"]][0]
    assert ntb["tokens"][0] == "nations" and "ntb" in ntb["tokens"] and "trust" not in ntb["tokens"]
    assert ntb["status"] == "MISSING"                                   # a trade confirmation is not a balance letter
