# -*- coding: utf-8 -*-
"""
第十九批 - 管理节律 Dashboard 适配器单元测试
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.dashboard_adapters.management_rhythm")

_MOD = "app.services.dashboard_adapters.management_rhythm"


def _make_level_enum():
    """构造 MeetingRhythmLevel mock，含 STRATEGIC/OPERATIONAL/OPERATION/TASK"""
    m = MagicMock()
    for name in ("STRATEGIC", "OPERATIONAL", "OPERATION", "TASK"):
        val = MagicMock()
        val.value = name
        setattr(m, name, val)
    return m


def make_adapter():
    from app.services.dashboard_adapters.management_rhythm import ManagementRhythmDashboardAdapter
    db = MagicMock()
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    adapter = ManagementRhythmDashboardAdapter.__new__(ManagementRhythmDashboardAdapter)
    adapter.db = db
    adapter.current_user = user
    return adapter


def test_module_id():
    """module_id 为 management_rhythm"""
    adapter = make_adapter()
    assert adapter.module_id == "management_rhythm"


def test_module_name():
    """module_name 为 管理节律"""
    adapter = make_adapter()
    assert adapter.module_name == "管理节律"


def test_supported_roles():
    """支持 admin、pmo、management 角色"""
    adapter = make_adapter()
    roles = adapter.supported_roles
    assert "admin" in roles
    assert "pmo" in roles
    assert "management" in roles


def test_get_stats_returns_stat_cards():
    """get_stats 返回 DashboardStatCard 列表"""
    fake_level = _make_level_enum()
    adapter = make_adapter()

    mock_query = MagicMock()
    adapter.db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.first.return_value = None
    mock_query.count.return_value = 5

    with patch(f"{_MOD}.MeetingRhythmLevel", fake_level), \
         patch(f"{_MOD}.ActionItemStatus") as mock_status:
        mock_status.COMPLETED.value = "COMPLETED"
        mock_status.OVERDUE.value = "OVERDUE"
        stats = adapter.get_stats()

    assert isinstance(stats, list)
    assert len(stats) > 0
    keys = [s.key for s in stats]
    assert "total_meetings" in keys


def test_get_stats_completion_rate():
    """完成率卡片值格式正确"""
    fake_level = _make_level_enum()
    adapter = make_adapter()

    mock_query = MagicMock()
    adapter.db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.first.return_value = None
    mock_query.count.return_value = 10

    with patch(f"{_MOD}.MeetingRhythmLevel", fake_level), \
         patch(f"{_MOD}.ActionItemStatus") as mock_status:
        mock_status.COMPLETED.value = "COMPLETED"
        mock_status.OVERDUE.value = "OVERDUE"
        stats = adapter.get_stats()

    rate_card = next((s for s in stats if s.key == "completion_rate"), None)
    assert rate_card is not None
    assert "%" in str(rate_card.value)


def test_get_widgets_returns_list():
    """get_widgets 返回 DashboardWidget 列表"""
    fake_level = _make_level_enum()
    adapter = make_adapter()

    mock_query = MagicMock()
    adapter.db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []

    with patch(f"{_MOD}.MeetingRhythmLevel", fake_level), \
         patch(f"{_MOD}.ActionItemStatus") as mock_status:
        mock_status.PENDING.value = "PENDING"
        mock_status.IN_PROGRESS.value = "IN_PROGRESS"
        widgets = adapter.get_widgets()

    assert isinstance(widgets, list)
    assert len(widgets) == 2
    widget_ids = [w.widget_id for w in widgets]
    assert "upcoming_meetings" in widget_ids
    assert "my_action_items" in widget_ids


def test_get_detailed_data_structure():
    """get_detailed_data 返回正确结构"""
    fake_level = _make_level_enum()
    adapter = make_adapter()

    mock_query = MagicMock()
    adapter.db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.first.return_value = None
    mock_query.count.return_value = 3
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []

    with patch(f"{_MOD}.MeetingRhythmLevel", fake_level), \
         patch(f"{_MOD}.ActionItemStatus") as mock_status:
        mock_status.COMPLETED.value = "COMPLETED"
        mock_status.OVERDUE.value = "OVERDUE"
        mock_status.PENDING.value = "PENDING"
        mock_status.IN_PROGRESS.value = "IN_PROGRESS"
        result = adapter.get_detailed_data()

    assert result.module == "management_rhythm"
    assert result.module_name == "管理节律"
    assert "level_stats" in result.details
    assert isinstance(result.generated_at, datetime)


def test_get_widgets_upcoming_meetings_data():
    """即将召开的会议数据格式正确"""
    fake_level = _make_level_enum()
    adapter = make_adapter()

    meeting = MagicMock()
    meeting.id = 1
    meeting.title = "战略会议"
    meeting.rhythm_level = "STRATEGIC"
    meeting.meeting_date = date(2024, 4, 1)
    meeting.status = "SCHEDULED"

    mock_query = MagicMock()
    adapter.db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.side_effect = [[meeting], []]

    with patch(f"{_MOD}.MeetingRhythmLevel", fake_level), \
         patch(f"{_MOD}.ActionItemStatus") as mock_status:
        mock_status.PENDING.value = "PENDING"
        mock_status.IN_PROGRESS.value = "IN_PROGRESS"
        widgets = adapter.get_widgets()

    upcoming_widget = next(w for w in widgets if w.widget_id == "upcoming_meetings")
    assert len(upcoming_widget.data) == 1
    assert upcoming_widget.data[0]['title'] == "战略会议"
