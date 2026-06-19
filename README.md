# FacilityWar

Adversarial war-gaming for supply-chain resilience. Load your supplier
graph, pick a scenario (Taiwan-strait blockade, Suez closure, US-China
substrate export controls, 1-in-50-year drought in Arizona), run a
Monte Carlo simulation of which BOM items go red in which weeks, get
suggested mitigations.

## What this is

Resilinc and Everstream do single-event impact. CSIS-style tabletops
give you a story. Neither gives you a calibrated, probability-weighted
forecast of which inputs go red, when, and by how much, across a
multi-scenario war game.

FacilityWar fuses four math repos (facility-location, robust-knapsack,
world-food-program-robust-simulator, semiconductor-wafer-robust-
optimization) with a supplier-graph schema borrowed from
chip-supply-chain-map. The first artifact is a public report: "What
happens to the NVDA H100 BOM if Taiwan substrate exports stop for 90
days" with the Monte Carlo simulation, an interactive page, and the
methodology fully cited.

Buyers: supply-chain risk leads at industrial OEMs, defense primes,
semis design houses, large-pharma; risk consultants running scenario
exercises; government supply-chain stress-testing groups (DOC, DOE).

## Status

v0 scaffold. No implementation. The repo holds the README, the
license, the agents contract, the foundation spec, and the literal
first PR plan. The first runnable PR after this scaffold lands the
graph loader and one scenario class against a fixture supply graph.

## How to run

Placeholder. Spec 0002 lands the run contract. After implementation
the entry point will look like:

```bash
uv run facility-war run \
  --graph data/graphs/h100_bom.json \
  --scenario scenarios/taiwan_substrate_90d.yaml \
  --trials 5000 \
  --out reports/2026-Q3-h100-substrate-shock/
```

## Layout

```
facility-war/
  README.md
  LICENSE
  AGENTS.md
  .gitignore
  specs/
    0001-foundation/
      requirements.md          # R-FW-NNN
      design.md
      tasks.md
      acceptance.md
  docs/
    first-pr.md
```

Downstream additions:

```
  src/facility_war/
    graph/loader.py
    graph/schema.py
    scenarios/base.py
    scenarios/taiwan_substrate.py
    scenarios/suez_closure.py
    scenarios/arizona_drought.py
    sim/monte_carlo.py
    sim/propagation.py            # tier-N shock propagation
    mitigations/suggester.py
    report/render.py
  schemas/
    supply_graph.schema.json
    scenario.schema.json
    sim_run.schema.json
  scenarios/
    taiwan_substrate_90d.yaml
    suez_closure_30d.yaml
    az_drought_1in50.yaml
  data/
    graphs/h100_bom.json          # checked-in fixture
  reports/
    2026-Q3-h100-substrate-shock/
  eval/
    backtest_2020_covid.py
    backtest_2021_suez.py
    calibration_brier.py
```

## License

MIT. See [LICENSE](LICENSE).
