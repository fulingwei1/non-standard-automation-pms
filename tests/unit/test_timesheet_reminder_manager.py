# -*- coding: utf-8 -*-
"""
TimesheetReminderManager 单元测试

覆盖：
- create_reminder_config (创建规则配置)
- update_reminder_config (更新规则配置)
- get_active_configs_by_type
- check_user_applicable (用户适用性检查)
- create_reminder_record (创建提醒记录)
- mark_reminder_sent / mark_reminder_read / dismiss_reminder / mark_reminder_resolved
- get_pending_reminders / get_reminder_history
- check_reminder_limit (每日次数限制)
- create_anomaly_record / resolve_anomaly / get_unresolved_anomalies
- _generate_reminder_no (编号生成)
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.timesheet_reminder import (
    AnomalyTypeEnum,
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
    TimesheetAnomalyRecord,
)
from app.services.timesheet_reminder.reminder_manager import TimesheetReminderManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def manager(db):
    return TimesheetReminderManager(db)


# ---------------------------------------------------------------------------
# Tests: create_reminder_config
# ---------------------------------------------------------------------------

class TestCreateReminderConfig:
    def test_basic_creation(self, manager, db):
        with patch("app.services.timesheet_reminder.reminder_manager.save_obj") as mock_save:
            config = manager.create_reminder_config(
                rule_code="RULE_001",
                rule_name="缺填提醒",
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                rule_parameters={"days": 1},
                created_by=1,
            )
        mock_save.assert_called_once()
        assert config.rule_code == "RULE_001"
        assert config.rule_name == "缺填提醒"
        assert config.is_active is True

    def test_default_channels_is_system(self, manager, db):
        with patch("app.services.timesheet_reminder.reminder_manager.save_obj"):
            config = manager.create_reminder_config(
                rule_code="R002",
                rule_name="测试",
                reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
                rule_parameters={},
            )
        assert config.notification_channels == ["SYSTEM"]

    def test_custom_channels(self, manager, db):
        with patch("app.services.timesheet_reminder.reminder_manager.save_obj"):
            config = manager.create_reminder_config(
                rule_code="R003",
                rule_name="测试",
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                rule_parameters={},
                notification_channels=["EMAIL", "WECHAT"],
            )
        assert "EMAIL" in config.notification_channels
        assert "WECHAT" in config.notification_channels


# ---------------------------------------------------------------------------
# Tests: update_reminder_config
# ---------------------------------------------------------------------------

class TestUpdateReminderConfig:
    def test_not_found_returns_none(self, manager, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = manager.update_reminder_config(999, rule_name="新名称")
        assert result is None

    def test_update_attribute(self, manager, db):
        config = MagicMock(spec=TimesheetReminderConfig)
        config.rule_code = "R001"
        config.rule_name = "旧名称"
        db.query.return_value.filter.return_value.first.return_value = config

        manager.update_reminder_config(1, rule_name="新名称")
        assert config.rule_name == "新名称"
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: check_user_applicable
# ---------------------------------------------------------------------------

class TestCheckUserApplicable:
    def test_no_restrictions_applies_to_all(self, manager):
        config = MagicMock()
        config.apply_to_users = []
        config.apply_to_departments = []
        config.apply_to_roles = []
        assert manager.check_user_applicable(config, user_id=42) is True

    def test_user_in_list(self, manager):
        config = MagicMock()
        config.apply_to_users = [1, 2, 3]
        config.apply_to_departments = []
        config.apply_to_roles = []
        assert manager.check_user_applicable(config, user_id=2) is True

    def test_user_not_in_any_list(self, manager):
        config = MagicMock()
        config.apply_to_users = [10, 20]
        config.apply_to_departments = [5]
        config.apply_to_roles = [3]
        assert manager.check_user_applicable(config, user_id=99, department_id=99, role_ids=[99]) is False

    def test_user_in_department(self, manager):
        config = MagicMock()
        config.apply_to_users = []
        config.apply_to_departments = [7, 8]
        config.apply_to_roles = []
        assert manager.check_user_applicable(config, user_id=42, department_id=7) is True

    def test_user_in_role(self, manager):
        config = MagicMock()
        config.apply_to_users = []
        config.apply_to_departments = []
        config.apply_to_roles = [100, 200]
        assert manager.check_user_applicable(config, user_id=42, role_ids=[200]) is True


# ---------------------------------------------------------------------------
# Tests: create_reminder_record
# ---------------------------------------------------------------------------

class TestCreateReminderRecord:
    def test_record_created_with_correct_fields(self, manager, db):
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0

        with patch("app.services.timesheet_reminder.reminder_manager.save_obj") as mock_save:
            record = manager.create_reminder_record(
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                user_id=1,
                title="工时提醒",
                content="请填报工时",
                priority="HIGH",
            )

        mock_save.assert_called_once()
        assert record.user_id == 1
        assert record.title == "工时提醒"
        assert record.status == ReminderStatusEnum.PENDING

    def test_reminder_no_generated(self, manager, db):
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 2

        with patch("app.services.timesheet_reminder.reminder_manager.save_obj"):
            record = manager.create_reminder_record(
                reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
                user_id=2,
                title="审批超时",
                content="工时记录待审批",
            )

        assert record.reminder_no.startswith("RA")


# ---------------------------------------------------------------------------
# Tests: mark_reminder_sent
# ---------------------------------------------------------------------------

class TestMarkReminderSent:
    def test_not_found_returns_none(self, manager, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = manager.mark_reminder_sent(999, channels=["SYSTEM"])
        assert result is None

    def test_status_changed_to_sent(self, manager, db):
        record = MagicMock(spec=TimesheetReminderRecord)
        record.reminder_no = "RM001"
        db.query.return_value.filter.return_value.first.return_value = record

        result = manager.mark_reminder_sent(1, channels=["SYSTEM"])
        assert record.status == ReminderStatusEnum.SENT
        assert record.sent_at is not None


# ---------------------------------------------------------------------------
# Tests: mark_reminder_read
# ---------------------------------------------------------------------------

class TestMarkReminderRead:
    def test_not_found_returns_none(self, manager, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert manager.mark_reminder_read(999) is None

    def test_status_changed_to_read(self, manager, db):
        record = MagicMock(spec=TimesheetReminderRecord)
        db.query.return_value.filter.return_value.first.return_value = record

        manager.mark_reminder_read(1)
        assert record.status == ReminderStatusEnum.READ
        assert record.read_at is not None


# ---------------------------------------------------------------------------
# Tests: dismiss_reminder
# ---------------------------------------------------------------------------

class TestDismissReminder:
    def test_not_found_returns_none(self, manager, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert manager.dismiss_reminder(999, dismissed_by=1) is None

    def test_dismissed_fields_set(self, manager, db):
        record = MagicMock(spec=TimesheetReminderRecord)
        record.reminder_no = "RM001"
        db.query.return_value.filter.return_value.first.return_value = record

        manager.dismiss_reminder(1, dismissed_by=5, reason="无需处理")
        assert record.status == ReminderStatusEnum.DISMISSED
        assert record.dismissed_by == 5
        assert record.dismissed_reason == "无需处理"


# ---------------------------------------------------------------------------
# Tests: mark_reminder_resolved
# ---------------------------------------------------------------------------

class TestMarkReminderResolved:
    def test_not_found_returns_none(self, manager, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert manager.mark_reminder_resolved(999) is None

    def test_resolved_status_set(self, manager, db):
        record = MagicMock(spec=TimesheetReminderRecord)
        record.reminder_no = "RM001"
        db.query.return_value.filter.return_value.first.return_value = record

        manager.mark_reminder_resolved(1)
        assert record.status == ReminderStatusEnum.RESOLVED
        assert record.resolved_at is not None


# ---------------------------------------------------------------------------
# Tests: check_reminder_limit
# ---------------------------------------------------------------------------

class TestCheckReminderLimit:
    def test_within_limit_returns_true(self, manager, db):
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 0
        result = manager.check_reminder_limit(user_id=1, reminder_type=ReminderTypeEnum.MISSING_TIMESHEET, max_per_day=3)
        assert result is True

    def test_at_limit_returns_false(self, manager, db):
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 3
        result = manager.check_reminder_limit(user_id=1, reminder_type=ReminderTypeEnum.MISSING_TIMESHEET, max_per_day=3)
        assert result is False

    def test_exceeded_limit_returns_false(self, manager, db):
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 5
        result = manager.check_reminder_limit(user_id=1, reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT, max_per_day=2)
        assert result is False


# ---------------------------------------------------------------------------
# Tests: create_anomaly_record
# ---------------------------------------------------------------------------

class TestCreateAnomalyRecord:
    def test_anomaly_created(self, manager, db):
        with patch("app.services.timesheet_reminder.reminder_manager.save_obj") as mock_save:
            record = manager.create_anomaly_record(
                timesheet_id=10,
                user_id=1,
                anomaly_type=AnomalyTypeEnum.HOURS_TOO_LONG,
                description="工时超过24小时",
                severity="WARNING",
            )
        mock_save.assert_called_once()
        assert record.timesheet_id == 10
        assert record.anomaly_type == AnomalyTypeEnum.HOURS_TOO_LONG
        assert record.is_resolved is False


# ---------------------------------------------------------------------------
# Tests: resolve_anomaly
# ---------------------------------------------------------------------------

class TestResolveAnomaly:
    def test_not_found_returns_none(self, manager, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert manager.resolve_anomaly(999, resolved_by=1) is None

    def test_resolved_fields_set(self, manager, db):
        record = MagicMock(spec=TimesheetAnomalyRecord)
        db.query.return_value.filter.return_value.first.return_value = record

        manager.resolve_anomaly(1, resolved_by=5, resolution_note="已核实")
        assert record.is_resolved is True
        assert record.resolved_by == 5
        assert record.resolution_note == "已核实"
        assert record.resolved_at is not None


# ---------------------------------------------------------------------------
# Tests: get_pending_reminders
# ---------------------------------------------------------------------------

class TestGetPendingReminders:
    def test_returns_list(self, manager, db):
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = manager.get_pending_reminders()
        assert result == []

    def test_filter_by_user_id(self, manager, db):
        r = MagicMock(spec=TimesheetReminderRecord)
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [r]
        result = manager.get_pending_reminders(user_id=1)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Tests: _generate_reminder_no
# ---------------------------------------------------------------------------

class TestGenerateReminderNo:
    def test_prefix_missing_timesheet(self, manager, db):
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        no = manager._generate_reminder_no(ReminderTypeEnum.MISSING_TIMESHEET)
        assert no.startswith("RM")

    def test_prefix_approval_timeout(self, manager, db):
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 5
        no = manager._generate_reminder_no(ReminderTypeEnum.APPROVAL_TIMEOUT)
        assert no.startswith("RA")

    def test_seq_increments(self, manager, db):
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 9
        no = manager._generate_reminder_no(ReminderTypeEnum.MISSING_TIMESHEET)
        # seq = 10 → last 4 chars = "0010"
        assert no.endswith("0010")
