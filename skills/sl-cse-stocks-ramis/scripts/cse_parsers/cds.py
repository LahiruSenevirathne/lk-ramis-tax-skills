"""Central Depository System (CDS) of the Colombo Stock Exchange: common to every investor.

Documents: dividend e-warrant / certificate of tax deduction, monthly eStatement.
Layout notes: ../references/cse-formats.md. Synthetic fixtures: tests/fixtures/cse/cds/.
"""
import re

from ._common import MON, NUM, ddmmyyyy, num

PROVIDER = {
    "id": "cds",
    "name": "CDS (Colombo Stock Exchange)",
    "family": "cds",
    "documents": ["Dividend e-warrant / certificate of tax deduction", "CDS monthly eStatement"],
    "tested": "Y/A 2025/26",
}


def parse_dividend_warrant(t, name):
    if not re.search(r"WARRANT NO", t) or not re.search(r"(?i)dividend", t):
        return None
    doc = {"kind": "dividend_warrant", "file": name, "checks": {}}
    wn = re.search(r"WARRANT NO\.?\s*:?\s*([A-Z0-9]+/[A-Z0-9]+/[A-Z0-9]+)", t)
    dt = re.search(r"(?m)^\s*DATE\s*:?\s*(\d\d/\d\d/\d{4})", t)
    sh = re.search(r"NO\. OF SHARES\s*:?\s*(" + NUM + ")", t)
    tot = re.search(r"TOTAL(?: DIVIDEND)?\s*\(3\s*\+\s*6\)\s+(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + ")", t)
    co = re.search(r"(?m)^\s*([A-Z][A-Z0-9&.,()' -]+? PLC)\b", t)
    title = re.search(r"(?m)^\s*([^\n]*DIVIDEND OF[^\n]*)$", t)
    doc.update({
        "warrant_no": wn.group(1) if wn else None,
        "code_root": wn.group(1).split("/")[0] if wn else None,
        "date": ddmmyyyy(dt.group(1)) if dt else None,
        "shares": int(num(sh.group(1))) if sh else None,
        "company": " ".join(co.group(1).split()) if co else None,
        "title": " ".join(title.group(1).split()) if title else None,
        "gross": num(tot.group(1)) if tot else None,
        "ait": num(tot.group(2)) if tot else None,
        "net": num(tot.group(3)) if tot else None,
    })
    doc["checks"] = {
        "fields_found": all(doc[k] is not None for k in ("warrant_no", "date", "gross", "net")),
        "gross_minus_ait_is_net": tot is not None and abs(doc["gross"] - doc["ait"] - doc["net"]) < 0.01,
    }
    return doc


def parse_cds_estatement(t, name):
    if not re.search(r"Balance C/F", t) or not re.search(r"(?i)(CDS|monthly statement)", t):
        return None
    doc = {"kind": "cds_estatement", "file": name, "movements": [], "checks": {}}
    current = None
    for line in t.splitlines():
        line = line.strip()
        h = re.match(r"^(.+?)-([A-Z0-9]+\.[A-Z]\d{4})(?:\s+(" + NUM + r"))?$", line)
        if h:
            current = {"code": h.group(2), "name": h.group(1).strip()}
            continue
        m = re.match(r"^(\d\d)-([A-Z]{3})-(\d{4})\s+(.+)$", line)
        if not (m and current):
            continue
        date = "%s-%02d-%s" % (m.group(3), MON[m.group(2)], m.group(1))
        rest = m.group(4)
        if rest.startswith(("PURCHASE", "SALE", "Balance")):
            continue  # trades come from the broker's confirmations
        dm = re.match(r"^(Direct Deposit|DirWithdrw[-\w]*)\s*-\s*(\S+)\s+(" + NUM + r")(?:\s+(" + NUM + r"))?\s*$", rest)
        if dm:
            kind = "deposit" if dm.group(1) == "Direct Deposit" else "withdrawal"
            doc["movements"].append({
                "date": date, "code": current["code"], "kind": kind, "ref": dm.group(2),
                "qty": int(num(dm.group(3))),
                "balance_after": int(num(dm.group(4))) if dm.group(4) else 0,
                "file": name,
            })
        else:
            doc["movements"].append({"date": date, "code": current["code"], "kind": "other",
                                     "text": rest, "file": name})
    doc["checks"] = {"parsed": True}
    return doc



DOCUMENTS = [parse_dividend_warrant, parse_cds_estatement]
