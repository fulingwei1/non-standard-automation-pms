# -*- coding: utf-8 -*-
"""
tests/unit/test_pc_project_collector_cov51.py
Unit tests for app/services/performance_collector/project_collector.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

try:
    from app.services.performance_collector.project_collector import ProjectCollector
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


START = date(2025, 1, 1)
END = date(2025, 1, 31)


def _make_collector():
    db = MagicMock()
    return ProjectCollector(db), db


def _make_task(status, actual_end=None, due=None):
    t = MagicMock()
    t.status = status
    t.actual_end_date = actual_end
    t.due_date = due
    return t


# ─── collect_task_completion_data ─────────────────────────────────────────────

def test_task_completion_no_tasks():
    collector, db = _make_collector()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []

    result = collector.collect_task_completion_data(1, START, END)

    assert result["total_tasks"] == 0
    assert result["completion_rate"] == 0.0
    assert result["on_time_rate"] == 0.0


def test_task_completion_all_completed_on_time():
    collector, db = _make_collector()
    t1 = _make_task("COMPLETED", actual_end=date(2025, 1, 10), due=date(2025, 1, 15))
    t2 = _make_task("COMPLETED", actual_end=date(2025, 1, 20), due=date(2025, 1, 25))
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [t1, t2]

    result = collector.collect_task_completion_data(1, START, END)

    assert result["total_tasks"] == 2
    assert result["completed_tasks"] == 2
    assert result["on_time_tasks"] == 2
    assert result["completion_rate"] == 100.0
    assert result["on_time_rate"] == 100.0


def test_task_completion_partial():
    collector, db = _make_collector()
    t1 = _make_task("COMPLETED", actual_end=date(2025, 1, 10), due=date(2025, 1, 15))
    t2 = _make_task("IN_PROGRESS")
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [t1, t2]

    result = collector.collect_task_completion_data(1, START, END)

    assert result["total_tasks"] == 2
    assert result["completed_tasks"] == 1
    assert result["completion_rate"] == 50.0


def test_task_completion_exception_returns_defaults():
    collector, db = _make_collector()
    db.query.side_effect = Exception("DB crash")

    result = collector.collect_task_completion_data(1, START, END)

    assert "error" in result
    assert result["total_tasks"] == 0


# ─── collect_project_participation_data ──────────────────────────────────────

def test_project_participation_no_projects():
    collector, db = _make_collector()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []

    result = collector.collect_project_participation_data(1, START, END)

    assert result["total_projects"] == 0
    assert result["project_ids"] == []


def test_project_participation_with_projects():
    collector, db = _make_collector()
    proj = MagicMock()
    proj.id = 99
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [proj]

    # evaluation query returns None
    db.query.return_value.filter.return_value.first.return_value = None

    result = collector.collect_project_participation_data(1, START, END)

    assert result["total_projects"] == 1
    assert 99 in result["project_ids"]


def test_project_participation_exception_returns_defaults():
    collector, db = _make_collector()
    db.query.side_effect = Exception("fail")

    result = collector.collect_project_participation_data(1, START, END)

    assert "error" in result
    assert result["total_projects"] == 0
