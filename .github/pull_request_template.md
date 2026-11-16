## What this changes

## Checklist
- [ ] No real documents (PDF, images, spreadsheets) and no real personal data anywhere in the diff
- [ ] Fixtures are synthetic: invented names, `000000000V` NICs, `0000`-placeholder numbers, consistent totals
- [ ] `python -m pytest -q` passes
- [ ] `python tools/check_fixtures.py` passes
- [ ] New parser: `PROVIDER` metadata, fixtures in `tests/fixtures/<wht|cse>/<id>/`, tests, format notes, and a **Tested providers** row in README
