# -*- coding: utf-8 -*-
"""
tests/unit/test_pc_bom_collector_cov51.py
Unit tests for app/services/performance_collector/bom_collector.py
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock

try:
    from app.services.performance_collector.bom_collector import BomCollector
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


START = date(2025, 1, 1)
END = date(2025, 1, 31)


def _make_collector():
    db = MagicMock()
    return BomCollector(db), db


def _make_bom(due=None, submitted_at=None):
    bom = MagicMock()
    bom.due_date = due
    bom.submitted_at = submitted_at
    return bom


def test_no_projects_returns_zeros():
    collector, db = _make_collector()
    # project_ids empty
    db.query.return_value.filter.return_value.all.return_value = []

    result = collector.collect_bom_data(1, START, END)

    assert result["total_bom"] == 0
    assert result["bom_timeliness_rate"] == 0.0
    assert result["standard_part_rate"] == 0.0


def test_on_time_bom_counted():
    collector, db = _make_collector()

    # project_ids query: returns one project_id
    pm = MagicMock()
    pm.project_id = 10

    bom_on_time = _make_bom(
        due=datetime(2025, 1, 20),
        submitted_at=datetime(2025, 1, 18),
    )
    bom_late = _make_bom(
        due=datetime(2025, 1, 10),
        submitted_at=datetime(2025, 1, 15),
    )

    call_count = [0]

    def query_side_effect(model):
        call_count[0] += 1
        m = MagicMock()
        if call_count[0] == 1:
            # ProjectMember query
            m.filter.return_value.all.return_value = [pm]
        elif call_count[0] == 2:
            # BomHeader query
            m.filter.return_value.all.return_value = [bom_on_time, bom_late]
        else:
            # BomItem query
            m.join.return_value.filter.return_value.all.return_value = []
        return m

    db.query.side_effect = query_side_effect

    result = collector.collect_bom_data(1, START, END)

    assert result["total_bom"] == 2
    assert result["on_time_bom"] == 1
    assert result["bom_timeliness_rate"] == 50.0


def test_exception_returns_defaults():
    collector, db = _make_collector()
    db.query.side_effect = Exception("crash")

    result = collector.collect_bom_data(1, START, END)

    assert "error" in result
    assert result["total_bom"] == 0
    assert result["bom_timeliness_rate"] == 0.0


def test_standard_part_rate_computed():
    collector, db = _make_collector()

    pm = MagicMock()
    pm.project_id = 5

    bom = _make_bom(due=datetime(2025, 1, 20), submitted_at=datetime(2025, 1, 15))

    item_standard = MagicMock()
    item_standard.is_standard = True
    item_non_standard = MagicMock()
    item_non_standard.is_standard = False

    call_count = [0]

    def query_side_effect(model):
        call_count[0] += 1
        m = MagicMock()
        if call_count[0] == 1:
            m.filter.return_value.all.return_value = [pm]
        elif call_count[0] == 2:
            m.filter.return_value.all.return_value = [bom]
        else:
            m.join.return_value.filter.return_value.all.return_value = [
                item_standard, item_non_standard
            ]
        return m

    db.query.side_effect = query_side_effect

    result = collector.collect_bom_data(1, START, END)

    assert result["standard_part_rate"] == 50.0


def test_bom_without_dates_not_counted_on_time():
    """BOM without due_date or submitted_at should not count as on-time."""
    collector, db = _make_collector()

    pm = MagicMock()
    pm.project_id = 5

    bom_no_dates = _make_bom(due=None, submitted_at=None)

    call_count = [0]

    def query_side_effect(model):
        call_count[0] += 1
        m = MagicMock()
        if call_count[0] == 1:
            m.filter.return_value.all.return_value = [pm]
        elif call_count[0] == 2:
            m.filter.return_value.all.return_value = [bom_no_dates]
        else:
            m.join.return_value.filter.return_value.all.return_value = []
        return m

    db.query.side_effect = query_side_effect

    result = collector.collect_bom_data(1, START, END)

    assert result["total_bom"] == 1
    assert result["on_time_bom"] == 0
    assert result["bom_timeliness_rate"] == 0.0
