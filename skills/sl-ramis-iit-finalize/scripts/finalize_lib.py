"""Shared catalogue for sl-ramis-iit-finalize: what each RAMIS grid is, which
column names the counterparty, and which supporting documents it needs.

Grids are matched by id prefix, so the catalogue survives small id changes.
Columns are found by title keywords, not field ids.
"""
import re

# id prefix -> section definition
SECTIONS = [
    {"prefix": "grid1A_", "key": "employment", "folder": "0-employment",
     "name": "Main Return – Employment income (Schedule 1)",
     "entity_col": ["employer/company name"], "amount_cols": ["remuneration"],
     "doc": "APIT certificate (T-10) / employment income statement from {entity}",
     "keywords": ["t10", "t-10", "apit", "salary", "employment"]},
    {"prefix": "grid7A_", "key": "interest_wht", "folder": "1-interest-wht",
     "name": "Schedule 7A – AIT/WHT deducted by the Withholding Agent (interest income)",
     "entity_col": ["name of the withholding agent"], "amount_cols": ["amount received", "deducted"],
     "doc": "AIT/WHT certificate(s) from {entity}",
     "keywords": ["wht", "ait", "withholding", "certificate"]},
    {"prefix": "gridStatement1A", "key": "property", "folder": "3-bank-liabilities",
     "name": "Statement of A/L – Part 01 A Immovable properties",
     "entity_col": None, "amount_cols": ["cost", "market value"],
     "doc": "Title deed / sale or tripartite agreement (and valuation, if market value is declared) for: {entity}",
     "keywords": ["deed", "agreement", "tripartite", "property_valuation", "valuation_report"]},
    {"prefix": "gridStatement1B1", "key": "vehicles", "folder": "3-bank-liabilities",
     "name": "Statement of A/L – Part 01 B i Motor vehicles",
     "entity_col": ["description"], "amount_cols": ["cost"],
     "doc": "Certificate of registration / purchase invoice for {entity}",
     "keywords": ["vehicle", "registration", "invoice"]},
    {"prefix": "gridStatement1B2", "key": "bank", "folder": "3-bank-liabilities",
     "name": "Statement of A/L – Part 01 B ii Bank balances including term deposits",
     "entity_col": ["name of bank"], "amount_cols": ["amount invested", "interest", "balance"],
     "doc": "Balance confirmation letter as at 31 March from {entity}",
     "keywords": ["balance"]},
    {"prefix": "gridStatement1B3", "key": "shares", "folder": "2-shares-cse",
     "name": "Statement of A/L – Part 01 B iii Shares/stocks/securities",
     "entity_col": None, "amount_cols": ["cost", "dividend"],
     "doc": "Broker portfolio valuation / statement of holdings as at 31 March; trade confirmations; dividend warrants",
     "keywords": ["valuation", "portfolio", "holding", "trade_confirmation", "warrant"]},
    {"prefix": "gridStatement1C", "key": "business", "folder": "3-bank-liabilities",
     "name": "Statement of A/L – Part 01 C Properties held as part of a business",
     "entity_col": ["name of business"], "amount_cols": ["balance"],
     "doc": "Balance sheet of {entity}", "keywords": ["balance sheet", "accounts"]},
    {"prefix": "gridStatement1D", "key": "liabilities", "folder": "3-bank-liabilities",
     "name": "Statement of A/L – Part 01 D Liabilities as at end of the Y/A",
     "entity_col": ["description of liability"], "amount_cols": ["original amount", "as at", "repaid"],
     "doc": "Loan balance confirmation / statement as at 31 March for: {entity}",
     "keywords": ["loan", "balance"]},
    {"prefix": "gridStatement2A", "key": "acquired", "folder": "3-bank-liabilities",
     "name": "Statement of A/L – Part 02 A Assets acquired or gifts received during the year",
     "entity_col": ["description of asset"], "amount_cols": ["cost"],
     "doc": "Purchase agreement / deed / invoice / gift deed for: {entity}",
     "keywords": ["deed", "agreement", "tripartite", "invoice", "gift"]},
    {"prefix": "gridStatement2B", "key": "disposals", "folder": "2-shares-cse",
     "name": "Statement of A/L – Part 02 B Disposal of assets including shares",
     "entity_col": ["description"], "amount_cols": ["sales proceed", "cost"],
     "doc": "Contract notes / trade confirmations (or sale deed) for the disposals",
     "keywords": ["trade_confirmation", "contract", "sale"]},
    {"prefix": "downloadGrid", "key": "uploaded", "folder": None,
     "name": "Document Details – documents uploaded to RAMIS",
     "entity_col": ["document name"], "amount_cols": [], "doc": None, "keywords": []},
]

# Main-return cages whose meaning is confirmed by arithmetic in check_main().
CAGES = {
    "Cage50": "Total income (assessable)",
    "Cage80": "Deductions / reliefs (incl. personal relief)",
    "Cage120": "Taxable income",
    "Cage170": "Income tax on taxable income",
    "Cage180": "Tax credits (APIT + AIT/WHT)",
    "Cage210": "Balance tax payable (+) / refundable",
    "Cage903A": "APIT deducted by primary employer (Schedule 9)",
    "APITTotal": "Total APIT (Schedule 9)",
}

# Folder / file-name aliases for counterparties whose short name differs.
ALIASES = {
    "NATIONS TRUST": ["ntb", "nations"],
    "COMMERCIAL BANK": ["combank", "comb"],
    "HATTON NATIONAL": ["hnb"],
    "BANK OF CEYLON": ["boc"],
    "PEOPLE'S BANK": ["peoples", "pb"],
    "NATIONAL DEVELOPMENT": ["ndb"],
    "CAPITAL TRUST": ["capital_trust", "capitaltrust"],
    "COLOMBO STOCK": ["cds"],
}

STOP = {"PLC", "LTD", "LIMITED", "PVT", "(PVT)", "BANK", "THE", "AND", "OF", "COMPANY", "FINANCE", "&"}


def norm(s):
    return re.sub(r"[^A-Z0-9 ]+", " ", str(s or "").upper()).strip()


def section_of(grid_id):
    for s in SECTIONS:
        if grid_id.startswith(s["prefix"]):
            return s
    return None


def col_index(grid, keywords):
    if not keywords:
        return None
    titles = [c[1].lower() for c in grid["columns"]]
    for kw in keywords:
        for i, t in enumerate(titles):
            if kw in t:
                return i
    return None


def numeric_cols(grid):
    return [i for i, c in enumerate(grid["columns"]) if c[2] == "number"]


def entity_tokens(name):
    """Tokens that identify a counterparty in folder / file names."""
    n = norm(name)
    words = [t.lower() for t in n.split() if t not in STOP and len(t) > 2 and not t.isdigit()]
    # the first significant word only (e.g. "nations", not "trust", which would also
    # match "capital_trust"), plus known aliases
    toks = words[:1]
    for key, al in ALIASES.items():
        if key in n:
            toks += al
    return toks


def bank_key(name):
    """Institution name without the parenthesised note, for grouping."""
    return norm(re.sub(r"\(.*", "", str(name or ""))).replace(" PLC", "").strip()
