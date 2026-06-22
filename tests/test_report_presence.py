from __future__ import annotations

from pathlib import Path

from facility_war.simulator import load_document


def test_report_and_run_are_committed() -> None:
    report = Path("reports/2026-Q3-h100-substrate-shock/report.md")
    run_json = Path("reports/2026-Q3-h100-substrate-shock/run.json")

    assert report.exists()
    assert run_json.exists()

    run = load_document(run_json)
    text = report.read_text(encoding="utf-8")
    assert run["run_id"] in text
    assert run["scenario_id"] in text
