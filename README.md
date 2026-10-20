# facility-war

Taiwan substrate and advanced-package exports stop for roughly 90 days, and the
H100 accelerator spends about 14 of the next 26 weeks unbuildable on average
(13.96 expected red weeks over 1,000 sampled shocks). facility-war runs that
playthrough and tells you which one move buys the most weeks back.

## What it does

A supply shock doesn't stop at the component it hits. It walks. A substrate plant
goes offline and the outage propagates up the dependency tree — substrate to
package to accelerator — until it lands on the thing you actually ship. facility-war
loads a supplier graph and a scenario, walks the tiered dependencies up to tier 4,
applies the substitution edges that route around the damage, and runs a thousand
Monte Carlo trials to get a distribution over outage weeks per BOM item. Each
trial draws its own shock duration and severity from the scenario: the committed
Taiwan scenario samples duration from a triangular 6/13/26-week range and
severity from a triangular 0.60/0.92/1.00 range. Both ranges are planning
assumptions, not sourced estimates.

Then it ranks the fixes. Each fix is applied as a change to the graph or to stock
and re-simulated on the same 1,000 shock draws as the baseline (common random
numbers), so a saving is a paired difference rather than a fixed fraction:

- dual source: a second supplier outside the shocked geography for everything a
  shocked supplier ships, qualified after 6 weeks. The alternate keeps the
  original's other inputs, so a shared upstream node can take both down.
- buffer: 4 weeks of finished stock for the most exposed BOM item, drawn down in
  red weeks.
- redesign: a substitute for the directly shocked component that drops inputs
  from the shocked geography, shipping after 12 weeks.

The lead times, buffer size and 0.20 post-mitigation risk live under
`mitigation_assumptions` in the scenario file. They are assumptions too, and the
ranking is conditional on them. Every candidate supplier in the shocked
geography is scored and the queue is sorted by saving, then by id, so the order
of lines in the graph file does not change the advice.

The run writes a checked-in record plus a markdown report. The run is
deterministic: explicit seed, fixed timestamp, same input gives the same report
every time. A scenario whose distributions are `fixed` / `fixed_weeks` is the
deterministic single-point mode: every trial draws the same shock. The covid
backtest scenario and the suez and arizona scenarios use that mode.

## try it

one command, no args, reads the committed run and prints the result:

```bash
python -m facility_war show
```

```
facility-war - supply-shock playthrough, 2026-Q3-h100-substrate-shock
scenario taiwan_substrate_90d | 1000 trials | seed 42 | 26-week horizon | tier walk to 4
sampled shock: 6-25 weeks (mean 14.9), severity 0.61-1.00 (mean 0.84)

1 bom item(s), ranked by expected weeks in 'red' (supply unavailable)

bom item               exp red wks  of horizon  any-red prob  red share
-----------------------------------------------------------------------
h100 accelerator            13.96w         54%          94%        54%

mitigation queue, ranked by expected red-week reduction (re-simulated on the same shock draws):
  1. dual_source on taiwan advanced packaging supplier - saves ~7.6 red weeks (...)
  2. buffer      on h100 accelerator - saves ~3.8 red weeks (...)
  3. redesign    on advanced package - saves ~2.9 red weeks (...)
  4. dual_source on taiwan substrate supplier a - saves ~0.0 red weeks (...)

headline: h100 accelerator spends ~14 of 26 weeks unavailable under this shock;
best single move is to dual_source taiwan advanced packaging supplier (~7.6 weeks back).
```

A second substrate source saves nothing here: the graph already routes ABF
substrate to a US alternate, so the accelerator's red weeks come from the
advanced package itself. An earlier version of this run recommended dual
sourcing the substrate supplier at 5.85 weeks. That figure was 0.45 times a fixed
13-week outage, and the target was the first Taiwan supplier in the graph file.

The mitigation queue is the point. A red-week count tells you how bad it is; the
ranked queue tells you which supplier to fix first instead of guessing.

## live demo

`streamlit_app.py` wraps the same result the `show` verb prints: the ranked bom
items, the mitigation queue, and the headline fix. it reads the committed
`reports/2026-Q3-h100-substrate-shock/run.json` directly — no network, no secrets.

run it locally:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

deploy on streamlit community cloud: new app -> repo `AthenaTheOwl/facility-war`,
branch `main`, main file `streamlit_app.py`.

<!-- live url: https://<your-app>.streamlit.app -->

## how it connects

facility-war is the war-game over the supply graph the rest of the portfolio
already maps:

- [chip-supply-chain-map](https://github.com/AthenaTheOwl/chip-supply-chain-map) —
  the graph schema here is a derivative of it; this repo shocks the map that one
  draws.
- [semiconductor-e2e-manufacturing-optimization](https://github.com/AthenaTheOwl/semiconductor-e2e-manufacturing-optimization) —
  the optimization side of the same silicon supply curve.

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
python eval/backtest_2020_covid.py   # recompute the committed brier result
python eval/calibration_brier.py     # gate: fails if missing, stale, or over ceiling
```

the calibration gate scores the simulator's per-node disruption probability
under `scenarios/covid_2020_supply_shock.yaml` against ten cited real outcomes
of the 2020 covid supply shock (`eval/covid_2020_outcomes.yaml`). the committed
brier is 0.098 against a 0.25 ceiling. the gate fails when the result file is
absent, when it disagrees with a fresh recompute, or when the score is over the
ceiling — there is no hardcoded fallback.

## package

the package entry points are:

- `python -m facility_war validate`
- `python -m facility_war run`
- `python -m facility_war show`
- `facility-war validate`
- `facility-war run`
- `facility-war show`

## Method update

[October method update: Compare mitigation on a shared shock draw](docs/mitigation-under-common-shocks.md).

## license

mit. see `LICENSE`.
