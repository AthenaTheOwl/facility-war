from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT / "graphs" / "h100_bom.yaml"
DEFAULT_SCENARIO = ROOT / "scenarios" / "taiwan_substrate_90d.yaml"
DEFAULT_SCENARIOS = (
    ROOT / "scenarios" / "taiwan_substrate_90d.yaml",
    ROOT / "scenarios" / "suez_closure_30d.yaml",
    ROOT / "scenarios" / "az_drought_1in50.yaml",
)
DEFAULT_REPORT_DIR = ROOT / "reports" / "2026-Q3-h100-substrate-shock"
DEFAULT_RUN = DEFAULT_REPORT_DIR / "run.json"
DEFAULT_REPORT = DEFAULT_REPORT_DIR / "report.md"

GREEN_LIMIT = 0.30
RED_LIMIT = 0.70
FIXED_STARTED_AT = "2026-06-22T00:00:00Z"
FIXED_FINISHED_AT = "2026-06-22T00:00:00Z"


def load_document(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def canonical_json(data: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_json(path: str | Path, data: Any) -> None:
    Path(path).write_text(canonical_json(data, pretty=True), encoding="utf-8")


def graph_hash(graph: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(graph).encode("utf-8")).hexdigest()


def _schema(name: str) -> dict[str, Any]:
    return load_document(ROOT / "schemas" / name)


def _validate_schema(instance: dict[str, Any], schema_name: str, label: str) -> None:
    validator = Draft202012Validator(_schema(schema_name))
    errors = sorted(validator.iter_errors(instance), key=lambda error: error.path)
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise ValueError(f"{label} failed {schema_name}: {path}: {first.message}")


def _indices(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = {node["id"]: node for node in graph["nodes"]}
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph["edges"]:
        incoming[edge["to"]].append(edge)
        outgoing[edge["from"]].append(edge)
    return {"nodes": nodes, "incoming": incoming, "outgoing": outgoing}


def status_for_risk(risk: float) -> str:
    if risk >= RED_LIMIT:
        return "red"
    if risk >= GREEN_LIMIT:
        return "amber"
    return "green"


def _sample_distribution(spec: dict[str, Any], rng: random.Random) -> float:
    kind = spec.get("type", "fixed")
    if kind == "fixed":
        return float(spec["value"])
    if kind == "fixed_weeks":
        return float(spec["weeks"])
    if kind == "triangular":
        return float(rng.triangular(spec["low"], spec["high"], spec["mode"]))
    if kind == "choice":
        choices = spec["choices"]
        total = sum(float(choice.get("weight", 1.0)) for choice in choices)
        pick = rng.uniform(0, total)
        cursor = 0.0
        for choice in choices:
            cursor += float(choice.get("weight", 1.0))
            if pick <= cursor:
                return float(choice["value"])
        return float(choices[-1]["value"])
    raise ValueError(f"unsupported distribution type: {kind}")


def _trial_seed(seed: int, trial_index: int) -> int:
    digest = hashlib.sha256(f"{seed}:{trial_index}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _direct_risks(
    graph: dict[str, Any],
    scenario: dict[str, Any],
    active_severity: float,
) -> dict[str, float]:
    if active_severity <= 0:
        return {}

    index = _indices(graph)
    affected_geographies = set(scenario["affected_geographies"])
    affected_components = set(scenario["affected_components"])
    risks: dict[str, float] = {}

    for edge in graph["edges"]:
        if edge["type"] == "located_in" and edge["to"] in affected_geographies:
            risks[edge["from"]] = max(risks.get(edge["from"], 0.0), active_severity)

    for component_id in affected_components:
        if component_id in index["nodes"]:
            risks[component_id] = max(risks.get(component_id, 0.0), active_severity)

    return risks


def propagate_week(
    graph: dict[str, Any],
    scenario: dict[str, Any],
    active_severity: float,
    *,
    max_tier: int = 4,
) -> dict[str, Any]:
    index = _indices(graph)
    nodes = index["nodes"]
    incoming = index["incoming"]
    direct = _direct_risks(graph, scenario, active_severity)
    substitution_threshold = float(scenario.get("substitution_severity_threshold", GREEN_LIMIT))
    memo: dict[tuple[str, int], float] = {}

    def risk_for(node_id: str, depth: int, visiting: frozenset[str]) -> float:
        key = (node_id, depth)
        if key in memo:
            return memo[key]

        raw = direct.get(node_id, 0.0)
        if depth < max_tier:
            for edge in incoming.get(node_id, []):
                if edge["type"] not in {"supplies", "depends_on"}:
                    continue
                source = edge["from"]
                if source in visiting:
                    continue
                source_risk = risk_for(source, depth + 1, visiting | {node_id})
                criticality = float(edge.get("criticality", 1.0))
                raw = max(raw, min(1.0, source_risk * criticality))

        node = nodes[node_id]
        if node["type"] == "component" and raw >= GREEN_LIMIT:
            for edge in incoming.get(node_id, []):
                if edge["type"] != "substitutes_for":
                    continue
                source = edge["from"]
                substitute_risk = risk_for(source, depth + 1, visiting | {node_id})
                max_severity = float(edge.get("max_substitutable_severity", 1.0))
                if raw <= max_severity and substitute_risk < substitution_threshold:
                    raw = min(raw, float(edge.get("post_substitution_risk", 0.20)))

        memo[key] = round(raw, 6)
        return memo[key]

    node_risks = {node_id: risk_for(node_id, 0, frozenset()) for node_id in sorted(nodes)}
    component_status = {
        node_id: status_for_risk(node_risks[node_id])
        for node_id, node in sorted(nodes.items())
        if node["type"] == "component"
    }
    bom_item_status = {
        node_id: status_for_risk(node_risks[node_id])
        for node_id, node in sorted(nodes.items())
        if node["type"] == "bom_item"
    }
    return {
        "node_risks": node_risks,
        "component_status": component_status,
        "bom_item_status": bom_item_status,
    }


def run_simulation(
    graph: dict[str, Any],
    scenario: dict[str, Any],
    *,
    trial_count: int,
    seed: int,
    run_id: str | None = None,
    max_tier: int = 4,
) -> dict[str, Any]:
    if trial_count <= 0:
        raise ValueError("trial_count must be positive")

    horizon_weeks = int(scenario.get("horizon_weeks", 26))
    index = _indices(graph)
    bom_items = [
        node_id
        for node_id, node in sorted(index["nodes"].items())
        if node["type"] == "bom_item"
    ]
    outage_histograms: dict[str, Counter[int]] = {bom_item: Counter() for bom_item in bom_items}
    status_counts: dict[str, Counter[str]] = {bom_item: Counter() for bom_item in bom_items}

    for trial_index in range(trial_count):
        rng = random.Random(_trial_seed(seed, trial_index))
        duration = int(round(_sample_distribution(scenario["duration_weeks_distribution"], rng)))
        severity = float(_sample_distribution(scenario["severity_distribution"], rng))
        trial_red_weeks = {bom_item: 0 for bom_item in bom_items}

        for week in range(1, horizon_weeks + 1):
            active_severity = severity if week <= duration else 0.0
            week_result = propagate_week(
                graph,
                scenario,
                active_severity,
                max_tier=max_tier,
            )
            for bom_item, status in week_result["bom_item_status"].items():
                status_counts[bom_item][status] += 1
                if status == "red":
                    trial_red_weeks[bom_item] += 1

        for bom_item, red_weeks in trial_red_weeks.items():
            outage_histograms[bom_item][red_weeks] += 1

    distributions: dict[str, dict[str, Any]] = {}
    for bom_item in bom_items:
        histogram = {
            str(weeks): outage_histograms[bom_item][weeks]
            for weeks in sorted(outage_histograms[bom_item])
        }
        expected = sum(weeks * count for weeks, count in outage_histograms[bom_item].items()) / trial_count
        any_red = sum(count for weeks, count in outage_histograms[bom_item].items() if weeks > 0) / trial_count
        total_status = sum(status_counts[bom_item].values()) or 1
        distributions[bom_item] = {
            "outage_weeks": histogram,
            "expected_red_weeks": round(expected, 4),
            "probability_any_red_week": round(any_red, 4),
            "status_share": {
                status: round(status_counts[bom_item][status] / total_status, 4)
                for status in ("green", "amber", "red")
            },
        }

    sim_run = {
        "run_id": run_id or f"{scenario['scenario_id']}-seed-{seed}-trials-{trial_count}",
        "graph_hash": graph_hash(graph),
        "scenario_id": scenario["scenario_id"],
        "trial_count": trial_count,
        "seed": seed,
        "started_at": FIXED_STARTED_AT,
        "finished_at": FIXED_FINISHED_AT,
        "max_tier": max_tier,
        "horizon_weeks": horizon_weeks,
        "per_bom_item_distribution": distributions,
        "mitigation_candidates": _rank_mitigations(graph, scenario, distributions),
    }
    return sim_run


def _rank_mitigations(
    graph: dict[str, Any],
    scenario: dict[str, Any],
    distributions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if not distributions:
        return []

    top_bom = max(
        sorted(distributions),
        key=lambda item: distributions[item]["expected_red_weeks"],
    )
    top_expected = float(distributions[top_bom]["expected_red_weeks"])
    index = _indices(graph)
    affected_geographies = set(scenario["affected_geographies"])

    affected_supplier = None
    for edge in graph["edges"]:
        if edge["type"] == "located_in" and edge["to"] in affected_geographies:
            affected_supplier = edge["from"]
            break

    affected_component = scenario["affected_components"][0] if scenario["affected_components"] else None

    candidates = [
        {
            "mitigation_id": "dual-source-highest-geography-hit",
            "type": "dual_source",
            "target": affected_supplier or affected_component or top_bom,
            "expected_reduction_weeks": round(top_expected * 0.45, 4),
            "rationale": "adds a checked supplier outside the affected geography",
        },
        {
            "mitigation_id": "buffer-top-bom-item",
            "type": "buffer",
            "target": top_bom,
            "expected_reduction_weeks": round(min(top_expected, 4.0), 4),
            "rationale": "covers early red weeks for the most exposed bom item",
        },
    ]
    if affected_component and affected_component in index["nodes"]:
        candidates.append(
            {
                "mitigation_id": "redesign-affected-component",
                "type": "redesign",
                "target": affected_component,
                "expected_reduction_weeks": round(top_expected * 0.30, 4),
                "rationale": "moves demand away from the directly affected component",
            }
        )

    return sorted(
        candidates,
        key=lambda item: (-item["expected_reduction_weeks"], item["mitigation_id"]),
    )


def render_report(
    sim_run: dict[str, Any],
    *,
    graph_path: str | Path,
    scenario_path: str | Path,
) -> str:
    rows = []
    for bom_item, distribution in sorted(sim_run["per_bom_item_distribution"].items()):
        histogram = distribution["outage_weeks"]
        common_weeks = max(histogram, key=lambda weeks: (histogram[weeks], int(weeks)))
        rows.append(
            "| {bom} | {expected:.2f} | {prob:.2%} | {common} |".format(
                bom=bom_item,
                expected=distribution["expected_red_weeks"],
                prob=distribution["probability_any_red_week"],
                common=common_weeks,
            )
        )

    mitigation_rows = [
        "| {rank} | {kind} | {target} | {weeks:.2f} |".format(
            rank=rank,
            kind=item["type"],
            target=item["target"],
            weeks=item["expected_reduction_weeks"],
        )
        for rank, item in enumerate(sim_run["mitigation_candidates"], start=1)
    ]

    return "\n".join(
        [
            "# h100 substrate shock playthrough",
            "",
            "source files: `graphs/h100_bom.yaml`, `scenarios/taiwan_substrate_90d.yaml`, and `run.json`.",
            "",
            "## inputs",
            "",
            f"- run id: `{sim_run['run_id']}`.",
            f"- graph: `{Path(graph_path).as_posix()}`. the committed graph hash in `run.json` is `{sim_run['graph_hash']}`.",
            f"- scenario: `{Path(scenario_path).as_posix()}` with id `{sim_run['scenario_id']}`.",
            f"- trials: `{sim_run['trial_count']}`. seed: `{sim_run['seed']}`. horizon: `{sim_run['horizon_weeks']}` weeks.",
            f"- traversal cap: tier `{sim_run['max_tier']}` from each bom item to upstream nodes.",
            "",
            "## outage distribution",
            "",
            "all values in this table are read from `run.json`.",
            "",
            "| bom item | expected red weeks | chance of any red week | most common red-week count |",
            "|---|---:|---:|---:|",
            *rows,
            "",
            "## mitigation queue",
            "",
            "the simulator ranks candidates by expected red-week reduction in `run.json`.",
            "",
            "| rank | type | target | expected red-week reduction |",
            "|---:|---|---|---:|",
            *mitigation_rows,
            "",
            "## interpretation",
            "",
            "the run treats a taiwan geography shock as active for each sampled scenario week. suppliers located in `geo_taiwan` degrade first, then the tier walk carries the risk through supplies and depends_on edges. substitution edges can keep a component green when the substitute is below the scenario threshold.",
            "",
        ]
    )


def _name_lookup(graph: dict[str, Any] | None) -> dict[str, str]:
    if not graph:
        return {}
    return {node["id"]: node.get("name", node["id"]) for node in graph.get("nodes", [])}


def render_show(sim_run: dict[str, Any], *, graph: dict[str, Any] | None = None) -> str:
    """Render a human-readable ranked view of a committed simulation run."""

    names = _name_lookup(graph)

    def label(node_id: str) -> str:
        return names.get(node_id, node_id)

    distributions = sim_run.get("per_bom_item_distribution", {})
    ranked = sorted(
        distributions.items(),
        key=lambda kv: kv[1].get("expected_red_weeks", 0.0),
        reverse=True,
    )

    horizon = sim_run.get("horizon_weeks", 0)
    lines: list[str] = []
    lines.append(
        f"facility-war - supply-shock playthrough, {sim_run.get('run_id', '?')}"
    )
    lines.append(
        f"scenario {sim_run.get('scenario_id', '?')} | "
        f"{sim_run.get('trial_count', 0)} trials | seed {sim_run.get('seed', '?')} | "
        f"{horizon}-week horizon | tier walk to {sim_run.get('max_tier', '?')}"
    )
    lines.append("")
    lines.append(
        f"{len(ranked)} bom item(s), ranked by expected weeks in 'red' (supply unavailable)"
    )
    lines.append("")

    header = (
        f"{'bom item':<22} {'exp red wks':>11} {'of horizon':>11} "
        f"{'any-red prob':>13} {'red share':>10}"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for bom_id, dist in ranked:
        exp = dist.get("expected_red_weeks", 0.0)
        of_horizon = f"{exp / horizon:.0%}" if horizon else "?"
        red_share = dist.get("status_share", {}).get("red", 0.0)
        lines.append(
            f"{label(bom_id)[:22]:<22} "
            f"{exp:>10.2f}w "
            f"{of_horizon:>11} "
            f"{dist.get('probability_any_red_week', 0.0):>12.0%} "
            f"{red_share:>10.0%}"
        )

    mitigations = sim_run.get("mitigation_candidates", [])
    if mitigations:
        lines.append("")
        lines.append("mitigation queue, ranked by expected red-week reduction:")
        for rank, item in enumerate(mitigations, start=1):
            lines.append(
                f"  {rank}. {item.get('type', '?'):<11} on {label(item.get('target', '?'))} "
                f"- saves ~{item.get('expected_reduction_weeks', 0.0):.1f} red weeks "
                f"({item.get('rationale', '')})"
            )

    if ranked:
        worst_id, worst = ranked[0]
        lines.append("")
        msg = (
            f"headline: {label(worst_id)} spends ~{worst.get('expected_red_weeks', 0.0):.0f} "
            f"of {horizon} weeks unavailable under this shock"
        )
        if mitigations:
            top = mitigations[0]
            msg += (
                f"; best single move is to {top.get('type', '?')} "
                f"{label(top.get('target', '?'))} "
                f"(~{top.get('expected_reduction_weeks', 0.0):.1f} weeks back)."
            )
        else:
            msg += "."
        lines.append(msg)

    return "\n".join(lines)


def validate_default_files() -> list[str]:
    messages: list[str] = []

    graph = load_document(DEFAULT_GRAPH)
    _validate_schema(graph, "supply_graph.schema.json", DEFAULT_GRAPH.as_posix())
    _validate_graph_integrity(graph, DEFAULT_GRAPH)
    messages.append(f"ok graph {DEFAULT_GRAPH.relative_to(ROOT).as_posix()}")

    for scenario_path in DEFAULT_SCENARIOS:
        scenario = load_document(scenario_path)
        _validate_schema(scenario, "scenario.schema.json", scenario_path.as_posix())
        messages.append(f"ok scenario {scenario_path.relative_to(ROOT).as_posix()}")

    sim_run = load_document(DEFAULT_RUN)
    _validate_schema(sim_run, "sim_run.schema.json", DEFAULT_RUN.as_posix())
    messages.append(f"ok run {DEFAULT_RUN.relative_to(ROOT).as_posix()}")

    expected_run = run_simulation(
        graph,
        load_document(DEFAULT_SCENARIO),
        trial_count=sim_run["trial_count"],
        seed=sim_run["seed"],
        run_id=sim_run["run_id"],
        max_tier=sim_run["max_tier"],
    )
    if canonical_json(expected_run) != canonical_json(sim_run):
        raise ValueError("committed run.json does not match deterministic rerun")
    messages.append("ok deterministic rerun")

    if not DEFAULT_REPORT.exists():
        raise ValueError(f"missing report: {DEFAULT_REPORT}")
    report_text = DEFAULT_REPORT.read_text(encoding="utf-8")
    for required in (sim_run["run_id"], sim_run["scenario_id"], "outage distribution"):
        if required not in report_text:
            raise ValueError(f"report missing required text: {required}")
    messages.append(f"ok report {DEFAULT_REPORT.relative_to(ROOT).as_posix()}")
    return messages


def _validate_graph_integrity(graph: dict[str, Any], path: Path) -> None:
    node_ids = [node["id"] for node in graph["nodes"]]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError(f"{path}: duplicate node id")
    node_set = set(node_ids)
    for edge in graph["edges"]:
        if edge["from"] not in node_set:
            raise ValueError(f"{path}: edge source missing: {edge['from']}")
        if edge["to"] not in node_set:
            raise ValueError(f"{path}: edge target missing: {edge['to']}")
