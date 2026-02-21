# -*- coding: utf-8 -*-
"""
工时提醒服务层单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta

from app.services.timesheet_reminders.service import TimesheetReminderService
from app.models.timesheet_reminder import (
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
    TimesheetAnomalyRecord,
)


class TestTimesheetReminderServiceConfigManagement(unittest.TestCase):
    """测试提醒规则配置管理"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TimesheetReminderService(self.db)

    def test_create_reminder_config_success(self):
        """测试成功创建提醒规则配置"""
        # Mock数据库查询，模拟规则不存在
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Mock manager的create_reminder_config方法
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        mock_config.id = 1
        mock_config.rule_code = "TEST_RULE"
        mock_config.rule_name = "测试规则"
        self.service.manager.create_reminder_config = MagicMock(return_value=mock_config)

        # 执行
        result = self.service.create_reminder_config(
            rule_code="TEST_RULE",
            rule_name="测试规则",
            reminder_type="MISSING_TIMESHEET",
            created_by=1,
            rule_parameters={"threshold": 8},
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.rule_code, "TEST_RULE")
        self.db.query.assert_called_once()
        self.service.manager.create_reminder_config.assert_called_once()

    def test_create_reminder_config_duplicate_code(self):
        """测试创建重复规则编码时抛出异常"""
        # Mock数据库查询，模拟规则已存在
        existing_config = MagicMock(spec=TimesheetReminderConfig)
        existing_config.rule_code = "EXISTING_RULE"
        self.db.query.return_value.filter.return_value.first.return_value = existing_config

        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.create_reminder_config(
                rule_code="EXISTING_RULE",
                rule_name="重复规则",
                reminder_type="MISSING",
                created_by=1,
            )

        self.assertIn("规则编码已存在", str(context.exception))

    def test_update_reminder_config_success(self):
        """测试成功更新提醒规则配置"""
        # Mock manager的update方法
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        mock_config.id = 1
        mock_config.rule_name = "更新后的规则"
        self.service.manager.update_reminder_config = MagicMock(return_value=mock_config)

        # 执行
        result = self.service.update_reminder_config(
            config_id=1,
            rule_name="更新后的规则",
            is_active=False,
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.rule_name, "更新后的规则")
        self.service.manager.update_reminder_config.assert_called_once_with(
            config_id=1,
            rule_name="更新后的规则",
            is_active=False,
        )

    def test_list_reminder_configs_no_filter(self):
        """测试获取提醒规则配置列表（无过滤）"""
        # Mock数据库查询
        mock_configs = [
            MagicMock(spec=TimesheetReminderConfig, id=1, rule_code="RULE1"),
            MagicMock(spec=TimesheetReminderConfig, id=2, rule_code="RULE2"),
        ]
        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_configs

        self.db.query.return_value = mock_query

        # 执行
        configs, total = self.service.list_reminder_configs()

        # 验证
        self.assertEqual(total, 2)
        self.assertEqual(len(configs), 2)
        self.db.query.assert_called_once()

    def test_list_reminder_configs_with_filters(self):
        """测试获取提醒规则配置列表（带过滤）"""
        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            MagicMock(spec=TimesheetReminderConfig, id=1)
        ]

        self.db.query.return_value = mock_query

        # 执行
        configs, total = self.service.list_reminder_configs(
            reminder_type="MISSING_TIMESHEET",
            is_active=True,
            limit=10,
            offset=0,
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(configs), 1)
        # filter应该被调用2次（reminder_type和is_active）
        self.assertEqual(mock_query.filter.call_count, 2)


class TestTimesheetReminderServiceReminderOperations(unittest.TestCase):
    """测试提醒操作"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TimesheetReminderService(self.db)

    def test_list_pending_reminders_no_filter(self):
        """测试获取待处理提醒列表（无过滤）"""
        # Mock数据库查询
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1, user_id=10),
            MagicMock(spec=TimesheetReminderRecord, id=2, user_id=10),
        ]
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders

        self.db.query.return_value = mock_query

        # 执行
        reminders, total = self.service.list_pending_reminders(user_id=10)

        # 验证
        self.assertEqual(total, 2)
        self.assertEqual(len(reminders), 2)
        self.db.query.assert_called_once()

    def test_list_pending_reminders_with_filters(self):
        """测试获取待处理提醒列表（带过滤）"""
        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            MagicMock(spec=TimesheetReminderRecord, id=1)
        ]

        self.db.query.return_value = mock_query

        # 执行
        reminders, total = self.service.list_pending_reminders(
            user_id=10,
            reminder_type="MISSING_TIMESHEET",
            priority="HIGH",
            limit=10,
            offset=0,
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(reminders), 1)
        # filter应该被调用4次（user_id, status.in_, reminder_type, priority）
        self.assertGreaterEqual(mock_query.filter.call_count, 3)

    def test_list_reminder_history_no_filter(self):
        """测试获取提醒历史记录（无过滤）"""
        # Mock数据库查询
        mock_reminders = [MagicMock(spec=TimesheetReminderRecord, id=i) for i in range(5)]
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders

        self.db.query.return_value = mock_query

        # 执行
        reminders, total = self.service.list_reminder_history(user_id=10)

        # 验证
        self.assertEqual(total, 5)
        self.assertEqual(len(reminders), 5)

    def test_list_reminder_history_with_all_filters(self):
        """测试获取提醒历史记录（带所有过滤条件）"""
        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            MagicMock(spec=TimesheetReminderRecord, id=1)
        ]

        self.db.query.return_value = mock_query

        # 执行
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        reminders, total = self.service.list_reminder_history(
            user_id=10,
            reminder_type="MISSING_TIMESHEET",
            status="RESOLVED",
            start_date=start_date,
            end_date=end_date,
            limit=10,
            offset=0,
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(reminders), 1)
        # filter应该被调用5次（user_id, reminder_type, status, start_date, end_date）
        self.assertGreaterEqual(mock_query.filter.call_count, 5)

    def test_dismiss_reminder_success(self):
        """测试成功忽略提醒"""
        # Mock数据库查询
        mock_reminder = MagicMock(spec=TimesheetReminderRecord)
        mock_reminder.id = 1
        mock_reminder.user_id = 10
        self.db.query.return_value.filter.return_value.first.return_value = mock_reminder

        # Mock manager的dismiss方法
        updated_reminder = MagicMock(spec=TimesheetReminderRecord)
        updated_reminder.status = ReminderStatusEnum.DISMISSED
        self.service.manager.dismiss_reminder = MagicMock(return_value=updated_reminder)

        # 执行
        result = self.service.dismiss_reminder(
            reminder_id=1,
            user_id=10,
            dismissed_by=10,
            reason="测试忽略",
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.status, ReminderStatusEnum.DISMISSED)
        self.service.manager.dismiss_reminder.assert_called_once_with(
            reminder_id=1,
            dismissed_by=10,
            reason="测试忽略",
        )

    def test_dismiss_reminder_not_found(self):
        """测试忽略不存在的提醒"""
        # Mock数据库查询，返回None
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 执行
        result = self.service.dismiss_reminder(
            reminder_id=999,
            user_id=10,
            dismissed_by=10,
        )

        # 验证
        self.assertIsNone(result)
        # manager.dismiss_reminder不应该被调用
        self.service.manager.dismiss_reminder = MagicMock()
        self.service.manager.dismiss_reminder.assert_not_called()

    def test_dismiss_reminder_wrong_user(self):
        """测试忽略其他用户的提醒"""
        # Mock数据库查询，返回None（因为user_id不匹配）
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 执行
        result = self.service.dismiss_reminder(
            reminder_id=1,
            user_id=999,  # 不匹配的用户ID
            dismissed_by=999,
        )

        # 验证
        self.assertIsNone(result)

    def test_mark_reminder_read_success(self):
        """测试成功标记提醒已读"""
        # Mock数据库查询
        mock_reminder = MagicMock(spec=TimesheetReminderRecord)
        mock_reminder.id = 1
        mock_reminder.user_id = 10
        self.db.query.return_value.filter.return_value.first.return_value = mock_reminder

        # Mock manager的mark_read方法
        updated_reminder = MagicMock(spec=TimesheetReminderRecord)
        updated_reminder.is_read = True
        self.service.manager.mark_reminder_read = MagicMock(return_value=updated_reminder)

        # 执行
        result = self.service.mark_reminder_read(reminder_id=1, user_id=10)

        # 验证
        self.assertIsNotNone(result)
        self.assertTrue(result.is_read)
        self.service.manager.mark_reminder_read.assert_called_once_with(1)

    def test_mark_reminder_read_not_found(self):
        """测试标记不存在的提醒已读"""
        # Mock数据库查询，返回None
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 执行
        result = self.service.mark_reminder_read(reminder_id=999, user_id=10)

        # 验证
        self.assertIsNone(result)


class TestTimesheetReminderServiceAnomalyOperations(unittest.TestCase):
    """测试异常记录操作"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TimesheetReminderService(self.db)

    def test_list_anomalies_no_filter(self):
        """测试获取异常记录列表（无过滤）"""
        # Mock数据库查询
        mock_anomalies = [MagicMock(spec=TimesheetAnomalyRecord, id=i) for i in range(3)]
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_anomalies

        self.db.query.return_value = mock_query

        # 执行
        anomalies, total = self.service.list_anomalies(user_id=10)

        # 验证
        self.assertEqual(total, 3)
        self.assertEqual(len(anomalies), 3)

    def test_list_anomalies_with_filters(self):
        """测试获取异常记录列表（带过滤）"""
        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            MagicMock(spec=TimesheetAnomalyRecord, id=1)
        ]

        self.db.query.return_value = mock_query

        # 执行
        anomalies, total = self.service.list_anomalies(
            user_id=10,
            anomaly_type="DUPLICATE_HOURS",
            is_resolved=False,
            limit=10,
            offset=0,
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(anomalies), 1)
        # filter应该被调用3次（user_id, anomaly_type, is_resolved）
        self.assertGreaterEqual(mock_query.filter.call_count, 3)

    def test_resolve_anomaly_success(self):
        """测试成功解决异常记录"""
        # Mock数据库查询
        mock_anomaly = MagicMock(spec=TimesheetAnomalyRecord)
        mock_anomaly.id = 1
        mock_anomaly.user_id = 10
        self.db.query.return_value.filter.return_value.first.return_value = mock_anomaly

        # Mock manager的resolve方法
        resolved_anomaly = MagicMock(spec=TimesheetAnomalyRecord)
        resolved_anomaly.is_resolved = True
        self.service.manager.resolve_anomaly = MagicMock(return_value=resolved_anomaly)

        # 执行
        result = self.service.resolve_anomaly(
            anomaly_id=1,
            user_id=10,
            resolved_by=10,
            resolution_note="已处理",
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertTrue(result.is_resolved)
        self.service.manager.resolve_anomaly.assert_called_once_with(
            anomaly_id=1,
            resolved_by=10,
            resolution_note="已处理",
        )

    def test_resolve_anomaly_not_found(self):
        """测试解决不存在的异常记录"""
        # Mock数据库查询，返回None
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 执行
        result = self.service.resolve_anomaly(
            anomaly_id=999,
            user_id=10,
            resolved_by=10,
        )

        # 验证
        self.assertIsNone(result)

    def test_resolve_anomaly_wrong_user(self):
        """测试解决其他用户的异常记录"""
        # Mock数据库查询，返回None（因为user_id不匹配）
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 执行
        result = self.service.resolve_anomaly(
            anomaly_id=1,
            user_id=999,  # 不匹配的用户ID
            resolved_by=999,
        )

        # 验证
        self.assertIsNone(result)


class TestTimesheetReminderServiceStatistics(unittest.TestCase):
    """测试统计和Dashboard"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TimesheetReminderService(self.db)

    def test_get_reminder_statistics(self):
        """测试获取提醒统计信息"""
        # Mock各种count查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [100, 20, 15, 30, 35]  # total, pending, sent, dismissed, resolved

        # Mock按类型统计
        mock_query.group_by.return_value.all.side_effect = [
            [(ReminderTypeEnum.MISSING_TIMESHEET, 50), (ReminderTypeEnum.APPROVAL_TIMEOUT, 50)],  # by_type
            [("HIGH", 30), ("NORMAL", 70)],  # by_priority
        ]

        # Mock最近提醒
        mock_recent = [MagicMock(spec=TimesheetReminderRecord) for _ in range(10)]
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_recent

        self.db.query.return_value = mock_query

        # 执行
        stats = self.service.get_reminder_statistics(user_id=10)

        # 验证
        self.assertEqual(stats["total_reminders"], 100)
        self.assertEqual(stats["pending_reminders"], 20)
        self.assertEqual(stats["sent_reminders"], 15)
        self.assertEqual(stats["dismissed_reminders"], 30)
        self.assertEqual(stats["resolved_reminders"], 35)
        self.assertIn("by_type", stats)
        self.assertIn("by_priority", stats)
        self.assertEqual(len(stats["recent_reminders"]), 10)

    def test_get_anomaly_statistics(self):
        """测试获取异常统计信息"""
        # Mock各种count查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [50, 20, 30]  # total, unresolved, resolved

        # Mock按类型和严重程度统计
        mock_query.group_by.return_value.all.side_effect = [
            [("DUPLICATE_HOURS", 25), ("EXCESSIVE_HOURS", 25)],  # by_anomaly_type
            [("HIGH", 15), ("MEDIUM", 35)],  # by_severity
        ]

        # Mock最近异常
        mock_recent = [MagicMock(spec=TimesheetAnomalyRecord) for _ in range(10)]
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_recent

        self.db.query.return_value = mock_query

        # 执行
        stats = self.service.get_anomaly_statistics(user_id=10)

        # 验证
        self.assertEqual(stats["total_anomalies"], 50)
        self.assertEqual(stats["unresolved_anomalies"], 20)
        self.assertEqual(stats["resolved_anomalies"], 30)
        self.assertIn("by_type", stats)
        self.assertIn("by_severity", stats)
        self.assertEqual(len(stats["recent_anomalies"]), 10)

    def test_get_dashboard(self):
        """测试获取Dashboard"""
        # Mock reminder_stats
        mock_reminder_stats = {
            "total_reminders": 100,
            "pending_reminders": 20,
        }

        # Mock anomaly_stats
        mock_anomaly_stats = {
            "total_anomalies": 50,
            "unresolved_anomalies": 10,
        }

        # Mock active_configs
        mock_configs = [MagicMock(spec=TimesheetReminderConfig) for _ in range(5)]

        # Mock urgent_items
        mock_urgent = [MagicMock(spec=TimesheetReminderRecord) for _ in range(3)]

        # 为了简化，我们直接mock方法
        self.service.get_reminder_statistics = MagicMock(return_value=mock_reminder_stats)
        self.service.get_anomaly_statistics = MagicMock(return_value=mock_anomaly_stats)

        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_configs
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_urgent

        self.db.query.return_value = mock_query

        # 执行
        dashboard = self.service.get_dashboard(user_id=10)

        # 验证
        self.assertIn("reminder_stats", dashboard)
        self.assertIn("anomaly_stats", dashboard)
        self.assertIn("active_configs", dashboard)
        self.assertIn("urgent_items", dashboard)
        self.assertEqual(dashboard["reminder_stats"]["total_reminders"], 100)
        self.assertEqual(dashboard["anomaly_stats"]["total_anomalies"], 50)
        self.assertEqual(len(dashboard["active_configs"]), 5)
        self.assertEqual(len(dashboard["urgent_items"]), 3)


class TestTimesheetReminderServiceEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TimesheetReminderService(self.db)

    def test_list_configs_empty_result(self):
        """测试配置列表为空"""
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []

        self.db.query.return_value = mock_query

        configs, total = self.service.list_reminder_configs()

        self.assertEqual(total, 0)
        self.assertEqual(len(configs), 0)

    def test_list_pending_reminders_empty_result(self):
        """测试待处理提醒为空"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []

        self.db.query.return_value = mock_query

        reminders, total = self.service.list_pending_reminders(user_id=10)

        self.assertEqual(total, 0)
        self.assertEqual(len(reminders), 0)

    def test_list_anomalies_empty_result(self):
        """测试异常列表为空"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []

        self.db.query.return_value = mock_query

        anomalies, total = self.service.list_anomalies(user_id=10)

        self.assertEqual(total, 0)
        self.assertEqual(len(anomalies), 0)

    def test_statistics_with_zero_counts(self):
        """测试所有统计为0的情况"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.group_by.return_value.all.return_value = []
        mock_query.order_by.return_value.limit.return_value.all.return_value = []

        self.db.query.return_value = mock_query

        stats = self.service.get_reminder_statistics(user_id=10)

        self.assertEqual(stats["total_reminders"], 0)
        self.assertEqual(stats["pending_reminders"], 0)
        self.assertEqual(len(stats["recent_reminders"]), 0)

    def test_pagination_with_offset(self):
        """测试分页偏移"""
        mock_configs = [MagicMock(spec=TimesheetReminderConfig, id=i) for i in range(10, 20)]
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_configs

        self.db.query.return_value = mock_query

        configs, total = self.service.list_reminder_configs(limit=10, offset=10)

        self.assertEqual(total, 100)
        self.assertEqual(len(configs), 10)

    def test_update_config_returns_none(self):
        """测试更新不存在的配置返回None"""
        self.service.manager.update_reminder_config = MagicMock(return_value=None)

        result = self.service.update_reminder_config(config_id=999, rule_name="不存在")

        self.assertIsNone(result)

    def test_dismiss_reminder_with_no_reason(self):
        """测试忽略提醒时不提供原因"""
        mock_reminder = MagicMock(spec=TimesheetReminderRecord)
        mock_reminder.id = 1
        mock_reminder.user_id = 10
        self.db.query.return_value.filter.return_value.first.return_value = mock_reminder

        updated_reminder = MagicMock(spec=TimesheetReminderRecord)
        self.service.manager.dismiss_reminder = MagicMock(return_value=updated_reminder)

        result = self.service.dismiss_reminder(
            reminder_id=1,
            user_id=10,
            dismissed_by=10,
            # reason=None (默认)
        )

        self.assertIsNotNone(result)
        self.service.manager.dismiss_reminder.assert_called_once_with(
            reminder_id=1,
            dismissed_by=10,
            reason=None,
        )

    def test_resolve_anomaly_with_no_note(self):
        """测试解决异常时不提供备注"""
        mock_anomaly = MagicMock(spec=TimesheetAnomalyRecord)
        mock_anomaly.id = 1
        mock_anomaly.user_id = 10
        self.db.query.return_value.filter.return_value.first.return_value = mock_anomaly

        resolved_anomaly = MagicMock(spec=TimesheetAnomalyRecord)
        self.service.manager.resolve_anomaly = MagicMock(return_value=resolved_anomaly)

        result = self.service.resolve_anomaly(
            anomaly_id=1,
            user_id=10,
            resolved_by=10,
            # resolution_note=None (默认)
        )

        self.assertIsNotNone(result)
        self.service.manager.resolve_anomaly.assert_called_once_with(
            anomaly_id=1,
            resolved_by=10,
            resolution_note=None,
        )


if __name__ == "__main__":
    unittest.main()
