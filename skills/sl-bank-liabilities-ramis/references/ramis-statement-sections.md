# RAMIS Statement of Assets & Liabilities: the grids this skill fills

Observed live on the Y/A 2025/26 return (`IITSimplifiedReturn`, tab
**Statement of assets & liabilities**). The editor window, widget API,
upper-casing and read-back behave as described in
`sl-cse-stocks-ramis/references/ramis-assets-shares.md`. `scripts/ramis_statement_fill.js`
has all of this in its `SECTIONS` table.

| Section key | Grid | Columns → input ids `StatementPart<ID>Model_…` |
|---|---|---|
| `property` | `#gridStatement1A`, Part 01 A Immovable properties | Situation of property `Sta_Cage1001` (text) · Date of acquisition `Sta_Cage1002` (date) · Cost `Sta_Cage1003` · Market value `Sta_Cage1004` |
| `bank` | `#gridStatement1B2`, Part 01 B ii Bank balances including term deposits | Name of bank/financial institution `Sta_Cage1009` · Account No. `Sta_Cage1010` · Amount invested `Sta_Cage1011` · Interest `Sta_Cage1012` · Balance `Sta_Cage1013` |
| `liabilities` | `#gridStatement1D`, Part 01 D Liabilities | Description `Sta_Cage1025` · Security `Sta_Cage1026` · Date of commencement `Sta_Cage1027` (date) · Original amount `Sta_Cage1028` · Amount as at 31.03 `Sta_Cage1029` · Repaid during the Y/A `Sta_Cage1030` |
| `acquired` | `#gridStatement2A`, Part 02 A Other assets acquired or gifts received | Description `Sta_Cage1031` · Gift/exchange/purchase `Sta_Cage1032` (text) · Date `Sta_Cage1033` (date) · Cost / market value `Sta_Cage1034` |

Every grid also has Type (`Sta_AssetType`, A/B dropdown). Amounts are Kendo
numeric boxes (`n2`). Text fields have no length limit. Buttons:
`#btnStatement<ID>AddRow` and `#btnStatement<ID>Add` only.

The header "Assets as at 31.03.YYYY" has **A. Local** / **B. Foreign**
checkboxes. Don't change them. Remind the user to check them before saving.
