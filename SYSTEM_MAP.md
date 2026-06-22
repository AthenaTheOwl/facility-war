# system map

## package

- `src/facility_war/cli.py` exposes `validate` and `run`.
- `src/facility_war/simulator.py` loads documents, validates schemas,
  propagates shocks, runs trials, ranks mitigations, renders reports,
  and checks the committed defaults.
- `src/facility_war/__main__.py` enables `python -m facility_war`.

## inputs

- `schemas/supply_graph.schema.json`
- `schemas/scenario.schema.json`
- `schemas/sim_run.schema.json`
- `graphs/h100_bom.yaml`
- `scenarios/taiwan_substrate_90d.yaml`
- `scenarios/suez_closure_30d.yaml`
- `scenarios/az_drought_1in50.yaml`

## outputs

- `reports/2026-Q3-h100-substrate-shock/run.json`
- `reports/2026-Q3-h100-substrate-shock/report.md`

## gates

- `uv run pytest`
- `python scripts/voice_lint.py`
- `python scripts/validate_schemas.py`
- `python eval/calibration_brier.py`
