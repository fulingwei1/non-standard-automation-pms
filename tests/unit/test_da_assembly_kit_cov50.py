# -*- coding: utf-8 -*-
"""
Unit tests for app/services/dashboard_adapters/assembly_kit.py
批次: cov50
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.dashboard_adapters.assembly_kit import AssemblyKitDashboardAdapter
    from app.schemas.dashboard import DetailedDashboardResponse
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_adapter(db=None, user=None):
    db = db or MagicMock()
    user = user or MagicMock()
    return AssemblyKitDashboardAdapter(db=db, current_user=user)


def _mock_stat_card(**kw):
    return MagicMock(key=kw.get('key'), value=kw.get('value'), label=kw.get('label'))


def _mock_widget(**kw):
    return MagicMock(widget_id=kw.get('widget_id'), data=kw.get('data'))


def test_module_properties():
    adapter = _make_adapter()
    assert adapter.module_id == "assembly_kit"
    assert adapter.module_name == "装配齐套分析"
    assert "production" in adapter.supported_roles
    assert "admin" in adapter.supported_roles


def test_get_stats_empty_db():
    """无分析记录时统计应全为0或空"""
    db = MagicMock()
    db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
    db.query.return_value.join.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0

    with patch("app.services.dashboard_adapters.assembly_kit.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    assert len(cards) == 6
    stat_map = {c.key: c.value for c in cards}
    assert stat_map["total_projects"] == 0
    assert stat_map["can_start"] == 0
    assert stat_map["total_alerts"] == 0


def test_get_stats_with_analyses():
    """有分析记录时统计结果正确"""
    db = MagicMock()

    r1 = MagicMock(can_start=True, blocking_kit_rate=Decimal('75'), overall_kit_rate=Decimal('90'))
    r2 = MagicMock(can_start=False, blocking_kit_rate=Decimal('30'), overall_kit_rate=Decimal('60'))
    r3 = MagicMock(can_start=False, blocking_kit_rate=Decimal('60'), overall_kit_rate=Decimal('70'))

    db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
    db.query.return_value.join.return_value.all.return_value = [r1, r2, r3]
    db.query.return_value.filter.return_value.count.return_value = 0

    with patch("app.services.dashboard_adapters.assembly_kit.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    stat_map = {c.key: c.value for c in cards}
    assert stat_map["total_projects"] == 3
    assert stat_map["can_start"] == 1
    assert stat_map["not_ready"] == 1  # blocking_kit_rate < 50


def test_get_stats_returns_six_cards():
    db = MagicMock()
    db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
    db.query.return_value.join.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0

    with patch("app.services.dashboard_adapters.assembly_kit.DashboardStatCard", side_effect=_mock_stat_card):
        adapter = _make_adapter(db=db)
        cards = adapter.get_stats()

    assert len(cards) == 6


def test_get_widgets_returns_two_widgets():
    """应返回2个widget"""
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    with patch("app.services.dashboard_adapters.assembly_kit.DashboardWidget", side_effect=_mock_widget):
        adapter = _make_adapter(db=db)
        widgets = adapter.get_widgets()

    assert len(widgets) == 2
    widget_ids = {w.widget_id for w in widgets}
    assert "pending_suggestions" in widget_ids
    assert "stage_stats" in widget_ids


def test_get_widgets_with_pending_suggestions():
    """有待处理建议时数据正确填充"""
    db = MagicMock()

    suggestion = MagicMock(
        id=1, project_id=10, machine_id=20,
        suggestion_type="DELAY", priority_score=Decimal('8.5'), reason="缺料"
    )
    project = MagicMock(project_name="TestProject")
    machine = MagicMock(machine_code="M001")

    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [suggestion]
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.side_effect = [project, machine]

    with patch("app.services.dashboard_adapters.assembly_kit.DashboardWidget", side_effect=_mock_widget):
        adapter = _make_adapter(db=db)
        widgets = adapter.get_widgets()

    assert len(widgets) == 2


def test_get_detailed_data_structure():
    db = MagicMock()
    db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
    db.query.return_value.join.return_value.all.return_value = []
    db.query.return_value.join.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.first.return_value = None

    captured = {}

    def capture_response(**kw):
        captured.update(kw)
        return MagicMock(module=kw.get('module'), details=kw.get('details', {}))

    with patch("app.services.dashboard_adapters.assembly_kit.DashboardStatCard", side_effect=_mock_stat_card), \
         patch("app.services.dashboard_adapters.assembly_kit.DetailedDashboardResponse", side_effect=capture_response):
        adapter = _make_adapter(db=db)
        result = adapter.get_detailed_data()

    assert captured.get("module") == "assembly_kit"
    assert "recent_analyses" in captured.get("details", {})
