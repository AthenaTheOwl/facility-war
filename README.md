# facility-war

One Taiwan substrate supplier goes dark for 90 days, and the H100 accelerator
spends 13 of the next 26 weeks unbuildable. Half the horizon, gone, traced back
to a single node three tiers down the bill of materials. facility-war runs that
playthrough and tells you which one move buys the most weeks back.

## What it does

A supply shock doesn't stop at the component it hits. It walks. A substrate plant
goes offline and the outage propagates up the dependency tree — substrate to
package to accelerator — until it lands on the thing you actually ship. facility-war
loads a supplier graph and a scenario, walks the tiered dependencies up to tier 4,
applies the substitution edges that route around the damage, and runs a thousand
Monte Carlo trials to get a distribution over outage weeks per BOM item.

Then it ranks the fixes. Dual-sourcing the affected substrate supplier, buffering
the accelerator, redesigning the package — each costs something, each buys back a
different number of red weeks. The run writes a checked-in record plus a markdown
report, and every number in it traces to a fixture, a scenario spec, or a backtest.
The run is deterministic: explicit seed, fixed timestamp, same input gives the same
report every time.

## try it

one command, no args, reads the committed run and prints the result:

```bash
python -m facility_war show
```

```
facility-war - supply-shock playthrough, 2026-Q3-h100-substrate-shock
scenario taiwan_substrate_90d | 1000 trials | seed 42 | 26-week horizon | tier walk to 4

1 bom item(s), ranked by expected weeks in 'red' (supply unavailable)

bom item               exp red wks  of horizon  any-red prob  red share
-----------------------------------------------------------------------
h100 accelerator            13.00w         50%         100%        50%

mitigation queue, ranked by expected red-week reduction:
  1. dual_source on taiwan substrate supplier a - saves ~5.8 red weeks (...)
  2. buffer      on h100 accelerator - saves ~4.0 red weeks (...)
  3. redesign    on advanced package - saves ~3.9 red weeks (...)

headline: h100 accelerator spends ~13 of 26 weeks unavailable under this shock;
best single move is to dual_source taiwan substrate supplier a (~5.8 weeks back).
```

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
- [semiconductor-wafer-robust-optimization](https://github.com/AthenaTheOwl/semiconductor-wafer-robust-optimization) —
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
python eval/calibration_brier.py
```

## package

the package entry points are:

- `python -m facility_war validate`
- `python -m facility_war run`
- `python -m facility_war show`
- `facility-war validate`
- `facility-war run`
- `facility-war show`

## license

mit. see `LICENSE`.
