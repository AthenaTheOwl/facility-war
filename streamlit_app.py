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

import json
from pathlib import Path

import streamlit as st
import yaml

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

st.caption(
    "v0.1 ships one h100 substrate-shock fixture run. the simulator lives in "
    "`facility_war/`; this page reads the committed `reports/*/run.json` + graph. "
    "repo: github.com/AthenaTheOwl/facility-war"
)
