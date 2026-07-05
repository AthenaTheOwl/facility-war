from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
# eval/ is a set of scripts, not a package; expose it so the calibration
# backtest and gate can be imported directly in tests.
sys.path.insert(0, str(ROOT / "eval"))
