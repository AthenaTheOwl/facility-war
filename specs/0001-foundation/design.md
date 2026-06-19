# Spec 0001 — Foundation design

## Shape

A Python CLI plus three layers: graph loader, scenario engine, Monte
Carlo simulator. A renderer turns simulation runs into reports. A
backtest harness calibrates the engine against known historical
shocks.

## Components

### Graph layer (`src/facility_war/graph/`)

- `loader.py` — reads a JSON or YAML supply graph from disk; validates
  against `schemas/supply_graph.schema.json`; returns an in-memory
  `SupplyGraph` object (nodes, edges, indices by tier and geography).
- `schema.py` — Python dataclasses for `Supplier`, `Component`,
  `BomItem`, `Geography`, and the four edge types.

### Scenario layer (`src/facility_war/scenarios/`)

- `base.py` — `Scenario` dataclass loaded from YAML; defines
  `geographies_affected()`, `components_affected()`,
  `severity_at_week(w, rng)`.
- One concrete scenario module per shock class. Each is a thin layer
  on the base, supplying the distributions and the affected sets.

### Simulator (`src/facility_war/sim/`)

- `propagation.py` — given a graph and a per-supplier degradation
  state at week `w`, compute the resulting per-BOM-item status by
  walking `depends_on` and `supplies` edges up to tier 4. Substitution
  edges short-circuit if the substitute is healthy.
- `monte_carlo.py` — runs N trials. Each trial seeds a per-supplier
  random latent, evolves the scenario week by week, calls the
  propagator, records the per-BOM-item status. Aggregates into a
  distribution.

Determinism: numpy.random.Generator with a per-trial sub-seed derived
from `(run.seed, trial_index)`.

### Mitigations (`src/facility_war/mitigations/`)

- `suggester.py` — given a sim run, enumerate candidate mitigations
  (dual-source on the highest-leverage supplier, buffer-stock at the
  highest-leverage BOM item, redesign-out the highest-leverage
  component). Re-simulate. Rank by reduction in expected outage
  weeks.

### Report renderer (`src/facility_war/report/render.py`)

Reads a sim_run record, emits:

- `reports/<run_id>/report.md`
- `reports/<run_id>/index.html` (static, no JS framework dependency)
- `reports/<run_id>/figures/*.png`

### Backtest (`eval/`)

- `backtest_2020_covid.py` — replay COVID-2020 China-Hubei shutdown
  against a checked-in 2020 supply-graph snapshot; compare predicted
  vs actual BOM-item outage weeks; compute Brier.
- `calibration_brier.py` — gate script. Reads backtest outputs,
  asserts Brier under threshold.

## Data model

```
SupplyGraph
  nodes: {supplier, component, bom_item, geography}
  edges: {supplies, located_in, depends_on, substitutes_for}

Scenario
  scenario_id, name, trigger
  duration_weeks_distribution (e.g. triangular(60, 90, 180))
  affected_geographies, affected_components
  severity_distribution per week

SimRun
  run_id, graph_hash, scenario_id, trial_count, seed
  per_bom_item_distribution: { bom_item_id: { outage_weeks: histogram } }
  mitigation_candidates: [ { mitigation, expected_reduction } ]
```

## Out of scope for spec 0001

- Cost-optimization of mitigations (only ranks by outage reduction).
- Interactive scenario builder UI.
- Multi-tenant access control.
- Stochastic recovery models (recovery in v0 is deterministic at
  end-of-scenario).
