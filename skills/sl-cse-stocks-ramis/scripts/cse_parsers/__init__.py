"""Document parser registry for sl-cse-stocks-ramis.

Every module here (except those starting with "_") handles one document
provider: the CDS (common to every CSE investor) or one stockbroker. A module
must define:

    PROVIDER = {"id", "name", "family": "broker" | "cds" | "registrar",
                "documents": [...], "tested": "<Y/A it was tested on>"}
    DOCUMENTS = [parse_fn, ...]   # each parse_fn(squashed_text, file_name) -> dict | None

A parse function returns None when the text isn't its document, otherwise a
dict with "kind", "file", "checks" and any of "trades", "holdings",
"dividends", "movements" in the canonical shapes (references/data-model.md).
Broker and registrar modules are tried before the CDS ones.

Add a broker: copy cse_parsers/_template.py to cse_parsers/<id>.py, and add SYNTHETIC
fixtures under tests/fixtures/cse/<id>/. Discovery is automatic. See
CONTRIBUTING.md.
"""
import importlib
import pkgutil

ORDER = {"broker": 0, "registrar": 1, "cds": 2}
REGISTRY = []
for _m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
    if _m.name.startswith("_"):
        continue
    _mod = importlib.import_module(f"{__name__}.{_m.name}")
    for _attr in ("PROVIDER", "DOCUMENTS"):
        if not hasattr(_mod, _attr):
            raise ImportError(f"parser {_m.name} is missing {_attr}")
    REGISTRY.append(_mod)
REGISTRY.sort(key=lambda m: (ORDER.get(m.PROVIDER.get("family"), 9), m.PROVIDER["id"]))


def providers():
    return [m.PROVIDER for m in REGISTRY]


def parse(text, name):
    """text must already be whitespace-squashed."""
    for mod in REGISTRY:
        for fn in mod.DOCUMENTS:
            d = fn(text, name)
            if d is not None:
                d["source"] = mod.PROVIDER["id"]
                return d
    return {"kind": "unrecognised", "file": name, "checks": {"recognised": False}}
