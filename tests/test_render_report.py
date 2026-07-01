from __future__ import annotations

from facility_war.simulator import render_report


def _sim_run_with_two_red_week_buckets() -> dict:
    # Two distinct red-week buckets so the "most common" cell (max by count,
    # tie-broken by week) differs from the min; a max->min swap on that line
    # would change 5 to 2 and fail this test.
    return {
        "run_id": "fixture-run",
        "graph_hash": "0" * 64,
        "scenario_id": "fixture-scenario",
        "trial_count": 10,
        "seed": 1,
        "max_tier": 4,
        "horizon_weeks": 26,
        "per_bom_item_distribution": {
            "bom_widget": {
                "outage_weeks": {"2": 3, "5": 7},
                "expected_red_weeks": 4.1,
                "probability_any_red_week": 1.0,
                "status_share": {"green": 0.0, "amber": 0.5, "red": 0.5},
            }
        },
        "mitigation_candidates": [
            {
                "mitigation_id": "dual-source",
                "type": "dual_source",
                "target": "sup_a",
                "expected_reduction_weeks": 1.85,
                "rationale": "adds a checked supplier",
            }
        ],
    }


def test_report_outage_row_pins_most_common_red_week() -> None:
    text = render_report(
        _sim_run_with_two_red_week_buckets(),
        graph_path="graphs/h100_bom.yaml",
        scenario_path="scenarios/taiwan_substrate_90d.yaml",
    )
    # the most-common red-week count is the higher-frequency bucket (5), not min (2)
    assert "| bom_widget | 4.10 | 100.00% | 5 |" in text


def test_report_mitigation_row_pins_values() -> None:
    text = render_report(
        _sim_run_with_two_red_week_buckets(),
        graph_path="graphs/h100_bom.yaml",
        scenario_path="scenarios/taiwan_substrate_90d.yaml",
    )
    assert "| 1 | dual_source | sup_a | 1.85 |" in text
