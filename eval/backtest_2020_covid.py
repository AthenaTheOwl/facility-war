"""Real COVID-2020 calibration backtest.

This replaces the earlier stub that wrote a hardcoded ``brier_score=0.16``
regardless of input. The score here is computed end-to-end:

  1. Load the fixture supply graph and the COVID-2020 scenario spec.
  2. Ask the *live* simulator (src/facility_war/simulator.py::propagate_week)
     for a per-node disruption probability under the scenario's severity.
  3. Score those probabilities against a checked-in fixture of real, cited
     binary outcomes of the 2020 COVID supply shock (eval/covid_2020_outcomes.yaml)
     with a Brier score.

The prediction for each node is its steady-state ``node_risk`` in [0, 1] while
the shock is active — exactly a "disruption probability for the corresponding
node/tier". The scoring is deterministic (no Monte Carlo sampling), so the
number is fully reproducible and hand-checkable.

Honest scope: the fixture graph is a synthetic H100 BOM (the H100 postdates
2020), so its nodes are used as proxies for real 2020-era supply categories.
See eval/covid_2020_outcomes.yaml for the per-outcome citations and caveats.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# The live package lives under src/ (see pyproject wheel target, tests/conftest.py,
# and scripts/validate_schemas.py). Put it on the path before importing.
_SRC = str(ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from facility_war.simulator import load_document, propagate_week  # noqa: E402

DEFAULT_GRAPH = ROOT / "graphs" / "h100_bom.yaml"
DEFAULT_SCENARIO = ROOT / "scenarios" / "covid_2020_supply_shock.yaml"
DEFAULT_OUTCOMES = ROOT / "eval" / "covid_2020_outcomes.yaml"
OUT = ROOT / "eval" / "backtest_2020_covid_result.json"

DEFAULT_THRESHOLD = 0.25  # a Brier of 0.25 is the uninformative "0.5 everywhere" baseline.
_PRECISION = 6


def brier_score(predictions: list[float], outcomes: list[int]) -> float:
    """Mean squared error between forecast probabilities and binary outcomes."""

    if len(predictions) != len(outcomes):
        raise ValueError("predictions and outcomes must have equal length")
    if not predictions:
        raise ValueError("cannot score an empty outcome set")
    total = sum((float(p) - float(o)) ** 2 for p, o in zip(predictions, outcomes))
    return total / len(predictions)


def point_severity(scenario: dict[str, Any]) -> float:
    """A single deterministic severity for the snapshot forecast.

    fixed -> value, fixed_weeks -> weeks (unused as a severity), triangular ->
    mode, choice -> weighted mean. The COVID scenario uses a fixed severity so
    the backtest is fully deterministic.
    """

    spec = scenario["severity_distribution"]
    kind = spec.get("type", "fixed")
    if kind == "fixed":
        return float(spec["value"])
    if kind == "triangular":
        return float(spec["mode"])
    if kind == "choice":
        choices = spec["choices"]
        weight = sum(float(c.get("weight", 1.0)) for c in choices)
        return sum(float(c["value"]) * float(c.get("weight", 1.0)) for c in choices) / weight
    raise ValueError(f"severity distribution type not usable as a point forecast: {kind}")


def run_backtest(
    graph_path: str | Path = DEFAULT_GRAPH,
    scenario_path: str | Path = DEFAULT_SCENARIO,
    outcomes_path: str | Path = DEFAULT_OUTCOMES,
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """Compute the backtest result dict from the fixtures (no I/O of results)."""

    graph = load_document(graph_path)
    scenario = load_document(scenario_path)
    outcomes_doc = load_document(outcomes_path)

    severity = point_severity(scenario)
    node_risks = propagate_week(graph, scenario, severity, max_tier=4)["node_risks"]

    node_ids = {node["id"] for node in graph["nodes"]}
    predictions: list[dict[str, Any]] = []
    preds: list[float] = []
    actuals: list[int] = []
    for entry in outcomes_doc["outcomes"]:
        node_id = entry["node_id"]
        if node_id not in node_ids:
            raise ValueError(f"outcome references unknown node: {node_id}")
        if node_id not in node_risks:
            raise ValueError(f"simulator produced no risk for node: {node_id}")
        predicted = float(node_risks[node_id])
        actual = int(entry["outcome"])
        if actual not in (0, 1):
            raise ValueError(f"outcome for {node_id} must be 0 or 1, got {actual}")
        preds.append(predicted)
        actuals.append(actual)
        predictions.append(
            {
                "node_id": node_id,
                "stands_for": entry.get("stands_for", ""),
                "predicted": round(predicted, _PRECISION),
                "actual": actual,
                "squared_error": round((predicted - actual) ** 2, _PRECISION),
            }
        )

    score = round(brier_score(preds, actuals), _PRECISION)

    def _rel(path: str | Path) -> str:
        resolved = Path(path).resolve()
        try:
            return resolved.relative_to(ROOT).as_posix()
        except ValueError:
            # path lives outside the repo (e.g. a tmp fixture in a test)
            return resolved.as_posix()

    return {
        "backtest_id": "covid_2020_supply_shock",
        "scenario_id": scenario["scenario_id"],
        "graph": _rel(graph_path),
        "scenario": _rel(scenario_path),
        "outcomes": _rel(outcomes_path),
        "severity": severity,
        "n_outcomes": len(preds),
        "brier_score": score,
        "threshold": threshold,
        "predictions": sorted(predictions, key=lambda p: p["node_id"]),
        "notes": (
            "computed by eval/backtest_2020_covid.py from the fixture graph, the "
            "covid_2020 scenario, and cited outcomes; not a hardcoded value. see "
            "eval/covid_2020_outcomes.yaml for citations and caveats."
        ),
    }


def main() -> int:
    result = run_backtest()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}")
    print(f"brier_score={result['brier_score']:.4f} over {result['n_outcomes']} cited outcomes")
    print(f"threshold={result['threshold']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
