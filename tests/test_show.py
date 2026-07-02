from __future__ import annotations

from facility_war.cli import main
from facility_war.simulator import (
    DEFAULT_GRAPH,
    DEFAULT_RUN,
    load_document,
    render_show,
)


def test_render_show_is_readable() -> None:
    run = load_document(DEFAULT_RUN)
    graph = load_document(DEFAULT_GRAPH)
    text = render_show(run, graph=graph)

    # human-readable, not a raw json dump
    assert "{" not in text
    assert "supply-shock playthrough" in text
    # uses the graph name, not the raw node id
    assert "h100 accelerator" in text
    assert "bom_h100_accelerator" not in text
    # surfaces the ranked mitigation queue and a headline
    assert "mitigation queue" in text
    assert "headline:" in text
    # pin the derived numbers so drift in the of-horizon percent (13.0/26)
    # or the headline weeks-back figure is caught. the whole data row is
    # pinned because the of-horizon "50%" shares its digits with the red-share
    # column, so a positional literal is what actually bites.
    assert (
        "h100 accelerator            13.00w         50%         100%        50%"
        in text
    )
    assert "(~5.8 weeks back)." in text


def test_show_command_exits_zero(capsys) -> None:
    rc = main(["show"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "facility-war" in out
    assert "headline:" in out


def test_show_missing_run_errors() -> None:
    import pytest

    with pytest.raises(SystemExit):
        main(["show", "--run", "does/not/exist.json"])
