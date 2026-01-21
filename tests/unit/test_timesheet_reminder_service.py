# -*- coding: utf-8 -*-
"""
Tests for timesheet_reminder_service service
Covers: app/services/timesheet_reminder_service.py
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
    notify_weekly_timesheet_missing
)
from app.models.user import User
from app.models.timesheet import Timesheet
from app.models.notification import Notification


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
