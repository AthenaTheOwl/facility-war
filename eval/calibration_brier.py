"""Calibration gate: fail when the COVID-2020 backtest is missing or too weak.

Contract (a gate that can actually fail):

  * If the backtest result file does not exist -> FAIL (exit 1). There is no
    silent fallback to a hardcoded score. Run eval/backtest_2020_covid.py first.
  * If the committed result does not match a fresh recompute from the fixtures
    -> FAIL. This stops anyone from hand-editing brier_score to sneak past.
  * If the Brier score exceeds --max-brier -> FAIL.
  * Otherwise pass (exit 0).

The old version returned 0.16 whenever the result file was absent, so the gate
could never fail. It can now.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_EVAL = str(ROOT / "eval")
if _EVAL not in sys.path:
    sys.path.insert(0, _EVAL)

from backtest_2020_covid import (  # noqa: E402
    DEFAULT_GRAPH,
    DEFAULT_OUTCOMES,
    DEFAULT_SCENARIO,
    run_backtest,
)

RESULT = ROOT / "eval" / "backtest_2020_covid_result.json"
_TOLERANCE = 1e-6


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="COVID-2020 Brier calibration gate")
    parser.add_argument("--max-brier", type=float, default=0.25)
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--outcomes", type=Path, default=DEFAULT_OUTCOMES)
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="skip the recompute-and-compare integrity check",
    )
    args = parser.parse_args(argv)

    if not args.result.is_file():
        print(f"no backtest result at {args.result} - run eval/backtest_2020_covid.py first")
        print("calibration failed")
        return 1

    result = json.loads(args.result.read_text(encoding="utf-8"))
    try:
        score = float(result["brier_score"])
    except (KeyError, TypeError, ValueError):
        print(f"backtest result at {args.result} has no numeric brier_score")
        print("calibration failed")
        return 1

    if not args.no_verify:
        recomputed = run_backtest(args.graph, args.scenario, args.outcomes)["brier_score"]
        if abs(recomputed - score) > _TOLERANCE:
            print(
                f"committed brier_score={score:.6f} does not match recompute "
                f"{recomputed:.6f} from the fixtures - result is stale or edited"
            )
            print("calibration failed")
            return 1

    print(f"brier_score={score:.4f}")
    print(f"max_brier={args.max_brier:.4f}")
    if score > args.max_brier:
        print("calibration failed")
        return 1
    print("calibration passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
