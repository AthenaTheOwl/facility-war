from __future__ import annotations

from copy import deepcopy

from facility_war.simulator import (
    _mitigated_red_weeks,
    _StatusCache,
    draw_shocks,
    dual_source_graph,
    load_document,
    run_simulation,
)

BOM = "bom_h100_accelerator"


def _graph() -> dict:
    return load_document("graphs/h100_bom.yaml")


def _scenario() -> dict:
    return load_document("scenarios/taiwan_substrate_90d.yaml")


def _fixed(scenario: dict, *, weeks: int = 13, severity: float = 0.92) -> dict:
    """Deterministic single-point mode: every trial draws the same shock."""

    scenario = deepcopy(scenario)
    scenario["duration_weeks_distribution"] = {"type": "fixed_weeks", "weeks": weeks}
    scenario["severity_distribution"] = {"type": "fixed", "value": severity}
    return scenario


def _queue(run: dict) -> list[tuple[str, str, float]]:
    return [
        (item["type"], item["target"], item["expected_reduction_weeks"])
        for item in run["mitigation_candidates"]
    ]


def test_fixed_distributions_are_a_deterministic_single_point() -> None:
    run = run_simulation(_graph(), _fixed(_scenario()), trial_count=50, seed=42)
    assert run["per_bom_item_distribution"][BOM]["outage_weeks"] == {"13": 50}


def test_mitigations_are_resimulated_not_fixed_fractions() -> None:
    # On a fixed 13-week, 0.92 shock the old coefficients gave 5.85 (0.45 x 13),
    # 4.0 and 3.9 (0.30 x 13). Re-simulation gives what the lead times allow:
    # the packaging second source covers weeks 7-13, the buffer covers 4 red
    # weeks, the redesign covers week 13 only, and a second substrate source
    # adds nothing because the substrate already has a qualified substitute.
    run = run_simulation(_graph(), _fixed(_scenario()), trial_count=20, seed=42)
    assert _queue(run) == [
        ("dual_source", "sup_taiwan_packaging", 7.0),
        ("buffer", BOM, 4.0),
        ("redesign", "cmp_advanced_package", 1.0),
        ("dual_source", "sup_taiwan_substrate_a", 0.0),
    ]
    for item in run["mitigation_candidates"]:
        assert item["residual_expected_red_weeks"] == 13.0 - item["expected_reduction_weeks"]


def test_mitigation_saving_moves_with_its_lead_time() -> None:
    scenario = _fixed(_scenario())
    scenario["mitigation_assumptions"] = {"dual_source_qualification_weeks": 2}
    run = run_simulation(_graph(), scenario, trial_count=10, seed=42)
    top = run["mitigation_candidates"][0]
    assert (top["target"], top["expected_reduction_weeks"]) == ("sup_taiwan_packaging", 11.0)


def test_savings_are_paired_on_the_same_shock_draws() -> None:
    graph = _graph()
    scenario = _scenario()
    run = run_simulation(graph, scenario, trial_count=200, seed=3)
    draws = draw_shocks(scenario, trial_count=200, seed=3)
    cache = _StatusCache(scenario, 4)
    common = {
        "bom_item": BOM,
        "draws": draws,
        "horizon_weeks": 26,
        "cache": cache,
        "baseline_graph": graph,
    }
    baseline = _mitigated_red_weeks(**common)
    mitigated = _mitigated_red_weeks(
        mitigated_key="dual",
        mitigated_graph=dual_source_graph(graph, "sup_taiwan_packaging"),
        effective_after_weeks=6,
        **common,
    )
    assert sum(baseline) / 200 == run["per_bom_item_distribution"][BOM]["expected_red_weeks"]
    assert all(after <= before for before, after in zip(baseline, mitigated))
    paired = round(sum(b - a for b, a in zip(baseline, mitigated)) / 200, 4)
    dual = next(
        item
        for item in run["mitigation_candidates"]
        if item["mitigation_id"] == "dual-source-sup_taiwan_packaging"
    )
    assert dual["expected_reduction_weeks"] == paired


def test_second_source_sharing_a_shocked_input_does_not_help() -> None:
    # Shock the substrate and its substitute too: a second packaging source
    # still needs abf substrate, so it fails with the original.
    scenario = _fixed(_scenario())
    scenario["affected_components"] = [
        "cmp_abf_substrate",
        "cmp_alt_substrate",
        "cmp_advanced_package",
    ]
    run = run_simulation(_graph(), scenario, trial_count=5, seed=42)
    by_id = {item["mitigation_id"]: item for item in run["mitigation_candidates"]}
    assert by_id["dual-source-sup_taiwan_packaging"]["expected_reduction_weeks"] == 0.0


def test_mitigation_queue_ignores_yaml_edge_order() -> None:
    graph = _graph()
    swapped = deepcopy(graph)
    located = [i for i, edge in enumerate(swapped["edges"]) if edge["to"] == "geo_taiwan"]
    first, second = located[:2]
    swapped["edges"][first], swapped["edges"][second] = (
        swapped["edges"][second],
        swapped["edges"][first],
    )
    scenario = _scenario()
    original = run_simulation(graph, scenario, trial_count=100, seed=42)
    reordered = run_simulation(swapped, scenario, trial_count=100, seed=42)
    assert _queue(original) == _queue(reordered)
    assert original["mitigation_candidates"][0]["target"] == "sup_taiwan_packaging"
