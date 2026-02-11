# -*- coding: utf-8 -*-
"""Tests for rd_report_data_service"""
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal

import pytest


class TestRdReportDataService:

    def _make_cost(self, project_id=1, cost_type_id=1, cost_date="2024-01-15",
                   cost_no="C001", cost_description="测试", cost_amount=1000,
                   deductible_amount=0):
        c = MagicMock()
        c.rd_project_id = project_id
        c.cost_type_id = cost_type_id
        c.cost_date = cost_date
        c.cost_no = cost_no
        c.cost_description = cost_description
        c.cost_amount = cost_amount
        c.deductible_amount = deductible_amount
        return c

    def _make_project(self, pid=1, name="研发项目A"):
        p = MagicMock()
        p.id = pid
        p.project_name = name
        return p

    def _make_cost_type(self, tid=1, name="人工费"):
        t = MagicMock()
        t.id = tid
        t.type_name = name
        return t

    @patch("app.services.rd_report_data_service.func")
    def test_build_auxiliary_ledger_data_happy(self, mock_func):
        from app.services.rd_report_data_service import build_auxiliary_ledger_data
        db = MagicMock()
        cost = self._make_cost()
        proj = self._make_project()
        ctype = self._make_cost_type()

        q = MagicMock()
        db.query.return_value.join.return_value.filter.return_value = q
        q.filter.return_value.order_by.return_value.all.return_value = [cost]
        q.order_by.return_value.all.return_value = [cost]
        # For project and cost_type lookups
        db.query.return_value.filter.return_value.first.side_effect = [proj, ctype]

        result = build_auxiliary_ledger_data(db, 2024)
        assert "details" in result
        assert result["title"] == "2024年研发费用辅助账"

    @patch("app.services.rd_report_data_service.func")
    def test_build_auxiliary_ledger_data_empty(self, mock_func):
        from app.services.rd_report_data_service import build_auxiliary_ledger_data
        db = MagicMock()
        q = MagicMock()
        db.query.return_value.join.return_value.filter.return_value = q
        q.order_by.return_value.all.return_value = []
        result = build_auxiliary_ledger_data(db, 2024)
        assert result["details"] == []

    @patch("app.services.rd_report_data_service.func")
    def test_build_deduction_detail_data(self, mock_func):
        from app.services.rd_report_data_service import build_deduction_detail_data
        db = MagicMock()
        cost = self._make_cost(deductible_amount=500)
        proj = self._make_project()
        ctype = self._make_cost_type()

        q = MagicMock()
        db.query.return_value.join.return_value.filter.return_value = q
        q.order_by.return_value.all.return_value = [cost]
        db.query.return_value.filter.return_value.first.side_effect = [proj, ctype]

        result = build_deduction_detail_data(db, 2024)
        assert "summary" in result
        assert "details" in result

    @patch("app.services.rd_report_data_service.func")
    def test_build_high_tech_data(self, mock_func):
        from app.services.rd_report_data_service import build_high_tech_data
        db = MagicMock()
        cost = self._make_cost(cost_amount=2000)
        ctype = self._make_cost_type()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [cost]
        db.query.return_value.filter.return_value.first.return_value = ctype

        result = build_high_tech_data(db, 2024)
        assert result["title"] == "2024年高新企业研发费用表"

    @patch("app.services.rd_report_data_service.func")
    def test_build_intensity_data(self, mock_func):
        from app.services.rd_report_data_service import build_intensity_data
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.return_value = 50000

        result = build_intensity_data(db, 2024)
        assert result["details"][0]["年度"] == 2024

    @patch("app.services.rd_report_data_service.func")
    @patch("app.services.rd_report_data_service.RdProject")
    @patch("app.services.rd_report_data_service.Timesheet")
    @patch("app.services.rd_report_data_service.User")
    def test_build_personnel_data(self, mock_user_cls, mock_ts_cls, mock_rdp_cls, mock_func):
        from app.services.rd_report_data_service import build_personnel_data
        db = MagicMock()
        proj = MagicMock()
        proj.linked_project_id = 10

        ts = MagicMock()
        ts.user_id = 1

        user = MagicMock()
        user.real_name = "张三"
        user.department = "研发"
        user.position = "工程师"

        # Make func.extract return a MagicMock that supports comparison
        extract_mock = MagicMock()
        extract_mock.__le__ = MagicMock(return_value=True)
        extract_mock.__ge__ = MagicMock(return_value=True)
        mock_func.extract.return_value = extract_mock

        db.query.return_value.filter.return_value.all.side_effect = [[proj], [ts]]
        db.query.return_value.filter.return_value.first.return_value = user
        db.query.return_value.filter.return_value.count.return_value = 50

        result = build_personnel_data(db, 2024)
        assert "summary" in result

    def test_get_rd_report_data_invalid_type(self):
        from app.services.rd_report_data_service import get_rd_report_data
        db = MagicMock()
        with pytest.raises(ValueError, match="不支持的报表类型"):
            get_rd_report_data(db, "invalid-type", 2024)

    @patch("app.services.rd_report_data_service.build_auxiliary_ledger_data")
    def test_get_rd_report_data_dispatch(self, mock_fn):
        from app.services.rd_report_data_service import get_rd_report_data
        db = MagicMock()
        mock_fn.return_value = {"details": [], "title": "test"}
        result = get_rd_report_data(db, "auxiliary-ledger", 2024)
        mock_fn.assert_called_once_with(db, 2024, None)
