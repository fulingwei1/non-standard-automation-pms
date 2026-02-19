# -*- coding: utf-8 -*-
"""第四十二批：ecn_bom_analysis_service/utils.py 单元测试"""
import pytest

pytest.importorskip("app.services.ecn_bom_analysis_service.utils")

from decimal import Decimal
from unittest.mock import MagicMock, patch
from app.services.ecn_bom_analysis_service.utils import (
    get_impact_description,
    save_bom_impact,
)


def make_affected_mat(change_type="ADD", old_qty=None, new_qty=None):
    m = MagicMock()
    m.change_type = change_type
    m.old_quantity = old_qty
    m.new_quantity = new_qty
    return m


# ------------------------------------------------------------------ tests ---

def test_get_impact_description_add():
    m = make_affected_mat("ADD")
    assert "新增" in get_impact_description(m)


def test_get_impact_description_delete():
    m = make_affected_mat("DELETE")
    assert "删除" in get_impact_description(m)


def test_get_impact_description_update():
    m = make_affected_mat("UPDATE")
    assert "修改" in get_impact_description(m)


def test_get_impact_description_with_quantity_change():
    m = make_affected_mat("UPDATE", old_qty=5, new_qty=10)
    desc = get_impact_description(m)
    assert "5" in desc and "10" in desc


def test_get_impact_description_unknown_type():
    m = make_affected_mat("UNKNOWN_OP")
    desc = get_impact_description(m)
    assert "UNKNOWN_OP" in desc


def test_save_bom_impact_creates_new():
    svc = MagicMock()
    svc.db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.ecn_bom_analysis_service.utils.EcnBomImpact") as MockImpact:
        mock_instance = MagicMock()
        MockImpact.return_value = mock_instance
        save_bom_impact(
            svc, ecn_id=1, bom_version_id=2, machine_id=3,
            project_id=4, affected_item_count=5,
            total_cost_impact=Decimal("100"), schedule_impact_days=3,
            impact_analysis={"detail": "test"}
        )
    svc.db.add.assert_called_once_with(mock_instance)
    svc.db.commit.assert_called_once()


def test_save_bom_impact_updates_existing():
    svc = MagicMock()
    existing = MagicMock()
    svc.db.query.return_value.filter.return_value.first.return_value = existing
    save_bom_impact(
        svc, ecn_id=1, bom_version_id=2, machine_id=3,
        project_id=4, affected_item_count=7,
        total_cost_impact=Decimal("200"), schedule_impact_days=5,
        impact_analysis={"updated": True}
    )
    assert existing.affected_item_count == 7
    assert existing.analysis_status == "COMPLETED"
    svc.db.commit.assert_called_once()
