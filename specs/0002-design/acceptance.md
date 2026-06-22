# spec 0002 acceptance

The v0.1 release is accepted when:

- `python -m facility_war validate` exits 0 with no flags.
- `python -m pytest -q` passes.
- all three scenarios parse against `schemas/scenario.schema.json`.
- `reports/2026-Q3-h100-substrate-shock/report.md` and `run.json` exist.
