# h100 substrate shock playthrough

source files: `graphs/h100_bom.yaml`, `scenarios/taiwan_substrate_90d.yaml`, and `run.json`.

## inputs

- run id: `2026-Q3-h100-substrate-shock`.
- graph: `graphs/h100_bom.yaml`. the committed graph hash in `run.json` is `1ddfa6b17ddf5be1769634664ba9babc886c7fb376fbcd572dc010d7094cbe41`.
- scenario: `scenarios/taiwan_substrate_90d.yaml` with id `taiwan_substrate_90d`.
- trials: `1000`. seed: `42`. horizon: `26` weeks.
- traversal cap: tier `4` from each bom item to upstream nodes.

## outage distribution

all values in this table are read from `run.json`.

| bom item | expected red weeks | chance of any red week | most common red-week count |
|---|---:|---:|---:|
| bom_h100_accelerator | 13.00 | 100.00% | 13 |

## mitigation queue

the simulator ranks candidates by expected red-week reduction in `run.json`.

| rank | type | target | expected red-week reduction |
|---:|---|---|---:|
| 1 | dual_source | sup_taiwan_substrate_a | 5.85 |
| 2 | buffer | bom_h100_accelerator | 4.00 |
| 3 | redesign | cmp_advanced_package | 3.90 |

## interpretation

the run treats a taiwan geography shock as active for each sampled scenario week. suppliers located in `geo_taiwan` degrade first, then the tier walk carries the risk through supplies and depends_on edges. substitution edges can keep a component green when the substitute is below the scenario threshold.
