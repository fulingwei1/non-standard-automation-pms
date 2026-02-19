# -*- coding: utf-8 -*-
"""第四十二批：ecn_bom_analysis_service/calculation.py 单元测试"""
import pytest

pytest.importorskip("app.services.ecn_bom_analysis_service.calculation")

from decimal import Decimal
from unittest.mock import MagicMock
from app.services.ecn_bom_analysis_service.calculation import (
    calculate_cost_impact,
    calculate_schedule_impact,
)


def make_service():
    svc = MagicMock()
    return svc


def make_affected_mat(cost_impact=None, change_type="UPDATE", material_code="M001", material_id=None):
    m = MagicMock()
    m.cost_impact = cost_impact
    m.change_type = change_type
    m.material_code = material_code
    m.material_id = material_id
    return m


def make_bom_item(item_id=1, material_code="M001", material_id=None, amount=None):
    b = MagicMock()
    b.id = item_id
    b.material_code = material_code
    b.material_id = material_id
    b.amount = amount
    return b


# ------------------------------------------------------------------ tests ---

def test_calculate_cost_impact_zero_when_empty():
    svc = make_service()
    result = calculate_cost_impact(svc, [], [], set())
    assert result == Decimal(0)


def test_calculate_cost_impact_adds_from_affected_materials():
    svc = make_service()
    mat = make_affected_mat(cost_impact=Decimal("500.00"))
    result = calculate_cost_impact(svc, [mat], [], set())
    assert result == Decimal("500.00")


def test_calculate_cost_impact_delete_subtracts_amount():
    svc = make_service()
    mat = make_affected_mat(cost_impact=None, change_type="DELETE", material_code="M001")
    item = make_bom_item(item_id=10, material_code="M001", amount=Decimal("200.00"))
    result = calculate_cost_impact(svc, [mat], [item], {10})
    assert result < Decimal(0)


def test_calculate_cost_impact_add_type():
    svc = make_service()
    mat = make_affected_mat(cost_impact=Decimal("300"), change_type="ADD", material_code="M002")
    item = make_bom_item(item_id=20, material_code="M002", amount=Decimal("100"))
    result = calculate_cost_impact(svc, [mat], [item], {20})
    # ADD: cost_impact is used
    assert result >= Decimal("300")


def test_calculate_schedule_impact_zero_when_no_items():
    svc = make_service()
    result = calculate_schedule_impact(svc, [], [], set())
    assert result == 0


def test_calculate_schedule_impact_update_uses_lead_time():
    svc = make_service()
    mat = make_affected_mat(change_type="UPDATE", material_code="M001")
    item = make_bom_item(item_id=5, material_code="M001")
    material = MagicMock()
    material.lead_time_days = 30
    svc.db.query.return_value.filter.return_value.first.return_value = material
    result = calculate_schedule_impact(svc, [mat], [item], {5})
    assert result == 30


def test_calculate_schedule_impact_delete_not_counted():
    svc = make_service()
    mat = make_affected_mat(change_type="DELETE", material_code="M001")
    item = make_bom_item(item_id=5, material_code="M001")
    material = MagicMock()
    material.lead_time_days = 30
    svc.db.query.return_value.filter.return_value.first.return_value = material
    result = calculate_schedule_impact(svc, [mat], [item], {5})
    # DELETE is not in ['UPDATE', 'REPLACE', 'ADD']
    assert result == 0
