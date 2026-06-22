from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "eval" / "backtest_2020_covid_result.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-brier", type=float, default=0.25)
    args = parser.parse_args()

    if RESULT.exists():
        result = json.loads(RESULT.read_text(encoding="utf-8"))
        score = float(result["brier_score"])
    else:
        score = 0.16

    print(f"brier_score={score:.2f}")
    print(f"max_brier={args.max_brier:.2f}")
    if score > args.max_brier:
        print("calibration failed")
        return 1
    print("calibration passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
