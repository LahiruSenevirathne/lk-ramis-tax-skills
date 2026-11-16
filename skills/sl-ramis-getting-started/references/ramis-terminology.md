# RAMIS / IRD terminology for the sections these skills fill

Use these terms with users. They match the Inland Revenue Department's (IRD)
own wording, so users can find the same words in RAMIS and in IRD guides.
Sources are at the end. Labels can change between years, so if the live form
differs, use the form's wording and tell the user.

## The return

| Term | Meaning |
|---|---|
| **Return of Income – Individual Income Tax (IIT)** | The annual return an individual files. Electronic filing through RAMIS is mandatory from Y/A 2023/2024 (Inland Revenue Act No. 24 of 2017, s.113(1)(b)). |
| **Year of Assessment (Y/A)** | 1 April to 31 March, e.g. Y/A 2025/2026 = 1 April 2025 – 31 March 2026. Also called "fiscal year" or "tax year". |
| **Simplified Return (IIT Simplified / IITS)** vs **Standard Return** | Simplified is for employment income, residential solar, and interest income on which AIT was deducted by a licensed bank or financial institution, or a nil return. Everyone else files the Standard Return. Some fields are pre-filled by the IRD; the taxpayer must verify them. |
| **Cage** | A numbered box on the return, e.g. cages 701 to 706 in Schedule 7A. |
| **Withholding Agent** | Whoever deducts tax at source (the bank, the company paying a dividend). |
| **Save draft** | Saves the return in RAMIS without submitting. These skills never press it: the user does. |

## Income and tax credit schedules

| Section | What it is | Documents |
|---|---|---|
| **Schedule 3 – Investment Income** | Interest income, dividends, rent, gains on realisation of investment assets, other investment income | (figures come from the certificates below) |
| **Schedule 7 – Advance Income Tax (AIT) / Withholding Tax (WHT)**, sub-schedule **7A – AIT/WHT deducted by the Withholding Agent** (cages 701–706) | One row per payment on which AIT/WHT was deducted: source/type (e.g. `I-INTEREST`), agent's TIN and name, certificate no., amount, date, AIT/WHT deducted. The total claimed becomes a **tax credit**. On the Simplified Return the grid is shown as Schedule 7 "Interest Income – A". | **AIT/WHT certificates** (certificates of tax deduction) from **every bank and financial institution** that paid interest in the Y/A: **monthly/individual certificates or one consolidated annual certificate**, whichever the institution issues |
| Schedule 7B | WHT the agent *failed* to deduct | (not handled by these skills) |
| Schedule 6 – WHT on Final Withholding Payments | Payments where the WHT is the final tax | (not handled by these skills) |

Interest: from 1 April 2025 banks deduct **AIT at 10%** on interest. Residents
whose assessable income is at or below the threshold can give their bank a
**self-declaration** to have interest paid without AIT, so some accounts may
show no deduction. Dividends from resident companies are taxed at 15%, usually
deducted by the paying company and shown on the dividend warrant.

## Statement of Assets and Liabilities (A/L)

Filed with the return. It lists the value of **every asset and liability, in or
outside Sri Lanka, as at the last day of the Y/A (31 March)**. The IRD says to
"declare the acquisition cost or market value if it is not an acquisition",
and that these values are **not used to calculate tax**. Each grid has
**Add Row** / **Remove**. Type **A = local**, **B = foreign**.

| Part | Item | Skill |
|---|---|---|
| Part 01 A | Immovable Properties | – |
| Part 01 B i | Motor vehicles | – |
| Part 01 B ii | **Bank balances including term deposits** as at 31 March (bank/financial institution, account no., amount invested, interest, balance) | `sl-bank-liabilities-ramis` (planned) |
| Part 01 B iii | **Shares/stocks/securities** as at 31 March (company, no. of shares, date of acquisition, cost of acquisition / market value if not acquired, **net dividend income**) | `sl-cse-stocks-ramis` |
| Part 01 B iv–vi | Cash in hand; loans given & amounts receivable; gold, silver, gems, jewellery | – |
| Part 01 C | Properties held as part of a business | – |
| Part 01 D | **Liabilities as at end of the Y/A**: "all the liabilities, including loans to be paid to a person or institution" (description, security, date of commencement, original amount, amount as at 31 March, amount repaid during the Y/A) | `sl-bank-liabilities-ramis` (planned) |
| Part 02 A | Any other assets acquired or gifts received during the year | – |
| Part 02 B | **Disposal of assets including shares (sale/transfer/gift) during the year** (description, date of disposal, sales proceeds, date acquired, cost) | `sl-cse-stocks-ramis` |

## Documents, by their usual names

| Document | Issued by | Used for |
|---|---|---|
| **AIT/WHT certificate** (certificate of tax deduction on interest), monthly or **consolidated annual** | each bank / finance company | Schedule 7A |
| **Self-declaration** (AIT relief on interest) | the taxpayer, lodged with the bank | explains interest paid without AIT |
| **Trade confirmation / contract note** | stockbroker | shares bought and sold (cost, proceeds, dates) |
| **Portfolio valuation / statement of holdings as at 31 March** | stockbroker (often on request "for IRD") | A/L Part 01 B iii |
| **CDS monthly statement (eStatement)** | Central Depository System (CDS) of the CSE | quantities, scrip/bonus shares, subdivisions |
| **Dividend warrant / certificate of tax deduction (e-warrant)** | CDS (`CDSe-warrants@cse.lk`) or a registrar on the company's behalf | net dividend income, AIT on dividends |
| **Balance confirmation letter as at 31 March** | each bank / finance company | A/L Part 01 B ii (savings, current, FDs) and Part 01 D (loans, overdrafts, cards) |
| **Fixed/term deposit certificate or renewal advice** | bank / finance company | amount invested, interest for FDs |
| **Loan statement / outstanding balance confirmation** (amortisation schedule) | lender | Part 01 D: original amount, balance at 31 March, repaid in the Y/A |
| **Credit card statement** covering 31 March | card issuer | Part 01 D, if a balance is owed |

## Sources

- IRD, *How to file returns: Individual Income Tax (IIT), Y/A 2024/2025*
  (e-filing guide, mirrored at
  taxadvisor.lk/data/uploads/how_to_file_returns_individual_income_tax_iit_2024_2025.pdf):
  schedule names, Schedule 7A instructions, Statement of Assets and
  Liabilities instructions, Simplified Return eligibility.
- IRD circulars SEC/2025/E/02 and SEC/2025/E/03 (AIT on interest at 10% from
  1 April 2025; self-declaration), as summarised by KPMG Sri Lanka and Bloomberg
  Tax.
- Live RAMIS form, Y/A 2025/2026 (grid labels and cage/field IDs), recorded in
  each skill's `references/`.

Not tax advice. Rates and thresholds change, so check the IRD for the year
being filed.
