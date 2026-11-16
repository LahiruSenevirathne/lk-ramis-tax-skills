# The tax working folder

One private folder per **year of assessment**, on the user's own machine, used by
every filing skill. Agree the location in Step 3 (default below) and create it
with the user's OK. Never use a code repository or a shared or synced folder
the user hasn't chosen.

Default root: `~/Documents/Tax-Sri-Lanka/` (the user can choose another, e.g.
an encrypted volume). Apple Mail MCP can save attachments under `~/Documents`,
`~/Downloads`, `~/Desktop` or iCloud Drive.

```
~/Documents/Tax-Sri-Lanka/
  YA-2025-26/                       one folder per year of assessment
    filing-plan.md                  written by sl-ramis-getting-started (no passwords)
    1-interest-wht/                 sl-wht-ramis       → Schedule 7A
      originals/<provider>/         as received (e.g. originals/ntb/, originals/sampath/)
      unlocked/                     decrypted copies made by unlock_pdfs.sh
      work/                         extracted JSON, canonical JSON written by Claude
      output/                       review tables (.xlsx/.csv) and RAMIS-ready rows
    2-shares-cse/                   sl-cse-stocks-ramis → A/L Part 01 B iii, Part 02 B
      originals/<provider>/         e.g. originals/cds/, originals/<broker>/
      unlocked/  work/  output/
    3-bank-liabilities/             sl-bank-liabilities-ramis → A/L Part 01 B ii, Part 01 D
      originals/<provider>/         e.g. originals/<bank>/ (balance confirmation letters)
      unlocked/  work/  output/
    ramis/                          snapshot.json, summary.md, checklist (sl-ramis-iit-finalize),
                                    screenshots, acknowledgement, copy of the submitted return
    final/                          built by sl-ramis-iit-finalize: copies of every supporting
                                    document by return section, README index, missing-documents.md
```

Rules:

- **`originals/` is never modified.** Unlock and extract into `unlocked/` and
  `work/`, and write tables into `output/`.
- Name provider folders by the parser id where one exists (`ntb`, `sampath`,
  `cds`, `capital_trust`), otherwise by a short lowercase name (`dfcc`).
- Keep file names as received. If one is meaningless (e.g. a scanner's
  timestamp), copy it with a descriptive name into `unlocked/` or `work/` and
  leave the original as it is.
- Permissions: `chmod 700` on the year folder (owner-only).
- Documents for sections no skill fills yet (e.g. employment T-10, vehicle papers)
  go in `0-employment/` or `9-other/` with an `originals/` sub-folder.
- A new filing skill gets the next number (`4-…`) and is added to this file
  and to `skills-registry.md`.
- Documents the user already has elsewhere (e.g. loose in Downloads) can be
  **copied** in with their OK. Don't move or delete their files.
