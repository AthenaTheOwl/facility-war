# AGENTS.md — facility-war

Operating contract for AI agents (Claude, Codex, Cursor). Same
conventions as the rest of the AthenaTheOwl portfolio. An agent
trained on chip-supply-chain-map or semiconductor-wafer-robust-
optimization will recognize the shape.

## What this repo is

A Monte Carlo war-gaming engine for supply-chain shock scenarios.
Input: a supplier graph plus a scenario description. Output: a
distribution over BOM-item outage weeks, plus a ranked list of
mitigations.

The math comes from four prior repos (facility-location,
robust-knapsack, world-food-program-robust-simulator, semiconductor-
wafer-robust-optimization). The graph schema is a derivative of
chip-supply-chain-map. The novelty is the scenario library plus the
calibration backtests.

## Roles you may see in tasks

| Role | What they do |
|---|---|
| `graph-loader` | Reads a supplier graph; validates against schema |
| `scenario-author` | Encodes a shock scenario as a YAML spec |
| `propagator` | Walks the graph applying tier-N shock propagation rules |
| `sim-runner` | Runs N Monte Carlo trials; aggregates outage distributions |
| `mitigation-suggester` | Ranks candidate mitigations (dual-source, buffer, redesign) |
| `report-renderer` | Produces the published markdown report |
| `backtester` | Re-runs historical shocks (COVID 2020, Suez 2021, Red Sea 2024) for calibration |

## Voice constraints

- Plain assertions. No marketing words. Banned set will land in
  `scripts/voice_lint.py::BANNED_FAIL` in spec 0002.
- No antithetical reversals as a structural device.
- Every quantitative claim in a report cites either a fixture, a
  scenario spec, or a backtest result.

## Gates (will land in spec 0002)

```bash
uv run pytest
python scripts/voice_lint.py
python scripts/validate_schemas.py
python eval/calibration_brier.py
```

The calibration gate fails when the simulator's Brier score on a
historical backtest exceeds a configured ceiling.

## Out of scope

- Real-time sensor ingest (no IoT, no shipment-trackers).
- Customer-confidential supplier lists. Public graphs and fixtures
  only in this repo.
- Equity-side trade recommendations.
- A hosted SaaS dashboard. The artifact is a CLI plus published
  reports plus an interactive page generator.
