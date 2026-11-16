# Canonical JSON for bank letters, loans and property

One file per document (e.g. `work/<bank>.json`). Claude usually writes it after
reading a (scanned) balance confirmation letter. `build_bank_table.py` merges
the files, checks them and builds the RAMIS rows. Dates are `YYYY-MM-DD`,
amounts are numbers in the account's currency, and `null` means not shown.
Never guess.

```json
{
  "source": "Example Bank PLC",
  "document": "Confirmation of Balances",
  "letter_date": "2026-11-12",
  "file": "originals/example/letter.pdf",
  "as_at": "2026-03-31",
  "deposits":   [ … ],
  "loans":      [ … ],
  "properties": [ … ]
}
```

## deposits: one per account or deposit

| Field | Required | Meaning |
|---|---|---|
| `institution` | yes | As it should appear in RAMIS, e.g. "Example Bank PLC" |
| `account` | yes | Account / deposit number |
| `kind` | yes | `savings`, `current`, `fixed` / `term`, `foreign_currency` |
| `currency` | yes | `LKR`, `USD`, … |
| `balance` | yes | Balance as at 31 March, in `currency` |
| `interest` | yes | Interest for the Y/A (gross), in `currency` |
| `ait` | no | AIT/WHT deducted in the Y/A, in `currency` |
| `amount_invested` | for term deposits | Principal |
| `fx_rate`, `fx_source` | for non-LKR | LKR per unit and where it came from, e.g. `311.7664`, `"CBSL TT buying"` |
| `product` | no | Product name shown on the letter |
| `type` | no | `A` (default; account held in Sri Lanka) or `B` (held abroad) |
| `include` | no | `false` to leave the account out |

## loans: one per loan, lease, overdraft or card balance

| Field | Required | Meaning |
|---|---|---|
| `institution`, `loan_no` | yes | |
| `loan_type` | no | housing loan, personal loan, vehicle lease, credit card… |
| `date_granted` | yes | Date of commencement |
| `amount_granted` | yes | Original amount of the facility |
| `amount_released` | no | If only part was disbursed by 31 March (defaults to `amount_granted`) |
| `outstanding` | yes | Capital outstanding as at 31 March |
| `principal_repaid` | yes | Principal recovered in the Y/A |
| `interest_paid` | no | Interest recovered in the Y/A |
| `repaid_basis` | no | `principal` (default) or `principal_plus_interest` |
| `security` | no | e.g. "Mortgage of <property>", "Vehicle", "None" |
| `description` | no | Overrides the generated description |

Check: `amount_released − principal_repaid = outstanding`. A mismatch is
reported for the user to explain (partial release, lump-sum prepayment,
capitalised interest, or a typo on the letter).

## properties: immovable property (land, house, apartment)

| Field | Required | Meaning |
|---|---|---|
| `situation` | yes | Address / description as it should appear in RAMIS |
| `date` | yes | Date of acquisition (agreed with the user, e.g. deed, or a registered agreement with handover) |
| `cost` | yes | Cost of acquisition |
| `market_value` | no | Market value at 31 March |
| `acquired_in_year` | no | `true` also creates a Part 02 A row |
| `short_description`, `how` | no | For Part 02 A (`how`: Purchase / Gift / Exchange) |

Synthetic examples: `tests/fixtures/bank/canonical/`.
