from __future__ import annotations

import json
from pathlib import Path

import pytest

import backtest_2020_covid as bt
import calibration_brier as gate

ROOT = Path(__file__).resolve().parents[1]


def test_brier_score_hand_checked_case() -> None:
    # three forecasts: perfect-0, perfect-1, and a 0.5 hedge on a true outcome.
    # squared errors: 0, 0, 0.25 -> mean 0.25/3 = 1/12.
    score = bt.brier_score([0.0, 1.0, 0.5], [0, 1, 1])
    assert score == pytest.approx(1.0 / 12.0)


def test_brier_score_rejects_empty_and_mismatched() -> None:
    with pytest.raises(ValueError):
        bt.brier_score([], [])
    with pytest.raises(ValueError):
        bt.brier_score([0.1, 0.2], [1])


def test_point_severity_reads_fixed() -> None:
    assert bt.point_severity({"severity_distribution": {"type": "fixed", "value": 0.7}}) == 0.7


def test_run_backtest_is_real_and_deterministic() -> None:
    first = bt.run_backtest()
    second = bt.run_backtest()
    assert first["brier_score"] == second["brier_score"]
    # the real computed score, not the old hardcoded 0.16 stub.
    assert first["brier_score"] == pytest.approx(0.0982)
    assert first["brier_score"] != 0.16
    assert first["n_outcomes"] == 10


def test_committed_result_matches_recompute() -> None:
    committed = json.loads(
        (ROOT / "eval" / "backtest_2020_covid_result.json").read_text(encoding="utf-8")
    )
    recomputed = bt.run_backtest()["brier_score"]
    assert committed["brier_score"] == pytest.approx(recomputed)


def test_gate_passes_on_committed_result() -> None:
    assert gate.main([]) == 0


def test_gate_fails_when_result_absent(tmp_path) -> None:
    missing = tmp_path / "nope.json"
    assert gate.main(["--result", str(missing)]) == 1


def test_gate_fails_on_bad_forecast_fixture(tmp_path) -> None:
    # A fixture that inverts every real outcome makes the simulator maximally
    # wrong -> a high Brier. Generate a matching result so the recompute check
    # passes and the gate fails specifically on the threshold.
    bad_outcomes = _inverted_outcomes()
    bad_path = tmp_path / "bad_outcomes.yaml"
    _dump_outcomes(bad_path, bad_outcomes)

    result = bt.run_backtest(outcomes_path=bad_path)
    assert result["brier_score"] > 0.25  # genuinely miscalibrated forecast

    result_path = tmp_path / "bad_result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    rc = gate.main(
        [
            "--result",
            str(result_path),
            "--outcomes",
            str(bad_path),
            "--max-brier",
            "0.25",
        ]
    )
    assert rc == 1


def test_gate_fails_on_tampered_result(tmp_path) -> None:
    result = bt.run_backtest()
    result["brier_score"] = 0.0  # pretend it is perfect
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    # recompute (0.0982) != committed (0.0) -> fail even though 0.0 < threshold.
    assert gate.main(["--result", str(tampered)]) == 1


def _inverted_outcomes() -> dict:
    doc = bt.load_document(bt.DEFAULT_OUTCOMES)
    flipped = []
    for entry in doc["outcomes"]:
        entry = dict(entry)
        entry["outcome"] = 1 - int(entry["outcome"])
        flipped.append(entry)
    doc = dict(doc)
    doc["outcomes"] = flipped
    return doc


def _dump_outcomes(path: Path, doc: dict) -> None:
    import yaml

    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
