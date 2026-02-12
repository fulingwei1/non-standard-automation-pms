# -*- coding: utf-8 -*-
"""Tests for app.services.dashboard_adapters.production"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.dashboard_adapters.production import ProductionDashboardAdapter


def _make_adapter():
    db = MagicMock()
    adapter = ProductionDashboardAdapter.__new__(ProductionDashboardAdapter)
    adapter.db = db
    return adapter


class TestProperties:
    def test_module_id(self):
        a = _make_adapter()
        assert a.module_id == "production"

    def test_module_name(self):
        a = _make_adapter()
        assert a.module_name == "生产管理"

    def test_supported_roles(self):
        a = _make_adapter()
        assert "production" in a.supported_roles


class TestGetStats:
    @patch("app.services.dashboard_adapters.production.month_start")
    def test_returns_five_cards(self, mock_ms):
        from datetime import date
        mock_ms.return_value = date(2025, 1, 1)
        a = _make_adapter()

        # workshop count
        a.db.query.return_value.filter.return_value.scalar.return_value = 3

        # work order stats
        stats = MagicMock()
        stats.total = 10
        stats.completed = 5
        stats.in_progress = 3
        a.db.query.return_value.filter.return_value.first.return_value = stats

        # recent reports
        a.db.query.return_value.filter.return_value.all.return_value = []

        cards = a.get_stats()
        assert len(cards) == 5


class TestGetWidgets:
    def test_returns_list(self):
        a = _make_adapter()
        widgets = a.get_widgets()
        assert len(widgets) == 1
        assert widgets[0].widget_id == "production_summary"


class TestGetDetailedData:
    @patch.object(ProductionDashboardAdapter, "get_stats")
    @patch("app.services.dashboard_adapters.production.month_start")
    def test_returns_response(self, mock_ms, mock_stats):
        from datetime import date
        mock_ms.return_value = date(2025, 1, 1)
        mock_stats.return_value = [
            MagicMock(key="k1", value="v1"),
        ]
        a = _make_adapter()
        result = a.get_detailed_data()
        assert result.module == "production"
