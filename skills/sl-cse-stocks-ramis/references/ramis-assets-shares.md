# RAMIS IIT return: shares and share disposals

Captured from the live form for year of assessment 2025/26 at
`https://eservices.ird.gov.lk/Assessment/IIT2/IITSimplifiedReturn`, on the tab
**Statement of assets & liabilities**. Both sections were filled and read back
successfully with `scripts/ramis_stocks_fill.js`. IDs may change in later
years: if a selector is missing, inspect the page instead of guessing.

## How every Statement section works

- Each section is a Kendo grid (`#gridStatement<ID>`, `editable: false`) with
  **Add Row** / **Remove** buttons under it.
- **Add Row** opens one shared Kendo window
  (`.k-window-content#statementWindow`, titled with the section heading). The
  section's input fields are moved into that window, and the section's own
  `#Statement<ID>DIV` stays `display:none`. To check that the editor is open,
  test whether the first input field is visible, not the DIV.
- The window has **Add** (commits the row), **Update** and **Reset**. Only
  **Add Row** and **Add** are ever pressed.
- Set Kendo numeric and date boxes through the widget API
  (`$(sel).data('kendoNumericTextBox').value(n)`, then `.trigger('change')`;
  for dates use `kendoDatePicker.value(new Date(y, m-1, d))`). Plain text
  inputs: `.val(v).trigger('change')`.
- Read rows back from `grid.dataSource.data()` (skip `IsDeleted`). Dates come
  back as `Date` objects. Some text is **upper-cased** by RAMIS (the disposal
  Description), so compare text case-insensitively.
- Validation errors appear in `#Statement<ID>Error`.
- Nothing is saved until the user presses **Save draft** (bottom of the tab,
  next to Cancel / Next / Back). Never press those.

All grids on the tab, for orientation:

| Grid | Section | Fields |
|---|---|---|
| `1A` | Part 1 A. Immovable properties | `Sta_Cage1001..1004` |
| `1B1` | i. Motor vehicles | `1005..1008` |
| `1B2` | ii. Bank balances incl. term deposits | `1009..1013` |
| **`1B3`** | **iii. Shares/stocks/securities as at 31.03.YYYY** | **`1014..1018`** |
| `1C` | C. (other movable assets) | `1022..1024` |
| `1D` | D. All liabilities | `1025..1030` |
| `2A` | Part 2 A. Other assets acquired or gifts received during the year | `1031..1034` |
| **`2B`** | **Part 2 B. Disposal of assets including shares (sale/transfer/gift) during the year** | **`1035..1039`** |

Single-value boxes iv to vi (cash in hand, loans given, gold/gems) are cages
1019 to 1021. They are not grids.

## Shares: `#gridStatement1B3`

| Column | Input id `StatementPart1B3Model_…` | Widget |
|---|---|---|
| Type (A local / B foreign) | `Sta_AssetType` | kendoDropDownList `A`/`B` |
| Name of company/institution | `Sta_Cage1014` | text |
| No. of shares/stocks etc. | `Sta_Cage1015` | text (string in the model) |
| Date of acquisition | `Sta_Cage1016` | kendoDatePicker `yyyy-MM-dd` |
| Cost of acquisition/market value if not acquired (Rs.) | `Sta_Cage1017` | kendoNumericTextBox `n2`, maxlength 16 |
| Net dividend income (Rs.) | `Sta_Cage1018` | kendoNumericTextBox `n2`, maxlength 16 |

Buttons: `#btnStatement1B3AddRow`, `#btnStatement1B3Add`. Never press
`#btnStatement1B3Remove`, `#btnStatement1B3Update`, or `#btnStatement1B3Reset`.

The model also carries `Sta_Cage964..968`, which are probably the foreign
counterparts. They are unused for CSE shares.

## Disposals: `#gridStatement2B`

| Column | Input id `StatementPart2BModel_…` | Widget |
|---|---|---|
| Type | `Sta_AssetType` | kendoDropDownList `A`/`B` |
| Description | `Sta_Cage1035` | text (stored upper-case) |
| Date of disposal | `Sta_Cage1036` | kendoDatePicker `yyyy-MM-dd` |
| Sales proceed (Rs.) | `Sta_Cage1037` | kendoNumericTextBox `n2`, maxlength 16 |
| Date acquired | `Sta_Cage1038` | kendoDatePicker `yyyy-MM-dd` |
| Cost (Rs.) | `Sta_Cage1039` | kendoNumericTextBox `n2`, maxlength 16 |

Buttons: `#btnStatement2BAddRow`, `#btnStatement2BAdd`. Never press
`#btnStatement2BRemove`, `#btnStatement2BUpdate`, or `#btnStatement2BReset`.

## What goes in the columns (conventions this skill uses, confirmed with a user)

- **Shares value column**: cost of acquisition for shares bought in the year
  (the trade confirmations' net amounts, including brokerage and fees). For
  shares held from before the year, the user chose the 31 March market value
  (broker VWA). A holding that straddles the year is split into two rows.
- **Date of acquisition**: first purchase date of the shares in that row.
- **Net dividend income**: net (after AIT) dividends paid in the year, from the
  CDS e-warrants. A company sold before year end that paid a dividend gets a
  row with 0 shares and only the dividend filled in.
- **Disposals**: one row per sale. Proceeds and cost are net of fees, with
  first-in-first-out cost. Scrip or bonus shares are at nil cost. A share
  subdivision changes the quantity, not the cost. Dates are trade dates.
- Description format: `Shares - <COMPANY> (<CODE>) - <qty> shares`.

These are data-entry conventions, not tax advice. Always confirm them with
the user at Stage 0.
