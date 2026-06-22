from __future__ import annotations

from copy import deepcopy

from facility_war.simulator import load_document, propagate_week


def test_geography_shock_propagates_to_bom_item() -> None:
    graph = load_document("graphs/h100_bom.yaml")
    scenario = load_document("scenarios/taiwan_substrate_90d.yaml")
    scenario = deepcopy(scenario)
    scenario["affected_components"] = []

    result = propagate_week(graph, scenario, active_severity=0.92)

    assert result["node_risks"]["sup_taiwan_packaging"] == 0.92
    assert result["component_status"]["cmp_advanced_package"] == "red"
    assert result["bom_item_status"]["bom_h100_accelerator"] == "red"


def test_substitution_keeps_substrate_component_green() -> None:
    graph = load_document("graphs/h100_bom.yaml")
    scenario = load_document("scenarios/taiwan_substrate_90d.yaml")
    scenario = deepcopy(scenario)
    scenario["affected_components"] = []

    result = propagate_week(graph, scenario, active_severity=0.92)

    assert result["component_status"]["cmp_abf_substrate"] == "green"
