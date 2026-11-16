# Privacy policy

*lk-ramis-tax-skills (LK Tax Return Helper, unofficial, for RAMIS). Last updated: 16 November 2026.*

This plugin is a set of instructions (skills) and small local helper scripts
that help you fill in your own Sri Lankan income tax return. It is an
independent, open-source project, not affiliated with the Inland Revenue
Department of Sri Lanka or any bank, broker or exchange.

## What the plugin collects

**Nothing.** The plugin has no server, no account, no analytics and no
telemetry. Its author receives no data from you.

## What data it handles, and where

To do its job, the plugin works with personal financial data that **you** point
it to: tax certificates, bank and broker statements, balance confirmation
letters, and the contents of your tax return.

- **Your documents** are read where you keep them (a folder, or a mail or Drive
  service you have connected to Claude yourself). The helper scripts run on
  your own machine and write their results (tables, JSON, a checklist, copies
  of documents) only to a folder you choose, by default
  `~/Documents/Tax-Sri-Lanka/`.
- **Passwords** for protected PDFs are used once to unlock a local copy and are
  never written to disk, logged or sent anywhere.
- **RAMIS:** with your approval, the browser helpers fill rows into the RAMIS
  page you have opened and signed in to yourself. Data goes only to the IRD's
  own website, in your own browser session, exactly as if you typed it.
- **Claude:** like any skill, the documents and figures you work with are
  processed by Claude in your conversation under Anthropic's terms and privacy
  policy, which apply to your use of Claude.
- **Connected services** (Gmail, Google Drive, Apple Mail, etc.) are used only
  if you have connected them, and are governed by those providers' terms.

## Retention

The plugin keeps nothing itself. Files it creates stay in your chosen folder
until you delete them.

## Children

The plugin is meant for adult taxpayers and is not intended for people under 18.

## Contact

Questions or concerns: open an issue at
https://github.com/LahiruSenevirathne/lk-ramis-tax-skills/issues
