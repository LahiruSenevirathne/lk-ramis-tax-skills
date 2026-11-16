# Bank certificate layouts

**Tested with two banks only: Nations Trust Bank and Sampath Bank.** Each has
a parser module in `scripts/wht_parsers/`. Certificates from any other bank,
finance company or leasing company are reported as "unrecognised". Read them
and write **canonical rows** (below), or add a parser (`CONTRIBUTING.md` in
the repository).

Text below refers to `pdftotext -layout` output. All examples in
`tests/fixtures/wht/<parser id>/` are synthetic.

## Canonical rows (any bank)

For a certificate with no parser, write a `.json` file and pass it to
`extract_certificates.py` with the PDFs. It is validated and merged:

```json
{"source": "<institution>", "rows": [{
  "source_type": "Savings interest | Fixed deposit interest | null",
  "agent_tin": "<withholding agent TIN, as printed>",
  "agent_name": "<institution, as it should appear in RAMIS>",
  "certificate_no": "<AIT/WHT certificate no.>",
  "account": "<account no.>",
  "amount_received": 0.00, "ait": 0.00, "ait_rate_pct": 10, "net_paid": 0.00,
  "interest_date": "YYYY-MM-DD | null", "ird_paid_date": "YYYY-MM-DD | null",
  "ird_receipt_no": null, "period_from": "YYYY-MM-DD", "period_to": "YYYY-MM-DD"}]}
```

Required: `agent_name`, `agent_tin`, `certificate_no`, `amount_received`, `ait`.
Leave a value `null` when the certificate doesn't show it. Never guess. One
row per account per certificate (or per interest credit, if the certificate
lists credits). Don't mix individual certificates with a consolidated annual
one for the same interest.

## Nations Trust Bank (withholding agent TIN 134008059)

### Monthly "Certificate of Advance Income Tax (AIT) Deduction"

- Emailed monthly from `estatement@info.nationstrust.com`, subject
  `WHT Certificate of 01-MMM-YYYY to DD-MMM-YYYY`, about 3–4 weeks after the month ends.
- Password protected (date of birth, `DDMMYYYY`).
- `Certificate No:/ Serial No : WHT/<YYYY>/<MON>/<customer no>`: one number per
  month covering **all** the customer's accounts, so several table rows can
  share it.
- `Interest/Discount paid for Period :from: 01-Sep-2025 to : 30-Sep-2025`
- `Gross amount of Interest/Discount: LKR 12,345.67`: the total of the account rows.
- Account rows: type (`Savings` / `Fixed`), account number, title, gross, rate,
  AIT deducted, net paid. The title wraps onto following lines.
- One line with the IRD payment receipt number and `Date of Payment` (when the
  bank paid the AIT to the IRD).
- **No interest credit date**, so with `--date-mode interest` these rows get an empty date.

### Consolidated yearly certificate

- Sent on request (subject `Request ID … - Withholding tax certificate`, from
  `Do-not-reply@alert.nationstrust.com`).
- `Certificate No / Serial No :-BC/01-APR-25/31-MAR-26/<customer no>`: the `BC/`
  prefix is how the extractor recognises it.
- Per-account yearly totals only (account numbers wrap over two lines), plus
  the list of all monthly IRD receipts.
- No per-deduction certificate numbers, so it isn't used for the RAMIS rows by
  default. Use it to cross-check the monthly certificates.

## Sampath Bank PLC (withholding agent TIN 134001194)

- Requested per year; arrives from `accounts_statements@sampath.lk`, subject
  `WHT/AIT Certificate for the Financial Year`, **one email and one PDF per account**.
- Usually **not** password protected.
- `Account Number:` and `Interest Paid for the Period.: From DD-MM-YYYY to DD-MM-YYYY`.
- One row per interest credit: Transaction Date (interest credited), AIT Rate,
  Gross Interest, Amount of AIT, Net Interest, Cheque No, Paid Date (paid to the
  IRD), and a 21-digit Certificate No (one per row).
- A `Total` row, which the extractor checks against the sum of the rows.
- The certificate does **not** say whether the account is savings or a fixed
  deposit, so pass `--account-type <account>=savings|fd` to `build_table.py`.
- The depositor name and address may differ from other banks' records. The
  NIC is the reliable identifier.

## Adding a bank

Follow `CONTRIBUTING.md` in the repository. In short: copy
`scripts/wht_parsers/_template.py` to `scripts/wht_parsers/<id>.py`, add
**synthetic** fixtures under `tests/fixtures/wht/<id>/`, self-check every
printed total, add tests and a section above, and add a row to **Tested
providers** in the README. Never commit real certificates or data.
