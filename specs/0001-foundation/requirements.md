# Spec 0001 — Foundation requirements

The first spec for FacilityWar. Names the supply-graph schema, the
scenario schema, the simulator run contract, and the calibration
gate.

## Requirements

- **R-FW-001** — The repo MUST expose a `facility-war` Python package
  with a `__version__` string and a CLI entry point.

- **R-FW-002** — A supply graph MUST conform to
  `schemas/supply_graph.schema.json` with node types
  `{supplier, component, bom_item, geography}` and edge types
  `{supplies, located_in, depends_on, substitutes_for}`.

- **R-FW-003** — A scenario MUST conform to
  `schemas/scenario.schema.json` with fields: `scenario_id`,
  `name`, `trigger`, `duration_weeks_distribution`,
  `affected_geographies[]`, `affected_components[]`,
  `severity_distribution`, `references[]` (citations to the
  historical or analytical basis).

- **R-FW-004** — The simulator MUST run `N` independent Monte Carlo
  trials, each producing a per-week per-BOM-item status in
  `{green, amber, red}` and an aggregate distribution over outage
  weeks per BOM item.

- **R-FW-005** — A simulation run MUST emit a record conforming to
  `schemas/sim_run.schema.json` with fields: `run_id`,
  `graph_hash`, `scenario_id`, `trial_count`, `seed`,
  `started_at`, `finished_at`, `per_bom_item_distribution`,
  `mitigation_candidates[]`.

- **R-FW-006** — Determinism: given identical inputs and seed, two
  runs MUST produce byte-identical `sim_run` records.

- **R-FW-007** — The propagation rules MUST support at minimum:
  tier-N traversal up to N=4, substitution edges (a component with
  a substitute under threshold severity remains green), geography
  shocks (every supplier in an affected geography is degraded for
  the scenario duration).

- **R-FW-008** — The repo MUST include at minimum three scenarios in
  `scenarios/`: `taiwan_substrate_90d.yaml`, `suez_closure_30d.yaml`,
  `az_drought_1in50.yaml`.

- **R-FW-009** — A calibration backtest MUST exist for at least one
  historical shock (COVID 2020 or Suez 2021) and produce a Brier
  score that the operator can read.

- **R-FW-010** — The report renderer MUST produce one markdown file
  plus one static HTML page per run, both passing voice_lint.

- **R-FW-011** — No live network access at gate time. All gates run
  against checked-in graphs, scenarios, and fixture historical-shock
  data.

- **R-FW-012** — The first published report MUST be
  `reports/2026-Q3-h100-substrate-shock/report.md` covering a Taiwan
  substrate shock scenario applied to an H100 BOM fixture graph.
