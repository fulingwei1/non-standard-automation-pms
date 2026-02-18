# -*- coding: utf-8 -*-
"""
第十六批：个人KPI管理 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.strategy.decomposition.personal_kpis import (
        create_personal_kpi,
        get_personal_kpi,
        batch_create_personal_kpis,
    )
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_create_data(**kwargs):
    data = MagicMock()
    data.user_id = kwargs.get("user_id", 1)
    data.dept_objective_id = kwargs.get("dept_objective_id", 10)
    data.source_kpi_id = kwargs.get("source_kpi_id", None)
    data.source_type = kwargs.get("source_type", "DEPT")
    data.year = kwargs.get("year", 2025)
    data.period = kwargs.get("period", "Q1")
    data.code = kwargs.get("code", "KPI-001")
    data.name = kwargs.get("name", "销售额")
    data.description = kwargs.get("description", "季度销售额目标")
    data.unit = kwargs.get("unit", "万元")
    data.direction = kwargs.get("direction", "HIGHER_BETTER")
    data.target_value = kwargs.get("target_value", Decimal("100"))
    data.weight = kwargs.get("weight", Decimal("0.3"))
    return data


class TestCreatePersonalKpi:
    def test_create_calls_db_add_commit(self):
        db = make_db()
        data = make_create_data()
        mock_kpi = MagicMock()
        with patch(
            "app.services.strategy.decomposition.personal_kpis.PersonalKPI",
            return_value=mock_kpi
        ):
            result = create_personal_kpi(db, data)
        db.add.assert_called_once_with(mock_kpi)
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_create_returns_kpi(self):
        db = make_db()
        data = make_create_data()
        mock_kpi = MagicMock()
        with patch(
            "app.services.strategy.decomposition.personal_kpis.PersonalKPI",
            return_value=mock_kpi
        ):
            result = create_personal_kpi(db, data)
        assert result is mock_kpi


class TestGetPersonalKpi:
    def test_get_returns_kpi_when_found(self):
        db = make_db()
        kpi = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi
        result = get_personal_kpi(db, 1)
        assert result is kpi

    def test_get_returns_none_when_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = get_personal_kpi(db, 999)
        assert result is None


class TestBatchCreatePersonalKpis:
    def test_batch_create_empty_list(self):
        db = make_db()
        result = batch_create_personal_kpis(db, [])
        assert result == []

    def test_batch_create_multiple_items(self):
        db = make_db()
        items = [make_create_data(code=f"KPI-{i:03d}") for i in range(3)]
        mock_kpi = MagicMock()
        with patch(
            "app.services.strategy.decomposition.personal_kpis.PersonalKPI",
            return_value=mock_kpi
        ):
            result = batch_create_personal_kpis(db, items)
        assert len(result) == 3
        assert db.add.call_count == 3

    def test_batch_create_single_item(self):
        db = make_db()
        items = [make_create_data()]
        mock_kpi = MagicMock()
        with patch(
            "app.services.strategy.decomposition.personal_kpis.PersonalKPI",
            return_value=mock_kpi
        ):
            result = batch_create_personal_kpis(db, items)
        assert len(result) == 1
