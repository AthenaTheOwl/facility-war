# facility-war

facility-war is a deterministic supply-shock playthrough for public
supplier graphs. it loads a graph, loads a scenario, walks tiered
dependencies up to tier 4, applies substitution edges, and writes a
run record plus a markdown report.

## run

validate the committed v0.1 fixture set:

```bash
python -m facility_war validate
```

run the h100 taiwan substrate scenario:

```bash
python -m facility_war run \
  --graph graphs/h100_bom.yaml \
  --scenario scenarios/taiwan_substrate_90d.yaml \
  --trials 1000 \
  --seed 42 \
  --out reports/2026-Q3-h100-substrate-shock/
```

## included fixtures

- `graphs/h100_bom.yaml`
- `scenarios/taiwan_substrate_90d.yaml`
- `scenarios/suez_closure_30d.yaml`
- `scenarios/az_drought_1in50.yaml`
- `reports/2026-Q3-h100-substrate-shock/run.json`
- `reports/2026-Q3-h100-substrate-shock/report.md`

## local gates

```bash
uv run pytest
python scripts/voice_lint.py
python scripts/validate_schemas.py
python eval/calibration_brier.py
```

## package

the package entry points are:

- `python -m facility_war validate`
- `python -m facility_war run`
- `facility-war validate`
- `facility-war run`

## license

mit. see `LICENSE`.
