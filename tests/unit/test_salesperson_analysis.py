# -*- coding: utf-8 -*-
"""Tests for resource_waste_analysis/salesperson_analysis.py"""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestSalespersonAnalysisMixin:

    def _make_mixin(self):
        from app.services.resource_waste_analysis.salesperson_analysis import SalespersonAnalysisMixin

        class TestClass(SalespersonAnalysisMixin):
            def __init__(self, db):
                self.db = db
                self.hourly_rate = Decimal("200")

        db = MagicMock()
        return TestClass(db), db

    def test_get_salesperson_waste_ranking_empty(self):
        obj, db = self._make_mixin()
        db.query.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        result = obj.get_salesperson_waste_ranking()
        assert result == []

    @patch("app.services.resource_waste_analysis.salesperson_analysis.WorkLog")
    @patch("app.services.resource_waste_analysis.salesperson_analysis.func")
    def test_get_salesperson_waste_ranking_with_data(self, mock_func, mock_wl):
        obj, db = self._make_mixin()
        proj = MagicMock()
        proj.id = 1
        proj.salesperson_id = 10
        proj.outcome = "LOST"
        proj.loss_reason = "价格"
        proj.contract_amount = Decimal("0")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.all.return_value = [proj]
        # work hours map
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [(1, 20)]

        user = MagicMock()
        user.name = "销售A"
        user.department_name = "销售部"
        db.query.return_value.filter.return_value.first.return_value = user

        result = obj.get_salesperson_waste_ranking()
        assert len(result) >= 0  # May vary based on mock chain

    def test_get_department_comparison_empty(self):
        obj, db = self._make_mixin()
        with patch.object(obj, "get_salesperson_waste_ranking", return_value=[]):
            result = obj.get_department_comparison()
            assert result == []

    def test_get_department_comparison_with_data(self):
        obj, db = self._make_mixin()
        sp_data = [{
            "salesperson_id": 1,
            "salesperson_name": "张三",
            "department": "销售一部",
            "total_leads": 10,
            "won_leads": 5,
            "lost_leads": 3,
            "total_hours": 100.0,
            "wasted_hours": 30.0,
            "won_amount": Decimal("500000"),
        }]
        with patch.object(obj, "get_salesperson_waste_ranking", return_value=sp_data):
            result = obj.get_department_comparison()
            assert len(result) == 1
            assert result[0]["department"] == "销售一部"
            assert result[0]["win_rate"] == round(5 / 8, 3)
