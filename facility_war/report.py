from __future__ import annotations

from pathlib import Path
from typing import Any

from .simulator import render_report as render_markdown_report


def write_report(run: dict[str, Any], out_dir: Path) -> Path:
    """Write the markdown report for a completed scenario run."""

    out_dir.mkdir(parents=True, exist_ok=True)
    graph_path = str(run.get("graph_path", "graphs/h100_bom.yaml"))
    scenario_path = str(run.get("scenario_path", "scenarios/taiwan_substrate_90d.yaml"))
    path = out_dir / "report.md"
    path.write_text(
        render_markdown_report(run, graph_path=graph_path, scenario_path=scenario_path),
        encoding="utf-8",
    )
    return path

