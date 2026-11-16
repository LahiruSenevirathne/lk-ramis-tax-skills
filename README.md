# lk-ramis-tax-skills

[Claude](https://claude.com) skills that help Sri Lankan taxpayers fill in the
**RAMIS** individual income tax return (https://eservices.ird.gov.lk) from the
documents banks, brokers and the CDS already email them.

Start with **`sl-ramis-getting-started`**: it asks what you want to file, tells
you which documents to gather (in the IRD's own terms), and asks where they are (a folder, Google Drive, Gmail, iCloud/Apple Mail,
Outlook, bank or broker portals), writes a short filing plan, and runs the
filing skills below in turn.

| Skill | From | To (RAMIS) |
|---|---|---|
| [`sl-ramis-getting-started`](skills/sl-ramis-getting-started) | Your answers: what to file, where the documents are | A filing plan; hands over to the skills below |
| [`sl-wht-ramis`](skills/sl-wht-ramis) | Bank AIT/WHT certificates for savings and FD interest | Schedule 7, Interest Income – A |
| [`sl-cse-stocks-ramis`](skills/sl-cse-stocks-ramis) | Any broker's trade confirmations/contract notes and 31 March valuation, plus CDS dividend e-warrants and eStatements | Statement of assets & liabilities: **iii. Shares/stocks/securities** (with net dividends) and **Part 2 B. Disposal of assets including shares** |
| [`sl-bank-liabilities-ramis`](skills/sl-bank-liabilities-ramis) | Balance confirmation letters (any bank; often scanned), loan letters, property papers | Statement of assets & liabilities: **ii. Bank balances**, **D. Liabilities**, **A. Immovable properties**, **Part 2 A. Assets acquired** |
| [`sl-ramis-iit-finalize`](skills/sl-ramis-iit-finalize) | Your filled return (read-only) and the year's tax folder | A section-by-section summary with checks, a supporting-documents checklist (found / elsewhere / missing) and a `final/` folder |

Every stage stops and waits for you. The skills never sign in to anything,
never type your password into a website, and never press Save, Submit or Next
in RAMIS. You review the rows and press **Save draft** yourself.

> **Not tax advice.** These are data-entry helpers. Check every figure against
> your documents and with your accountant or the IRD before you file.
>
> **Unofficial.** This is an independent, community project. It is not made,
> endorsed or supported by the Inland Revenue Department (IRD) of Sri Lanka,
> the Colombo Stock Exchange, the CDS, or any bank or broker named in it. "RAMIS"
> refers to the IRD's online tax system, which these skills help you fill in.

## What this plugin does on your machine

So you know exactly what runs and where your data goes:

- **No servers, no telemetry, no network calls of its own.** The plugin is skills
  (instructions for Claude) plus small Python, shell and JavaScript helpers in
  `skills/*/scripts/`. None of them sends data anywhere.
- **Reads your documents locally.** The Python scripts read PDFs/text you point
  them at (`pdftotext`/`pypdf`), and write JSON, `.xlsx` and Markdown files into
  a folder you choose (by default `~/Documents/Tax-Sri-Lanka/YA-<year>/`).
  `unlock_pdfs.sh` decrypts copies of password-protected PDFs with `qpdf`; the
  password comes from an environment variable or a hidden prompt and is never
  stored.
- **Uses only the tools you have connected.** To collect documents, Claude may
  use mail or Drive connectors (e.g. Gmail, Apple Mail MCP) that *you* installed,
  and asks before saving any attachment.
- **Fills RAMIS only in your own browser, only when you say so.** The `*.js`
  helpers are pasted into your already signed-in RAMIS tab (via a browser tool
  such as Claude in Chrome). They set form fields and press only RAMIS's own
  **Add Row / Add** buttons, read rows back to check them, and never press Save,
  Submit, Next or Remove. `ramis_snapshot.js` (finalize) only reads the page,
  masks long numbers, and saves a JSON file only if you agree.
- **Never signs in, never types passwords into websites, never uploads
  documents to RAMIS.** You stay in control of saving and submitting.

---

## sl-wht-ramis: interest certificates → Schedule 7

1. **Scope.** Confirms the year of assessment, where your certificates are
   (any source), whether they're password-protected, what to exclude, and which
   date to use as "Date of payment".
2. **Find.** Searches your mail or lists a folder/Drive, shows what it found and
   what it skipped, and asks before downloading anything.
3. **Unlock and extract.** Unlocks copies of the PDFs and reads them, checking
   each certificate's printed totals and the AIT rate.
4. **Table.** Builds an .xlsx (plus CSV) with these columns:
   `Source/type | TIN of the Withholding Agent | Name of the Withholding Agent | AIT/WHT certificate No. | Amount received (Rs.) | Date of payment | AIT/ WHT deducted by the withholding agent (Rs.)`
5. **RAMIS (optional).** With your go-ahead and your RAMIS tab open, adds the
   rows through the form's own **Add** button, checks each one, and hands back
   to you to review and press **Save draft**.

**Works with any bank or financial institution, but parsers are tested with
only two banks so far** (see [Tested providers](#tested-providers)).
Certificates from any other bank, finance or leasing company come back as
"unrecognised". Claude then reads them and writes the rows in a documented
JSON shape, and the same checks and table apply. Adding a parser for your
bank makes it automatic for everyone: see [Contributing](#contributing).

## sl-cse-stocks-ramis: CSE shares → assets and disposals

1. **Scope.** Confirms the year, broker and CDS account, where the documents
   are, the passwords, and the conventions: cost vs 31 March market value,
   first purchase date, how to show dividends from shares you've sold, and net
   vs gross amounts.
2. **Find.** Collects, from wherever you keep them, the trade confirmations,
   dividend e-warrants, CDS eStatements and the broker's 31 March portfolio
   valuation, going back far enough to explain every share you sold.
3. **Unlock and extract.** Reads every document and checks it against its own
   printed totals.
4. **Tables.** Builds both RAMIS tables in one .xlsx:
   - **Shares at 31 March**: company, no. of shares, date of acquisition,
     cost (or market value for shares held from before the year), and net
     dividend income;
   - **Disposals**: description, date of disposal, sale proceeds, date
     acquired, cost (first in, first out).

   Scrip dividends (CDS direct deposits with no purchase) count at nil cost.
   Share subdivisions keep the cost and rescale the quantity. Every such
   inference is put to you to confirm.
5. **RAMIS (optional).** Adds rows to both sections through RAMIS's own
   **Add Row** / **Add**: one row first for you to check, then the rest. Then
   it reads everything back against the totals.

**Works with any broker, but broker parsers are tested with only one broker
so far.** CDS documents (e-warrants, eStatements) are the same for everyone
and are always parsed. Broker documents differ: **Capital TRUST Securities**
is the worked example. For other brokers, Claude reads the documents into a
documented JSON shape
([`data-model.md`](skills/sl-cse-stocks-ramis/references/data-model.md)), and
the same checks and tables apply.

## Tested providers

Each parser below was written from real documents and tested on a real return
(the documents themselves are **not** in this repository; only synthetic
fixtures are). Anything not listed works through Claude reading the
document, without a parser.

| Skill | Provider | Parser id | Documents | Tested on |
|---|---|---|---|---|
| `sl-wht-ramis` | Nations Trust Bank PLC | `ntb` | Monthly Certificate of AIT Deduction; consolidated yearly certificate (cross-check only) | Y/A 2025/26 |
| `sl-wht-ramis` | Sampath Bank PLC | `sampath` | Yearly Certificate of AIT Deduction, one per account | Y/A 2025/26 |
| `sl-cse-stocks-ramis` | CDS (Colombo Stock Exchange): every investor | `cds` | Dividend e-warrant / certificate of tax deduction; monthly eStatement | Y/A 2025/26 |
| `sl-cse-stocks-ramis` | Capital TRUST Securities | `capital_trust` | Trade Confirmation; Portfolio Valuation as at 31 March | Y/A 2025/26 |

Run `extract_certificates.py --list-providers` or `extract_cse.py
--list-providers` to see what an installed copy supports.

## Contributing

**Contributions are very welcome**, especially parsers for more banks,
finance companies, stockbrokers and dividend registrars, so the skills work
automatically for more people. Each parser is one small file in a
`wht_parsers/` or `cse_parsers/` folder, discovered automatically, with a
`_template.py` to copy.

**Never add real documents or real data.** No PDFs, screenshots or spreadsheets,
and no names, NIC numbers, addresses, account or certificate numbers, or real
amounts, not even "redacted" copies of real files. Write a synthetic text sample
that keeps the layout and invent every value. CI runs
[`tools/check_fixtures.py`](tools/check_fixtures.py), which rejects fixtures
that look real, but it is a safety net, not a guarantee.

Step-by-step guide: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Install

### Claude Code: plugin marketplace (recommended)

This repository is a Claude Code plugin marketplace (`lk-ramis`) containing
one plugin (`lk-ramis-tax-skills`) with all five skills. In Claude Code:

```
/plugin marketplace add LahiruSenevirathne/lk-ramis-tax-skills
/plugin install lk-ramis-tax-skills@lk-ramis
```

On Claude Code 2.1.275 or later you can do both in one step:

```
/plugin install lk-ramis-tax-skills --marketplace LahiruSenevirathne/lk-ramis-tax-skills
```

From a shell, use `claude plugin marketplace add …` and `claude plugin install …`.
Then ask Claude *"I want to do my tax return"*, or run a skill directly, e.g.
`/lk-ramis-tax-skills:sl-ramis-getting-started`. Update later with
`/plugin marketplace update lk-ramis`.

### Claude Code: copy the skills

```bash
git clone https://github.com/LahiruSenevirathne/lk-ramis-tax-skills.git
mkdir -p ~/.claude/skills
cp -r lk-ramis-tax-skills/skills/* ~/.claude/skills/
```

### Claude apps (claude.ai / desktop)

Zip a skill folder (e.g. `skills/sl-cse-stocks-ramis`) and upload it under
**Settings → Capabilities → Skills**.

### Requirements

- `qpdf` and `pdftotext` (poppler-utils): `brew install qpdf poppler` or `apt install qpdf poppler-utils`
  (both extractors fall back to the `pypdf` package when `pdftotext` isn't installed)
- Python 3.9+ with `openpyxl` (`pip install -r requirements.txt`)
- Optional, depending on where your documents are: a Gmail, Google Drive or
  Outlook connector, or an Apple Mail MCP server. Otherwise just put the files
  in a folder.
- For RAMIS entry: Claude in Chrome (or another browser tool), with you signed in to RAMIS yourself

## Use

Ask Claude something like:

> I want to do my 2025/26 tax return. (starts `sl-ramis-getting-started`)

> Get my WHT certificates for 2025/26 from Gmail and make the RAMIS interest table.

> Put my CSE shares, dividends and the shares I sold in 2025/26 into RAMIS.

You can also run the scripts directly:

```bash
# interest certificates
S=skills/sl-wht-ramis/scripts
PDF_PASSWORD=DDMMYYYY $S/unlock_pdfs.sh work/unlocked ~/Downloads/*.pdf
python3 $S/extract_certificates.py work/unlocked > work/rows.json
python3 $S/build_table.py work/rows.json --fy 2025 --date-mode ird \
  --out WHT_FY2025-26.xlsx --csv WHT_FY2025-26.csv

# CSE shares
S=skills/sl-cse-stocks-ramis/scripts
python3 $S/extract_cse.py work/unlocked > work/extracted.json
python3 $S/build_stocks_table.py work/extracted.json --fy 2025 \
  --out Shares_FY2025-26.xlsx --ramis-json work/ramis_rows.json
```

## Privacy

Full policy: [PRIVACY.md](PRIVACY.md). The plugin collects nothing.

- Everything runs on your machine or in your Claude session. Nothing is sent anywhere else.
- PDF passwords are passed to `qpdf` through a temporary file, not on the command line.
- `.gitignore` excludes PDFs, spreadsheets and `work/` so you don't commit your own documents by accident.
- Test fixtures are synthetic. Never add real certificates, statements or holdings to this repository. `tools/check_fixtures.py` (run in CI) rejects fixtures that look real.

## Development

```bash
pip install -r requirements.txt pytest
python -m pytest -q
python tools/check_fixtures.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) to add a bank, broker or registrar.

## License

MIT, see [LICENSE](LICENSE).
