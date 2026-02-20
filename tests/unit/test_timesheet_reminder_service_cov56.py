# -*- coding: utf-8 -*-
"""
工时提醒服务单元测试
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.timesheet_reminder import (
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
    TimesheetAnomalyRecord,
)
from app.services.timesheet_reminders.service import TimesheetReminderService


class TestTimesheetReminderService(unittest.TestCase):
    """工时提醒服务测试类"""

    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.service = TimesheetReminderService(self.db)

    def tearDown(self):
        """测试清理"""
        self.db.reset_mock()

    # ==================== 提醒规则配置测试 ====================

    def test_create_reminder_config_success(self):
        """测试创建提醒规则配置成功"""
        # Mock 数据库查询，规则不存在
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Mock manager 创建方法
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        mock_config.id = 1
        mock_config.rule_code = "DAILY_SUBMIT"
        self.service.manager.create_reminder_config = MagicMock(return_value=mock_config)

        # 调用服务方法
        result = self.service.create_reminder_config(
            rule_code="DAILY_SUBMIT",
            rule_name="每日提交提醒",
            reminder_type="DAILY",
            created_by=1,
        )

        # 验证结果
        self.assertEqual(result.id, 1)
        self.assertEqual(result.rule_code, "DAILY_SUBMIT")
        self.db.query.assert_called_once()

    def test_create_reminder_config_duplicate_code(self):
        """测试创建提醒规则配置 - 规则编码重复"""
        # Mock 数据库查询，规则已存在
        existing_config = MagicMock(spec=TimesheetReminderConfig)
        existing_config.rule_code = "DAILY_SUBMIT"
        self.db.query.return_value.filter.return_value.first.return_value = existing_config

        # 调用服务方法，预期抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.create_reminder_config(
                rule_code="DAILY_SUBMIT",
                rule_name="每日提交提醒",
                reminder_type="DAILY",
                created_by=1,
            )

        self.assertIn("规则编码已存在", str(context.exception))

    def test_list_reminder_configs(self):
        """测试获取提醒规则配置列表"""
        # Mock 数据库查询
        mock_configs = [
            MagicMock(spec=TimesheetReminderConfig, id=1),
            MagicMock(spec=TimesheetReminderConfig, id=2),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_configs

        # 调用服务方法
        configs, total = self.service.list_reminder_configs(limit=10, offset=0)

        # 验证结果
        self.assertEqual(len(configs), 2)
        self.assertEqual(total, 2)
        self.db.query.assert_called_once()

    # ==================== 待处理提醒测试 ====================

    def test_list_pending_reminders(self):
        """测试获取待处理提醒列表"""
        # Mock 数据库查询
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1, user_id=1),
            MagicMock(spec=TimesheetReminderRecord, id=2, user_id=1),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders

        # 调用服务方法
        reminders, total = self.service.list_pending_reminders(user_id=1, limit=10, offset=0)

        # 验证结果
        self.assertEqual(len(reminders), 2)
        self.assertEqual(total, 2)

    # ==================== 提醒历史测试 ====================

    def test_list_reminder_history(self):
        """测试获取提醒历史记录"""
        # Mock 数据库查询
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1, user_id=1),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders

        # 调用服务方法
        reminders, total = self.service.list_reminder_history(user_id=1, limit=10, offset=0)

        # 验证结果
        self.assertEqual(len(reminders), 1)
        self.assertEqual(total, 1)

    # ==================== 提醒操作测试 ====================

    def test_dismiss_reminder_success(self):
        """测试忽略提醒成功"""
        # Mock 数据库查询
        mock_reminder = MagicMock(spec=TimesheetReminderRecord, id=1, user_id=1)
        self.db.query.return_value.filter.return_value.first.return_value = mock_reminder

        # Mock manager 方法
        self.service.manager.dismiss_reminder = MagicMock(return_value=mock_reminder)

        # 调用服务方法
        result = self.service.dismiss_reminder(
            reminder_id=1, user_id=1, dismissed_by=1, reason="测试忽略"
        )

        # 验证结果
        self.assertIsNotNone(result)
        self.service.manager.dismiss_reminder.assert_called_once_with(
            reminder_id=1, dismissed_by=1, reason="测试忽略"
        )

    def test_dismiss_reminder_not_found(self):
        """测试忽略提醒 - 提醒不存在"""
        # Mock 数据库查询，提醒不存在
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 调用服务方法
        result = self.service.dismiss_reminder(
            reminder_id=999, user_id=1, dismissed_by=1, reason="测试忽略"
        )

        # 验证结果
        self.assertIsNone(result)

    # ==================== 异常记录测试 ====================

    def test_list_anomalies(self):
        """测试获取异常记录列表"""
        # Mock 数据库查询
        mock_anomalies = [
            MagicMock(spec=TimesheetAnomalyRecord, id=1, user_id=1),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_anomalies

        # 调用服务方法
        anomalies, total = self.service.list_anomalies(user_id=1, limit=10, offset=0)

        # 验证结果
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(total, 1)

    def test_resolve_anomaly_success(self):
        """测试解决异常记录成功"""
        # Mock 数据库查询
        mock_anomaly = MagicMock(spec=TimesheetAnomalyRecord, id=1, user_id=1)
        self.db.query.return_value.filter.return_value.first.return_value = mock_anomaly

        # Mock manager 方法
        self.service.manager.resolve_anomaly = MagicMock(return_value=mock_anomaly)

        # 调用服务方法
        result = self.service.resolve_anomaly(
            anomaly_id=1, user_id=1, resolved_by=1, resolution_note="已解决"
        )

        # 验证结果
        self.assertIsNotNone(result)
        self.service.manager.resolve_anomaly.assert_called_once_with(
            anomaly_id=1, resolved_by=1, resolution_note="已解决"
        )

    # ==================== 统计测试 ====================

    def test_get_reminder_statistics(self):
        """测试获取提醒统计信息"""
        # Mock 各种统计查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        
        # Mock count 方法返回值
        mock_query.filter.return_value.count.return_value = 10
        
        # Mock 按类型统计
        mock_query.filter.return_value.group_by.return_value.all.return_value = [
            ("DAILY", 5),
            ("WEEKLY", 5),
        ]
        
        # Mock 最近提醒
        mock_reminders = [MagicMock(spec=TimesheetReminderRecord) for _ in range(3)]
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_reminders

        # 调用服务方法
        result = self.service.get_reminder_statistics(user_id=1)

        # 验证结果
        self.assertIn("total_reminders", result)
        self.assertIn("pending_reminders", result)
        self.assertIn("by_type", result)
        self.assertIn("recent_reminders", result)


if __name__ == "__main__":
    unittest.main()
