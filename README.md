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

the point: a taiwan substrate shock idles the h100 accelerator for half the
horizon, and `show` ranks the cheapest fix first so you act on the supplier that
buys back the most weeks instead of guessing.

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
