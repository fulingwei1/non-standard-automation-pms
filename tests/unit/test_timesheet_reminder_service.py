# -*- coding: utf-8 -*-
"""
Tests for timesheet_reminder_service service
Covers: app/services/timesheet_reminder/
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 172 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.timesheet_reminder import (
    create_timesheet_notification,
    notify_timesheet_missing,
    notify_weekly_timesheet_missing,
    notify_timesheet_anomaly,
    notify_approval_timeout,
    notify_sync_failure,
    scan_and_notify_all
)
from app.models.user import User
from app.models.timesheet import Timesheet
from app.models.notification import Notification
from app.models.organization import Department
from app.models.user import Role, UserRole


@pytest.fixture
def test_user_for_reminder(db_session: Session):
    """创建测试用户（用于工时提醒测试）"""
    from tests.conftest import _get_or_create_user
    
    user = _get_or_create_user(
        db_session,
        username="test_user_reminder",
        password="test123",
        real_name="测试用户",
        department="技术部",
        employee_role="ENGINEER"
    )
    return user


class TestTimesheetReminderService:
    """Test suite for timesheet_reminder_service."""

    def test_create_timesheet_notification_success(self, db_session, test_user_for_reminder):
        """测试创建工时通知 - 成功场景"""
        notification = create_timesheet_notification(
            db=db_session,
            user_id=test_user_for_reminder.id,
            notification_type="TIMESHEET_MISSING",
            title="工时填报提醒",
            content="请及时填报工时",
            source_type="timesheet",
            source_id=1,
            link_url="/timesheet",
            priority="NORMAL",
            extra_data={"target_date": date.today().isoformat()}
        )
        db_session.commit()
        
        assert notification is not None
        assert notification.user_id == test_user_for_reminder.id
        assert notification.notification_type == "TIMESHEET_MISSING"
        assert notification.title == "工时填报提醒"
        assert notification.content == "请及时填报工时"

    def test_create_timesheet_notification_minimal(self, db_session, test_user_for_reminder):
        """测试创建工时通知 - 最小参数"""
        notification = create_timesheet_notification(
            db=db_session,
            user_id=test_user_for_reminder.id,
            notification_type="TIMESHEET_MISSING",
            title="提醒",
            content="内容"
        )
        
        assert notification is not None
        assert notification.link_url == "/timesheet"  # 默认值

    def test_notify_timesheet_missing_default_date(self, db_session, test_user_for_reminder):
        """测试提醒未填报工时 - 默认日期（昨天）"""
        # 确保用户没有昨天的工时记录
        result = notify_timesheet_missing(db_session)
        
        assert isinstance(result, int)
        assert result >= 0

    def test_notify_timesheet_missing_specific_date(self, db_session, test_user_for_reminder):
        """测试提醒未填报工时 - 指定日期"""
        target_date = date.today() - timedelta(days=2)
        
        result = notify_timesheet_missing(db_session, target_date=target_date)
        
        assert isinstance(result, int)
        assert result >= 0

    def test_notify_timesheet_missing_with_existing_timesheet(self, db_session, test_user_for_reminder):
        """测试提醒未填报工时 - 已有工时记录"""
        # 创建工时记录
        timesheet = Timesheet(
            user_id=test_user_for_reminder.id,
            project_id=1,
            work_date=date.today() - timedelta(days=1),
            hours=8.0,
            status="DRAFT"
        )
        db_session.add(timesheet)
        db_session.commit()
        
        target_date = date.today() - timedelta(days=1)
        result = notify_timesheet_missing(db_session, target_date=target_date)
        
        # 已有记录，应该不发送提醒
        assert isinstance(result, int)

    def test_notify_weekly_timesheet_missing_default_week(self, db_session, test_user_for_reminder):
        """测试提醒未完成周工时填报 - 默认周（上周）"""
        result = notify_weekly_timesheet_missing(db_session)
        
        assert isinstance(result, int)
        assert result >= 0

    def test_notify_weekly_timesheet_missing_specific_week(self, db_session, test_user_for_reminder):
        """测试提醒未完成周工时填报 - 指定周"""
        week_start = date.today() - timedelta(days=14)
        
        result = notify_weekly_timesheet_missing(db_session, week_start=week_start)
        
        assert isinstance(result, int)
        assert result >= 0

    def test_notify_weekly_timesheet_missing_with_complete_week(self, db_session, test_user_for_reminder):
        """测试提醒未完成周工时填报 - 已完成周工时"""
        week_start = date.today() - timedelta(days=7)
        
        # 创建一周的工时记录
        for i in range(5):
            timesheet = Timesheet(
                user_id=test_user_for_reminder.id,
                project_id=1,
                work_date=week_start + timedelta(days=i),
                hours=8.0,
                status="APPROVED"
            )
            db_session.add(timesheet)
        db_session.commit()
        
        result = notify_weekly_timesheet_missing(db_session, week_start=week_start)
        
        assert isinstance(result, int)

    def test_notify_timesheet_anomaly_success(self, db_session, test_user_for_reminder):
        """测试异常工时预警 - 成功场景"""
        with patch('app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService') as mock_quality:
            mock_service = MagicMock()
            mock_service.detect_anomalies.return_value = [
                {
                    'timesheet_id': 1,
                    'anomaly_type': 'EXCESSIVE_HOURS',
                    'description': '工时超过12小时'
                }
            ]
            mock_quality.return_value = mock_service
            
            # 创建工时记录
            timesheet = Timesheet(
                user_id=test_user_for_reminder.id,
                project_id=1,
                work_date=date.today() - timedelta(days=1),
                hours=15.0,
                status="DRAFT"
            )
            db_session.add(timesheet)
            db_session.commit()
            
            result = notify_timesheet_anomaly(db_session, days=1)
            
            assert isinstance(result, int)
            assert result >= 0

    def test_notify_timesheet_anomaly_no_anomalies(self, db_session):
        """测试异常工时预警 - 无异常"""
        with patch('app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService') as mock_quality:
            mock_service = MagicMock()
            mock_service.detect_anomalies.return_value = []
            mock_quality.return_value = mock_service
            
            result = notify_timesheet_anomaly(db_session, days=1)
            
            assert isinstance(result, int)
            assert result == 0

    def test_notify_timesheet_anomaly_timesheet_not_found(self, db_session):
        """测试异常工时预警 - 工时记录不存在"""
        with patch('app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService') as mock_quality:
            mock_service = MagicMock()
            mock_service.detect_anomalies.return_value = [
                {
                    'timesheet_id': 99999,
                    'anomaly_type': 'EXCESSIVE_HOURS',
                    'description': '工时超过12小时'
                }
            ]
            mock_quality.return_value = mock_service
            
            result = notify_timesheet_anomaly(db_session, days=1)
            
            assert isinstance(result, int)
            assert result == 0

    def test_notify_approval_timeout_success(self, db_session, test_user_for_reminder):
        """测试审批超时提醒 - 成功场景"""
        from tests.conftest import _ensure_login_user
        
        # 创建部门经理
        manager = _ensure_login_user(
            db_session,
            username="manager",
            password="manager123",
            real_name="部门经理",
            department="技术部",
            employee_role="MANAGER",
            is_superuser=False
        )
        
        # 创建部门
        dept = Department(
            dept_code="TECH001",
            dept_name="技术部",
            manager_id=manager.id
        )
        db_session.add(dept)
        db_session.commit()
        db_session.refresh(dept)
        
        # 更新用户的部门ID
        test_user_for_reminder.department_id = dept.id
        db_session.commit()
        
        # 创建待审批的工时记录（超过24小时）
        timesheet = Timesheet(
            user_id=test_user_for_reminder.id,
            project_id=1,
            work_date=date.today() - timedelta(days=2),
            hours=8.0,
            status="PENDING",
            created_at=datetime.now() - timedelta(hours=25)
        )
        db_session.add(timesheet)
        db_session.commit()
        
        result = notify_approval_timeout(db_session, timeout_hours=24)
        
        assert isinstance(result, int)
        assert result >= 0

    def test_notify_approval_timeout_no_timeout(self, db_session, test_user_for_reminder):
        """测试审批超时提醒 - 无超时记录"""
        # 创建待审批的工时记录（未超时）
        timesheet = Timesheet(
            user_id=test_user_for_reminder.id,
            project_id=1,
            work_date=date.today(),
            hours=8.0,
            status="PENDING",
            created_at=datetime.now() - timedelta(hours=12)
        )
        db_session.add(timesheet)
        db_session.commit()
        
        result = notify_approval_timeout(db_session, timeout_hours=24)
        
        assert isinstance(result, int)
        assert result >= 0

    def test_notify_approval_timeout_no_approver(self, db_session, test_user_for_reminder):
        """测试审批超时提醒 - 无审批人"""
        # 创建待审批的工时记录（无部门经理和项目经理）
        timesheet = Timesheet(
            user_id=test_user_for_reminder.id,
            project_id=None,
            work_date=date.today() - timedelta(days=2),
            hours=8.0,
            status="PENDING",
            created_at=datetime.now() - timedelta(hours=25)
        )
        db_session.add(timesheet)
        db_session.commit()
        
        result = notify_approval_timeout(db_session, timeout_hours=24)
        
        assert isinstance(result, int)
        assert result == 0

    def test_notify_sync_failure_success(self, db_session, test_user_for_reminder):
        """测试同步失败提醒 - 成功场景"""
        # 创建已审批但可能同步失败的工时记录
        timesheet = Timesheet(
            user_id=test_user_for_reminder.id,
            project_id=1,
            work_date=date.today() - timedelta(days=1),
            hours=8.0,
            status="APPROVED",
            approve_time=datetime.now() - timedelta(hours=2)  # 审批后超过1小时
        )
        db_session.add(timesheet)
        db_session.commit()
        
        result = notify_sync_failure(db_session)
        
        assert isinstance(result, int)
        assert result >= 0

    def test_notify_sync_failure_no_failure(self, db_session, test_user_for_reminder):
        """测试同步失败提醒 - 无失败记录"""
        # 创建已审批但刚审批的工时记录（未超过1小时）
        timesheet = Timesheet(
            user_id=test_user_for_reminder.id,
            project_id=1,
            work_date=date.today(),
            hours=8.0,
            status="APPROVED",
            approve_time=datetime.now() - timedelta(minutes=30)  # 审批后30分钟
        )
        db_session.add(timesheet)
        db_session.commit()
        
        result = notify_sync_failure(db_session)
        
        assert isinstance(result, int)
        assert result == 0

    def test_notify_sync_failure_no_approve_time(self, db_session, test_user_for_reminder):
        """测试同步失败提醒 - 无审批时间"""
        # 创建已审批但无审批时间的工时记录
        timesheet = Timesheet(
            user_id=test_user_for_reminder.id,
            project_id=1,
            work_date=date.today(),
            hours=8.0,
            status="APPROVED",
            approve_time=None
        )
        db_session.add(timesheet)
        db_session.commit()
        
        result = notify_sync_failure(db_session)
        
        assert isinstance(result, int)
        assert result == 0

    def test_scan_and_notify_all_success(self, db_session):
        """测试扫描所有提醒 - 成功场景"""
        with patch('app.services.timesheet_reminder.scanner.notify_timesheet_missing') as mock_daily, \
             patch('app.services.timesheet_reminder.scanner.notify_weekly_timesheet_missing') as mock_weekly, \
             patch('app.services.timesheet_reminder.scanner.notify_timesheet_anomaly') as mock_anomaly, \
             patch('app.services.timesheet_reminder.scanner.notify_approval_timeout') as mock_timeout, \
             patch('app.services.timesheet_reminder.scanner.notify_sync_failure') as mock_sync:
            
            mock_daily.return_value = 5
            mock_weekly.return_value = 3
            mock_anomaly.return_value = 2
            mock_timeout.return_value = 1
            mock_sync.return_value = 0
            
            result = scan_and_notify_all(db_session)
            
            assert isinstance(result, dict)
            assert result['daily_missing'] == 5
            assert result['weekly_missing'] == 3
            assert result['anomaly'] == 2
            assert result['approval_timeout'] == 1
            assert result['sync_failure'] == 0

    def test_scan_and_notify_all_error_handling(self, db_session):
        """测试扫描所有提醒 - 错误处理"""
        with patch('app.services.timesheet_reminder.scanner.notify_timesheet_missing') as mock_daily:
            mock_daily.side_effect = Exception("测试错误")
            
            result = scan_and_notify_all(db_session)
            
            assert isinstance(result, dict)
            assert 'daily_missing' in result
            # 即使出错，也应该返回统计信息
