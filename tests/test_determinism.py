from __future__ import annotations

from facility_war.simulator import canonical_json, load_document, run_simulation


def test_same_seed_produces_same_run_record() -> None:
    graph = load_document("graphs/h100_bom.yaml")
    scenario = load_document("scenarios/taiwan_substrate_90d.yaml")

    first = run_simulation(graph, scenario, trial_count=50, seed=7, run_id="test-run")
    second = run_simulation(graph, scenario, trial_count=50, seed=7, run_id="test-run")

    assert canonical_json(first) == canonical_json(second)
