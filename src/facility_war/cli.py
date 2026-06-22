from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .simulator import (
    DEFAULT_GRAPH,
    DEFAULT_REPORT_DIR,
    DEFAULT_SCENARIO,
    load_document,
    render_report,
    run_simulation,
    validate_default_files,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="facility-war")
    parser.add_argument("--version", action="version", version=f"facility-war {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="validate committed schemas, fixtures, scenarios, run json, and report",
    )
    validate_parser.set_defaults(func=_validate)

    run_parser = subparsers.add_parser("run", help="run a deterministic scenario playthrough")
    run_parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    run_parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    run_parser.add_argument("--trials", type=int, default=1000)
    run_parser.add_argument("--seed", type=int, default=42)
    run_parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_DIR)
    run_parser.add_argument("--run-id", default="2026-Q3-h100-substrate-shock")
    run_parser.set_defaults(func=_run)

    return parser


def _validate(_args: argparse.Namespace) -> int:
    messages = validate_default_files()
    for message in messages:
        print(message)
    print("validation passed")
    return 0


def _run(args: argparse.Namespace) -> int:
    graph = load_document(args.graph)
    scenario = load_document(args.scenario)
    sim_run = run_simulation(
        graph,
        scenario,
        trial_count=args.trials,
        seed=args.seed,
        run_id=args.run_id,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_json(args.out / "run.json", sim_run)
    (args.out / "report.md").write_text(
        render_report(sim_run, graph_path=args.graph, scenario_path=args.scenario),
        encoding="utf-8",
    )
    print(f"wrote {args.out / 'run.json'}")
    print(f"wrote {args.out / 'report.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
