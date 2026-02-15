# -*- coding: utf-8 -*-
"""
工时提醒系统单元测试
包含15+测试用例
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.timesheet import Timesheet
from app.models.timesheet_reminder import (
    AnomalyTypeEnum,
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetAnomalyRecord,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
)
from app.models.user import User
from app.services.timesheet_reminder.anomaly_detector import TimesheetAnomalyDetector
from app.services.timesheet_reminder.reminder_manager import TimesheetReminderManager


# ==================== Fixtures ====================


@pytest.fixture
def test_user(db: Session):
    """创建测试用户"""
    user = User(
        username="test_engineer",
        email="test@example.com",
        real_name="测试工程师",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def reminder_manager(db: Session):
    """创建提醒管理器"""
    return TimesheetReminderManager(db)


@pytest.fixture
def anomaly_detector(db: Session):
    """创建异常检测器"""
    return TimesheetAnomalyDetector(db)


# ==================== 规则配置测试 ====================


def test_create_reminder_config(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试1: 创建提醒规则配置"""
    config = reminder_manager.create_reminder_config(
        rule_code="TEST_MISSING_001",
        rule_name="测试未填报提醒",
        reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
        rule_parameters={"check_days_ago": 1, "remind_time": "09:00"},
        notification_channels=["SYSTEM", "EMAIL"],
        priority="NORMAL",
        created_by=test_user.id,
    )

    assert config.id is not None
    assert config.rule_code == "TEST_MISSING_001"
    assert config.reminder_type == ReminderTypeEnum.MISSING_TIMESHEET
    assert config.is_active is True


def test_update_reminder_config(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试2: 更新提醒规则配置"""
    config = reminder_manager.create_reminder_config(
        rule_code="TEST_UPDATE_001",
        rule_name="测试更新",
        reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
        rule_parameters={"timeout_days": 3},
        created_by=test_user.id,
    )

    updated = reminder_manager.update_reminder_config(
        config_id=config.id,
        rule_name="更新后的名称",
        priority="HIGH"
    )

    assert updated.rule_name == "更新后的名称"
    assert updated.priority == "HIGH"


def test_check_user_applicable(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试3: 检查用户是否适用规则"""
    config = reminder_manager.create_reminder_config(
        rule_code="TEST_APPLY_001",
        rule_name="测试适用性",
        reminder_type=ReminderTypeEnum.ANOMALY_TIMESHEET,
        rule_parameters={},
        apply_to_users=[test_user.id],
        created_by=test_user.id,
    )

    is_applicable = reminder_manager.check_user_applicable(
        config=config,
        user_id=test_user.id
    )

    assert is_applicable is True


# ==================== 提醒记录测试 ====================


def test_create_reminder_record(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试4: 创建提醒记录"""
    record = reminder_manager.create_reminder_record(
        reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
        user_id=test_user.id,
        user_name=test_user.real_name,
        title="未填报工时提醒",
        content="您还未填报昨天的工时",
        priority="NORMAL",
    )

    assert record.id is not None
    assert record.reminder_no.startswith("RM")
    assert record.status == ReminderStatusEnum.PENDING


def test_mark_reminder_sent(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试5: 标记提醒已发送"""
    record = reminder_manager.create_reminder_record(
        reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
        user_id=test_user.id,
        title="测试",
        content="测试内容",
    )

    updated = reminder_manager.mark_reminder_sent(
        reminder_id=record.id,
        channels=["SYSTEM", "EMAIL"]
    )

    assert updated.status == ReminderStatusEnum.SENT
    assert updated.sent_at is not None
    assert "SYSTEM" in updated.notification_channels


def test_dismiss_reminder(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试6: 忽略提醒"""
    record = reminder_manager.create_reminder_record(
        reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
        user_id=test_user.id,
        title="测试",
        content="测试内容",
    )

    dismissed = reminder_manager.dismiss_reminder(
        reminder_id=record.id,
        dismissed_by=test_user.id,
        reason="已手动填报"
    )

    assert dismissed.status == ReminderStatusEnum.DISMISSED
    assert dismissed.dismissed_at is not None
    assert dismissed.dismissed_reason == "已手动填报"


def test_check_reminder_limit(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试7: 检查提醒次数限制"""
    # 创建多个提醒
    for i in range(3):
        reminder_manager.create_reminder_record(
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            user_id=test_user.id,
            title=f"测试{i}",
            content="测试内容",
        )

    # 检查是否超过限制
    can_send = reminder_manager.check_reminder_limit(
        user_id=test_user.id,
        reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
        max_per_day=3
    )

    assert can_send is False


# ==================== 异常检测测试 ====================


def test_detect_daily_over_12(db: Session, anomaly_detector: TimesheetAnomalyDetector, test_user: User):
    """测试8: 检测单日工时>12小时"""
    # 创建超时工时记录
    today = date.today()
    timesheet = Timesheet(
        user_id=test_user.id,
        user_name=test_user.real_name,
        work_date=today,
        hours=Decimal("14.5"),
        status="APPROVED",
    )
    db.add(timesheet)
    db.commit()

    anomalies = anomaly_detector.detect_daily_over_12(
        start_date=today,
        end_date=today,
        user_id=test_user.id
    )

    assert len(anomalies) > 0
    assert anomalies[0].anomaly_type == AnomalyTypeEnum.DAILY_OVER_12


def test_detect_daily_invalid(db: Session, anomaly_detector: TimesheetAnomalyDetector, test_user: User):
    """测试9: 检测无效工时（<0或>24）"""
    today = date.today()
    timesheet = Timesheet(
        user_id=test_user.id,
        user_name=test_user.real_name,
        work_date=today,
        hours=Decimal("25.0"),  # 超过24小时
        status="APPROVED",
    )
    db.add(timesheet)
    db.commit()

    anomalies = anomaly_detector.detect_daily_invalid(
        start_date=today,
        end_date=today,
        user_id=test_user.id
    )

    assert len(anomalies) > 0
    assert anomalies[0].anomaly_type == AnomalyTypeEnum.DAILY_INVALID


def test_detect_weekly_over_60(db: Session, anomaly_detector: TimesheetAnomalyDetector, test_user: User):
    """测试10: 检测周工时>60小时"""
    # 创建一周的工时记录，总计超过60小时
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    for i in range(7):
        timesheet = Timesheet(
            user_id=test_user.id,
            user_name=test_user.real_name,
            work_date=week_start + timedelta(days=i),
            hours=Decimal("10.0"),  # 每天10小时，7天=70小时
            status="APPROVED",
        )
        db.add(timesheet)
    db.commit()

    anomalies = anomaly_detector.detect_weekly_over_60(
        start_date=week_start,
        end_date=week_start + timedelta(days=6),
        user_id=test_user.id
    )

    assert len(anomalies) > 0
    assert anomalies[0].anomaly_type == AnomalyTypeEnum.WEEKLY_OVER_60


def test_detect_no_rest_7days(db: Session, anomaly_detector: TimesheetAnomalyDetector, test_user: User):
    """测试11: 检测连续7天无休息"""
    # 创建连续7天的工时记录
    today = date.today()

    for i in range(7):
        timesheet = Timesheet(
            user_id=test_user.id,
            user_name=test_user.real_name,
            work_date=today - timedelta(days=6-i),
            hours=Decimal("8.0"),
            status="APPROVED",
        )
        db.add(timesheet)
    db.commit()

    anomalies = anomaly_detector.detect_no_rest_7days(
        start_date=today - timedelta(days=6),
        end_date=today,
        user_id=test_user.id
    )

    assert len(anomalies) > 0
    assert anomalies[0].anomaly_type == AnomalyTypeEnum.NO_REST_7DAYS


def test_detect_progress_mismatch(db: Session, anomaly_detector: TimesheetAnomalyDetector, test_user: User):
    """测试12: 检测工时与进度不匹配"""
    today = date.today()
    timesheet = Timesheet(
        user_id=test_user.id,
        user_name=test_user.real_name,
        work_date=today,
        hours=Decimal("8.0"),
        task_id=1,
        progress_before=50,
        progress_after=50,  # 进度未变化
        status="APPROVED",
    )
    db.add(timesheet)
    db.commit()

    anomalies = anomaly_detector.detect_progress_mismatch(
        start_date=today,
        end_date=today,
        user_id=test_user.id
    )

    assert len(anomalies) > 0
    assert anomalies[0].anomaly_type == AnomalyTypeEnum.PROGRESS_MISMATCH


# ==================== 异常记录测试 ====================


def test_create_anomaly_record(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试13: 创建异常记录"""
    # 先创建工时记录
    timesheet = Timesheet(
        user_id=test_user.id,
        user_name=test_user.real_name,
        work_date=date.today(),
        hours=Decimal("8.0"),
        status="APPROVED",
    )
    db.add(timesheet)
    db.commit()

    anomaly = reminder_manager.create_anomaly_record(
        timesheet_id=timesheet.id,
        user_id=test_user.id,
        user_name=test_user.real_name,
        anomaly_type=AnomalyTypeEnum.DAILY_OVER_12,
        description="单日工时超标",
        anomaly_data={"hours": 14.5},
        severity="WARNING",
    )

    assert anomaly.id is not None
    assert anomaly.is_resolved is False


def test_resolve_anomaly(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试14: 解决异常"""
    timesheet = Timesheet(
        user_id=test_user.id,
        work_date=date.today(),
        hours=Decimal("8.0"),
        status="APPROVED",
    )
    db.add(timesheet)
    db.commit()

    anomaly = reminder_manager.create_anomaly_record(
        timesheet_id=timesheet.id,
        user_id=test_user.id,
        anomaly_type=AnomalyTypeEnum.DAILY_OVER_12,
        description="测试异常",
    )

    resolved = reminder_manager.resolve_anomaly(
        anomaly_id=anomaly.id,
        resolved_by=test_user.id,
        resolution_note="已修正工时"
    )

    assert resolved.is_resolved is True
    assert resolved.resolved_at is not None
    assert resolved.resolution_note == "已修正工时"


# ==================== 综合测试 ====================


def test_detect_all_anomalies(db: Session, anomaly_detector: TimesheetAnomalyDetector, test_user: User):
    """测试15: 检测所有类型异常"""
    # 创建各种异常工时
    today = date.today()

    # 异常1: 单日>12小时
    db.add(Timesheet(
        user_id=test_user.id,
        work_date=today,
        hours=Decimal("15.0"),
        status="APPROVED"
    ))

    # 异常2: 无效工时
    db.add(Timesheet(
        user_id=test_user.id,
        work_date=today - timedelta(days=1),
        hours=Decimal("30.0"),
        status="APPROVED"
    ))

    db.commit()

    anomalies = anomaly_detector.detect_all_anomalies(
        start_date=today - timedelta(days=1),
        end_date=today,
        user_id=test_user.id
    )

    assert len(anomalies) >= 2


def test_reminder_no_generation(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试16: 提醒编号生成规则"""
    # 创建不同类型的提醒
    missing_reminder = reminder_manager.create_reminder_record(
        reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
        user_id=test_user.id,
        title="未填报",
        content="测试",
    )

    approval_reminder = reminder_manager.create_reminder_record(
        reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
        user_id=test_user.id,
        title="审批超时",
        content="测试",
    )

    assert missing_reminder.reminder_no.startswith("RM")
    assert approval_reminder.reminder_no.startswith("RA")


def test_get_pending_reminders(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试17: 获取待处理提醒列表"""
    # 创建多个提醒
    for i in range(5):
        reminder_manager.create_reminder_record(
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            user_id=test_user.id,
            title=f"提醒{i}",
            content="测试",
            priority="NORMAL" if i < 3 else "HIGH"
        )

    pending = reminder_manager.get_pending_reminders(
        user_id=test_user.id,
        limit=10
    )

    assert len(pending) == 5
    # 验证按优先级排序（HIGH在前）
    assert pending[0].priority == "HIGH"


def test_get_reminder_history(db: Session, reminder_manager: TimesheetReminderManager, test_user: User):
    """测试18: 获取提醒历史"""
    # 创建并处理一些提醒
    reminder1 = reminder_manager.create_reminder_record(
        reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
        user_id=test_user.id,
        title="历史1",
        content="测试",
    )
    reminder_manager.mark_reminder_sent(reminder1.id, ["SYSTEM"])

    reminder2 = reminder_manager.create_reminder_record(
        reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
        user_id=test_user.id,
        title="历史2",
        content="测试",
    )
    reminder_manager.dismiss_reminder(reminder2.id, test_user.id)

    history, total = reminder_manager.get_reminder_history(
        user_id=test_user.id,
        limit=10
    )

    assert total >= 2
    assert len(history) >= 2
