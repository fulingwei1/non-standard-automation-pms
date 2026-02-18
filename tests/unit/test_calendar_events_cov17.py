# -*- coding: utf-8 -*-
"""第十七批 - 战略日历事件服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date

pytest.importorskip("app.services.strategy.review.calendar_events")


def _make_db():
    return MagicMock()


def _make_create_data(**kwargs):
    data = MagicMock()
    data.strategy_id = kwargs.get("strategy_id", 1)
    data.event_type = kwargs.get("event_type", "REVIEW")
    data.title = kwargs.get("title", "月度回顾")
    data.description = kwargs.get("description", "")
    data.event_date = kwargs.get("event_date", date(2026, 3, 15))
    data.start_time = kwargs.get("start_time", None)
    data.end_time = kwargs.get("end_time", None)
    data.is_recurring = kwargs.get("is_recurring", False)
    data.recurrence_pattern = kwargs.get("recurrence_pattern", None)
    data.owner_user_id = kwargs.get("owner_user_id", 1)
    data.related_csf_id = kwargs.get("related_csf_id", None)
    data.related_kpi_id = kwargs.get("related_kpi_id", None)
    return data


class TestCalendarEvents:

    def test_create_calendar_event(self):
        """create_calendar_event 创建事件并刷新"""
        from app.services.strategy.review.calendar_events import create_calendar_event
        db = _make_db()
        data = _make_create_data()

        with patch("app.services.strategy.review.calendar_events.StrategyCalendarEvent") as MockEvent:
            mock_event = MagicMock()
            MockEvent.return_value = mock_event
            result = create_calendar_event(db, data)

        db.add.assert_called_once_with(mock_event)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(mock_event)
        assert result is mock_event

    def test_get_calendar_event_not_found(self):
        """事件不存在时返回 None"""
        from app.services.strategy.review.calendar_events import get_calendar_event
        db = _make_db()
        # filter 返回链路：query().filter().first() -> None
        db.query.return_value.filter.return_value.first.return_value = None
        result = get_calendar_event(db, event_id=999)
        assert result is None

    def test_get_calendar_event_found(self):
        """事件存在时返回事件对象"""
        from app.services.strategy.review.calendar_events import get_calendar_event
        db = _make_db()
        event = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = event
        result = get_calendar_event(db, event_id=1)
        assert result is event

    def test_delete_calendar_event_not_found(self):
        """事件不存在时返回 False"""
        from app.services.strategy.review.calendar_events import delete_calendar_event
        db = _make_db()
        with patch("app.services.strategy.review.calendar_events.get_calendar_event", return_value=None):
            result = delete_calendar_event(db, event_id=999)
        assert result is False

    def test_delete_calendar_event_soft_delete(self):
        """软删除：is_active 设为 False"""
        from app.services.strategy.review.calendar_events import delete_calendar_event
        event = MagicMock()
        event.is_active = True
        db = _make_db()
        with patch("app.services.strategy.review.calendar_events.get_calendar_event", return_value=event):
            result = delete_calendar_event(db, event_id=1)
        assert result is True
        assert event.is_active is False
        db.commit.assert_called_once()

    def test_update_calendar_event_not_found(self):
        """更新不存在的事件时返回 None"""
        from app.services.strategy.review.calendar_events import update_calendar_event
        with patch("app.services.strategy.review.calendar_events.get_calendar_event", return_value=None):
            result = update_calendar_event(_make_db(), event_id=999, data=MagicMock())
        assert result is None

    def test_update_calendar_event_applies_changes(self):
        """更新存在的事件时应用字段变更"""
        from app.services.strategy.review.calendar_events import update_calendar_event
        db = _make_db()
        event = MagicMock()
        update_data = MagicMock()
        update_data.model_dump.return_value = {"title": "新标题"}

        with patch("app.services.strategy.review.calendar_events.get_calendar_event", return_value=event):
            result = update_calendar_event(db, event_id=1, data=update_data)

        assert event.title == "新标题"
        db.commit.assert_called_once()

    def test_list_calendar_events_returns_tuple(self):
        """list_calendar_events 返回 (列表, 总数) 元组"""
        from app.services.strategy.review.calendar_events import list_calendar_events
        db = _make_db()
        query_mock = db.query.return_value.filter.return_value
        query_mock.count.return_value = 5

        with patch("app.services.strategy.review.calendar_events.StrategyCalendarEvent") as MockSCE, \
             patch("app.services.strategy.review.calendar_events.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [MagicMock()] * 5
            items, total = list_calendar_events(db, strategy_id=1)

        assert total == 5
        assert len(items) == 5
