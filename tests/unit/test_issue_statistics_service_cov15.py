# -*- coding: utf-8 -*-
"""第十五批: issue_statistics_service 单元测试"""
import pytest

pytest.importorskip("app.services.issue_statistics_service")

from unittest.mock import MagicMock
from app.services.issue_statistics_service import (
    check_existing_snapshot,
    count_issues_by_status,
    count_issues_by_severity,
    count_issues_by_priority,
)


def _make_db_count(value):
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = value
    db.query.return_value.filter.return_value.first.return_value = None
    return db


def test_check_existing_snapshot_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    from datetime import date
    result = check_existing_snapshot(db, date.today())
    assert result is False


def test_check_existing_snapshot_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    from datetime import date
    result = check_existing_snapshot(db, date.today())
    assert result is True


def test_count_issues_by_status_keys():
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = 5
    result = count_issues_by_status(db)
    for key in ["total", "open", "processing", "resolved", "closed", "cancelled", "deferred"]:
        assert key in result
        assert result[key] == 5


def test_count_issues_by_severity_keys():
    db = MagicMock()
    db.query.return_value.filter.return_value.filter.return_value.count.return_value = 3
    result = count_issues_by_severity(db)
    for key in ["critical", "major", "minor"]:
        assert key in result


def test_count_issues_by_priority_returns_dict():
    db = MagicMock()
    db.query.return_value.filter.return_value.filter.return_value.count.return_value = 1
    result = count_issues_by_priority(db)
    assert isinstance(result, dict)


def test_count_issues_by_status_zero():
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = 0
    result = count_issues_by_status(db)
    assert result["total"] == 0
    assert result["open"] == 0
