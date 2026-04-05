from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models.sales.sales_funnel import FunnelEntityTypeEnum
from app.services.sales.funnel_state_machine import FunnelStateMachine


def test_coerce_entity_type_accepts_case_insensitive_string():
    assert FunnelStateMachine._coerce_entity_type("lead") == FunnelEntityTypeEnum.LEAD
    assert FunnelStateMachine._coerce_entity_type("OPPORTUNITY") == FunnelEntityTypeEnum.OPPORTUNITY


def test_coerce_entity_type_rejects_invalid_value():
    with pytest.raises(ValueError):
        FunnelStateMachine._coerce_entity_type("unknown")


def test_transition_accepts_string_entity_type_when_skipping_gate_validation(monkeypatch):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    state_machine = FunnelStateMachine(db)
    entity = SimpleNamespace(
        id=1,
        created_at=datetime(2026, 3, 1, 10, 0, 0),
        updated_at=None,
        lead_code="LD-001",
    )

    monkeypatch.setattr(state_machine, "_get_entity", lambda entity_type, entity_id: entity)
    monkeypatch.setattr(state_machine, "get_entity_stage", lambda entity_type, entity_id: "NEW")
    monkeypatch.setattr(state_machine, "_calculate_dwell_hours", lambda entity_type, entity: 6)
    monkeypatch.setattr(
        state_machine,
        "_update_entity_stage",
        lambda entity_type, entity, to_stage: None,
    )

    success, log, errors = state_machine.transition(
        entity_type="lead",
        entity_id=1,
        to_stage="QUALIFIED",
        validate_gate=False,
    )

    assert success is True
    assert errors == ["状态已从 NEW 转换为 QUALIFIED"]
    assert log is not None
    assert log.entity_type == FunnelEntityTypeEnum.LEAD.value
    assert log.from_stage == "NEW"
    assert log.to_stage == "QUALIFIED"
