# -*- coding: utf-8 -*-
"""
Unit tests for app/services/dashboard_adapters/strategy.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.dashboard_adapters.strategy import StrategyDashboardAdapter
    from app.schemas.dashboard import DashboardWidget, DetailedDashboardResponse
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_adapter(db=None, user=None):
    db = db or MagicMock()
    user = user or MagicMock()
    return StrategyDashboardAdapter(db=db, current_user=user)


def _mock_stat_card(**kw):
    return MagicMock(key=kw.get('key'), value=kw.get('value'), label=kw.get('label'))


def _mock_widget(**kw):
    return MagicMock(widget_id=kw.get('widget_id'), data=kw.get('data'))


def test_module_properties():
    adapter = _make_adapter()
    assert adapter.module_id == "strategy"
    assert adapter.module_name == "战略管理"
    assert "admin" in adapter.supported_roles
    assert "pmo" in adapter.supported_roles


def test_get_stats_no_active_strategy():
    """无活跃战略时统计应全为0（除strategy_count）"""
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = 2

    with patch("app.services.strategy.get_active_strategy", return_value=None), \
         patch("app.services.dashboard_adapters.strategy.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    assert len(cards) == 6
    stat_map = {c.key: c.value for c in cards}
    assert stat_map["csf_count"] == 0
    assert stat_map["kpi_count"] == 0


def test_get_stats_with_active_strategy():
    """有活跃战略时统计KPI状态"""
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = 1

    kpi1 = MagicMock()
    kpi2 = MagicMock()
    kpi3 = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [kpi1, kpi2, kpi3]

    with patch("app.services.strategy.get_active_strategy", return_value=MagicMock(id=1)), \
         patch("app.services.strategy.calculate_kpi_completion_rate", side_effect=[85.0, 60.0, 30.0]), \
         patch("app.services.dashboard_adapters.strategy.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    assert len(cards) == 6


def test_get_stats_returns_six_cards():
    """统计卡片应始终返回6张"""
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = 0

    with patch("app.services.strategy.get_active_strategy", return_value=None), \
         patch("app.services.dashboard_adapters.strategy.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    assert len(cards) == 6


def test_get_widgets_no_active_strategy():
    """无活跃战略时widgets应为空列表"""
    db = MagicMock()
    with patch("app.services.strategy.get_active_strategy", return_value=None):
        adapter = _make_adapter(db=db)
        widgets = adapter.get_widgets()

    assert widgets == []


def test_get_widgets_with_active_strategy():
    """有活跃战略时应返回2个widget"""
    db = MagicMock()
    user = MagicMock(id=42)
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []

    with patch("app.services.strategy.get_active_strategy", return_value=MagicMock(id=1)), \
         patch("app.services.strategy.calculate_kpi_completion_rate", return_value=90.0), \
         patch("app.services.dashboard_adapters.strategy.DashboardWidget", side_effect=_mock_widget):
        adapter = _make_adapter(db=db, user=user)
        widgets = adapter.get_widgets()

    assert len(widgets) == 2
    widget_ids = {w.widget_id for w in widgets}
    assert "my_kpis" in widget_ids
    assert "my_annual_works" in widget_ids


def test_get_detailed_data_no_active_strategy():
    """无活跃战略时详细数据details应为空"""
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = 0

    mock_response = MagicMock(module="strategy", details={})
    with patch("app.services.strategy.get_active_strategy", return_value=None), \
         patch("app.services.dashboard_adapters.strategy.DashboardStatCard", side_effect=_mock_stat_card), \
         patch("app.services.dashboard_adapters.strategy.DetailedDashboardResponse", return_value=mock_response):
        adapter = _make_adapter(db=db)
        result = adapter.get_detailed_data()

    assert result.module == "strategy"
    assert result.details == {}


def test_get_detailed_data_with_dimensions():
    """有活跃战略时详细数据应包含dimension_stats"""
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = 0
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []

    captured = {}

    def capture_response(**kw):
        captured.update(kw)
        return MagicMock(module=kw.get('module'), details=kw.get('details', {}))

    with patch("app.services.strategy.get_active_strategy", return_value=MagicMock(id=5)), \
         patch("app.services.strategy.calculate_kpi_completion_rate", return_value=90.0), \
         patch("app.services.dashboard_adapters.strategy.DashboardStatCard", side_effect=_mock_stat_card), \
         patch("app.services.dashboard_adapters.strategy.DetailedDashboardResponse", side_effect=capture_response):
        adapter = _make_adapter(db=db)
        result = adapter.get_detailed_data()

    assert "dimension_stats" in captured.get("details", {})
    assert len(captured["details"]["dimension_stats"]) == 4
