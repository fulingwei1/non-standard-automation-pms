# -*- coding: utf-8 -*-
"""
TimesheetQualityService 综合单元测试

测试覆盖:
- detect_anomalies: 检测工时异常
- check_work_log_completeness: 检查工作日志完整性
- validate_data_consistency: 校验数据一致性
- check_labor_law_compliance: 检查劳动法合规性
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestTimesheetQualityServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        service = TimesheetQualityService(mock_db)

        assert service.db == mock_db

    def test_threshold_constants(self):
        """测试阈值常量"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        assert TimesheetQualityService.MAX_DAILY_HOURS == 16
        assert TimesheetQualityService.MIN_DAILY_HOURS == 0.5
        assert TimesheetQualityService.MAX_WEEKLY_HOURS == 80
        assert TimesheetQualityService.MAX_MONTHLY_HOURS == 300


class TestDetectAnomalies:
    """测试 detect_anomalies 方法"""

    def test_returns_empty_when_no_anomalies(self):
        """测试无异常时返回空列表"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.detect_anomalies()

        assert result == []

    def test_detects_excessive_daily_hours(self):
        """测试检测单日工时过多"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()

        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.work_date = date.today()
        mock_timesheet.hours = 18  # Exceeds MAX_DAILY_HOURS (16)

        mock_user = MagicMock()
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_timesheet]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = TimesheetQualityService(mock_db)
        result = service.detect_anomalies()

        assert len(result) >= 1
        anomaly = next((a for a in result if a["type"] == "EXCESSIVE_DAILY_HOURS"), None)
        assert anomaly is not None
        assert anomaly["severity"] == "HIGH"
        assert anomaly["hours"] == 18

    def test_detects_excessive_weekly_hours(self):
        """测试检测单周工时过多"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()

        # Create timesheets totaling > 80 hours in one week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        timesheets = []
        for i in range(7):
            ts = MagicMock()
            ts.user_id = 1
            ts.work_date = week_start + timedelta(days=i)
            ts.hours = 12  # 12 * 7 = 84 > 80
            timesheets.append(ts)

        mock_user = MagicMock()
        mock_user.real_name = "李四"
        mock_user.username = "lisi"

        mock_db.query.return_value.filter.return_value.all.return_value = timesheets
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = TimesheetQualityService(mock_db)
        result = service.detect_anomalies()

        anomaly = next((a for a in result if a["type"] == "EXCESSIVE_WEEKLY_HOURS"), None)
        assert anomaly is not None
        assert anomaly["severity"] == "MEDIUM"

    def test_detects_excessive_monthly_hours(self):
        """测试检测单月工时过多"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()

        # Create timesheets totaling > 300 hours in one month
        today = date.today()
        month_start = today.replace(day=1)

        timesheets = []
        for i in range(25):
            ts = MagicMock()
            ts.user_id = 1
            ts.work_date = month_start + timedelta(days=i)
            ts.hours = 13  # 13 * 25 = 325 > 300
            timesheets.append(ts)

        mock_user = MagicMock()
        mock_user.real_name = "王五"
        mock_user.username = "wangwu"

        mock_db.query.return_value.filter.return_value.all.return_value = timesheets
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = TimesheetQualityService(mock_db)
        result = service.detect_anomalies()

        anomaly = next((a for a in result if a["type"] == "EXCESSIVE_MONTHLY_HOURS"), None)
        assert anomaly is not None

    def test_filters_by_user_id(self):
        """测试按用户ID筛选"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.detect_anomalies(user_id=1)

        assert result == []

    def test_filters_by_date_range(self):
        """测试按日期范围筛选"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.detect_anomalies(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )

        assert result == []


class TestCheckWorkLogCompleteness:
    """测试 check_work_log_completeness 方法"""

    def test_returns_100_completeness_when_all_logs_present(self):
        """测试所有日志都存在时返回100%完整度"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()

        # No missing logs
        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.check_work_log_completeness()

        assert result["completeness_rate"] == 100

    def test_detects_missing_work_logs(self):
        """测试检测缺失的工作日志"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()

        timesheet_dates = [(date.today(), 1), (date.today() - timedelta(days=1), 1)]

        mock_user = MagicMock()
        mock_user.real_name = "测试用户"
        mock_user.username = "testuser"

        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = timesheet_dates
        # First call returns None (no work log), second returns user
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No work log for first date
            mock_user,
            None,  # No work log for second date
            mock_user,
        ]

        service = TimesheetQualityService(mock_db)
        result = service.check_work_log_completeness()

        assert result["missing_log_count"] == 2
        assert result["completeness_rate"] == 0

    def test_uses_default_date_range(self):
        """测试使用默认日期范围"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.check_work_log_completeness()

        # Default is last 30 days
        expected_start = date.today() - timedelta(days=30)
        assert result["start_date"] == str(expected_start)
        assert result["end_date"] == str(date.today())


class TestValidateDataConsistency:
    """测试 validate_data_consistency 方法"""

    def test_returns_100_consistency_when_all_consistent(self):
        """测试所有数据一致时返回100%一致性"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.validate_data_consistency()

        assert result["consistency_rate"] == 100

    def test_detects_mismatched_association(self):
        """测试检测关联不匹配"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()

        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.user_id = 10
        mock_timesheet.work_date = date.today()
        mock_timesheet.project_id = None

        mock_work_log = MagicMock()
        mock_work_log.id = 100
        mock_work_log.timesheet_id = 999  # Different from timesheet.id

        mock_user = MagicMock()
        mock_user.real_name = "测试用户"
        mock_user.username = "testuser"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_timesheet]
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_work_log,  # Work log exists but mismatched
            mock_user,
        ]

        service = TimesheetQualityService(mock_db)
        result = service.validate_data_consistency()

        assert result["inconsistency_count"] >= 1
        inconsistency = next(
            (i for i in result["inconsistencies"] if i["type"] == "MISMATCHED_ASSOCIATION"),
            None
        )
        assert inconsistency is not None

    def test_uses_default_date_range(self):
        """测试使用默认日期范围"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.validate_data_consistency()

        expected_start = date.today() - timedelta(days=30)
        assert result["start_date"] == str(expected_start)


class TestCheckLaborLawCompliance:
    """测试 check_labor_law_compliance 方法"""

    def test_returns_compliant_when_within_limit(self):
        """测试在限制内时返回合规"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()

        mock_timesheet = MagicMock()
        mock_timesheet.hours = 30  # Within 36 hour limit

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_timesheet]

        service = TimesheetQualityService(mock_db)
        result = service.check_labor_law_compliance(user_id=1, year=2026, month=1)

        assert result["is_compliant"] is True
        assert result["overtime_hours"] == 30
        assert result["violation_hours"] == 0

    def test_returns_non_compliant_when_exceeds_limit(self):
        """测试超过限制时返回不合规"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()

        mock_timesheet1 = MagicMock()
        mock_timesheet1.hours = 20

        mock_timesheet2 = MagicMock()
        mock_timesheet2.hours = 20  # Total: 40 > 36

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_timesheet1,
            mock_timesheet2,
        ]

        service = TimesheetQualityService(mock_db)
        result = service.check_labor_law_compliance(user_id=1, year=2026, month=1)

        assert result["is_compliant"] is False
        assert result["overtime_hours"] == 40
        assert result["violation_hours"] == 4  # 40 - 36

    def test_handles_december_correctly(self):
        """测试正确处理12月"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.check_labor_law_compliance(user_id=1, year=2026, month=12)

        assert result["year"] == 2026
        assert result["month"] == 12

    def test_returns_zero_when_no_overtime(self):
        """测试无加班时返回零"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.check_labor_law_compliance(user_id=1, year=2026, month=1)

        assert result["overtime_hours"] == 0
        assert result["is_compliant"] is True

    def test_message_contains_compliance_status(self):
        """测试消息包含合规状态"""
        from app.services.timesheet_quality_service import TimesheetQualityService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = TimesheetQualityService(mock_db)
        result = service.check_labor_law_compliance(user_id=1, year=2026, month=1)

        assert "符合" in result["message"]
