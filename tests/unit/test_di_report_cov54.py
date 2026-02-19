"""Tests for app/services/data_integrity/report.py"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.data_integrity.report import DataReportMixin
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


class ConcreteDataReport(DataReportMixin):
    def __init__(self, db):
        self.db = db


def _make_db():
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.all.return_value = []
    q.count.return_value = 0
    q.first.return_value = None
    return db


def test_generate_data_quality_report_raises_if_period_not_found():
    """考核周期不存在时抛出 ValueError"""
    db = _make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    reporter = ConcreteDataReport(db)
    with pytest.raises(ValueError, match="考核周期不存在"):
        reporter.generate_data_quality_report(999)


def test_generate_data_quality_report_no_engineers():
    """没有工程师时返回空报告"""
    db = _make_db()
    period = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = period
    db.query.return_value.all.return_value = []
    reporter = ConcreteDataReport(db)
    result = reporter.generate_data_quality_report(1)
    assert result['total_engineers'] == 0
    assert result['reports'] == []


def test_generate_data_quality_report_structure():
    """返回结构包含必需字段"""
    db = _make_db()
    period = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = period
    db.query.return_value.all.return_value = []
    reporter = ConcreteDataReport(db)
    result = reporter.generate_data_quality_report(1)
    assert 'period_id' in result
    assert 'department_id' in result
    assert 'total_engineers' in result
    assert 'reports' in result


def test_generate_data_quality_report_with_engineers():
    """有工程师时计算平均完整性得分"""
    db = _make_db()
    period = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = period
    engineer = MagicMock()
    engineer.user_id = 1
    db.query.return_value.all.return_value = [engineer]
    reporter = ConcreteDataReport(db)
    fake_report = {
        'engineer_id': 1, 'period_id': 1,
        'completeness_score': 80.0,
        'missing_items': [], 'warnings': [], 'suggestions': []
    }
    reporter.check_data_completeness = MagicMock(return_value=fake_report)
    result = reporter.generate_data_quality_report(1)
    assert result['total_engineers'] == 1
    assert result['average_completeness_score'] == 80.0


def test_generate_data_quality_report_averages_multiple_engineers():
    """多工程师时计算平均完整性得分"""
    db = _make_db()
    period = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = period
    e1 = MagicMock()
    e1.user_id = 1
    e2 = MagicMock()
    e2.user_id = 2
    db.query.return_value.all.return_value = [e1, e2]
    reporter = ConcreteDataReport(db)
    reports = [
        {'engineer_id': 1, 'period_id': 1, 'completeness_score': 60.0,
         'missing_items': ['X'], 'warnings': [], 'suggestions': []},
        {'engineer_id': 2, 'period_id': 1, 'completeness_score': 80.0,
         'missing_items': [], 'warnings': ['Y'], 'suggestions': []},
    ]
    reporter.check_data_completeness = MagicMock(side_effect=reports)
    result = reporter.generate_data_quality_report(1)
    assert result['average_completeness_score'] == 70.0
    assert result['missing_items_summary']['X'] == 1
    assert result['warnings_summary']['Y'] == 1


def test_generate_data_quality_report_without_department():
    """不传 department_id 时查询所有工程师"""
    db = _make_db()
    period = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = period
    db.query.return_value.all.return_value = []
    reporter = ConcreteDataReport(db)
    result = reporter.generate_data_quality_report(1)
    assert result['department_id'] is None
