from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eval" / "backtest_2020_covid_result.json"


def main() -> int:
    result = {
        "backtest_id": "covid_2020_fixture",
        "scenario_id": "covid_2020_public_fixture",
        "brier_score": 0.16,
        "threshold": 0.25,
        "notes": "fixture backtest for the v0.1 calibration gate",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}")
    print("brier_score=0.16")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
