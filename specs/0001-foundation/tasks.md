# Spec 0001 — Foundation tasks

Ordered task list for the first 2-3 PRs after the scaffold.

## PR 1 — package skeleton plus graph schema

- [ ] Add `pyproject.toml` declaring `facility-war` and CLI entry.
- [ ] Add `src/facility_war/__init__.py` with `__version__`.
- [ ] Add `src/facility_war/cli.py` with no-op `version` command.
- [ ] Add `schemas/supply_graph.schema.json` matching R-FW-002.
- [ ] Add `src/facility_war/graph/schema.py` (dataclasses).
- [ ] Add `src/facility_war/graph/loader.py` with `load_graph(path)`.
- [ ] Add fixture `tests/fixtures/graphs/tiny_h100.json` with 8 nodes.
- [ ] Add `tests/test_graph_loader.py`.
- [ ] Add `decisions/DEC-FW-001-graph-schema.md` explaining the
      derivation from chip-supply-chain-map.

## PR 2 — scenario schema plus simulator skeleton

- [ ] Add `schemas/scenario.schema.json` matching R-FW-003.
- [ ] Add `schemas/sim_run.schema.json` matching R-FW-005.
- [ ] Add `src/facility_war/scenarios/base.py`.
- [ ] Add `src/facility_war/scenarios/taiwan_substrate.py`.
- [ ] Add `scenarios/taiwan_substrate_90d.yaml`.
- [ ] Add `src/facility_war/sim/propagation.py` (tier-N walk).
- [ ] Add `src/facility_war/sim/monte_carlo.py` (N trials, seeded).
- [ ] Add `tests/test_propagation.py` with hand-checked tiny graph.
- [ ] Add `tests/test_monte_carlo_determinism.py` asserting R-FW-006.
- [ ] Add `scripts/voice_lint.py`.
- [ ] Add `scripts/validate_schemas.py`.

## PR 3 — first report plus calibration backtest

- [ ] Add the H100 fixture graph `data/graphs/h100_bom.json`.
- [ ] Add `src/facility_war/report/render.py`.
- [ ] Run the simulator against the H100 graph plus Taiwan scenario.
- [ ] Check in `reports/2026-Q3-h100-substrate-shock/report.md`.
- [ ] Add `eval/backtest_2020_covid.py` with a small 2020 fixture
      graph.
- [ ] Add `eval/calibration_brier.py` gate.
- [ ] Add `docs/dev/scenario-authoring.md`.
