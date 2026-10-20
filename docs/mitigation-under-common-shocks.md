# Compare mitigation on a shared shock draw

Method update: October 18, 2026.

The simulator ranks dual sourcing, buffers and redesign by reduced outage weeks. Those reductions are fixed rules in `_rank_mitigations`: 0.45 of the most-exposed BOM item's expected red weeks for dual sourcing, that same figure capped at 4 weeks for a buffer, and 0.30 of it for redesign, which is offered only when the scenario's affected component is in the graph. No mitigation is re-simulated, and the published order follows from those coefficients. A mitigation ranking is conditional on the graph, scenario and response assumptions. Two alternatives that depend on the same upstream substrate can fail together; adding an alternative edge alone does not establish independent supply.

For the next proposed synthetic experiment, model each mitigation as a graph or scenario change, then run the baseline and each mitigation on identical shock draws. Give the alternate a qualification delay and an explicitly shared upstream node, then compare the result with an independent alternate. Report outage-week reduction, mitigation cost, time to become effective and residual outage probability separately. An expensive option that begins after the shock should not receive immediate protection credit.

Keep the existing historical calibration gate and fixture traceability. A fit on one disruption does not establish coverage of every new scenario. Preserve the original run and state which changed assumptions require a rerun. This note proposes a matched experiment; it does not claim a new backtest or change the published mitigation ranking.
