"""Repository rules: parsers are registered with metadata, fixtures and docs,
and fixtures contain nothing that looks like real personal data."""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
README = (ROOT / "README.md").read_text()

sys.path.insert(0, str(ROOT / "tools"))
import check_fixtures  # noqa: E402

# skill folder -> fixtures sub-folder
SKILLS = {"sl-wht-ramis": ("wht", "wht_parsers"), "sl-cse-stocks-ramis": ("cse", "cse_parsers")}


def registry(skill, package):
    scripts = str(ROOT / "skills" / skill / "scripts")
    sys.path.insert(0, scripts)
    try:
        return importlib.import_module(package).providers()
    finally:
        sys.path.remove(scripts)


def test_every_parser_has_metadata_fixtures_and_readme_entry():
    for skill, (fx, package) in SKILLS.items():
        provs = registry(skill, package)
        assert provs, skill
        for p in provs:
            for key in ("id", "name", "documents", "tested"):
                assert p.get(key), f"{skill}/{p.get('id')}: PROVIDER needs {key}"
            folder = FIXTURES / fx / p["id"]
            assert folder.is_dir() and any(folder.iterdir()), f"no synthetic fixtures in {folder}"
            assert f"`{p['id']}`" in README, f"{p['id']} missing from README 'Tested providers'"


def test_fixtures_look_synthetic():
    assert check_fixtures.check(FIXTURES) == []


def test_checker_catches_real_looking_data(tmp_path):
    # Values in real-looking FORMATS that cannot belong to anyone; they must all be flagged.
    # NICs use day-of-year 999 (doesn't exist); the account number is sequential; the
    # phone number is a placeholder; .invalid is a reserved, never-real email domain.
    (tmp_path / "leak.txt").write_text(
        "NIC No: 859994321V\n"
        "NIC: 198599912345\n"
        "Account Number: 123456789012\n"
        "Mobile 071 000 0001\n"
        "mail jane.doe@mail.invalid\n"
    )
    (tmp_path / "real.pdf").write_bytes(b"%PDF-1.7")
    found = "\n".join(check_fixtures.check(tmp_path))
    for label in ("not allowed", "NIC number (old format)", "NIC number (new format)",
                  "long number", "mobile phone", "email"):
        assert label in found, label
