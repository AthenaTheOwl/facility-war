"""facility-war — live demo (Streamlit Community Cloud).

Reads the committed run under reports/2026-Q3-h100-substrate-shock/run.json and
shows the same result the `python -m facility_war show` verb prints: which bom
item spends the most weeks 'red' (supply unavailable) under a supply shock, and
the mitigation queue ranked by how many red weeks each fix buys back.

No network, no secrets — runs entirely off the committed fixture run + graph.

Deploy: Streamlit Community Cloud -> New app -> repo AthenaTheOwl/facility-war,
branch main, main file streamlit_app.py.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import streamlit as st
import yaml

from facility_war.simulator import (
    DEFAULT_GRAPH,
    DEFAULT_SCENARIO,
    load_document,
    run_simulation,
)

REPO = Path(__file__).resolve().parent
RUN = REPO / "reports" / "2026-Q3-h100-substrate-shock" / "run.json"
GRAPH = REPO / "graphs" / "h100_bom.yaml"


def load_run() -> dict | None:
    if not RUN.is_file():
        return None
    return json.loads(RUN.read_text(encoding="utf-8"))


def load_names() -> dict[str, str]:
    """node id -> human-readable name, same lookup the show verb uses."""
    if not GRAPH.is_file():
        return {}
    graph = yaml.safe_load(GRAPH.read_text(encoding="utf-8")) or {}
    return {n["id"]: n.get("name", n["id"]) for n in graph.get("nodes", [])}


st.set_page_config(page_title="facility-war — supply-shock playthrough", layout="wide")
st.title("facility-war")
st.caption(
    "deterministic supply-shock playthrough: which bom item idles the longest "
    "under a shock, and the cheapest fix that buys back the most red weeks."
)

run = load_run()
if not run:
    st.warning("no committed run found under reports/*/run.json")
    st.stop()

names = load_names()


def label(node_id: str) -> str:
    return names.get(node_id, node_id)


horizon = run.get("horizon_weeks", 0)
distributions = run.get("per_bom_item_distribution", {})
ranked = sorted(
    distributions.items(),
    key=lambda kv: kv[1].get("expected_red_weeks", 0.0),
    reverse=True,
)
mitigations = run.get("mitigation_candidates", [])

st.subheader(
    f"{run.get('scenario_id', '?')} — {run.get('run_id', '?')}"
)
st.caption(
    f"{run.get('trial_count', 0):,} trials | seed {run.get('seed', '?')} | "
    f"{horizon}-week horizon | tier walk to {run.get('max_tier', '?')}"
)

worst_red = ranked[0][1].get("expected_red_weeks", 0.0) if ranked else 0.0
top_saving = (
    mitigations[0].get("expected_reduction_weeks", 0.0) if mitigations else 0.0
)

c1, c2, c3 = st.columns(3)
c1.metric("bom items modeled", f"{len(ranked)}")
c2.metric(
    "worst expected red weeks",
    f"{worst_red:.1f}w",
    help=f"of a {horizon}-week horizon",
)
c3.metric(
    "best single fix",
    f"-{top_saving:.1f}w",
    help="red weeks bought back by the top-ranked mitigation",
)

# --- ranked bom table (mirrors the show verb's table) -----------------------
st.markdown("##### bom items, ranked by expected weeks 'red' (supply unavailable)")
bom_rows = []
for bom_id, dist in ranked:
    exp = dist.get("expected_red_weeks", 0.0)
    bom_rows.append(
        {
            "bom item": label(bom_id),
            "exp red weeks": round(exp, 2),
            "of horizon": f"{exp / horizon:.0%}" if horizon else "?",
            "any-red prob": f"{dist.get('probability_any_red_week', 0.0):.0%}",
            "red share": f"{dist.get('status_share', {}).get('red', 0.0):.0%}",
        }
    )
st.dataframe(bom_rows, use_container_width=True, hide_index=True)

# --- mitigation queue with one interactive control --------------------------
st.markdown("##### mitigation queue, ranked by expected red-week reduction")
if mitigations:
    max_saving = max(m.get("expected_reduction_weeks", 0.0) for m in mitigations)
    min_saving = st.slider(
        "minimum red weeks saved",
        0.0,
        float(round(max_saving, 1)) or 1.0,
        0.0,
        step=0.1,
        help="filter the mitigation queue to fixes that buy back at least this many red weeks",
    )
    shown = [
        m for m in mitigations
        if m.get("expected_reduction_weeks", 0.0) >= min_saving
    ]
    st.dataframe(
        [
            {
                "rank": i,
                "type": m.get("type", "?"),
                "target": label(m.get("target", "?")),
                "red weeks saved": round(m.get("expected_reduction_weeks", 0.0), 2),
                "rationale": m.get("rationale", ""),
            }
            for i, m in enumerate(shown, start=1)
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("no mitigation candidates in this run.")

# --- headline callout (same insight as the show verb) -----------------------
if ranked:
    worst_id, worst = ranked[0]
    msg = (
        f"**headline:** {label(worst_id)} spends ~{worst.get('expected_red_weeks', 0.0):.0f} "
        f"of {horizon} weeks unavailable under this shock"
    )
    if mitigations:
        top = mitigations[0]
        msg += (
            f"; best single move is to **{top.get('type', '?')}** "
            f"{label(top.get('target', '?'))} "
            f"(~{top.get('expected_reduction_weeks', 0.0):.1f} weeks back)."
        )
    else:
        msg += "."
    st.info(msg)

# --- interactive: drive the real simulator on your own scenario -------------
st.divider()
st.header("war-game your own shock")
st.caption(
    "this section does not read the committed run. it builds a scenario from your "
    "inputs and calls the real monte-carlo engine "
    "(`facility_war.simulator.run_simulation`) live against the committed h100 bom "
    "graph — the same function that produced `run.json`."
)


@st.cache_data(show_spinner=False)
def load_graph_doc() -> dict:
    return load_document(DEFAULT_GRAPH)


@st.cache_data(show_spinner=False)
def base_scenario() -> dict:
    return load_document(DEFAULT_SCENARIO)


try:
    graph_doc = load_graph_doc()
    base = base_scenario()
except Exception as exc:  # pragma: no cover - surfaced in the UI
    st.error(f"could not load graph/scenario fixtures: {exc}")
    st.stop()

geo_nodes = [n["id"] for n in graph_doc.get("nodes", []) if n.get("type") == "geography"]
cmp_nodes = [n["id"] for n in graph_doc.get("nodes", []) if n.get("type") == "component"]


def node_label(node_id: str) -> str:
    return f"{label(node_id)} ({node_id})"


with st.form("scenario_form"):
    fc1, fc2 = st.columns(2)
    with fc1:
        geo = st.selectbox(
            "affected geography (the shock origin)",
            geo_nodes,
            index=geo_nodes.index("geo_taiwan") if "geo_taiwan" in geo_nodes else 0,
            format_func=node_label,
            help="suppliers located here degrade first; risk then walks upstream",
        )
        comp = st.selectbox(
            "directly affected component",
            cmp_nodes,
            index=cmp_nodes.index("cmp_advanced_package") if "cmp_advanced_package" in cmp_nodes else 0,
            format_func=node_label,
        )
        severity = st.slider(
            "shock severity",
            0.0,
            1.0,
            0.92,
            step=0.01,
            help="risk injected at the affected nodes. red kicks in at 0.70, amber at 0.30.",
        )
    with fc2:
        horizon = st.slider("horizon (weeks)", 4, 52, int(base.get("horizon_weeks", 26)))
        duration = st.slider(
            "shock duration (weeks active)",
            1,
            52,
            13,
            help="how many of the horizon weeks the shock is live",
        )
        sub_threshold = st.slider(
            "substitution severity threshold",
            0.0,
            1.0,
            float(base.get("substitution_severity_threshold", 0.30)),
            step=0.01,
            help="below this, a checked substitute can keep a component out of red",
        )

    fc3, fc4, fc5 = st.columns(3)
    trials = fc3.slider("trials", 50, 2000, 300, step=50)
    seed = fc4.number_input("seed", min_value=0, value=42, step=1)
    max_tier = fc5.slider("tier walk depth", 1, 6, int(run.get("max_tier", 4)))

    submitted = st.form_submit_button("run simulation", type="primary")

if submitted:
    scenario = copy.deepcopy(base)
    scenario["scenario_id"] = f"custom_{geo}_{comp}_sev{int(severity * 100)}"
    scenario["horizon_weeks"] = int(horizon)
    scenario["affected_geographies"] = [geo]
    scenario["affected_components"] = [comp]
    scenario["severity_distribution"] = {"type": "fixed", "value": float(severity)}
    scenario["duration_weeks_distribution"] = {
        "type": "fixed_weeks",
        "weeks": int(min(duration, horizon)),
    }
    scenario["substitution_severity_threshold"] = float(sub_threshold)

    with st.spinner(f"running {trials} trials of the real engine..."):
        live = run_simulation(
            graph_doc,
            scenario,
            trial_count=int(trials),
            seed=int(seed),
            max_tier=int(max_tier),
        )

    live_dists = live.get("per_bom_item_distribution", {})
    live_ranked = sorted(
        live_dists.items(),
        key=lambda kv: kv[1].get("expected_red_weeks", 0.0),
        reverse=True,
    )
    live_mit = live.get("mitigation_candidates", [])
    live_worst = live_ranked[0][1].get("expected_red_weeks", 0.0) if live_ranked else 0.0
    live_top_save = live_mit[0].get("expected_reduction_weeks", 0.0) if live_mit else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("bom items modeled", f"{len(live_ranked)}")
    m2.metric(
        "worst expected red weeks",
        f"{live_worst:.1f}w",
        delta=f"{live_worst - worst_red:+.1f}w vs committed run",
        help=f"of a {horizon}-week horizon",
    )
    m3.metric(
        "best single fix",
        f"-{live_top_save:.1f}w",
        help="red weeks bought back by the top-ranked mitigation",
    )

    st.markdown("##### your run — bom items ranked by expected red weeks")
    st.dataframe(
        [
            {
                "bom item": label(bom_id),
                "exp red weeks": round(dist.get("expected_red_weeks", 0.0), 2),
                "of horizon": f"{dist.get('expected_red_weeks', 0.0) / horizon:.0%}" if horizon else "?",
                "any-red prob": f"{dist.get('probability_any_red_week', 0.0):.0%}",
                "red share": f"{dist.get('status_share', {}).get('red', 0.0):.0%}",
            }
            for bom_id, dist in live_ranked
        ],
        use_container_width=True,
        hide_index=True,
    )

    if live_mit:
        st.markdown("##### your run — mitigation queue")
        st.dataframe(
            [
                {
                    "rank": i,
                    "type": m.get("type", "?"),
                    "target": label(m.get("target", "?")),
                    "red weeks saved": round(m.get("expected_reduction_weeks", 0.0), 2),
                    "rationale": m.get("rationale", ""),
                }
                for i, m in enumerate(live_mit, start=1)
            ],
            use_container_width=True,
            hide_index=True,
        )

    if live_ranked:
        w_id, w = live_ranked[0]
        if live_worst <= 0:
            st.success(
                "no bom item ever reaches 'red' under this scenario — the shock stays "
                "below the 0.70 red threshold after the tier walk and substitution."
            )
        else:
            note = (
                f"**your headline:** {label(w_id)} spends ~{w.get('expected_red_weeks', 0.0):.0f} "
                f"of {horizon} weeks unavailable"
            )
            if live_mit:
                t = live_mit[0]
                note += (
                    f"; best single move is to **{t.get('type', '?')}** "
                    f"{label(t.get('target', '?'))} "
                    f"(~{t.get('expected_reduction_weeks', 0.0):.1f} weeks back)."
                )
            st.info(note)
    st.caption(f"run_id: `{live.get('run_id', '?')}` | graph_hash: `{live.get('graph_hash', '?')[:16]}...`")
else:
    st.caption("set your scenario above and press **run simulation** to drive the engine live.")

st.caption(
    "v0.1 ships one h100 substrate-shock fixture run, then lets you re-run the real "
    "simulator on your own scenario. the engine lives in `facility_war/simulator.py`; "
    "the committed view above reads `reports/*/run.json`. "
    "repo: github.com/AthenaTheOwl/facility-war"
)
