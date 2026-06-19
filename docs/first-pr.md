# First PR after the scaffold

Branch: `feat/0001-graph-schema`

## Scope

Land the package skeleton, the supply-graph JSON schema, the
in-memory loader, and one tiny fixture graph the rest of the spec can
exercise.

### Files added

- `pyproject.toml` — declares `facility-war`, CLI entry
  `facility-war = "facility_war.cli:main"`, dev deps (pytest,
  jsonschema, pyyaml, numpy, click).
- `src/facility_war/__init__.py` — `__version__ = "0.0.1"`.
- `src/facility_war/cli.py` — Click app, single `version` command.
- `src/facility_war/graph/__init__.py`
- `src/facility_war/graph/schema.py` — dataclasses for `Supplier`,
  `Component`, `BomItem`, `Geography`, and the edge enum.
- `src/facility_war/graph/loader.py` — `load_graph(path)` reads JSON
  or YAML, validates against `schemas/supply_graph.schema.json`,
  returns a `SupplyGraph`.
- `schemas/supply_graph.schema.json` — node and edge types per
  R-FW-002.
- `tests/fixtures/graphs/tiny_h100.json` — 8 nodes, 9 edges,
  hand-built so a propagation test in PR 2 can hand-check results.
- `tests/test_graph_loader.py` — three tests: schema-valid input
  loads, schema-invalid input raises, round-trip preserves structure.
- `decisions/DEC-FW-001-graph-schema.md` — names the four node types
  and four edge types, explains the derivation from
  chip-supply-chain-map.

### Files NOT touched

- `scenarios/` — empty until PR 2.
- `src/facility_war/sim/` — empty until PR 2.
- `reports/` — empty until PR 3.
- `eval/` — empty until PR 3.

## Verification

```bash
uv pip install -e .[dev]
python -m facility_war version
# expect: facility-war 0.0.1

uv run pytest
# expect: 3 tests in tests/test_graph_loader.py pass

python -c "
from facility_war.graph.loader import load_graph
g = load_graph('tests/fixtures/graphs/tiny_h100.json')
print(f'{len(g.nodes)} nodes, {len(g.edges)} edges')
"
# expect: 8 nodes, 9 edges
```

## Out of scope for this PR

- The scenario engine.
- Any Monte Carlo code.
- The report renderer.
- The voice_lint script.
- Any backtest or calibration code.
