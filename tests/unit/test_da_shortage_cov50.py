# -*- coding: utf-8 -*-
"""
Unit tests for app/services/dashboard_adapters/shortage.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.dashboard_adapters.shortage import ShortageDashboardAdapter
    from app.schemas.dashboard import DetailedDashboardResponse
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_adapter(db=None, user=None):
    db = db or MagicMock()
    user = user or MagicMock()
    return ShortageDashboardAdapter(db=db, current_user=user)


def _mock_stat_card(**kw):
    return MagicMock(key=kw.get('key'), value=kw.get('value'), label=kw.get('label'))


def _mock_widget(**kw):
    return MagicMock(widget_id=kw.get('widget_id'), data=kw.get('data'))


def test_module_properties():
    adapter = _make_adapter()
    assert adapter.module_id == "shortage"
    assert adapter.module_name == "缺料管理"
    assert "procurement" in adapter.supported_roles
    assert "admin" in adapter.supported_roles


def test_get_stats_all_zero():
    """全为0时统计卡片值应为0"""
    db = MagicMock()
    db.query.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.count.return_value = 0

    with patch("app.services.dashboard_adapters.shortage.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    assert len(cards) == 6
    for card in cards:
        assert card.value == 0


def test_get_stats_with_counts():
    """有数据时统计卡片个数正确"""
    db = MagicMock()
    db.query.return_value.count.return_value = 10
    db.query.return_value.filter.return_value.count.return_value = 3

    with patch("app.services.dashboard_adapters.shortage.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    assert len(cards) == 6
    keys = {c.key for c in cards}
    assert "total_reports" in keys
    assert "urgent_reports" in keys
    assert "resolved_reports" in keys


def test_get_stats_returns_six_cards():
    db = MagicMock()
    db.query.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.count.return_value = 0

    with patch("app.services.dashboard_adapters.shortage.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    assert len(cards) == 6


def test_get_widgets_empty_reports():
    """无缺料上报时widget数据应为空列表"""
    db = MagicMock()
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.count.return_value = 0

    with patch("app.services.dashboard_adapters.shortage.DashboardWidget", side_effect=_mock_widget), \
         patch("app.services.dashboard_adapters.shortage.DashboardListItem"):
        adapter = _make_adapter(db=db)
        widgets = adapter.get_widgets()

    assert len(widgets) == 2
    widget_ids = {w.widget_id for w in widgets}
    assert "recent_reports" in widget_ids
    assert "operation_stats" in widget_ids


def test_get_widgets_with_report():
    """有上报记录时widget应包含数据"""
    db = MagicMock()

    report = MagicMock(
        id=1, project_id=5, material_name="螺栓",
        status="REPORTED", urgent_level="URGENT",
        report_time=MagicMock(), report_no="SR001",
        shortage_qty=Decimal('10')
    )
    project = MagicMock(project_name="TestProject")

    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [report]
    db.query.return_value.filter.return_value.first.return_value = project
    db.query.return_value.count.return_value = 5
    db.query.return_value.filter.return_value.count.return_value = 2

    with patch("app.services.dashboard_adapters.shortage.DashboardWidget", side_effect=_mock_widget), \
         patch("app.services.dashboard_adapters.shortage.DashboardListItem") as mock_list_item:
        mock_list_item.return_value = MagicMock()
        adapter = _make_adapter(db=db)
        widgets = adapter.get_widgets()

    assert len(widgets) == 2


def test_get_detailed_data_structure():
    db = MagicMock()
    db.query.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.count.return_value = 0

    captured = {}

    def capture_response(**kw):
        captured.update(kw)
        return MagicMock(module=kw.get('module'), details=kw.get('details', {}))

    with patch("app.services.dashboard_adapters.shortage.DashboardStatCard", side_effect=_mock_stat_card), \
         patch("app.services.dashboard_adapters.shortage.DetailedDashboardResponse", side_effect=capture_response):
        adapter = _make_adapter(db=db)
        adapter.get_detailed_data()

    assert captured.get("module") == "shortage"
    assert "by_status" in captured.get("details", {})
    assert "by_urgent" in captured.get("details", {})


def test_get_detailed_data_by_status_keys():
    """详细数据应包含所有状态键"""
    db = MagicMock()
    db.query.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.count.return_value = 0

    captured = {}

    def capture_response(**kw):
        captured.update(kw)
        return MagicMock(module=kw.get('module'), details=kw.get('details', {}))

    with patch("app.services.dashboard_adapters.shortage.DashboardStatCard", side_effect=_mock_stat_card), \
         patch("app.services.dashboard_adapters.shortage.DetailedDashboardResponse", side_effect=capture_response):
        adapter = _make_adapter(db=db)
        adapter.get_detailed_data()

    expected_statuses = {"REPORTED", "CONFIRMED", "HANDLING", "RESOLVED"}
    assert set(captured["details"]["by_status"].keys()) == expected_statuses

    expected_levels = {"LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL"}
    assert set(captured["details"]["by_urgent"].keys()) == expected_levels
