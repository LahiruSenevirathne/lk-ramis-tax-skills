# RAMIS: Schedule 7, Interest Income – A

Observed on the 2025/26 individual income tax return
(`https://eservices.ird.gov.lk/Assessment/IIT2/IITSimplifiedReturn`).
The IRD can change the page at any time, so check the selectors before relying
on them.

## The table

"A - Advance income tax / withholding tax deducted by the withholding agent"
lists rows with Source/type, TIN, agent name, certificate no., amount received,
date of payment and AIT. A totals row under the table shows the Amount received total.

Below the table are two buttons: **Add** (`#btnS7A`, opens the pop-up) and
**Remove**. Never press Remove.

## The pop-up

| Cage | Field | Element | How to set it |
|---|---|---|---|
| 701 | Source/type | `#Schedule7_Schedule7AModel_Sch7_2021Cage701`, text | `I-INTEREST` |
| 702 | TIN of the withholding agent | `…Sch7_2021Cage702`, Kendo NumericTextBox | widget `.value(n)` + `trigger('change')` |
| 707 | Name of the withholding agent | `#Schedule7_Schedule7AModel_Sch7_2526Cage707`, text | capitals, e.g. `NATIONS TRUST BANK` |
| 703 | AIT/WHT certificate No. | `…Sch7_2021Cage703`, text | as printed |
| 704 | Amount received (Rs.) | `…Sch7_2021Cage704`, Kendo NumericTextBox | widget `.value(n)` |
| 705 | Date of payment | `…Sch7_2021Cage705`, Kendo DatePicker | widget `.value(new Date(y, m-1, d))` |
| 706 | AIT/WHT deducted (Rs.) | `…Sch7_2021Cage706`, Kendo NumericTextBox | widget `.value(n)` |

The pop-up buttons are **Add** (`#btnS7AAdd`), Update (`#btnS7AUpdate`) and
Reset (`#btnS7AReset`). Only Add is used.

Notes:

- The page also contains hidden twins of these fields without `2021` in the id
  (`…Sch7_Cage701` and so on). Use the visible `2021` / `2526` ones.
- Typing into the Kendo number boxes with simulated key presses doesn't keep
  the value. Set them through the widget API, as `ramis_fill.js` does.
- After pressing Add, the pop-up closes and the row appears at the end of the table.
- Rows added this way are only on the page until the user presses **Save draft**.
- Users in practice have entered the date the AIT was remitted to the IRD as
  "Date of payment". Ask the user which reading they want; don't decide for them.
