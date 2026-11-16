# Canonical data model (broker-agnostic)

Everything downstream (`build_stocks_table.py`, `ramis_stocks_fill.js`) works
on four lists. Parsers produce them from documents they recognise. For anything
else (another broker, a scanned contract note, a spreadsheet the user keeps),
**Claude reads the document and writes the same rows into a `.json` file**,
then passes that file to `extract_cse.py` with the PDFs. It is validated and
merged.

```json
{
  "source": "acuity",               // free text: broker or document family
  "note": "from 12 contract notes, read by hand",
  "trades":    [ … ],
  "holdings":  [ … ],
  "dividends": [ … ],
  "movements": [ … ]
}
```

Dates are `YYYY-MM-DD`, amounts are numbers in rupees, and codes are CSE codes
like `ABC.N0000` or `ABC.X0000`.

## trades: one per security per contract day (from contract notes or trade confirmations)

| Field | Required | Meaning |
|---|---|---|
| `date` | yes | **Trade** date (not settlement) |
| `side` | yes | `buy` or `sell` |
| `code` | yes | CSE security code |
| `name` | yes | Company name |
| `qty` | yes | Shares (integer) |
| `net` | yes | Net amount: buy = gross + all fees; sell = gross − all fees |
| `gross`, `avg_price`, `isin`, `contracts` | no | Kept for reference |

If a broker shows several contracts for one security on one day, either sum
them into one row or give one row per contract. Both work, because FIFO
handles either.

## holdings: the broker's position report as at year end (31 March)

| Field | Required | Meaning |
|---|---|---|
| `as_at` | yes | `YYYY-03-31` for the year being filed |
| `code`, `name` | yes | |
| `quantity` | yes | Total shares held (cleared + unsettled as the report shows) |
| `vwa_price` | yes | Price used for market value (VWA or closing) |
| `market_value` | yes | quantity × price |

No position report? The CDS eStatement for March, or the broker's online
portfolio screen, gives quantities. Ask the user for a 31 March price source
before inventing one.

## dividends: one per payment (from CDS e-warrants or registrar warrants)

| Field | Required | Meaning |
|---|---|---|
| `date` | yes | Payment/warrant date. It decides which year the dividend belongs to |
| `company` | yes | |
| `code_root` | yes | CSE code root (`SUN` for `SUN.N0000`), used to match the security |
| `gross`, `ait`, `net` | yes | gross − ait must equal net |
| `warrant_no`, `shares`, `title` | no | Reference |

## movements: CDS changes that aren't trades

| Field | Required | Meaning |
|---|---|---|
| `date` | yes | |
| `code` | yes | |
| `kind` | yes | `deposit` or `withdrawal` |
| `qty` | yes | |
| `ref`, `balance_after` | no | |

How `build_stocks_table.py` reads them (each one is shown to the user for
confirmation):

- a deposit with no withdrawal on the same day is **scrip/bonus at nil cost**;
- a withdrawal plus a deposit of a different quantity on the same day is a
  **subdivision/consolidation**: quantity is rescaled, cost kept;
- a withdrawal alone is flagged (transfer out?).

A rights issue is a **trade** (`buy` at the subscription price plus fees), not
a movement.
