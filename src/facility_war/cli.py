from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from . import __version__
from .simulator import (
    DEFAULT_GRAPH,
    DEFAULT_REPORT_DIR,
    DEFAULT_RUN,
    DEFAULT_SCENARIO,
    load_document,
    render_report,
    render_show,
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

    show_parser = subparsers.add_parser(
        "show",
        help="print a readable ranked view of the committed run (no args needed)",
    )
    show_parser.add_argument(
        "--run",
        type=Path,
        default=DEFAULT_RUN,
        help="path to a run.json (default: the committed h100 substrate-shock run)",
    )
    show_parser.add_argument(
        "--graph",
        type=Path,
        default=DEFAULT_GRAPH,
        help="path to the bom graph used for human-readable node names",
    )
    show_parser.set_defaults(func=_show)

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


def _show(args: argparse.Namespace) -> int:
    if not args.run.is_file():
        raise SystemExit(
            f"no run found at {args.run} - run `python -m facility_war run` first"
        )
    sim_run = load_document(args.run)
    graph = load_document(args.graph) if args.graph.is_file() else None
    print(render_show(sim_run, graph=graph))
    return 0


def _run(args: argparse.Namespace) -> int:
    # A path typo is the mainline mistake here, so name the input and what
    # was expected rather than surfacing a raw traceback from load_document.
    for label, path in (("graph", args.graph), ("scenario", args.scenario)):
        if not path.is_file():
            raise SystemExit(f"no {label} file at {path} - expected a readable yaml file")
    try:
        graph = load_document(args.graph)
        scenario = load_document(args.scenario)
    except (OSError, yaml.YAMLError) as error:
        raise SystemExit(f"could not read graph/scenario yaml: {error}")
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
