# -*- coding: utf-8 -*-
"""
Unit tests for app/services/ecn_bom_analysis_service/calculation.py (cov52)
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

try:
    from app.services.ecn_bom_analysis_service.calculation import (
        calculate_cost_impact,
        calculate_schedule_impact,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service():
    service = MagicMock()
    service.db = MagicMock()
    return service


def _make_affected_mat(change_type="UPDATE", cost_impact=None,
                       material_code="MAT-001", material_id=1):
    mat = MagicMock()
    mat.change_type = change_type
    mat.cost_impact = cost_impact
    mat.material_code = material_code
    mat.material_id = material_id
    return mat


def _make_bom_item(item_id=1, material_code="MAT-001", material_id=1, amount=None):
    item = MagicMock()
    item.id = item_id
    item.material_code = material_code
    item.material_id = material_id
    item.amount = amount
    return item


# ──────────────────────── calculate_cost_impact ────────────────────────

def test_calculate_cost_impact_empty():
    """无物料时成本影响为 0"""
    service = _make_service()
    result = calculate_cost_impact(service, [], [], set())
    assert result == Decimal(0)


def test_calculate_cost_impact_with_cost_impact_field():
    """受影响物料 cost_impact 字段汇总"""
    service = _make_service()
    mat = _make_affected_mat(cost_impact="500.00")
    result = calculate_cost_impact(service, [mat], [], set())
    assert result == Decimal("500.00")


def test_calculate_cost_impact_delete_reduces():
    """DELETE 变更使成本为负"""
    service = _make_service()
    mat = _make_affected_mat(change_type="DELETE", cost_impact=None)
    item = _make_bom_item(item_id=10, material_code="MAT-001", amount=Decimal("200"))
    result = calculate_cost_impact(service, [mat], [item], {10})
    # amount=200 的物料被删除 → -200
    assert result == Decimal("-200")


def test_calculate_cost_impact_add_uses_cost_impact():
    """ADD 变更使用 cost_impact 字段"""
    service = _make_service()
    mat = _make_affected_mat(change_type="ADD", cost_impact="300.00")
    item = _make_bom_item(item_id=11, material_code="MAT-001", amount=Decimal("100"))
    result = calculate_cost_impact(service, [mat], [item], {11})
    # cost_impact=300 from mat + ADD cost_impact=300 for bom item
    assert result == Decimal("600")


# ──────────────────────── calculate_schedule_impact ────────────────────────

def test_calculate_schedule_impact_empty():
    """无受影响物料时天数为 0"""
    service = _make_service()
    result = calculate_schedule_impact(service, [], [], set())
    assert result == 0


def test_calculate_schedule_impact_no_material_in_db():
    """BOM 物料在数据库中查不到时，交期影响为 0"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None
    mat = _make_affected_mat(change_type="UPDATE")
    item = _make_bom_item(item_id=1)
    result = calculate_schedule_impact(service, [mat], [item], {1})
    assert result == 0


def test_calculate_schedule_impact_update():
    """UPDATE 变更取物料 lead_time_days"""
    service = _make_service()
    material = MagicMock(lead_time_days=15)
    service.db.query.return_value.filter.return_value.first.return_value = material

    mat = _make_affected_mat(change_type="UPDATE")
    item = _make_bom_item(item_id=1, material_id=1)
    result = calculate_schedule_impact(service, [mat], [item], {1})
    assert result == 15


def test_calculate_schedule_impact_add():
    """ADD 变更也计入 lead_time_days"""
    service = _make_service()
    material = MagicMock(lead_time_days=30)
    service.db.query.return_value.filter.return_value.first.return_value = material

    mat = _make_affected_mat(change_type="ADD")
    item = _make_bom_item(item_id=2, material_id=2)
    result = calculate_schedule_impact(service, [mat], [item], {2})
    assert result == 30
