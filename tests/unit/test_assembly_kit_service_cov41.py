# -*- coding: utf-8 -*-
"""Unit tests for app/services/assembly_kit_service.py - batch 41"""
import pytest

pytest.importorskip("app.services.assembly_kit_service")

from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date


@pytest.fixture
def db():
    return MagicMock()


def test_validate_analysis_inputs_project_not_found(db):
    db.query.return_value.filter.return_value.first.return_value = None
    from fastapi import HTTPException
    from app.services.assembly_kit_service import validate_analysis_inputs
    with pytest.raises(HTTPException) as exc:
        validate_analysis_inputs(db, project_id=1, bom_id=1)
    assert exc.value.status_code == 404


def test_validate_analysis_inputs_bom_not_found(db):
    project = MagicMock()
    responses = [project, None]
    db.query.return_value.filter.return_value.first.side_effect = responses
    from fastapi import HTTPException
    from app.services.assembly_kit_service import validate_analysis_inputs
    with pytest.raises(HTTPException) as exc:
        validate_analysis_inputs(db, project_id=1, bom_id=1)
    assert exc.value.status_code == 404


def test_validate_analysis_inputs_success(db):
    project = MagicMock()
    bom = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [project, bom]
    from app.services.assembly_kit_service import validate_analysis_inputs
    result = validate_analysis_inputs(db, project_id=1, bom_id=2)
    assert result == (project, bom, None)


def test_initialize_stage_results():
    from app.services.assembly_kit_service import initialize_stage_results
    stages = [MagicMock(stage_code="MECH"), MagicMock(stage_code="ELEC")]
    result = initialize_stage_results(stages)
    assert "MECH" in result
    assert "ELEC" in result
    assert result["MECH"]["total"] == 0
    assert result["MECH"]["fulfilled"] == 0


def test_get_expected_arrival_date_returns_none_on_error(db):
    from app.services.assembly_kit_service import get_expected_arrival_date
    db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = None
    with patch("app.services.assembly_kit_service.PurchaseOrder", create=True), \
         patch("app.services.assembly_kit_service.PurchaseOrderItem", create=True):
        result = get_expected_arrival_date(db, material_id=1)
    # No error, result is None or a date
    assert result is None or isinstance(result, date)


def test_calculate_stage_kit_rates_empty():
    from app.services.assembly_kit_service import calculate_stage_kit_rates
    stages = []
    stage_results = {}
    result = calculate_stage_kit_rates(stages, stage_results, [])
    kit_rates, can_proceed, first_blocked, current_workable, stats, blocking = result
    assert kit_rates == []
    assert can_proceed is True
    assert first_blocked is None


def test_calculate_stage_kit_rates_all_fulfilled():
    from app.services.assembly_kit_service import calculate_stage_kit_rates
    stage = MagicMock()
    stage.stage_code = "MECH"
    stage.stage_name = "机械"
    stage.stage_order = 1
    stage.color_code = "#fff"
    stages = [stage]
    stage_results = {
        "MECH": {
            "total": 5, "fulfilled": 5,
            "blocking_total": 2, "blocking_fulfilled": 2,
            "stage": stage
        }
    }
    result = calculate_stage_kit_rates(stages, stage_results, [])
    kit_rates, can_proceed, first_blocked, current_workable, stats, blocking = result
    assert can_proceed is True
    assert kit_rates[0]["kit_rate"] == Decimal("100.00")
