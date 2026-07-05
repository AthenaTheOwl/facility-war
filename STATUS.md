# status

## Current state

v0.1 has a python package, schemas, one h100 graph fixture, three
scenario specs, a deterministic simulator, a cli, tests, and one
published report directory.

## Known limits

the fixture graph is small and public. trial sampling covers duration
and severity only. mitigation ranking uses simple expected red-week
reduction estimates.

the calibration gate now runs a real backtest. `eval/backtest_2020_covid.py`
asks the live simulator for a per-node disruption probability under
`scenarios/covid_2020_supply_shock.yaml` and scores it against ten cited,
falsifiable binary outcomes of the 2020 covid supply shock in
`eval/covid_2020_outcomes.yaml`. the committed brier score is 0.098 (below
the 0.25 uninformative baseline). `eval/calibration_brier.py` fails when the
result file is missing, when the committed score does not match a fresh
recompute, or when the score exceeds the ceiling — it no longer falls back to
a hardcoded number, so the gate can actually fail.

the honest scale-down: the fixture graph is a synthetic h100 bom that
postdates 2020, so its nodes stand in for real 2020-era supply categories, and
it has no china-manufacturing node — so the early-2020 china assembly shutdown
is the model's single largest miss (pcie board: predicted 0.28, actual 1).

## Next feature queue

- add a larger public supplier graph with source notes, including a china
  manufacturing node so the backtest can score that outcome fairly.
- add a static html report renderer.
- add more historical backtests (suez 2021, red sea 2024) beside covid 2020.
- add scenario authoring docs for new shock files.
