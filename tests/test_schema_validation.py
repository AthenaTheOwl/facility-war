from __future__ import annotations

from facility_war.simulator import validate_default_files


def test_default_validation_passes() -> None:
    messages = validate_default_files()

    assert "ok deterministic rerun" in messages
    assert any(message.endswith("graphs/h100_bom.yaml") for message in messages)
