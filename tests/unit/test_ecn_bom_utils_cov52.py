# -*- coding: utf-8 -*-
"""
Unit tests for app/services/ecn_bom_analysis_service/utils.py (cov52)
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.ecn_bom_analysis_service.utils import (
        get_impact_description,
        save_bom_impact,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service():
    service = MagicMock()
    service.db = MagicMock()
    return service


def _make_affected_mat(change_type="UPDATE", old_qty=None, new_qty=None,
                       old_spec=None, new_spec=None):
    mat = MagicMock()
    mat.change_type = change_type
    mat.old_quantity = old_qty
    mat.new_quantity = new_qty
    # 用 spec attributes via getattr
    if old_spec is not None:
        mat.old_specification = old_spec
    else:
        mat.configure_mock(**{"old_specification": None})
    if new_spec is not None:
        mat.new_specification = new_spec
    else:
        mat.configure_mock(**{"new_specification": None})
    return mat


# ──────────────────────── get_impact_description ────────────────────────

def test_get_impact_description_add():
    # ADD 类型应返回 "新增"
    mat = _make_affected_mat(change_type="ADD")
    desc = get_impact_description(mat)
    assert "新增" in desc


def test_get_impact_description_delete():
    # DELETE 类型应返回 "删除"
    mat = _make_affected_mat(change_type="DELETE")
    desc = get_impact_description(mat)
    assert "删除" in desc


def test_get_impact_description_with_quantity():
    """有数量变更时，描述中包含箭头"""
    mat = _make_affected_mat(change_type="UPDATE", old_qty=2, new_qty=5)
    desc = get_impact_description(mat)
    assert "2" in desc
    assert "5" in desc
    assert "→" in desc


def test_get_impact_description_unknown_type():
    """未知变更类型原样返回"""
    mat = _make_affected_mat(change_type="MYSTERY")
    mat.old_quantity = None
    mat.new_quantity = None
    desc = get_impact_description(mat)
    assert "MYSTERY" in desc


# ──────────────────────── save_bom_impact ────────────────────────

def test_save_bom_impact_create_new():
    """不存在时应 add 新记录并 commit"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None

    save_bom_impact(
        service=service,
        ecn_id=1,
        bom_version_id=10,
        machine_id=5,
        project_id=3,
        affected_item_count=2,
        total_cost_impact=Decimal("500"),
        schedule_impact_days=7,
        impact_analysis={"bom_impacts": []}
    )

    service.db.add.assert_called_once()
    service.db.commit.assert_called_once()


def test_save_bom_impact_update_existing():
    """已存在时应更新字段并 commit，不应 add"""
    service = _make_service()
    existing = MagicMock()
    service.db.query.return_value.filter.return_value.first.return_value = existing

    save_bom_impact(
        service=service,
        ecn_id=1,
        bom_version_id=10,
        machine_id=5,
        project_id=3,
        affected_item_count=4,
        total_cost_impact=Decimal("999"),
        schedule_impact_days=14,
        impact_analysis={"bom_impacts": []}
    )

    service.db.add.assert_not_called()
    service.db.commit.assert_called_once()
    assert existing.affected_item_count == 4
    assert existing.schedule_impact_days == 14
    assert existing.analysis_status == "COMPLETED"
