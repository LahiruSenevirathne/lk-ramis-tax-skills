# Contributing

Thank you for helping more Sri Lankan taxpayers file with less typing. The
most useful contribution is a **parser for a provider that isn't supported
yet**: a bank or finance company's AIT/WHT certificate, a stockbroker's
contract notes or holdings statement, or a registrar's dividend warrant.

## The one rule: no real documents, no real data

This repository is public. Never commit, attach to an issue, or paste into a
pull request:

- PDFs, scans, screenshots, spreadsheets or emails from a real person;
- names, NIC/passport numbers, TINs of individuals, addresses, phone numbers,
  email addresses;
- account, certificate, CDS, contract or receipt numbers;
- real amounts or dates from someone's documents;
- "redacted" copies of real files. Redaction misses things (metadata, hidden
  text layers, totals that identify a person). Write a synthetic sample instead.

Public, non-personal identifiers that are printed on every customer's document
(e.g. a bank's withholding-agent TIN) may be used. List them in
`PUBLIC_IDENTIFIERS` in `tools/check_fixtures.py` with the reason.

## How parsers are organised

```
skills/
  sl-wht-ramis/scripts/
    extract_certificates.py   core: text extraction, canonical JSON, checks, CLI
    wht_parsers/              one module per bank / financial institution
      __init__.py             registry (discovers every module automatically)
      _common.py              shared helpers (money, dates)
      _template.py            copy this to start a new bank
      ntb.py, sampath.py      tested providers
  sl-cse-stocks-ramis/scripts/
    extract_cse.py            core: text extraction, canonical JSON, checks, CLI
    cse_parsers/              one module per provider
      cds.py                  CDS documents, common to every investor
      capital_trust.py        a stockbroker (the worked example)
      _template.py            copy this to start a new broker or registrar
tests/fixtures/
  wht/<parser id>/            synthetic samples for each bank parser
  cse/<parser id>/            synthetic samples for each CSE parser
  */canonical/                hand-written canonical JSON examples
tools/check_fixtures.py       rejects fixtures that look real (runs in CI)
```

Each parser module declares a `PROVIDER` dict (`id`, `name`, `documents`,
`tested`) and its parse function(s). It returns rows in the shape the rest of
the skill already understands:

- bank certificates: the row fields in
  `skills/sl-wht-ramis/references/bank-formats.md`;
- CSE documents: the canonical shapes in
  `skills/sl-cse-stocks-ramis/references/data-model.md`.

Nothing else has to change. The registry finds the module, and the table
builders and RAMIS fillers work as before.

## Adding a provider, step by step

1. **Look at the layout locally.** On your own machine, run
   `pdftotext -layout your.pdf -` (or pypdf) on your document. Keep that output
   private.
2. **Write a synthetic fixture** in `tests/fixtures/<wht|cse>/<id>/`. Keep the
   structure (headings, column order, line breaks, how totals are printed)
   and **invent every value**:
   - names like `Mr. A B Sample`, addresses like `1 Sample Road`;
   - NIC `000000000V`; long numbers with a `0000` placeholder, e.g. account
     `100000000001`, certificate `XYZ/2025/000001`;
   - small round amounts that still add up, so the self-checks run (e.g.
     rows 100.00 + 250.00 = printed total 350.00).
   Add one fixture per layout variant (e.g. monthly and yearly, or an old and a
   new column layout).
3. **Copy the template**: `wht_parsers/_template.py` or `cse_parsers/_template.py`
   to `<id>.py`. Fill in `PROVIDER`, the detection phrase, and the parse
   function(s).
4. **Self-check everything printed.** Compare rows with every printed total,
   check rates (AIT = rate × gross), and fail loudly instead of guessing a
   missing value.
5. **Tests**: add cases to `tests/test_extract.py` (banks) or
   `tests/test_cse.py` (CSE) that parse your fixture and assert the rows.
6. **Document**: add a section to `bank-formats.md` or `cse-formats.md` (sender,
   subject, whether it's password-protected and the *kind* of password, never
   the value), and add a row to **Tested providers** in `README.md`.
7. **Run the checks**:
   ```bash
   pip install -r requirements.txt pytest
   python -m pytest -q
   python tools/check_fixtures.py
   ```
   `tests/test_repository_rules.py` fails if a parser has no fixtures folder,
   no README entry, or incomplete `PROVIDER` metadata.

## Can't write code? Describe the layout instead

Open an issue using the **New provider** template. Describe the document in
words (title, which columns, where the totals are) or paste a **synthetic**
sample you typed yourself. Never attach the real document.

## Other contributions

Fixes to the RAMIS field maps (labels and IDs change between years), better
wording in the skills, and new filing skills (see
`skills/sl-ramis-getting-started/references/skills-registry.md`) are all welcome.
