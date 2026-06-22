# spec 0002 design

## purpose

spec 0002 turns the scaffold into a v0.1 repo that a first user can run
without choosing paths. the default command is:

```bash
python -m facility_war validate
```

## contracts

- package name: `facility-war`
- import package: `facility_war`
- default graph: `graphs/h100_bom.yaml`
- default scenarios: all three yaml files under `scenarios/`
- default run: `reports/2026-Q3-h100-substrate-shock/run.json`
- default report: `reports/2026-Q3-h100-substrate-shock/report.md`

## simulator rules

- all runs take an explicit seed.
- run timestamps are fixed in v0.1 so a deterministic rerun can compare
  the full json record.
- geography shocks start at supplier nodes reached by `located_in`.
- dependency risk walks through `supplies` and `depends_on` edges.
- traversal stops at tier 4.
- `substitutes_for` edges can lower a component risk when the substitute
  stays below the scenario threshold.

## validation

the default validation command checks schemas, graph edge integrity,
the committed run json, the report, and a deterministic rerun of the
taiwan substrate scenario.
