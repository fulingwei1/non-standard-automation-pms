# -*- coding: utf-8 -*-
"""Tests for performance_collector/project_collector.py"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date


class TestProjectCollector:
    def _make_collector(self):
        from app.services.performance_collector.project_collector import ProjectCollector
        db = MagicMock()
        collector = ProjectCollector(db)
        return collector, db

    def test_task_completion_no_tasks(self):
        c, db = self._make_collector()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = c.collect_task_completion_data(1, date(2025, 1, 1), date(2025, 12, 31))
        assert result['total_tasks'] == 0
        assert result['completion_rate'] == 0.0

    def test_task_completion_with_tasks(self):
        c, db = self._make_collector()
        task1 = MagicMock(status='COMPLETED', actual_end_date=date(2025, 3, 1), due_date=date(2025, 3, 5))
        task2 = MagicMock(status='IN_PROGRESS', actual_end_date=None, due_date=date(2025, 4, 1))
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [task1, task2]
        result = c.collect_task_completion_data(1, date(2025, 1, 1), date(2025, 12, 31))
        assert result['total_tasks'] == 2
        assert result['completed_tasks'] == 1
        assert result['on_time_tasks'] == 1

    def test_task_completion_exception(self):
        c, db = self._make_collector()
        db.query.side_effect = Exception("db error")
        result = c.collect_task_completion_data(1, date(2025, 1, 1), date(2025, 12, 31))
        assert 'error' in result

    def test_project_participation_no_projects(self):
        c, db = self._make_collector()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = c.collect_project_participation_data(1, date(2025, 1, 1), date(2025, 12, 31))
        assert result['total_projects'] == 0

    def test_project_participation_exception(self):
        c, db = self._make_collector()
        db.query.side_effect = Exception("db error")
        result = c.collect_project_participation_data(1, date(2025, 1, 1), date(2025, 12, 31))
        assert 'error' in result
