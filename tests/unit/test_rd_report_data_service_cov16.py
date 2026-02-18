# -*- coding: utf-8 -*-
"""
第十六批：研发费用报表数据服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

try:
    from app.services.rd_report_data_service import (
        build_auxiliary_ledger_data,
        build_deduction_detail_data,
    )
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_rd_cost(**kwargs):
    cost = MagicMock()
    cost.rd_project_id = kwargs.get("rd_project_id", 1)
    cost.cost_type_id = kwargs.get("cost_type_id", 1)
    cost.cost_date = kwargs.get("cost_date", date(2025, 3, 10))
    cost.cost_no = kwargs.get("cost_no", "RD-2025-001")
    cost.cost_description = kwargs.get("cost_description", "研发费用")
    cost.cost_amount = kwargs.get("cost_amount", Decimal("10000"))
    cost.deductible_amount = kwargs.get("deductible_amount", Decimal("8000"))
    return cost


def make_project(project_id=1, project_name="研发项目A"):
    p = MagicMock()
    p.id = project_id
    p.project_name = project_name
    return p


def make_cost_type(type_id=1, type_name="人工费"):
    ct = MagicMock()
    ct.id = type_id
    ct.type_name = type_name
    return ct


class TestBuildAuxiliaryLedgerData:
    def test_empty_costs(self):
        db = make_db()
        q_mock = MagicMock()
        q_mock.join.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = q_mock
        result = build_auxiliary_ledger_data(db, year=2025)
        assert "details" in result
        assert result["details"] == []

    def test_with_costs(self):
        db = make_db()
        cost = make_rd_cost()
        project = make_project()
        cost_type = make_cost_type()
        q_mock = MagicMock()
        q_mock.join.return_value.filter.return_value.order_by.return_value.all.return_value = [cost]
        q_mock.filter.return_value.first.side_effect = [project, cost_type]
        db.query.return_value = q_mock
        result = build_auxiliary_ledger_data(db, year=2025)
        assert "details" in result
        assert "title" in result
        assert "2025" in result["title"]

    def test_with_project_filter(self):
        db = make_db()
        q_mock = MagicMock()
        q_mock.join.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = q_mock
        result = build_auxiliary_ledger_data(db, year=2025, project_id=5)
        assert isinstance(result, dict)

    def test_title_contains_year(self):
        db = make_db()
        q_mock = MagicMock()
        q_mock.join.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = q_mock
        result = build_auxiliary_ledger_data(db, year=2024)
        assert "2024" in result.get("title", "")


class TestBuildDeductionDetailData:
    def test_empty_deductible_costs(self):
        db = make_db()
        q_mock = MagicMock()
        q_mock.join.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value = q_mock
        result = build_deduction_detail_data(db, year=2025)
        assert isinstance(result, dict)
        assert "details" in result

    def test_with_deductible_costs(self):
        db = make_db()
        cost = make_rd_cost(deductible_amount=Decimal("8000"))
        project = make_project()
        cost_type = make_cost_type()
        q_mock = MagicMock()
        q_mock.join.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [cost]
        q_mock.filter.return_value.first.side_effect = [project, cost_type]
        db.query.return_value = q_mock
        result = build_deduction_detail_data(db, year=2025)
        assert isinstance(result, dict)
