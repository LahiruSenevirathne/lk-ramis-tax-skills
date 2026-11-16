# CSE documents: what exists and what the extractor understands

**Tested so far:** CDS documents, and one broker (Capital TRUST Securities).

Two families:

- **CDS documents** are issued by the Central Depository System to every CSE
  investor, whatever their broker. The parsers for these are common.
- **Broker documents** (trade confirmations / contract notes, the year-end
  portfolio valuation) differ by broker. **Capital TRUST Securities** is the
  worked example with a parser. For any other broker, Claude reads the
  documents and writes canonical JSON (`data-model.md`), or a contributor adds
  a parser.

Whether a document is password-protected depends on who sent it. Check each
file (`qpdf --is-encrypted`, or try to open it) and ask the user for any
password. Never guess, store or commit passwords.

`extract_cse.py` works on text from `pdftotext -layout` (pypdf as a fallback),
with runs of spaces collapsed. Synthetic examples of every format are in
`tests/fixtures/cse/`.

---

## Common to everyone (CDS)

### CDS dividend e-warrant: parser `dividend_warrant`

- Sender `CDSe-warrants@cse.lk`. Subject: `<COMPANY> - CERTIFICATE OF TAX
  DEDUCTION …` / `… DIVIDEND WARRANT`.
- **Encrypted.** The email body gives the rule: the CDS account number,
  zero-padded to 9 digits (account `ABC-12345-LI-00` gives `000012345`).
- Fields: `DATE`, `WARRANT NO <ROOT>/<series>/<n>`, `NO. OF SHARES`, the
  company line `… PLC`, and the summary line `TOTAL (3+6)` or `TOTAL DIVIDEND
  (3+6)`, which gives gross, AIT and net.
- The warrant number's first part (`SUN`, `UML`, …) is the CSE code root. It
  links the warrant to a security.
- pypdf's layout mode returns no text for these. The extractor falls back to
  plain mode.
- Self-check: gross − AIT = net.
- Some companies pay through a **registrar** instead (e.g. `SSP
  <DoNotReply@sspsec.com>`). Those layouts aren't parsed yet: read them and
  write canonical `dividends` rows.

### CDS monthly eStatement: parser `cds_estatement`

- Sender `CDSestatements@cse.lk`. Subject:
  `CDS eStatements - STMT_T_nnnn - …`. Attachment `STMT_T_nnnn.PDF`.
- **Encrypted**, with a password the user sets or receives from the CDS. Ask
  for it; it may differ from the e-warrant password.
- Only issued for months with activity. Per security: a header
  `SHORT NAME-CODE <opening balance>`, then dated lines
  (`DD-MON-YYYY PURCHASE|SALE|Direct Deposit|DirWithdrw-ALL - ref qty [price] [balance]`).
  Dates are **settlement** dates.
- Only **non-trade movements** are kept. Trades come from the broker, which
  has the fees. See `data-model.md` for how deposits and withdrawals are read
  (scrip, bonus, split).
- Use these to explain any gap between bought − sold and what's held. They are
  also a fallback for quantities when the broker has no position report.

---

## Broker-specific: Capital TRUST Securities (worked example)

### Trade confirmation: parser `capital_trust` (trade_confirmation)

- Email subject: `CDS A/C <account>: Trade Confirmation for DD_MM_YYYY`.
  Sender: `statement@ctsinfo*.lk`. Attachment:
  `Trade_Confirmation_as_at_DD_MM_YYYY_<account>.pdf`.
- Not encrypted (when this was written).
- One block per security: `Purchase of NAME ( CODE / ISIN )` or `Sale of …`,
  then one line per contract, then a `Total` line.
- Two layouts. From early 2026 there's an extra **Clearing Fees** column, so
  the net amount is taken as the **second-to-last number** of the `Total` line.
- Self-check: net amounts add up to the printed `Purchase Total` and
  `Sales Total`.

### Portfolio valuation: parser `capital_trust` (portfolio_valuation)

- `Portfolio Valuation as at DD/MM/YYYY`. The client asks the broker for one
  "as at 31 March <year> for IRD".
- One row per equity: `CODE NAME unsettled-buy unsettled-sell cleared balance
  pledged VWA value`, then `Total`.
- Self-checks: qty × VWA = value, the rows add up to `Total`, and nothing is
  unsettled.

---

## Other brokers

Acuity, CT CLSA, John Keells Stock Brokers, Asha Securities, NDB Securities,
First Capital and the rest each send their own contract notes and statements,
and some send none by email (only an online portal).

1. Ask the user what their broker sends and where (email, portal download,
   paper).
2. Read a few documents, then write canonical JSON (`data-model.md`) and run
   it through `extract_cse.py` with the CDS PDFs. Show the user what you read.
3. To add a parser for everyone: copy `scripts/cse_parsers/_template.py` to
   `scripts/cse_parsers/<id>.py` (it is discovered automatically), add
   **synthetic** fixtures under `tests/fixtures/cse/<id>/` plus tests, and add
   a row to **Tested providers** in the README. See `CONTRIBUTING.md`. Never
   commit real PDFs, names, account numbers or amounts.
