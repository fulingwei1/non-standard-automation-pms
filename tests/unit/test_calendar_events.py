# -*- coding: utf-8 -*-
"""Tests for app/services/strategy/review/calendar_events.py"""
from unittest.mock import MagicMock

from app.services.strategy.review.calendar_events import (
    create_calendar_event,
    get_calendar_event,
    delete_calendar_event,
)


class TestCalendarEvents:
    def setup_method(self):
        self.db = MagicMock()

    def test_create_calendar_event(self):
        data = MagicMock()
        result = create_calendar_event(self.db, data, created_by=1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_get_calendar_event_found(self):
        mock_event = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_event
        result = get_calendar_event(self.db, 1)
        assert result == mock_event

    def test_get_calendar_event_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = get_calendar_event(self.db, 999)
        assert result is None

    def test_delete_calendar_event_found(self):
        mock_event = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_event
        result = delete_calendar_event(self.db, 1)
        assert result is True

    def test_delete_calendar_event_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = delete_calendar_event(self.db, 999)
        assert result is False
