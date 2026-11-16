#!/usr/bin/env python3
"""Refuse fixtures that look like real, sensitive documents.

Usage:  python3 tools/check_fixtures.py [tests/fixtures]

Fixtures must be SYNTHETIC text (pdftotext -layout output or canonical JSON)
with every personal value replaced. This checker is a safety net, not a
guarantee: it catches the common leaks (real PDFs or images, NIC numbers,
account-like numbers, phone numbers, personal email addresses) and is run in
CI. Exit code 1 lists every finding.

Placeholder conventions it accepts:
  * long numbers (9+ digits) must contain "0000"   e.g. 100000000001, 310000000000000000001
  * NIC numbers must be all zeros                  e.g. 000000000V
  * email addresses only at institutional or example domains (ALLOWED_EMAIL_DOMAINS)
  * real public identifiers (e.g. a bank's withholding-agent TIN) only if listed
    in PUBLIC_IDENTIFIERS below, with the reason
"""
import re
import sys
from pathlib import Path

ALLOWED_SUFFIXES = {".txt", ".json", ".md"}

# Public, non-personal identifiers that may appear verbatim. Add with a reason.
PUBLIC_IDENTIFIERS = {
    "134008059": "Nations Trust Bank withholding-agent TIN (printed on every certificate)",
    "134001194": "Sampath Bank withholding-agent TIN (printed on every certificate)",
}

ALLOWED_EMAIL_DOMAINS = (
    "example.com", "example.org", "example.lk",
    "cse.lk", "nationstrust.com", "sampath.lk", "capitaltrust.lk", "sspsec.com",
)

RULES = [
    ("long number without a 0000 placeholder", re.compile(r"(?<![\d.,])\d{9,}(?![\d.,])"),
     lambda m: "0000" in m or m in PUBLIC_IDENTIFIERS),
    ("NIC number (old format)", re.compile(r"\b\d{9}[VvXx]\b"), lambda m: set(m[:9]) == {"0"}),
    ("NIC number (new format)", re.compile(r"\b(?:19|20)\d{10}\b"), lambda m: "0000" in m[4:]),
    ("mobile phone number", re.compile(r"(?<!\d)(?:\+94|0)7\d[ -]?\d{3}[ -]?\d{4}(?!\d)"), lambda m: "0000" in m),
    ("email address", re.compile(r"[\w.%+-]+@([\w-]+\.)+[a-z]{2,}", re.I),
     lambda m: m.lower().split("@", 1)[1].endswith(ALLOWED_EMAIL_DOMAINS)),
]


def check(root):
    findings = []
    for f in sorted(Path(root).rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(root)
        if f.suffix.lower() not in ALLOWED_SUFFIXES:
            findings.append(f"{rel}: file type {f.suffix or '(none)'} not allowed; fixtures are synthetic .txt/.json only")
            continue
        text = f.read_text(errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            for label, rx, ok in RULES:
                for m in rx.finditer(line):
                    if not ok(m.group(0)):
                        findings.append(f"{rel}:{n}: {label}: {m.group(0)}")
    return findings


def main(argv):
    root = Path(argv[0]) if argv else Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    findings = check(root)
    for x in findings:
        print(x)
    if findings:
        print(f"\n{len(findings)} finding(s). Replace real values with placeholders (see CONTRIBUTING.md).")
        return 1
    print("fixtures look synthetic")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
