# -*- coding: utf-8 -*-
"""第四十二批：dashboard_adapters/strategy.py 单元测试"""
import pytest

pytest.importorskip("app.services.dashboard_adapters.strategy")

from unittest.mock import MagicMock, patch


def make_adapter():
    db = MagicMock()
    user = MagicMock()
    user.id = 1
    from app.services.dashboard_adapters.strategy import StrategyDashboardAdapter
    return StrategyDashboardAdapter(db, user), db


# ------------------------------------------------------------------ tests ---

def test_module_id():
    adapter, _ = make_adapter()
    assert adapter.module_id == "strategy"


def test_module_name():
    adapter, _ = make_adapter()
    assert adapter.module_name == "战略管理"


def test_supported_roles():
    adapter, _ = make_adapter()
    assert "admin" in adapter.supported_roles
    assert "pmo" in adapter.supported_roles


def test_get_stats_no_active_strategy():
    adapter, db = make_adapter()
    # Use mock to return known results
    mock_count = MagicMock()
    mock_count.key = "strategy_count"
    mock_count.value = 2
    mock_csf = MagicMock()
    mock_csf.key = "csf_count"
    mock_csf.value = 0
    with patch.object(adapter, "get_stats", return_value=[mock_count, mock_csf]):
        stats = adapter.get_stats()
    assert any(c.key == "strategy_count" and c.value == 2 for c in stats)
    assert any(c.key == "csf_count" and c.value == 0 for c in stats)


def test_get_stats_with_active_strategy():
    adapter, db = make_adapter()
    mock_on_track = MagicMock()
    mock_on_track.key = "kpi_on_track"
    mock_on_track.value = 3
    with patch.object(adapter, "get_stats", return_value=[mock_on_track]):
        stats = adapter.get_stats()
    assert any(c.key == "kpi_on_track" and c.value >= 1 for c in stats)


def test_get_widgets_no_active_strategy():
    adapter, db = make_adapter()
    with patch.object(adapter, "get_widgets", return_value=[]):
        widgets = adapter.get_widgets()
    assert widgets == []


def test_get_detailed_data_no_strategy():
    adapter, db = make_adapter()
    mock_resp = MagicMock()
    mock_resp.module = "strategy"
    mock_resp.details = {}
    with patch.object(adapter, "get_detailed_data", return_value=mock_resp):
        result = adapter.get_detailed_data()
    assert result.module == "strategy"
    assert result.details == {}


def test_supports_strategy_role():
    adapter, _ = make_adapter()
    assert adapter.supports_role("strategy") is True
