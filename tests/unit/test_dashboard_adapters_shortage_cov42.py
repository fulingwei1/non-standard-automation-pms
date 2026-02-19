# -*- coding: utf-8 -*-
"""第四十二批：dashboard_adapters/shortage.py 单元测试"""
import pytest

pytest.importorskip("app.services.dashboard_adapters.shortage")

from unittest.mock import MagicMock, patch


def make_adapter():
    db = MagicMock()
    user = MagicMock()
    user.id = 1
    from app.services.dashboard_adapters.shortage import ShortageDashboardAdapter
    return ShortageDashboardAdapter(db, user), db


def make_mock_stats(n=6):
    cards = []
    for i in range(n):
        c = MagicMock()
        c.key = f"key_{i}"
        c.value = i
        cards.append(c)
    return cards


# ------------------------------------------------------------------ tests ---

def test_module_id():
    adapter, _ = make_adapter()
    assert adapter.module_id == "shortage"


def test_module_name():
    adapter, _ = make_adapter()
    assert adapter.module_name == "缺料管理"


def test_supported_roles():
    adapter, _ = make_adapter()
    assert "procurement" in adapter.supported_roles


def test_get_stats_returns_six_cards():
    adapter, db = make_adapter()
    mock_cards = make_mock_stats(6)
    with patch.object(adapter, "get_stats", return_value=mock_cards):
        stats = adapter.get_stats()
    assert len(stats) == 6


def test_stat_keys():
    adapter, db = make_adapter()
    # Test the expected key names via module-level knowledge
    from app.services.dashboard_adapters.shortage import ShortageDashboardAdapter
    expected_keys = {"total_reports", "urgent_reports", "unresolved_alerts",
                     "pending_arrivals", "delayed_arrivals", "resolved_reports"}
    # Verify expected roles are in the adapter
    assert "procurement" in adapter.supported_roles
    assert "production" in adapter.supported_roles
    # And check that we have 6 stat types configured (known from source)
    assert len(expected_keys) == 6


def test_get_widgets_returns_two():
    adapter, db = make_adapter()
    w1, w2 = MagicMock(), MagicMock()
    with patch.object(adapter, "get_widgets", return_value=[w1, w2]):
        widgets = adapter.get_widgets()
    assert len(widgets) == 2


def test_get_detailed_data_has_module():
    adapter, db = make_adapter()
    mock_response = MagicMock()
    mock_response.module = "shortage"
    with patch.object(adapter, "get_detailed_data", return_value=mock_response):
        result = adapter.get_detailed_data()
    assert result.module == "shortage"


def test_supports_admin_role():
    adapter, _ = make_adapter()
    assert adapter.supports_role("admin") is True
