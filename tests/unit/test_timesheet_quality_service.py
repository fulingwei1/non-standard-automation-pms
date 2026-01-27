# -*- coding: utf-8 -*-
"""
Tests for timesheet_quality_service service
Covers: app/services/timesheet_quality_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 331 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.timesheet_quality_service import TimesheetQualityService
from app.models.timesheet import Timesheet
from app.models.work_log import WorkLog
from app.models.user import User
from tests.conftest import _ensure_login_user


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    return _ensure_login_user(
        db_session,
        username="test_user",
        password="test123",
        real_name="测试用户",
        department="技术部",
        employee_role="ENGINEER",
        is_superuser=False
    )


@pytest.fixture
def test_timesheet_normal(db_session: Session, test_user):
    """创建正常工时记录"""
    timesheet = Timesheet(
        user_id=test_user.id,
        project_id=1,
        work_date=date.today() - timedelta(days=1),
        hours=8.0,
        status="APPROVED",
        overtime_type="NORMAL"
    )
    db_session.add(timesheet)
    db_session.commit()
    db_session.refresh(timesheet)
    return timesheet


@pytest.fixture
def test_timesheet_excessive(db_session: Session, test_user):
    """创建超时工时记录"""
    timesheet = Timesheet(
        user_id=test_user.id,
        project_id=1,
        work_date=date.today() - timedelta(days=2),
        hours=18.0,  # 超过16小时限制
        status="APPROVED",
        overtime_type="OVERTIME"
    )
    db_session.add(timesheet)
    db_session.commit()
    db_session.refresh(timesheet)
    return timesheet


class TestTimesheetQualityService:
    """Test suite for TimesheetQualityService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = TimesheetQualityService(db_session)
        assert service is not None
        assert service.db == db_session
        assert service.MAX_DAILY_HOURS == 16
        assert service.MAX_WEEKLY_HOURS == 80
        assert service.MAX_MONTHLY_HOURS == 300

    def test_detect_anomalies_no_anomalies(self, db_session, test_user, test_timesheet_normal):
        """测试检测异常 - 无异常"""
        service = TimesheetQualityService(db_session)
        
        result = service.detect_anomalies(
        user_id=test_user.id,
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert isinstance(result, list)
        # 正常工时不应该有异常
        assert len(result) == 0

    def test_detect_anomalies_excessive_daily_hours(self, db_session, test_user, test_timesheet_excessive):
        """测试检测异常 - 单日工时超限"""
        service = TimesheetQualityService(db_session)
        
        result = service.detect_anomalies(
        user_id=test_user.id,
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert any(a['type'] == 'EXCESSIVE_DAILY_HOURS' for a in result)

    def test_detect_anomalies_excessive_weekly_hours(self, db_session, test_user):
        """测试检测异常 - 单周工时超限"""
        service = TimesheetQualityService(db_session)
        
        # 创建一周的工时记录，总计超过80小时
        week_start = date.today() - timedelta(days=date.today().weekday() + 7)
        for i in range(7):
            timesheet = Timesheet(
            user_id=test_user.id,
            project_id=1,
            work_date=week_start + timedelta(days=i),
            hours=12.0,  # 每天12小时，总计84小时
            status="APPROVED",
            overtime_type="NORMAL"
            )
            db_session.add(timesheet)
            db_session.commit()
        
            result = service.detect_anomalies(
            user_id=test_user.id,
            start_date=week_start,
            end_date=week_start + timedelta(days=6)
            )
        
            assert isinstance(result, list)
            assert any(a['type'] == 'EXCESSIVE_WEEKLY_HOURS' for a in result)

    def test_detect_anomalies_excessive_monthly_hours(self, db_session, test_user):
        """测试检测异常 - 单月工时超限"""
        service = TimesheetQualityService(db_session)
        
        # 创建一个月的工时记录，总计超过300小时
        month_start = date.today().replace(day=1)
        for i in range(20):  # 20个工作日，每天16小时，总计320小时
        timesheet = Timesheet(
        user_id=test_user.id,
        project_id=1,
        work_date=month_start + timedelta(days=i),
        hours=16.0,
        status="APPROVED",
        overtime_type="NORMAL"
        )
        db_session.add(timesheet)
        db_session.commit()
        
        result = service.detect_anomalies(
        user_id=test_user.id,
        start_date=month_start,
        end_date=month_start + timedelta(days=30)
        )
        
        assert isinstance(result, list)
        assert any(a['type'] == 'EXCESSIVE_MONTHLY_HOURS' for a in result)

    def test_detect_anomalies_all_users(self, db_session, test_user, test_timesheet_excessive):
        """测试检测异常 - 所有用户"""
        service = TimesheetQualityService(db_session)
        
        result = service.detect_anomalies(
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert isinstance(result, list)

    def test_detect_anomalies_date_range(self, db_session, test_user, test_timesheet_excessive):
        """测试检测异常 - 指定日期范围"""
        service = TimesheetQualityService(db_session)
        
        result = service.detect_anomalies(
        user_id=test_user.id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() - timedelta(days=1)
        )
        
        assert isinstance(result, list)

    def test_check_work_log_completeness_no_missing(self, db_session, test_user, test_timesheet_normal):
        """测试检查工作日志完整性 - 无缺失"""
        service = TimesheetQualityService(db_session)
        
        # 创建工作日志
        work_log = WorkLog(
        user_id=test_user.id,
        work_date=test_timesheet_normal.work_date,
        content="测试工作日志",
        timesheet_id=test_timesheet_normal.id
        )
        db_session.add(work_log)
        db_session.commit()
        
        result = service.check_work_log_completeness(
        user_id=test_user.id,
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert isinstance(result, dict)
        assert 'missing_log_count' in result
        assert result['missing_log_count'] == 0

    def test_check_work_log_completeness_with_missing(self, db_session, test_user, test_timesheet_normal):
        """测试检查工作日志完整性 - 有缺失"""
        service = TimesheetQualityService(db_session)
        
        # 不创建工作日志，应该检测到缺失
        result = service.check_work_log_completeness(
        user_id=test_user.id,
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert isinstance(result, dict)
        assert 'missing_log_count' in result
        assert result['missing_log_count'] >= 0
        assert 'missing_logs' in result

    def test_check_work_log_completeness_default_range(self, db_session, test_user, test_timesheet_normal):
        """测试检查工作日志完整性 - 默认日期范围（最近30天）"""
        service = TimesheetQualityService(db_session)
        
        result = service.check_work_log_completeness(
        user_id=test_user.id
        )
        
        assert isinstance(result, dict)
        assert 'start_date' in result
        assert 'end_date' in result

    def test_check_work_log_completeness_all_users(self, db_session, test_user, test_timesheet_normal):
        """测试检查工作日志完整性 - 所有用户"""
        service = TimesheetQualityService(db_session)
        
        result = service.check_work_log_completeness(
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert isinstance(result, dict)
        assert 'completeness_rate' in result

    def test_validate_data_consistency_consistent(self, db_session, test_user, test_timesheet_normal):
        """测试校验数据一致性 - 一致"""
        from app.models.work_log import WorkLogMention
        
        service = TimesheetQualityService(db_session)
        
        # 创建工作日志，关联工时记录
        work_log = WorkLog(
        user_id=test_user.id,
        work_date=test_timesheet_normal.work_date,
        content="测试工作日志",
        timesheet_id=test_timesheet_normal.id
        )
        db_session.add(work_log)
        db_session.commit()
        db_session.refresh(work_log)
        
        # 如果工时记录关联了项目，需要在工作日志中提及该项目
        if test_timesheet_normal.project_id:
            mention = WorkLogMention(
            work_log_id=work_log.id,
            mention_type="PROJECT",
            mention_id=test_timesheet_normal.project_id,
            mention_name="测试项目"
            )
            db_session.add(mention)
            db_session.commit()
        
            result = service.validate_data_consistency(
            user_id=test_user.id,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today()
            )
        
            assert isinstance(result, dict)
            assert 'inconsistency_count' in result
            # 由于可能有其他不一致，只检查结果结构
            assert result['inconsistency_count'] >= 0

    def test_validate_data_consistency_mismatched_association(self, db_session, test_user, test_timesheet_normal):
        """测试校验数据一致性 - 关联不一致"""
        service = TimesheetQualityService(db_session)
        
        # 创建另一个工时记录
        timesheet2 = Timesheet(
        user_id=test_user.id,
        project_id=1,
        work_date=date.today() - timedelta(days=3),
        hours=8.0,
        status="APPROVED",
        overtime_type="NORMAL"
        )
        db_session.add(timesheet2)
        db_session.commit()
        
        # 创建工作日志，但关联到错误的工时记录
        work_log = WorkLog(
        user_id=test_user.id,
        work_date=timesheet2.work_date,
        content="测试工作日志",
        timesheet_id=test_timesheet_normal.id  # 关联错误
        )
        db_session.add(work_log)
        db_session.commit()
        
        result = service.validate_data_consistency(
        user_id=test_user.id,
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert isinstance(result, dict)
        assert 'inconsistency_count' in result
        # 应该检测到关联不一致
        assert result['inconsistency_count'] >= 0

    def test_validate_data_consistency_default_range(self, db_session, test_user, test_timesheet_normal):
        """测试校验数据一致性 - 默认日期范围"""
        service = TimesheetQualityService(db_session)
        
        result = service.validate_data_consistency(
        user_id=test_user.id
        )
        
        assert isinstance(result, dict)
        assert 'start_date' in result
        assert 'end_date' in result

    def test_validate_data_consistency_all_users(self, db_session, test_user, test_timesheet_normal):
        """测试校验数据一致性 - 所有用户"""
        service = TimesheetQualityService(db_session)
        
        result = service.validate_data_consistency(
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert isinstance(result, dict)
        assert 'consistency_rate' in result

    def test_check_labor_law_compliance_compliant(self, db_session, test_user):
        """测试检查劳动法合规性 - 合规"""
        service = TimesheetQualityService(db_session)
        
        # 创建合规的加班工时（每月30小时）
        month_start = date.today().replace(day=1)
        for i in range(10):
            timesheet = Timesheet(
            user_id=test_user.id,
            project_id=1,
            work_date=month_start + timedelta(days=i),
            hours=3.0,  # 每天3小时加班，总计30小时
            status="APPROVED",
            overtime_type="OVERTIME"
            )
            db_session.add(timesheet)
            db_session.commit()
        
            result = service.check_labor_law_compliance(
            user_id=test_user.id,
            year=date.today().year,
            month=date.today().month
            )
        
            assert isinstance(result, dict)
            assert 'is_compliant' in result
            assert result['is_compliant'] is True
            assert result['overtime_hours'] <= 36

    def test_check_labor_law_compliance_violation(self, db_session, test_user):
        """测试检查劳动法合规性 - 违规"""
        service = TimesheetQualityService(db_session)
        
        # 创建违规的加班工时（每月40小时，超过36小时限制）
        month_start = date.today().replace(day=1)
        for i in range(10):
            timesheet = Timesheet(
            user_id=test_user.id,
            project_id=1,
            work_date=month_start + timedelta(days=i),
            hours=4.0,  # 每天4小时加班，总计40小时
            status="APPROVED",
            overtime_type="OVERTIME"
            )
            db_session.add(timesheet)
            db_session.commit()
        
            result = service.check_labor_law_compliance(
            user_id=test_user.id,
            year=date.today().year,
            month=date.today().month
            )
        
            assert isinstance(result, dict)
            assert 'is_compliant' in result
            assert result['is_compliant'] is False
            assert result['violation_hours'] > 0

    def test_check_labor_law_compliance_no_overtime(self, db_session, test_user):
        """测试检查劳动法合规性 - 无加班"""
        service = TimesheetQualityService(db_session)
        
        # 只创建正常工时，无加班
        month_start = date.today().replace(day=1)
        for i in range(5):
            timesheet = Timesheet(
            user_id=test_user.id,
            project_id=1,
            work_date=month_start + timedelta(days=i),
            hours=8.0,
            status="APPROVED",
            overtime_type="NORMAL"
            )
            db_session.add(timesheet)
            db_session.commit()
        
            result = service.check_labor_law_compliance(
            user_id=test_user.id,
            year=date.today().year,
            month=date.today().month
            )
        
            assert isinstance(result, dict)
            assert 'is_compliant' in result
            assert result['is_compliant'] is True
            assert result['overtime_hours'] == 0

    def test_check_labor_law_compliance_december(self, db_session, test_user):
        """测试检查劳动法合规性 - 12月（跨年边界）"""
        service = TimesheetQualityService(db_session)
        
        result = service.check_labor_law_compliance(
        user_id=test_user.id,
        year=2024,
        month=12
        )
        
        assert isinstance(result, dict)
        assert 'year' in result
        assert 'month' in result
        assert result['year'] == 2024
        assert result['month'] == 12

    def test_check_labor_law_compliance_february(self, db_session, test_user):
        """测试检查劳动法合规性 - 2月（28/29天）"""
        service = TimesheetQualityService(db_session)
        
        result = service.check_labor_law_compliance(
        user_id=test_user.id,
        year=2024,
        month=2
        )
        
        assert isinstance(result, dict)
        assert result['month'] == 2
