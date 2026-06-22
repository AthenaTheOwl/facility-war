from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from facility_war.simulator import validate_default_files  # noqa: E402


def main() -> int:
    for message in validate_default_files():
        print(message)
    print("schema validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
