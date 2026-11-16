# Supporting documents each section of the return needs

Used by `check_documents.py` (the catalogue is in `scripts/finalize_lib.py`).
These are the documents a taxpayer would normally keep, or upload under
**Document Details**, to support each entry. Use the IRD's terms (see
`sl-ramis-getting-started/references/ramis-terminology.md`).

| Section | One requirement per… | Document | Looked for in |
|---|---|---|---|
| Main Return: Employment income (Schedule 1) | employer | APIT certificate (T-10) / employment income statement | `0-employment/`, or file names with `t10`, `apit`, `salary` |
| Schedule 7A: AIT/WHT deducted by the Withholding Agent | withholding agent | AIT/WHT certificates (monthly, per-credit or consolidated annual) | `1-interest-wht/originals/<bank>/` |
| A/L Part 01 A: Immovable properties | property | Title deed, sale or tripartite agreement, valuation report (if market value is declared) | file names with `deed`, `agreement`, `tripartite` |
| A/L Part 01 B i: Motor vehicles | vehicle | Certificate of registration / invoice | file names with `vehicle`, `registration`, `invoice` |
| A/L Part 01 B ii: Bank balances | institution | Balance confirmation letter as at 31 March | `3-bank-liabilities/originals/<bank>/` |
| A/L Part 01 B iii: Shares | (once) | Broker portfolio valuation as at 31 March; trade confirmations; dividend warrants | file names with `valuation`/`portfolio`/`holding`, `trade_confirmation`, `dividend`/`warrant` |
| A/L Part 01 D: Liabilities | liability | Loan balance confirmation / statement as at 31 March | the lender's folder in `3-bank-liabilities/originals/` |
| A/L Part 02 A: Assets acquired | asset | Purchase agreement / deed / invoice / gift deed | file names with `deed`, `agreement`, `invoice`, `gift` |
| A/L Part 02 B: Disposals | (once) | Contract notes / trade confirmations, or sale deed | file names with `trade_confirmation`, `contract`, `sale` |

Also checked:

- **Every institution in Schedule 7A** should normally also appear in **bank
  balances** (and have a balance confirmation), unless the account was closed
  before 31 March. The summary flags it, and the checklist adds the missing letter.
- A requirement is **FOUND** when a file in the year folder sits in the
  counterparty's folder under the right section, or its name carries the
  document keyword. It's **ELSEWHERE** when it's found only in a `--search`
  folder, and **MISSING** otherwise.

Counterparty matching uses the name's significant words plus `ALIASES` in
`finalize_lib.py` (e.g. Nations Trust Bank ↔ `ntb`). Add an alias rather than
renaming the user's folders.
