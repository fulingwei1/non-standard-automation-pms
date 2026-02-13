# -*- coding: utf-8 -*-
"""Tests for sales_reminder/milestone_reminders.py"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime


class TestNotifyMilestoneUpcoming:
    @patch('app.services.sales_reminder.milestone_reminders.create_notification')
    def test_no_milestones(self, mock_create):
        from app.services.sales_reminder.milestone_reminders import notify_milestone_upcoming
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        count = notify_milestone_upcoming(db)
        assert count == 0

    @patch('app.services.sales_reminder.milestone_reminders.create_notification')
    def test_with_milestone(self, mock_create):
        from app.services.sales_reminder.milestone_reminders import notify_milestone_upcoming
        db = MagicMock()
        milestone = MagicMock(
            id=1, owner_id=10, milestone_name='M1', milestone_code='MC001',
            planned_date=date.today(), project_id=5
        )
        db.query.return_value.filter.return_value.all.return_value = [milestone]
        # No existing notification
        db.query.return_value.filter.return_value.first.return_value = None
        count = notify_milestone_upcoming(db)
        assert count == 1
        mock_create.assert_called_once()

    @patch('app.services.sales_reminder.milestone_reminders.create_notification')
    def test_already_notified(self, mock_create):
        from app.services.sales_reminder.milestone_reminders import notify_milestone_upcoming
        db = MagicMock()
        milestone = MagicMock(id=1, owner_id=10)
        db.query.return_value.filter.return_value.all.return_value = [milestone]
        db.query.return_value.filter.return_value.first.return_value = MagicMock()  # existing
        count = notify_milestone_upcoming(db)
        assert count == 0


class TestNotifyMilestoneOverdue:
    @patch('app.services.sales_reminder.milestone_reminders.create_notification')
    def test_no_overdue(self, mock_create):
        from app.services.sales_reminder.milestone_reminders import notify_milestone_overdue
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        count = notify_milestone_overdue(db)
        assert count == 0
