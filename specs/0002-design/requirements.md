# spec 0002 requirements

## R-FW-002-001 - default validation

`python -m facility_war validate` must run with no flags and validate the
graph, the three scenarios, the committed run json, and the markdown report.

## R-FW-002-002 - scenario set

The repo must include the three required scenarios:
`taiwan_substrate_90d.yaml`, `suez_closure_30d.yaml`, and
`az_drought_1in50.yaml`.

## R-FW-002-003 - deterministic run

The committed Taiwan substrate run must be stable for the same seed and inputs.
