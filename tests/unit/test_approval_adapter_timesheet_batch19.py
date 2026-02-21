# -*- coding: utf-8 -*-
"""
审批适配器 - 工时适配器 单元测试 (Batch 19)

测试 app/services/approval_engine/adapters/timesheet.py
覆盖率目标: 60%+
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.approval import ApprovalInstance
from app.models.timesheet import Timesheet
from app.services.approval_engine.adapters.timesheet import TimesheetApprovalAdapter


@pytest.mark.unit
class TestTimesheetApprovalAdapterInit:
    """测试初始化"""

    def test_init_success(self):
        """测试成功初始化"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        assert adapter.db == mock_db
        assert adapter.entity_type == "TIMESHEET"


@pytest.mark.unit
class TestGetEntity:
    """测试 get_entity 方法"""

    def test_get_entity_found(self):
        """测试获取存在的工时记录"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 123
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = adapter.get_entity(123)

        assert result == mock_timesheet
        mock_db.query.assert_called_once()

    def test_get_entity_not_found(self):
        """测试获取不存在的工时记录"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity(999)

        assert result is None


@pytest.mark.unit
class TestGetEntityData:
    """测试 get_entity_data 方法"""

    def test_get_entity_data_success(self):
        """测试成功获取工时数据"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 123
        mock_timesheet.timesheet_no = "TS-2024-001"
        mock_timesheet.status = "DRAFT"
        mock_timesheet.user_id = 100
        mock_timesheet.user_name = "张三"
        mock_timesheet.department_id = 10
        mock_timesheet.department_name = "研发部"
        mock_timesheet.project_id = 200
        mock_timesheet.project_code = "PRJ-001"
        mock_timesheet.project_name = "测试项目"
        mock_timesheet.task_name = "开发任务"
        mock_timesheet.work_date = datetime(2024, 1, 15)
        mock_timesheet.hours = Decimal("8.0")
        mock_timesheet.overtime_type = "NORMAL"
        mock_timesheet.work_content = "完成功能开发"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = adapter.get_entity_data(123)

        assert result["timesheet_no"] == "TS-2024-001"
        assert result["status"] == "DRAFT"
        assert result["user_name"] == "张三"
        assert result["hours"] == 8.0
        assert result["overtime_type"] == "NORMAL"
        assert result["is_overtime"] is False

    def test_get_entity_data_overtime(self):
        """测试获取加班工时数据"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.timesheet_no = "TS-2024-002"
        mock_timesheet.status = "SUBMITTED"
        mock_timesheet.user_id = 101
        mock_timesheet.user_name = "李四"
        mock_timesheet.department_id = 20
        mock_timesheet.department_name = "测试部"
        mock_timesheet.project_id = 201
        mock_timesheet.project_code = "PRJ-002"
        mock_timesheet.project_name = "紧急项目"
        mock_timesheet.task_name = "Bug修复"
        mock_timesheet.work_date = datetime(2024, 1, 20)
        mock_timesheet.hours = Decimal("4.0")
        mock_timesheet.overtime_type = "WEEKDAY"
        mock_timesheet.work_content = "加班修复Bug"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = adapter.get_entity_data(123)

        assert result["overtime_type"] == "WEEKDAY"
        assert result["is_overtime"] is True

    def test_get_entity_data_timesheet_not_found(self):
        """测试工时记录不存在时返回空字典"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity_data(999)

        assert result == {}

    def test_get_entity_data_null_fields(self):
        """测试空值字段处理"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.timesheet_no = "TS-2024-003"
        mock_timesheet.status = "DRAFT"
        mock_timesheet.user_id = 102
        mock_timesheet.user_name = "王五"
        mock_timesheet.department_id = None
        mock_timesheet.department_name = None
        mock_timesheet.project_id = None
        mock_timesheet.project_code = None
        mock_timesheet.project_name = None
        mock_timesheet.task_name = None
        mock_timesheet.work_date = None
        mock_timesheet.hours = None
        mock_timesheet.overtime_type = "NORMAL"
        mock_timesheet.work_content = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = adapter.get_entity_data(123)

        assert result["work_date"] is None
        assert result["hours"] == 0
        assert result["is_overtime"] is False


@pytest.mark.unit
class TestCallbacks:
    """测试生命周期回调方法"""

    def test_on_submit(self):
        """测试提交时回调"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet
        mock_instance = MagicMock(spec=ApprovalInstance)

        adapter.on_submit(123, mock_instance)

        assert mock_timesheet.status == "SUBMITTED"
        assert mock_timesheet.submit_time is not None
        mock_db.flush.assert_called_once()

    def test_on_approved(self):
        """测试审批通过时回调"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet
        mock_instance = MagicMock(spec=ApprovalInstance)

        adapter.on_approved(123, mock_instance)

        assert mock_timesheet.status == "APPROVED"
        assert mock_timesheet.approve_time is not None
        mock_db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回时回调"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet
        mock_instance = MagicMock(spec=ApprovalInstance)

        adapter.on_rejected(123, mock_instance)

        assert mock_timesheet.status == "REJECTED"
        mock_db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试撤回时回调"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet
        mock_instance = MagicMock(spec=ApprovalInstance)

        adapter.on_withdrawn(123, mock_instance)

        assert mock_timesheet.status == "DRAFT"
        assert mock_timesheet.submit_time is None
        mock_db.flush.assert_called_once()

    def test_callback_timesheet_not_found(self):
        """测试工时记录不存在时回调不报错"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_instance = MagicMock(spec=ApprovalInstance)

        # 这些方法不应抛出异常
        adapter.on_submit(999, mock_instance)
        adapter.on_approved(999, mock_instance)
        adapter.on_rejected(999, mock_instance)
        adapter.on_withdrawn(999, mock_instance)


@pytest.mark.unit
class TestGetTitleAndSummary:
    """测试获取标题和摘要"""

    def test_get_title_success(self):
        """测试成功获取标题"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.user_name = "张三"
        mock_timesheet.work_date = datetime(2024, 1, 15)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        title = adapter.get_title(123)

        assert title == "工时审批 - 张三 2024-01-15"

    def test_get_title_no_work_date(self):
        """测试无工作日期时的标题"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.user_name = "李四"
        mock_timesheet.work_date = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        title = adapter.get_title(123)

        assert title == "工时审批 - 李四 "

    def test_get_title_timesheet_not_found(self):
        """测试工时记录不存在时的标题"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        title = adapter.get_title(999)

        assert title == "工时审批 - #999"

    def test_get_summary_success(self):
        """测试成功获取摘要"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.timesheet_no = "TS-001"
        mock_timesheet.status = "DRAFT"
        mock_timesheet.user_id = 1
        mock_timesheet.user_name = "张三"
        mock_timesheet.department_id = 10
        mock_timesheet.department_name = "研发部"
        mock_timesheet.project_id = 100
        mock_timesheet.project_code = "PRJ-001"
        mock_timesheet.project_name = "测试项目"
        mock_timesheet.task_name = "开发"
        mock_timesheet.work_date = datetime(2024, 1, 15)
        mock_timesheet.hours = Decimal("8.0")
        mock_timesheet.overtime_type = "WEEKDAY"
        mock_timesheet.work_content = "加班开发"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = adapter.get_summary(123)

        assert "员工: 张三" in summary
        assert "日期: 2024-01-15" in summary
        assert "工时: 8.0小时" in summary
        assert "项目: 测试项目" in summary
        assert "加班: WEEKDAY" in summary

    def test_get_summary_normal_hours(self):
        """测试正常工时的摘要（不显示加班）"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.timesheet_no = "TS-002"
        mock_timesheet.status = "DRAFT"
        mock_timesheet.user_id = 2
        mock_timesheet.user_name = "李四"
        mock_timesheet.department_id = 20
        mock_timesheet.department_name = "测试部"
        mock_timesheet.project_id = 101
        mock_timesheet.project_code = "PRJ-002"
        mock_timesheet.project_name = "项目B"
        mock_timesheet.task_name = "测试"
        mock_timesheet.work_date = datetime(2024, 1, 16)
        mock_timesheet.hours = Decimal("7.5")
        mock_timesheet.overtime_type = "NORMAL"
        mock_timesheet.work_content = "正常工作"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = adapter.get_summary(123)

        assert "员工: 李四" in summary
        assert "工时: 7.5小时" in summary
        assert "加班" not in summary  # 正常工时不显示加班

    def test_get_summary_minimal_data(self):
        """测试最小数据的摘要"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.timesheet_no = "TS-003"
        mock_timesheet.status = "DRAFT"
        mock_timesheet.user_id = 3
        mock_timesheet.user_name = None
        mock_timesheet.department_id = None
        mock_timesheet.department_name = None
        mock_timesheet.project_id = None
        mock_timesheet.project_code = None
        mock_timesheet.project_name = None
        mock_timesheet.task_name = None
        mock_timesheet.work_date = None
        mock_timesheet.hours = None
        mock_timesheet.overtime_type = "NORMAL"
        mock_timesheet.work_content = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = adapter.get_summary(123)

        assert summary == ""

    def test_get_summary_timesheet_not_found(self):
        """测试工时记录不存在时的摘要"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        summary = adapter.get_summary(999)

        assert summary == ""


@pytest.mark.unit
class TestValidateSubmit:
    """测试提交验证"""

    def test_validate_submit_success_draft(self):
        """测试草稿状态可以提交"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "DRAFT"
        mock_timesheet.hours = Decimal("8.0")
        mock_timesheet.work_date = datetime(2024, 1, 15)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        assert valid is True
        assert message == ""

    def test_validate_submit_success_rejected(self):
        """测试驳回状态可以重新提交"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "REJECTED"
        mock_timesheet.hours = Decimal("4.5")
        mock_timesheet.work_date = datetime(2024, 1, 16)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        assert valid is True
        assert message == ""

    def test_validate_submit_timesheet_not_found(self):
        """测试工时记录不存在"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        valid, message = adapter.validate_submit(999)

        assert valid is False
        assert message == "工时记录不存在"

    def test_validate_submit_invalid_status(self):
        """测试无效状态不能提交"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "APPROVED"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert "当前状态(APPROVED)不允许提交审批" in message

    def test_validate_submit_pending_status(self):
        """测试待审批状态不能重复提交"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "SUBMITTED"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert "当前状态(SUBMITTED)不允许提交审批" in message

    def test_validate_submit_zero_hours(self):
        """测试工时为0不能提交"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "DRAFT"
        mock_timesheet.hours = Decimal("0")
        mock_timesheet.work_date = datetime(2024, 1, 15)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert message == "工时必须大于0"

    def test_validate_submit_negative_hours(self):
        """测试负工时不能提交"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "DRAFT"
        mock_timesheet.hours = Decimal("-2.0")
        mock_timesheet.work_date = datetime(2024, 1, 15)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert message == "工时必须大于0"

    def test_validate_submit_null_hours(self):
        """测试空工时不能提交"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "DRAFT"
        mock_timesheet.hours = None
        mock_timesheet.work_date = datetime(2024, 1, 15)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert message == "工时必须大于0"

    def test_validate_submit_no_work_date(self):
        """测试无工作日期不能提交"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "DRAFT"
        mock_timesheet.hours = Decimal("8.0")
        mock_timesheet.work_date = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        assert valid is False
        assert message == "请填写工作日期"

    def test_validate_submit_all_conditions_failed(self):
        """测试多个条件同时失败（按顺序返回第一个错误）"""
        mock_db = MagicMock()
        adapter = TimesheetApprovalAdapter(mock_db)

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = "APPROVED"
        mock_timesheet.hours = None
        mock_timesheet.work_date = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, message = adapter.validate_submit(123)

        # 应该返回第一个失败的验证
        assert valid is False
        assert "当前状态(APPROVED)不允许提交审批" in message
