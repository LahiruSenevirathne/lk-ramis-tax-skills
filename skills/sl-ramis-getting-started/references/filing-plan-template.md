# Filing plan template

Write this as `filing-plan.md` in the user's private working folder (never
in a repository). No passwords. Account numbers only as the last 4 digits.

```markdown
# RAMIS filing plan: YoA 2025/26

- Year of assessment: 2025/26 (1 Apr 2025 – 31 Mar 2026)
- Enter rows into RAMIS: yes (browser: Claude in Chrome; user signs in and saves)
- Working folder: ~/Documents/Tax-Sri-Lanka/YA-2025-26/ (layout: references/working-folder.md)

## 1. Interest (sl-wht-ramis) → Schedule 7
- Documents: AIT/WHT certificates, banks: <bank A>, <bank B>
- Source: Gmail (connector) / folder <path> / …
- Known gaps: <bank B> yearly certificate not received yet
- Status: [ ] scope [ ] collected [ ] table approved [ ] entered [ ] user saved draft

## 2. CSE shares (sl-cse-stocks-ramis) → Statement: iii shares, Part 2 B disposals
- Broker: <broker> (parser: yes/no, otherwise hand-read into canonical JSON)
- Documents: trade confirmations (source …), 31 March valuation (source …),
  CDS e-warrants (source …), CDS eStatements (source …)
- Known gaps: valuation must be requested from the broker
- Status: [ ] scope [ ] collected [ ] tables approved [ ] entered [ ] user saved draft

## Order
1 → 2 (→ 3 when available)
```
