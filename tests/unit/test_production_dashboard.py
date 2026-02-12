# -*- coding: utf-8 -*-
"""生产管理Dashboard适配器 单元测试"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.dashboard_adapters.production import ProductionDashboardAdapter


def _make_adapter():
    db = MagicMock()
    adapter = ProductionDashboardAdapter.__new__(ProductionDashboardAdapter)
    adapter.db = db
    return adapter


class TestProductionDashboardAdapter:
    def test_module_id(self):
        a = _make_adapter()
        assert a.module_id == "production"

    def test_module_name(self):
        a = _make_adapter()
        assert a.module_name == "生产管理"

    def test_supported_roles(self):
        a = _make_adapter()
        assert "production" in a.supported_roles

    def test_get_stats_returns_cards(self):
        a = _make_adapter()
        # Mock workshop count
        a.db.query.return_value.filter.return_value.scalar.return_value = 3
        # Mock work order stats
        stats = MagicMock()
        stats.total = 10
        stats.completed = 5
        stats.in_progress = 3
        a.db.query.return_value.filter.return_value.first.return_value = stats
        # Mock daily reports
        a.db.query.return_value.filter.return_value.all.return_value = []

        cards = a.get_stats()
        assert len(cards) == 5
        keys = [c.key for c in cards]
        assert "workshop_count" in keys
        assert "total_orders" in keys

    def test_get_widgets(self):
        a = _make_adapter()
        widgets = a.get_widgets()
        assert len(widgets) == 1
        assert widgets[0].widget_id == "production_summary"

    def test_get_detailed_data(self):
        a = _make_adapter()
        # Mock for get_stats
        a.db.query.return_value.filter.return_value.scalar.return_value = 0
        stats = MagicMock()
        stats.total = 0
        stats.completed = 0
        stats.in_progress = 0
        a.db.query.return_value.filter.return_value.first.return_value = stats
        a.db.query.return_value.filter.return_value.all.return_value = []

        result = a.get_detailed_data()
        assert result.module == "production"
