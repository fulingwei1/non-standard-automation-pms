# -*- coding: utf-8 -*-
"""
工时提醒服务单元测试

目标：
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.services.timesheet_reminders.service import TimesheetReminderService
from app.models.timesheet_reminder import (
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
    TimesheetAnomalyRecord,
)


class TestTimesheetReminderServiceCreateConfig(unittest.TestCase):
    """测试提醒规则配置创建"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_create_reminder_config_success(self):
        """测试创建提醒规则配置成功"""
        # Mock: 规则编码不存在
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock

        # Mock manager.create_reminder_config 返回值
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
            rule_parameters={"check_days_ago": 1},
            priority="HIGH"
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.rule_code, "TEST_RULE")
        self.service.manager.create_reminder_config.assert_called_once()

    def test_create_reminder_config_duplicate_code(self):
        """测试创建重复规则编码"""
        # Mock: 规则编码已存在
        existing_config = MagicMock(spec=TimesheetReminderConfig)
        existing_config.rule_code = "EXISTING_RULE"
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = existing_config
        self.db.query.return_value = query_mock

        # 执行 & 验证
        with self.assertRaises(ValueError) as context:
            self.service.create_reminder_config(
                rule_code="EXISTING_RULE",
                rule_name="重复规则",
                reminder_type="MISSING_TIMESHEET",
                created_by=1
            )
        
        self.assertIn("规则编码已存在", str(context.exception))

    def test_create_reminder_config_with_all_parameters(self):
        """测试创建规则配置时传入所有参数"""
        # Mock: 规则编码不存在
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock

        # Mock manager 返回
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        self.service.manager.create_reminder_config = MagicMock(return_value=mock_config)

        # 执行
        result = self.service.create_reminder_config(
            rule_code="FULL_RULE",
            rule_name="完整规则",
            reminder_type="APPROVAL_TIMEOUT",
            created_by=1,
            rule_parameters={"timeout_days": 3},
            apply_to_departments=[1, 2],
            apply_to_roles=[3, 4],
            apply_to_users=[5, 6],
            notification_channels=["EMAIL", "WECHAT"],
            notification_template="您有工时待审批",
            remind_frequency="TWICE_DAILY",
            max_reminders_per_day=2,
            priority="URGENT"
        )

        # 验证
        self.assertIsNotNone(result)
        call_kwargs = self.service.manager.create_reminder_config.call_args[1]
        self.assertEqual(call_kwargs['rule_code'], "FULL_RULE")
        self.assertEqual(call_kwargs['apply_to_departments'], [1, 2])
        self.assertEqual(call_kwargs['notification_channels'], ["EMAIL", "WECHAT"])


class TestTimesheetReminderServiceUpdateConfig(unittest.TestCase):
    """测试提醒规则配置更新"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_update_reminder_config_success(self):
        """测试更新提醒规则配置成功"""
        # Mock manager返回
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        mock_config.id = 1
        mock_config.rule_name = "更新后的规则"
        self.service.manager.update_reminder_config = MagicMock(return_value=mock_config)

        # 执行
        result = self.service.update_reminder_config(
            config_id=1,
            rule_name="更新后的规则",
            is_active=False
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.rule_name, "更新后的规则")
        self.service.manager.update_reminder_config.assert_called_once_with(
            config_id=1,
            rule_name="更新后的规则",
            is_active=False
        )

    def test_update_reminder_config_not_found(self):
        """测试更新不存在的规则"""
        # Mock manager返回None
        self.service.manager.update_reminder_config = MagicMock(return_value=None)

        # 执行
        result = self.service.update_reminder_config(
            config_id=999,
            rule_name="不存在的规则"
        )

        # 验证
        self.assertIsNone(result)


class TestTimesheetReminderServiceListConfigs(unittest.TestCase):
    """测试提醒规则配置列表查询"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_list_reminder_configs_all(self):
        """测试查询所有规则配置"""
        # Mock返回
        mock_configs = [
            MagicMock(spec=TimesheetReminderConfig, id=1, rule_code="RULE1"),
            MagicMock(spec=TimesheetReminderConfig, id=2, rule_code="RULE2"),
        ]
        
        query_mock = MagicMock()
        query_mock.count.return_value = 2
        query_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_configs
        self.db.query.return_value = query_mock

        # 执行
        configs, total = self.service.list_reminder_configs()

        # 验证
        self.assertEqual(total, 2)
        self.assertEqual(len(configs), 2)
        self.assertEqual(configs[0].rule_code, "RULE1")

    def test_list_reminder_configs_filter_by_type(self):
        """测试按类型过滤"""
        # Mock返回
        mock_configs = [
            MagicMock(spec=TimesheetReminderConfig, id=1, reminder_type="MISSING_TIMESHEET"),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_configs
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        configs, total = self.service.list_reminder_configs(
            reminder_type="MISSING_TIMESHEET"
        )

        # 验证
        self.assertEqual(total, 1)
        self.assertEqual(len(configs), 1)
        query_mock.filter.assert_called()

    def test_list_reminder_configs_filter_by_active(self):
        """测试按启用状态过滤"""
        # Mock返回
        mock_configs = [
            MagicMock(spec=TimesheetReminderConfig, id=1, is_active=True),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_configs
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        configs, total = self.service.list_reminder_configs(is_active=True)

        # 验证
        self.assertEqual(total, 1)
        query_mock.filter.assert_called()

    def test_list_reminder_configs_with_pagination(self):
        """测试分页"""
        # Mock返回
        mock_configs = [
            MagicMock(spec=TimesheetReminderConfig, id=3, rule_code="RULE3"),
        ]
        
        query_mock = MagicMock()
        query_mock.count.return_value = 10
        limit_mock = MagicMock()
        offset_mock = MagicMock()
        offset_mock.all.return_value = mock_configs
        limit_mock.offset.return_value = offset_mock
        query_mock.order_by.return_value.limit.return_value = limit_mock
        self.db.query.return_value = query_mock

        # 执行
        configs, total = self.service.list_reminder_configs(limit=5, offset=10)

        # 验证
        self.assertEqual(total, 10)
        limit_mock.offset.assert_called_with(10)


class TestTimesheetReminderServicePendingReminders(unittest.TestCase):
    """测试待处理提醒列表"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_list_pending_reminders_success(self):
        """测试查询待处理提醒"""
        # Mock返回
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1, status=ReminderStatusEnum.PENDING),
            MagicMock(spec=TimesheetReminderRecord, id=2, status=ReminderStatusEnum.SENT),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.count.return_value = 2
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        reminders, total = self.service.list_pending_reminders(user_id=1)

        # 验证
        self.assertEqual(total, 2)
        self.assertEqual(len(reminders), 2)

    def test_list_pending_reminders_filter_by_type(self):
        """测试按类型过滤待处理提醒"""
        # Mock返回
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1, reminder_type="MISSING_TIMESHEET"),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        # 多次filter调用需要返回同一个对象
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        reminders, total = self.service.list_pending_reminders(
            user_id=1,
            reminder_type="MISSING_TIMESHEET"
        )

        # 验证
        self.assertEqual(total, 1)

    def test_list_pending_reminders_filter_by_priority(self):
        """测试按优先级过滤"""
        # Mock返回
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1, priority="URGENT"),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        # 多次filter调用需要返回同一个对象
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        reminders, total = self.service.list_pending_reminders(
            user_id=1,
            priority="URGENT"
        )

        # 验证
        self.assertEqual(total, 1)


class TestTimesheetReminderServiceReminderHistory(unittest.TestCase):
    """测试提醒历史记录"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_list_reminder_history_all(self):
        """测试查询所有历史记录"""
        # Mock返回
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1),
            MagicMock(spec=TimesheetReminderRecord, id=2),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.count.return_value = 2
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        reminders, total = self.service.list_reminder_history(user_id=1)

        # 验证
        self.assertEqual(total, 2)
        self.assertEqual(len(reminders), 2)

    def test_list_reminder_history_filter_by_status(self):
        """测试按状态过滤"""
        # Mock返回
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1, status="RESOLVED"),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        # 多次filter调用需要返回同一个对象
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        reminders, total = self.service.list_reminder_history(
            user_id=1,
            status="RESOLVED"
        )

        # 验证
        self.assertEqual(total, 1)

    def test_list_reminder_history_filter_by_date_range(self):
        """测试按日期范围过滤"""
        # Mock返回
        mock_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        # 多次filter调用需要返回同一个对象
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_reminders
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        start_date = datetime(2024, 2, 1)
        end_date = datetime(2024, 2, 28)
        reminders, total = self.service.list_reminder_history(
            user_id=1,
            start_date=start_date,
            end_date=end_date
        )

        # 验证
        self.assertEqual(total, 1)


class TestTimesheetReminderServiceDismissReminder(unittest.TestCase):
    """测试忽略提醒"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_dismiss_reminder_success(self):
        """测试忽略提醒成功"""
        # Mock: 提醒存在
        mock_reminder = MagicMock(spec=TimesheetReminderRecord)
        mock_reminder.id = 1
        mock_reminder.user_id = 1
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_reminder
        self.db.query.return_value = query_mock

        # Mock manager返回
        updated_reminder = MagicMock(spec=TimesheetReminderRecord)
        updated_reminder.status = ReminderStatusEnum.DISMISSED
        self.service.manager.dismiss_reminder = MagicMock(return_value=updated_reminder)

        # 执行
        result = self.service.dismiss_reminder(
            reminder_id=1,
            user_id=1,
            dismissed_by=1,
            reason="误报"
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.status, ReminderStatusEnum.DISMISSED)
        self.service.manager.dismiss_reminder.assert_called_once_with(
            reminder_id=1,
            dismissed_by=1,
            reason="误报"
        )

    def test_dismiss_reminder_not_found(self):
        """测试忽略不存在的提醒"""
        # Mock: 提醒不存在
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock

        # 执行
        result = self.service.dismiss_reminder(
            reminder_id=999,
            user_id=1,
            dismissed_by=1
        )

        # 验证
        self.assertIsNone(result)

    def test_dismiss_reminder_wrong_user(self):
        """测试忽略他人的提醒"""
        # Mock: 提醒属于其他用户
        mock_reminder = MagicMock(spec=TimesheetReminderRecord)
        mock_reminder.id = 1
        mock_reminder.user_id = 2  # 不同用户
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None  # filter会过滤掉
        self.db.query.return_value = query_mock

        # 执行
        result = self.service.dismiss_reminder(
            reminder_id=1,
            user_id=1,  # 请求用户ID为1
            dismissed_by=1
        )

        # 验证
        self.assertIsNone(result)


class TestTimesheetReminderServiceMarkRead(unittest.TestCase):
    """测试标记提醒已读"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_mark_reminder_read_success(self):
        """测试标记提醒已读成功"""
        # Mock: 提醒存在
        mock_reminder = MagicMock(spec=TimesheetReminderRecord)
        mock_reminder.id = 1
        mock_reminder.user_id = 1
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_reminder
        self.db.query.return_value = query_mock

        # Mock manager返回
        updated_reminder = MagicMock(spec=TimesheetReminderRecord)
        updated_reminder.status = ReminderStatusEnum.READ
        self.service.manager.mark_reminder_read = MagicMock(return_value=updated_reminder)

        # 执行
        result = self.service.mark_reminder_read(reminder_id=1, user_id=1)

        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.status, ReminderStatusEnum.READ)
        self.service.manager.mark_reminder_read.assert_called_once_with(1)

    def test_mark_reminder_read_not_found(self):
        """测试标记不存在的提醒"""
        # Mock: 提醒不存在
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock

        # 执行
        result = self.service.mark_reminder_read(reminder_id=999, user_id=1)

        # 验证
        self.assertIsNone(result)


class TestTimesheetReminderServiceAnomalies(unittest.TestCase):
    """测试异常记录列表"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_list_anomalies_all(self):
        """测试查询所有异常记录"""
        # Mock返回
        mock_anomalies = [
            MagicMock(spec=TimesheetAnomalyRecord, id=1),
            MagicMock(spec=TimesheetAnomalyRecord, id=2),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.count.return_value = 2
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_anomalies
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        anomalies, total = self.service.list_anomalies(user_id=1)

        # 验证
        self.assertEqual(total, 2)
        self.assertEqual(len(anomalies), 2)

    def test_list_anomalies_filter_by_type(self):
        """测试按异常类型过滤"""
        # Mock返回
        mock_anomalies = [
            MagicMock(spec=TimesheetAnomalyRecord, id=1, anomaly_type="DAILY_OVER_12"),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        # 多次filter调用需要返回同一个对象
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_anomalies
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        anomalies, total = self.service.list_anomalies(
            user_id=1,
            anomaly_type="DAILY_OVER_12"
        )

        # 验证
        self.assertEqual(total, 1)

    def test_list_anomalies_filter_by_resolved(self):
        """测试按解决状态过滤"""
        # Mock返回
        mock_anomalies = [
            MagicMock(spec=TimesheetAnomalyRecord, id=1, is_resolved=False),
        ]
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        # 多次filter调用需要返回同一个对象
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_anomalies
        query_mock.filter.return_value = filter_mock
        self.db.query.return_value = query_mock

        # 执行
        anomalies, total = self.service.list_anomalies(
            user_id=1,
            is_resolved=False
        )

        # 验证
        self.assertEqual(total, 1)


class TestTimesheetReminderServiceResolveAnomaly(unittest.TestCase):
    """测试解决异常记录"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_resolve_anomaly_success(self):
        """测试解决异常记录成功"""
        # Mock: 异常存在
        mock_anomaly = MagicMock(spec=TimesheetAnomalyRecord)
        mock_anomaly.id = 1
        mock_anomaly.user_id = 1
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_anomaly
        self.db.query.return_value = query_mock

        # Mock manager返回
        resolved_anomaly = MagicMock(spec=TimesheetAnomalyRecord)
        resolved_anomaly.is_resolved = True
        self.service.manager.resolve_anomaly = MagicMock(return_value=resolved_anomaly)

        # 执行
        result = self.service.resolve_anomaly(
            anomaly_id=1,
            user_id=1,
            resolved_by=1,
            resolution_note="已修正"
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertTrue(result.is_resolved)
        self.service.manager.resolve_anomaly.assert_called_once_with(
            anomaly_id=1,
            resolved_by=1,
            resolution_note="已修正"
        )

    def test_resolve_anomaly_not_found(self):
        """测试解决不存在的异常"""
        # Mock: 异常不存在
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock

        # 执行
        result = self.service.resolve_anomaly(
            anomaly_id=999,
            user_id=1,
            resolved_by=1
        )

        # 验证
        self.assertIsNone(result)


class TestTimesheetReminderServiceStatistics(unittest.TestCase):
    """测试提醒统计信息"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_get_reminder_statistics(self):
        """测试获取提醒统计信息"""
        # Mock返回值
        query_mock = MagicMock()
        
        # Mock count查询（多次调用，返回不同值）
        count_results = [10, 3, 2, 4, 1]  # total, pending, sent, dismissed, resolved
        query_mock.filter.return_value.count.side_effect = count_results
        
        # Mock按类型统计
        by_type_results = [
            ("MISSING_TIMESHEET", 5),
            ("APPROVAL_TIMEOUT", 3),
            ("ANOMALY_TIMESHEET", 2),
        ]
        query_mock.filter.return_value.group_by.return_value.all.return_value = by_type_results
        
        # Mock按优先级统计
        by_priority_results = [
            ("HIGH", 3),
            ("NORMAL", 5),
            ("LOW", 2),
        ]
        
        # Mock最近提醒
        recent_reminders = [
            MagicMock(spec=TimesheetReminderRecord, id=1),
            MagicMock(spec=TimesheetReminderRecord, id=2),
        ]
        
        # 配置复杂的mock链
        def query_side_effect(*args, **kwargs):
            mock = MagicMock()
            
            # 为不同的查询返回不同的mock
            if len(args) > 0:
                model = args[0]
                if hasattr(model, '__name__') and 'reminder_type' in str(model):
                    # 按类型统计
                    mock.filter.return_value.group_by.return_value.all.return_value = by_type_results
                elif hasattr(model, '__name__') and 'priority' in str(model):
                    # 按优先级统计
                    mock.filter.return_value.group_by.return_value.all.return_value = by_priority_results
                else:
                    # 最近提醒
                    mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = recent_reminders
            
            # count查询
            mock.filter.return_value.count.side_effect = count_results
            
            return mock
        
        self.db.query.side_effect = query_side_effect

        # 执行
        stats = self.service.get_reminder_statistics(user_id=1)

        # 验证基础统计
        self.assertIn("total_reminders", stats)
        self.assertIn("pending_reminders", stats)
        self.assertIn("sent_reminders", stats)
        self.assertIn("dismissed_reminders", stats)
        self.assertIn("resolved_reminders", stats)
        
        # 验证分组统计
        self.assertIn("by_type", stats)
        self.assertIn("by_priority", stats)
        self.assertIn("recent_reminders", stats)

    def test_get_anomaly_statistics(self):
        """测试获取异常统计信息"""
        # Mock返回值
        query_mock = MagicMock()
        
        # Mock count查询
        count_results = [10, 3, 7]  # total, unresolved, resolved
        query_mock.filter.return_value.count.side_effect = count_results
        
        # Mock按类型统计
        by_type_results = [
            ("DAILY_OVER_12", 4),
            ("WEEKLY_OVER_60", 2),
        ]
        
        # Mock按严重度统计
        by_severity_results = [
            ("WARNING", 6),
            ("ERROR", 4),
        ]
        
        # Mock最近异常
        recent_anomalies = [
            MagicMock(spec=TimesheetAnomalyRecord, id=1),
        ]
        
        # 配置复杂的mock链
        def query_side_effect(*args, **kwargs):
            mock = MagicMock()
            mock.filter.return_value.count.side_effect = count_results
            mock.filter.return_value.group_by.return_value.all.return_value = by_type_results
            mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = recent_anomalies
            return mock
        
        self.db.query.side_effect = query_side_effect

        # 执行
        stats = self.service.get_anomaly_statistics(user_id=1)

        # 验证
        self.assertIn("total_anomalies", stats)
        self.assertIn("unresolved_anomalies", stats)
        self.assertIn("resolved_anomalies", stats)
        self.assertIn("by_type", stats)
        self.assertIn("by_severity", stats)
        self.assertIn("recent_anomalies", stats)


class TestTimesheetReminderServiceDashboard(unittest.TestCase):
    """测试Dashboard"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_get_dashboard(self):
        """测试获取Dashboard"""
        # Mock reminder_stats
        reminder_stats = {
            "total_reminders": 10,
            "pending_reminders": 3,
        }
        self.service.get_reminder_statistics = MagicMock(return_value=reminder_stats)

        # Mock anomaly_stats
        anomaly_stats = {
            "total_anomalies": 5,
            "unresolved_anomalies": 2,
        }
        self.service.get_anomaly_statistics = MagicMock(return_value=anomaly_stats)

        # Mock active_configs
        active_configs = [
            MagicMock(spec=TimesheetReminderConfig, id=1),
        ]
        query_mock = MagicMock()
        query_mock.filter.return_value.limit.return_value.all.return_value = active_configs
        
        # Mock urgent_items
        urgent_items = [
            MagicMock(spec=TimesheetReminderRecord, id=1, priority="URGENT"),
        ]
        
        # 配置db.query的返回
        def query_side_effect(model):
            if model == TimesheetReminderConfig:
                return query_mock
            else:
                # TimesheetReminderRecord
                mock = MagicMock()
                mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = urgent_items
                return mock
        
        self.db.query.side_effect = query_side_effect

        # 执行
        dashboard = self.service.get_dashboard(user_id=1)

        # 验证
        self.assertIn("reminder_stats", dashboard)
        self.assertIn("anomaly_stats", dashboard)
        self.assertIn("active_configs", dashboard)
        self.assertIn("urgent_items", dashboard)
        
        self.assertEqual(dashboard["reminder_stats"]["total_reminders"], 10)
        self.assertEqual(dashboard["anomaly_stats"]["total_anomalies"], 5)
        self.assertEqual(len(dashboard["active_configs"]), 1)
        self.assertEqual(len(dashboard["urgent_items"]), 1)


class TestTimesheetReminderServiceEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = TimesheetReminderService(self.db)

    def test_list_configs_empty_result(self):
        """测试查询结果为空"""
        query_mock = MagicMock()
        query_mock.count.return_value = 0
        query_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []
        self.db.query.return_value = query_mock

        configs, total = self.service.list_reminder_configs()
        
        self.assertEqual(total, 0)
        self.assertEqual(len(configs), 0)

    def test_list_pending_reminders_with_zero_limit(self):
        """测试limit为0的情况"""
        query_mock = MagicMock()
        query_mock.filter.return_value.count.return_value = 10
        query_mock.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []
        self.db.query.return_value = query_mock

        reminders, total = self.service.list_pending_reminders(user_id=1, limit=0)
        
        self.assertEqual(total, 10)
        self.assertEqual(len(reminders), 0)

    def test_create_config_with_minimal_params(self):
        """测试只传必需参数创建配置"""
        # Mock: 规则编码不存在
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock

        # Mock manager
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        self.service.manager.create_reminder_config = MagicMock(return_value=mock_config)

        # 执行（只传必需参数）
        result = self.service.create_reminder_config(
            rule_code="MIN_RULE",
            rule_name="最小规则",
            reminder_type="MISSING_TIMESHEET",
            created_by=1
        )

        # 验证
        self.assertIsNotNone(result)
        call_kwargs = self.service.manager.create_reminder_config.call_args[1]
        self.assertIsNone(call_kwargs.get('rule_parameters'))
        self.assertIsNone(call_kwargs.get('apply_to_departments'))

    def test_dismiss_reminder_without_reason(self):
        """测试忽略提醒时不提供原因"""
        # Mock: 提醒存在
        mock_reminder = MagicMock(spec=TimesheetReminderRecord)
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_reminder
        self.db.query.return_value = query_mock

        # Mock manager
        updated_reminder = MagicMock(spec=TimesheetReminderRecord)
        self.service.manager.dismiss_reminder = MagicMock(return_value=updated_reminder)

        # 执行（不提供reason）
        result = self.service.dismiss_reminder(
            reminder_id=1,
            user_id=1,
            dismissed_by=1
        )

        # 验证
        self.assertIsNotNone(result)
        call_kwargs = self.service.manager.dismiss_reminder.call_args[1]
        self.assertIsNone(call_kwargs.get('reason'))


if __name__ == "__main__":
    unittest.main()
