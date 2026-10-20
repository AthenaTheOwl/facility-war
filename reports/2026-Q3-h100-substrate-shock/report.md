# h100 substrate shock playthrough

source files: `graphs/h100_bom.yaml`, `scenarios/taiwan_substrate_90d.yaml`, and `run.json`.

## inputs

- run id: `2026-Q3-h100-substrate-shock`.
- graph: `graphs/h100_bom.yaml`. the committed graph hash in `run.json` is `1ddfa6b17ddf5be1769634664ba9babc886c7fb376fbcd572dc010d7094cbe41`.
- scenario: `scenarios/taiwan_substrate_90d.yaml` with id `taiwan_substrate_90d`.
- trials: `1000`. seed: `42`. horizon: `26` weeks.
- traversal cap: tier `4` from each bom item to upstream nodes.
- sampled shock duration: min `13`, mean `13`, max `13` weeks.
- sampled shock severity: min `0.92`, mean `0.92`, max `0.92`.

## outage distribution

all values in this table are read from `run.json`.

| bom item | expected red weeks | chance of any red week | most common red-week count |
|---|---:|---:|---:|
| bom_h100_accelerator | 13.00 | 100.00% | 13 |

## mitigation queue

the simulator ranks candidates by expected red-week reduction in `run.json`. each mitigation is applied as a graph or stock change and re-simulated on the baseline's shock draws (common random numbers).
lead times, buffer size and post-mitigation risk are the scenario's `mitigation_assumptions`, not sourced figures.

| rank | type | target | expected red-week reduction | effective after week | residual expected red weeks |
|---:|---|---|---:|---:|---:|
| 1 | dual_source | sup_taiwan_packaging | 7.00 | 6 | 6.00 |
| 2 | buffer | bom_h100_accelerator | 4.00 | 0 | 9.00 |
| 3 | redesign | cmp_advanced_package | 1.00 | 12 | 12.00 |
| 4 | dual_source | sup_taiwan_substrate_a | 0.00 | 6 | 13.00 |

## interpretation

each trial draws one shock duration and one severity from the scenario's distributions; the shock is active from week 1 through the sampled duration. suppliers located in `geo_taiwan` degrade first, then the tier walk carries the risk through supplies and depends_on edges. substitution edges can keep a component green when the substitute is below the scenario threshold. a second source counts only when its inputs avoid the shocked nodes; an alternate that shares an upstream node with the original fails with it.
