# Balance confirmation letters seen so far

There's no standard format. Each bank's branch issues its own letter on request,
often signed and **scanned** (no text layer), sometimes weeks after the request.
Ask for: *"a balance confirmation as at 31 March <year> for all my accounts,
deposits and loans, with interest and AIT for the year, for the IRD"*.

**Tested with two banks so far** (Y/A 2025/26), both scanned, both read by
Claude into canonical JSON:

## DFCC Bank PLC: "Confirmation of Balances"

- Emailed by the branch as a scanned PDF (file name is a timestamp). Not
  password-protected.
- **Account details** table: type of account, account number, currency,
  balance as at 31-Mar, interest earned/charged (01-Apr to 31-Mar), Advance
  Income Tax (same period), joint party.
- **Loan details** table: loan number, date granted, currency, amount
  granted, capital outstanding as at 31-Mar, interest recovered, principal
  recovered (for the year).
- Note on the letter: amounts recovered for premature upliftment aren't
  shown. "Amount granted" can be more than what was released, e.g. a housing
  loan released in stages, so check the loan reconciliation.

## Sampath Bank PLC: "Confirmation of Account Balances"

- Scanned PDF. Not password-protected.
- One block per account: product name and currency, account number, open date
  (and closed date if closed), then **opening clear balance** (1 April),
  **interest for the period**, **WHT deducted for the period**, **clear balance as
  at 31-03**.
- Foreign-currency accounts (e.g. PFCA in USD) are shown in that currency, with
  WHT often 0. Convert to LKR for RAMIS.
- Interest and WHT per account match Sampath's yearly AIT certificates
  (`sl-wht-ramis`), so use `--wht` to cross-check.

## Adding a bank

Most letters are scans, so a text parser rarely helps. A contribution is
usually a **short description** of the letter's layout, added to this file,
plus a **synthetic** canonical JSON example in `tests/fixtures/bank/canonical/`.
If a bank sends text PDFs with a stable layout, a parser can be added later
(see `CONTRIBUTING.md`). Never commit real letters or data.
