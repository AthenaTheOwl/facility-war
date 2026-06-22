from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BANNED_FAIL = [
    "best-in-class",
    "breakthrough",
    "cutting edge",
    "game changing",
    "next generation",
    "revolutionary",
    "seamless",
    "world class",
]

SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "PRODUCT_BRIEF.md",
    ROOT / "SYSTEM_MAP.md",
    ROOT / "STATUS.md",
    ROOT / "reports",
    ROOT / "specs" / "0002-design",
]


def _iter_markdown_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    if path.is_file():
        return [path]
    return sorted(item for item in path.rglob("*.md") if item.is_file())


def main() -> int:
    failures: list[str] = []
    for scan_path in SCAN_PATHS:
        for path in _iter_markdown_files(scan_path):
            text = path.read_text(encoding="utf-8").lower()
            for term in BANNED_FAIL:
                if re.search(rf"\b{re.escape(term)}\b", text):
                    failures.append(f"{path.relative_to(ROOT).as_posix()}: banned term: {term}")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print("voice lint passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
