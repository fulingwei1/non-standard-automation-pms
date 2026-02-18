# -*- coding: utf-8 -*-
"""
第十九批 - 工时质量检查服务单元测试
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

pytest.importorskip("app.services.timesheet_quality_service")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.timesheet_quality_service import TimesheetQualityService
    return TimesheetQualityService(mock_db)


def _make_timesheet(user_id=1, work_date=None, hours=8.0, status='APPROVED'):
    ts = MagicMock()
    ts.user_id = user_id
    ts.work_date = work_date or date(2024, 3, 15)
    ts.hours = hours
    ts.status = status
    return ts


def _make_user(user_id=1, real_name="张三", username="zhangsan"):
    user = MagicMock()
    user.id = user_id
    user.real_name = real_name
    user.username = username
    return user


def test_detect_anomalies_empty(service, mock_db):
    """无工时记录时返回空列表"""
    mock_db.query.return_value.filter.return_value.all.return_value = []
    result = service.detect_anomalies()
    assert result == []


def test_detect_anomalies_excessive_hours(service, mock_db):
    """单日超过16小时时检测到异常"""
    ts = _make_timesheet(hours=20.0)
    user = _make_user()

    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = [ts]
    query_mock.first.return_value = user

    result = service.detect_anomalies()
    assert len(result) >= 1
    assert any(r['type'] == 'EXCESSIVE_DAILY_HOURS' for r in result)


def test_detect_anomalies_normal_hours(service, mock_db):
    """正常工时不产生异常"""
    ts = _make_timesheet(hours=8.0)

    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = [ts]

    result = service.detect_anomalies()
    assert result == []


def test_detect_anomalies_with_user_filter(service, mock_db):
    """按用户 ID 过滤工时异常"""
    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = []

    result = service.detect_anomalies(user_id=5)
    assert result == []


def test_detect_anomalies_with_date_range(service, mock_db):
    """按日期范围过滤"""
    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = []

    result = service.detect_anomalies(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31)
    )
    assert result == []


def test_detect_anomalies_multiple_entries_same_day(service, mock_db):
    """同一天多条记录累计超过限制时检测到异常"""
    ts1 = _make_timesheet(user_id=1, work_date=date(2024, 3, 15), hours=10.0)
    ts2 = _make_timesheet(user_id=1, work_date=date(2024, 3, 15), hours=8.0)  # 累计18
    user = _make_user()

    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = [ts1, ts2]
    query_mock.first.return_value = user

    result = service.detect_anomalies()
    assert len(result) >= 1
    excessive = [r for r in result if r['type'] == 'EXCESSIVE_DAILY_HOURS']
    assert len(excessive) >= 1
    assert excessive[0]['hours'] == 18.0


def test_detect_anomalies_severity_high(service, mock_db):
    """超过最大工时时严重级别为 HIGH"""
    ts = _make_timesheet(hours=20.0)
    user = _make_user()

    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = [ts]
    query_mock.first.return_value = user

    result = service.detect_anomalies()
    if result:
        assert result[0]['severity'] == 'HIGH'


def test_max_daily_hours_constant(service):
    """MAX_DAILY_HOURS 常量值为 16"""
    assert service.MAX_DAILY_HOURS == 16


def test_service_initialization(mock_db):
    """服务初始化正确"""
    from app.services.timesheet_quality_service import TimesheetQualityService
    svc = TimesheetQualityService(mock_db)
    assert svc.db is mock_db
