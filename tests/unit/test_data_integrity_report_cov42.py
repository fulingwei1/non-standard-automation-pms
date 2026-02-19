# -*- coding: utf-8 -*-
"""第四十二批：data_integrity/report.py 单元测试"""
import pytest

pytest.importorskip("app.services.data_integrity.report")

from unittest.mock import MagicMock, patch
from app.services.data_integrity.report import DataReportMixin


class ConcreteReport(DataReportMixin):
    def __init__(self, db):
        self.db = db

    def check_data_completeness(self, engineer_id, period_id):
        return {
            "completeness_score": 80.0,
            "missing_items": [],
            "warnings": ["warning_one"],
        }


def make_service():
    db = MagicMock()
    return ConcreteReport(db), db


def setup_period(db, period):
    """Make db.query(PerformancePeriod).filter().first() return period"""
    from app.models.performance import PerformancePeriod
    period_q = MagicMock()
    period_q.filter.return_value.first.return_value = period

    def q_router(*args):
        if args and args[0] is PerformancePeriod:
            return period_q
        return MagicMock()

    db.query.side_effect = q_router
    return db


# ------------------------------------------------------------------ tests ---

def test_raises_when_period_not_found():
    svc, db = make_service()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="考核周期不存在"):
        svc.generate_data_quality_report(999)


def test_returns_empty_when_no_engineers():
    svc, db = make_service()
    period = MagicMock()
    setup_period(db, period)
    # query for EngineerProfile
    from app.models.engineer_performance import EngineerProfile
    engineer_q = MagicMock()
    engineer_q.all.return_value = []

    orig_side = db.query.side_effect

    def q_router(*args):
        from app.models.performance import PerformancePeriod
        if args and args[0] is PerformancePeriod:
            q = MagicMock()
            q.filter.return_value.first.return_value = period
            return q
        return engineer_q

    db.query.side_effect = q_router
    result = svc.generate_data_quality_report(1)
    assert result["total_engineers"] == 0
    assert result["reports"] == []


def test_average_completeness_calculated():
    svc, db = make_service()
    period = MagicMock()

    eng1 = MagicMock()
    eng1.user_id = 1
    eng2 = MagicMock()
    eng2.user_id = 2

    from app.models.performance import PerformancePeriod
    from app.models.engineer_performance import EngineerProfile

    def q_router(*args):
        if args and args[0] is PerformancePeriod:
            q = MagicMock()
            q.filter.return_value.first.return_value = period
            return q
        q = MagicMock()
        q.all.return_value = [eng1, eng2]
        return q

    db.query.side_effect = q_router
    result = svc.generate_data_quality_report(1)
    assert result["average_completeness_score"] == 80.0


def test_warnings_summarized():
    svc, db = make_service()
    period = MagicMock()
    eng = MagicMock()
    eng.user_id = 10

    from app.models.performance import PerformancePeriod

    def q_router(*args):
        if args and args[0] is PerformancePeriod:
            q = MagicMock()
            q.filter.return_value.first.return_value = period
            return q
        q = MagicMock()
        q.all.return_value = [eng]
        return q

    db.query.side_effect = q_router
    result = svc.generate_data_quality_report(1)
    assert "warning_one" in result["warnings_summary"]
    assert result["warnings_summary"]["warning_one"] == 1


def test_result_has_period_and_department_id():
    svc, db = make_service()
    period = MagicMock()

    from app.models.performance import PerformancePeriod

    def q_router(*args):
        if args and args[0] is PerformancePeriod:
            q = MagicMock()
            q.filter.return_value.first.return_value = period
            return q
        q = MagicMock()
        q.all.return_value = []
        return q

    db.query.side_effect = q_router
    result = svc.generate_data_quality_report(42, department_id=None)
    assert result["period_id"] == 42
    assert result["department_id"] is None


def test_department_filter_applied():
    svc, db = make_service()
    period = MagicMock()

    from app.models.performance import PerformancePeriod

    def q_router(*args):
        if args and args[0] is PerformancePeriod:
            q = MagicMock()
            q.filter.return_value.first.return_value = period
            return q
        q = MagicMock()
        q.all.return_value = []
        q.filter.return_value.all.return_value = []
        return q

    db.query.side_effect = q_router
    # Should not raise even with department_id
    result = svc.generate_data_quality_report(1, department_id=5)
    assert result["total_engineers"] == 0
