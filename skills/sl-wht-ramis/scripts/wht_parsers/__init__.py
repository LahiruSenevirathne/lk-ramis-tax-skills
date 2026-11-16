"""Bank parser registry for sl-wht-ramis.

Every module in this package (except those starting with "_") is a parser for
one bank or financial institution. A module must define:

    PROVIDER = {"id": "<short id>", "name": "<institution>",
                "documents": ["<certificate names>"], "tested": "<Y/A it was tested on>"}
    def detect(text) -> bool          # is this document from this institution?
    def parse(text, name) -> dict     # {"bank", "kind", "file", "rows", "checks"}

Rows use the fields documented in references/bank-formats.md. Checks named
"*_matches" must be True for the document to be accepted.

Add a bank: copy wht_parsers/_template.py to wht_parsers/<id>.py, and add SYNTHETIC
fixtures under tests/fixtures/wht/<id>/. Discovery is automatic. See
CONTRIBUTING.md.
"""
import importlib
import pkgutil

REGISTRY = []
for _m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
    if _m.name.startswith("_"):
        continue
    _mod = importlib.import_module(f"{__name__}.{_m.name}")
    for _attr in ("PROVIDER", "detect", "parse"):
        if not hasattr(_mod, _attr):
            raise ImportError(f"parser {_m.name} is missing {_attr}")
    REGISTRY.append(_mod)


def providers():
    return [m.PROVIDER for m in REGISTRY]


def parse(text, name):
    for mod in REGISTRY:
        if mod.detect(text):
            doc = mod.parse(text, name)
            doc.setdefault("provider", mod.PROVIDER["id"])
            return doc
    return {"bank": None, "provider": None, "kind": "unrecognised", "file": name, "rows": [], "checks": {}}
