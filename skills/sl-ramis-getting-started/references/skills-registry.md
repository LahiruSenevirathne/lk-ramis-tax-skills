# Filing skills registry

The filing skills `sl-ramis-getting-started` can hand over to, in the
default order to run them. Only offer skills that are installed. Mention
"planned" ones so users know they're coming.

| Order | Skill | Status | RAMIS return: where it goes | Documents it needs |
|---|---|---|---|---|
| 1 | `sl-wht-ramis` | available | **Schedule 7A – AIT/WHT deducted by the Withholding Agent** (cages 701–706; shown as Schedule 7 "Interest Income – A" on the Simplified Return), one row per certificate entry | **AIT/WHT certificates** from every bank and financial institution that paid interest in the Y/A (savings, current, fixed/term deposits), either individual (monthly/per-credit) or **consolidated annual** |
| 2 | `sl-cse-stocks-ramis` | available | **Statement of Assets and Liabilities**: Part 01 B iii **Shares/stocks/securities** as at 31 March (with net dividend income) and Part 02 B **Disposal of assets including shares (sale/transfer/gift) during the year** | **Dividend warrants / certificates of tax deduction** (CDS e-warrants or registrar) for dividends paid in the Y/A; **trade confirmations / contract notes** for the Y/A (and earlier ones for shares sold or held); **portfolio valuation / statement of holdings as at 31 March** from each broker; **CDS monthly statements** (scrip, bonus, subdivisions) |
| 3 | `sl-bank-liabilities-ramis` | available | **Statement of Assets and Liabilities**: Part 01 B ii **Bank balances including term deposits**, Part 01 D **Liabilities as at end of the Y/A**, Part 01 A **Immovable Properties** and Part 02 A **Assets acquired during the year** | **Balance confirmation letters as at 31 March** from every bank and financial institution (deposits, and loans, overdrafts, leases, cards); FD certificates/renewal advices; loan statements |

| 9 | `sl-ramis-iit-finalize` | available | **Whole return, read-only**: summary of every section with totals and cross-checks, supporting-documents checklist, `final/` folder | Nothing new: it checks the year working folder for the documents above (and any others the return needs, e.g. T-10, deeds) |

Why this order: interest first, so its figures can cross-check the "Interest"
column of bank balances later. Shares are independent. Balances and
liabilities come third. **Finalize always runs last**, and again whenever a late
document arrives.

## Adding a skill

A filing skill in this collection must:

1. Live in `skills/<name>/` with a `SKILL.md` whose front-matter `description`
   names the RAMIS section(s) it fills.
2. Start with a **Stage 0 (scope) gate** that accepts what the filing plan
   already settled (year, sources, working folder, RAMIS entry yes/no) and only
   asks what's specific to it.
3. Be **source-agnostic**: take documents from wherever the user keeps them
   (see `document-sources.md`). Name providers (banks, brokers) only as worked
   examples, and fall back to Claude reading unknown layouts into a documented
   JSON shape.
4. Not assume documents are encrypted or unencrypted: check each one, and ask
   for a password only when needed. Never store passwords.
5. Self-check every document against its own printed totals, and produce a
   reviewable table (.xlsx) before any RAMIS entry.
6. Enter into RAMIS only after an explicit "yes": one row first, then small
   batches, then a read-back against totals. Press only the section's own
   "Add" controls. The user presses Save draft.
7. Ship synthetic test fixtures only.

Then add a row to the table above (status `available`), plus the skill to the
repo `README.md`, `.claude-plugin/plugin.json` and CI.
