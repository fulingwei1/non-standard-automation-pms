# -*- coding: utf-8 -*-
"""MilestoneAlertService 单元测试"""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest

from app.services.alert.milestone_alert_service import MilestoneAlertService


class TestMilestoneAlertService:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = MilestoneAlertService(self.db)

    def test_get_upcoming_milestones(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.svc._get_upcoming_milestones(date.today())
        assert result == []

    def test_get_overdue_milestones(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.svc._get_overdue_milestones(date.today())
        assert result == []

    def test_should_create_alert_no_existing(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        milestone = MagicMock()
        milestone.id = 1
        assert self.svc._should_create_alert(milestone, "MILESTONE") is True

    def test_should_create_alert_existing(self):
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()
        milestone = MagicMock()
        milestone.id = 1
        assert self.svc._should_create_alert(milestone, "MILESTONE") is False

    def test_create_milestone_alert_overdue(self):
        rule = MagicMock()
        rule.id = 1
        milestone = MagicMock()
        milestone.milestone_name = "M1"
        milestone.milestone_code = "MC1"
        milestone.planned_date = date.today() - timedelta(days=5)
        milestone.project_id = 10
        self.svc._create_milestone_alert("MS001", rule, milestone, 5, is_overdue=True)
        self.db.add.assert_called_once()

    def test_create_milestone_alert_upcoming(self):
        rule = MagicMock()
        rule.id = 1
        milestone = MagicMock()
        milestone.milestone_name = "M2"
        milestone.milestone_code = "MC2"
        milestone.planned_date = date.today() + timedelta(days=2)
        milestone.project_id = 10
        self.svc._create_milestone_alert("MS002", rule, milestone, 2, is_overdue=False)
        self.db.add.assert_called_once()

    def test_get_or_create_warning_rule_exists(self):
        existing = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = existing
        result = self.svc._get_or_create_warning_rule()
        assert result is existing

    def test_get_or_create_warning_rule_creates(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.svc._get_or_create_warning_rule()
        self.db.add.assert_called_once()

    def test_process_upcoming_milestones_empty(self):
        count = self.svc._process_upcoming_milestones([], MagicMock(), date.today(), 0)
        assert count == 0
