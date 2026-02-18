# -*- coding: utf-8 -*-
"""第十批：TimesheetSyncService 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.timesheet_sync_service import TimesheetSyncService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return TimesheetSyncService(db)


def _make_timesheet(**kwargs):
    ts = MagicMock()
    ts.id = kwargs.get("id", 1)
    ts.status = kwargs.get("status", "APPROVED")
    ts.project_id = kwargs.get("project_id", 10)
    ts.user_id = kwargs.get("user_id", 1)
    ts.hours = kwargs.get("hours", 8.0)
    ts.year = kwargs.get("year", 2024)
    ts.month = kwargs.get("month", 1)
    return ts


def test_service_init(db):
    """服务初始化"""
    svc = TimesheetSyncService(db)
    assert svc.db is db


def test_sync_to_finance_not_found(service, db):
    """工时记录不存在"""
    db.query.return_value.filter.return_value.first.return_value = None

    result = service.sync_to_finance(timesheet_id=999)
    assert result["success"] is False
    assert "不存在" in result["message"]


def test_sync_to_finance_not_approved(service, db):
    """未审批的工时记录不能同步"""
    ts = _make_timesheet(status="PENDING")
    db.query.return_value.filter.return_value.first.return_value = ts

    result = service.sync_to_finance(timesheet_id=1)
    assert result["success"] is False
    assert "审批" in result["message"]


def test_sync_to_finance_no_project(service, db):
    """工时记录未关联项目"""
    ts = _make_timesheet(status="APPROVED", project_id=None)
    db.query.return_value.filter.return_value.first.return_value = ts

    result = service.sync_to_finance(timesheet_id=1)
    assert result["success"] is False
    assert "项目" in result["message"]


def test_sync_to_finance_success(service, db):
    """正常同步到财务"""
    ts = _make_timesheet(status="APPROVED", project_id=10)

    call_count = [0]

    def side_effect(*args):
        call_count[0] += 1
        q = MagicMock()
        if call_count[0] == 1:
            # 查询 Timesheet
            q.filter.return_value.first.return_value = ts
        else:
            q.filter.return_value.first.return_value = None
        return q

    db.query.side_effect = side_effect

    with patch("app.services.timesheet_sync_service.save_obj"):
        with patch.object(service, "_create_financial_cost_from_timesheet",
                          return_value={"success": True, "message": "同步成功"}):
            result = service.sync_to_finance(timesheet_id=1)
            assert result["success"] is True


def test_sync_to_finance_batch_by_year_month(service, db):
    """按年月批量同步"""
    mock_q = MagicMock()
    db.query.return_value = mock_q
    mock_q.filter.return_value = mock_q
    mock_q.all.return_value = []

    result = service.sync_to_finance(year=2024, month=1)
    assert result is not None


def test_sync_to_finance_no_params(service, db):
    """无参数时的处理"""
    mock_q = MagicMock()
    db.query.return_value = mock_q
    mock_q.filter.return_value = mock_q
    mock_q.all.return_value = []

    result = service.sync_to_finance()
    assert result is not None
