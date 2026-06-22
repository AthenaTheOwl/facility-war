# product brief

facility-war v0.1 ships one checked playthrough: a public h100 bom
fixture under a taiwan substrate shock scenario. the useful artifact is
the committed run record and the report that explains which bom items
turn red by week.

the first user action is:

```bash
python -m facility_war validate
```

that command validates the graph schema, the three scenario specs, the
committed simulation run, and the markdown report. it also reruns the
taiwan scenario with the committed seed and checks that the run record
matches.

the simulator is intentionally small. it uses an explicit seed, a fixed
run timestamp, tier-n traversal capped at tier 4, geography shocks, and
substitution edges.
