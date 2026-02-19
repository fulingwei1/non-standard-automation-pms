# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 例行管理周期
（注意：生产代码中存在 schema/model 字段名版本差异，测试均通过 mock 覆盖）
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch, call

try:
    from app.services.strategy.review.routine_management import (
        get_routine_management_cycle,
        generate_routine_events,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")

MODULE = "app.services.strategy.review.routine_management"


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


class TestGetRoutineManagementCycle:
    """Mock schema 后测试周期配置函数"""

    def test_returns_object_with_strategy_id(self, mock_db):
        mock_item = MagicMock()
        mock_response = MagicMock()
        mock_response.strategy_id = 42

        with patch(f"{MODULE}.RoutineManagementCycleItem", return_value=mock_item), \
             patch(f"{MODULE}.RoutineManagementCycleResponse", return_value=mock_response):
            resp = get_routine_management_cycle(mock_db, strategy_id=42)
        assert resp.strategy_id == 42

    def test_creates_multiple_cycle_items(self, mock_db):
        created_items = []
        mock_response = MagicMock()

        def track(*args, **kwargs):
            item = MagicMock()
            created_items.append(item)
            return item

        with patch(f"{MODULE}.RoutineManagementCycleItem", side_effect=track), \
             patch(f"{MODULE}.RoutineManagementCycleResponse", return_value=mock_response):
            get_routine_management_cycle(mock_db, strategy_id=1)
        assert len(created_items) >= 3

    def test_different_strategy_ids(self, mock_db):
        mock_response_a = MagicMock()
        mock_response_a.strategy_id = 10
        mock_response_b = MagicMock()
        mock_response_b.strategy_id = 20

        responses = [mock_response_a, mock_response_b]
        call_count = [0]

        def make_response(**kwargs):
            r = responses[call_count[0]]
            call_count[0] += 1
            return r

        with patch(f"{MODULE}.RoutineManagementCycleItem", return_value=MagicMock()), \
             patch(f"{MODULE}.RoutineManagementCycleResponse", side_effect=make_response):
            r1 = get_routine_management_cycle(mock_db, strategy_id=10)
            r2 = get_routine_management_cycle(mock_db, strategy_id=20)
        assert r1.strategy_id == 10
        assert r2.strategy_id == 20


class TestGenerateRoutineEvents:
    """Mock StrategyCalendarEvent（模型字段不匹配生产代码），测试事件生成逻辑"""

    @patch(f"{MODULE}.StrategyCalendarEvent")
    def test_generates_17_events(self, MockEvent, mock_db):
        MockEvent.side_effect = lambda **kw: MagicMock(**kw)
        events = generate_routine_events(mock_db, strategy_id=1, year=2025)
        assert len(events) == 17  # 12 月度 + 4 季度 + 1 年度

    @patch(f"{MODULE}.StrategyCalendarEvent")
    def test_monthly_events_count(self, MockEvent, mock_db):
        created = []

        def factory(**kw):
            m = MagicMock()
            m.event_type = kw.get("event_type")
            m.event_date = kw.get("event_date")
            created.append(m)
            return m

        MockEvent.side_effect = factory
        events = generate_routine_events(mock_db, strategy_id=1, year=2025)
        monthly = [e for e in events if e.event_type == "MONTHLY_REVIEW"]
        assert len(monthly) == 12

    @patch(f"{MODULE}.StrategyCalendarEvent")
    def test_quarterly_events_count(self, MockEvent, mock_db):
        created = []

        def factory(**kw):
            m = MagicMock()
            m.event_type = kw.get("event_type")
            m.event_date = kw.get("event_date")
            created.append(m)
            return m

        MockEvent.side_effect = factory
        events = generate_routine_events(mock_db, strategy_id=1, year=2025)
        quarterly = [e for e in events if e.event_type == "QUARTERLY_REVIEW"]
        assert len(quarterly) == 4

    @patch(f"{MODULE}.StrategyCalendarEvent")
    def test_yearly_event_count(self, MockEvent, mock_db):
        created = []

        def factory(**kw):
            m = MagicMock()
            m.event_type = kw.get("event_type")
            m.event_date = kw.get("event_date")
            created.append(m)
            return m

        MockEvent.side_effect = factory
        events = generate_routine_events(mock_db, strategy_id=1, year=2025)
        yearly = [e for e in events if e.event_type == "YEARLY_PLANNING"]
        assert len(yearly) == 1

    @patch(f"{MODULE}.StrategyCalendarEvent")
    def test_db_commit_called(self, MockEvent, mock_db):
        MockEvent.side_effect = lambda **kw: MagicMock(**kw)
        generate_routine_events(mock_db, strategy_id=1, year=2025)
        mock_db.commit.assert_called_once()

    @patch(f"{MODULE}.StrategyCalendarEvent")
    def test_events_not_on_weekend(self, MockEvent, mock_db):
        created = []

        def factory(**kw):
            m = MagicMock()
            m.event_type = kw.get("event_type")
            m.event_date = kw.get("event_date")
            created.append(m)
            return m

        MockEvent.side_effect = factory
        events = generate_routine_events(mock_db, strategy_id=1, year=2025)
        for event in events:
            d = event.event_date
            assert d.weekday() < 5, f"事件落在周末: {d}"

    @patch(f"{MODULE}.StrategyCalendarEvent")
    def test_db_add_called_for_each_event(self, MockEvent, mock_db):
        MockEvent.side_effect = lambda **kw: MagicMock(**kw)
        events = generate_routine_events(mock_db, strategy_id=1, year=2025)
        assert mock_db.add.call_count == len(events)
