# -*- coding: utf-8 -*-
"""
TimesheetReminderManager 单元测试

策略：
- 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
- 让业务逻辑真正执行
- 覆盖主要方法和边界情况
- 目标覆盖率：70%+
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch, call

from app.models.timesheet_reminder import (
    AnomalyTypeEnum,
    NotificationChannelEnum,
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetAnomalyRecord,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
)
from app.services.timesheet_reminder.reminder_manager import (
    TimesheetReminderManager,
)


class TestTimesheetReminderManager(unittest.TestCase):
    """测试TimesheetReminderManager核心功能"""

    def setUp(self):
        """每个测试前初始化"""
        self.db = MagicMock()
        self.manager = TimesheetReminderManager(self.db)

    # ==================== 规则配置管理测试 ====================

    def test_create_reminder_config_minimal(self):
        """测试创建提醒规则配置（最小参数）"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            result = self.manager.create_reminder_config(
                rule_code='TEST_001',
                rule_name='测试规则',
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                rule_parameters={'check_days_ago': 1}
            )

            # 验证save_obj被调用
            mock_save.assert_called_once()
            saved_config = mock_save.call_args[0][1]

            # 验证返回值
            self.assertIsInstance(saved_config, TimesheetReminderConfig)
            self.assertEqual(saved_config.rule_code, 'TEST_001')
            self.assertEqual(saved_config.rule_name, '测试规则')
            self.assertEqual(saved_config.reminder_type, ReminderTypeEnum.MISSING_TIMESHEET)
            self.assertEqual(saved_config.rule_parameters, {'check_days_ago': 1})
            self.assertTrue(saved_config.is_active)
            self.assertEqual(saved_config.notification_channels, ['SYSTEM'])
            self.assertEqual(saved_config.remind_frequency, 'ONCE_DAILY')

    def test_create_reminder_config_full_parameters(self):
        """测试创建提醒规则配置（完整参数）"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            result = self.manager.create_reminder_config(
                rule_code='TEST_002',
                rule_name='完整测试规则',
                reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
                rule_parameters={'timeout_days': 3},
                apply_to_departments=[1, 2, 3],
                apply_to_roles=[10, 20],
                apply_to_users=[100, 200],
                notification_channels=['EMAIL', 'WECHAT'],
                notification_template='您有审批超时',
                remind_frequency='HOURLY',
                max_reminders_per_day=5,
                priority='HIGH',
                created_by=999
            )

            saved_config = mock_save.call_args[0][1]
            self.assertEqual(saved_config.apply_to_departments, [1, 2, 3])
            self.assertEqual(saved_config.apply_to_roles, [10, 20])
            self.assertEqual(saved_config.apply_to_users, [100, 200])
            self.assertEqual(saved_config.notification_channels, ['EMAIL', 'WECHAT'])
            self.assertEqual(saved_config.priority, 'HIGH')
            self.assertEqual(saved_config.created_by, 999)

    def test_update_reminder_config_success(self):
        """测试更新提醒规则配置（成功）"""
        mock_config = Mock(spec=TimesheetReminderConfig)
        mock_config.id = 1
        mock_config.rule_code = 'TEST_001'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_config
        self.db.query.return_value = mock_query

        result = self.manager.update_reminder_config(
            config_id=1,
            rule_name='更新后的规则',
            is_active=False,
            priority='LOW'
        )

        # 验证查询
        self.db.query.assert_called_once_with(TimesheetReminderConfig)
        
        # 验证属性更新
        self.assertEqual(result, mock_config)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_config)

    def test_update_reminder_config_not_found(self):
        """测试更新提醒规则配置（不存在）"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.manager.update_reminder_config(
            config_id=999,
            rule_name='不存在的规则'
        )

        self.assertIsNone(result)
        self.db.commit.assert_not_called()

    def test_get_reminder_config(self):
        """测试获取提醒规则配置"""
        mock_config = Mock(spec=TimesheetReminderConfig)
        mock_config.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_config
        self.db.query.return_value = mock_query

        result = self.manager.get_reminder_config(1)

        self.assertEqual(result, mock_config)
        self.db.query.assert_called_once_with(TimesheetReminderConfig)

    def test_get_active_configs_by_type(self):
        """测试获取指定类型的活跃配置"""
        mock_configs = [
            Mock(spec=TimesheetReminderConfig, id=1),
            Mock(spec=TimesheetReminderConfig, id=2)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_configs
        self.db.query.return_value = mock_query

        result = self.manager.get_active_configs_by_type(
            ReminderTypeEnum.MISSING_TIMESHEET
        )

        self.assertEqual(len(result), 2)
        self.db.query.assert_called_once_with(TimesheetReminderConfig)

    def test_check_user_applicable_no_restrictions(self):
        """测试用户适用性检查（无限制，所有用户适用）"""
        config = Mock(spec=TimesheetReminderConfig)
        config.apply_to_users = []
        config.apply_to_departments = []
        config.apply_to_roles = []

        result = self.manager.check_user_applicable(
            config=config,
            user_id=100
        )

        self.assertTrue(result)

    def test_check_user_applicable_user_match(self):
        """测试用户适用性检查（用户匹配）"""
        config = Mock(spec=TimesheetReminderConfig)
        config.apply_to_users = [100, 200, 300]
        config.apply_to_departments = []
        config.apply_to_roles = []

        result = self.manager.check_user_applicable(
            config=config,
            user_id=200
        )

        self.assertTrue(result)

    def test_check_user_applicable_department_match(self):
        """测试用户适用性检查（部门匹配）"""
        config = Mock(spec=TimesheetReminderConfig)
        config.apply_to_users = []
        config.apply_to_departments = [1, 2, 3]
        config.apply_to_roles = []

        result = self.manager.check_user_applicable(
            config=config,
            user_id=100,
            department_id=2
        )

        self.assertTrue(result)

    def test_check_user_applicable_role_match(self):
        """测试用户适用性检查（角色匹配）"""
        config = Mock(spec=TimesheetReminderConfig)
        config.apply_to_users = []
        config.apply_to_departments = []
        config.apply_to_roles = [10, 20, 30]

        result = self.manager.check_user_applicable(
            config=config,
            user_id=100,
            role_ids=[5, 20, 25]
        )

        self.assertTrue(result)

    def test_check_user_applicable_no_match(self):
        """测试用户适用性检查（不匹配）"""
        config = Mock(spec=TimesheetReminderConfig)
        config.apply_to_users = [100, 200]
        config.apply_to_departments = [1, 2]
        config.apply_to_roles = [10, 20]

        result = self.manager.check_user_applicable(
            config=config,
            user_id=999,
            department_id=99,
            role_ids=[99]
        )

        self.assertFalse(result)

    # ==================== 提醒记录管理测试 ====================

    def test_create_reminder_record_minimal(self):
        """测试创建提醒记录（最小参数）"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            # Mock _generate_reminder_no
            with patch.object(self.manager, '_generate_reminder_no', return_value='RM20260221140001'):
                result = self.manager.create_reminder_record(
                    reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                    user_id=100,
                    title='您有未填报的工时',
                    content='请及时填报2月20日的工时'
                )

                saved_record = mock_save.call_args[0][1]
                self.assertIsInstance(saved_record, TimesheetReminderRecord)
                self.assertEqual(saved_record.reminder_no, 'RM20260221140001')
                self.assertEqual(saved_record.user_id, 100)
                self.assertEqual(saved_record.title, '您有未填报的工时')
                self.assertEqual(saved_record.status, ReminderStatusEnum.PENDING)
                self.assertEqual(saved_record.notification_channels, ['SYSTEM'])

    def test_create_reminder_record_full_parameters(self):
        """测试创建提醒记录（完整参数）"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            with patch.object(self.manager, '_generate_reminder_no', return_value='RA20260221140002'):
                result = self.manager.create_reminder_record(
                    reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
                    user_id=200,
                    title='审批超时提醒',
                    content='您有审批单已超时3天',
                    user_name='张三',
                    config_id=10,
                    source_type='APPROVAL',
                    source_id=5000,
                    extra_data={'approval_no': 'AP001'},
                    priority='HIGH',
                    notification_channels=['EMAIL', 'WECHAT']
                )

                saved_record = mock_save.call_args[0][1]
                self.assertEqual(saved_record.user_name, '张三')
                self.assertEqual(saved_record.config_id, 10)
                self.assertEqual(saved_record.source_type, 'APPROVAL')
                self.assertEqual(saved_record.priority, 'HIGH')
                self.assertEqual(saved_record.extra_data, {'approval_no': 'AP001'})

    def test_mark_reminder_sent_success(self):
        """测试标记提醒已发送（成功）"""
        mock_record = Mock(spec=TimesheetReminderRecord)
        mock_record.id = 1
        mock_record.reminder_no = 'RM20260221140001'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        self.db.query.return_value = mock_query

        result = self.manager.mark_reminder_sent(
            reminder_id=1,
            channels=['EMAIL', 'WECHAT']
        )

        self.assertEqual(result.status, ReminderStatusEnum.SENT)
        self.assertEqual(result.notification_channels, ['EMAIL', 'WECHAT'])
        self.assertIsNotNone(result.sent_at)
        self.db.commit.assert_called_once()

    def test_mark_reminder_sent_not_found(self):
        """测试标记提醒已发送（不存在）"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.manager.mark_reminder_sent(999, ['EMAIL'])

        self.assertIsNone(result)
        self.db.commit.assert_not_called()

    def test_mark_reminder_read(self):
        """测试标记提醒已读"""
        mock_record = Mock(spec=TimesheetReminderRecord)
        mock_record.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        self.db.query.return_value = mock_query

        result = self.manager.mark_reminder_read(1)

        self.assertEqual(result.status, ReminderStatusEnum.READ)
        self.assertIsNotNone(result.read_at)
        self.db.commit.assert_called_once()

    def test_dismiss_reminder_success(self):
        """测试忽略提醒（成功）"""
        mock_record = Mock(spec=TimesheetReminderRecord)
        mock_record.id = 1
        mock_record.reminder_no = 'RM20260221140001'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        self.db.query.return_value = mock_query

        result = self.manager.dismiss_reminder(
            reminder_id=1,
            dismissed_by=100,
            reason='误报'
        )

        self.assertEqual(result.status, ReminderStatusEnum.DISMISSED)
        self.assertEqual(result.dismissed_by, 100)
        self.assertEqual(result.dismissed_reason, '误报')
        self.assertIsNotNone(result.dismissed_at)
        self.db.commit.assert_called_once()

    def test_dismiss_reminder_without_reason(self):
        """测试忽略提醒（无原因）"""
        mock_record = Mock(spec=TimesheetReminderRecord)
        mock_record.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        self.db.query.return_value = mock_query

        result = self.manager.dismiss_reminder(
            reminder_id=1,
            dismissed_by=100
        )

        self.assertEqual(result.status, ReminderStatusEnum.DISMISSED)
        self.assertEqual(result.dismissed_reason, None)

    def test_mark_reminder_resolved(self):
        """测试标记提醒已解决"""
        mock_record = Mock(spec=TimesheetReminderRecord)
        mock_record.id = 1
        mock_record.reminder_no = 'RM20260221140001'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        self.db.query.return_value = mock_query

        result = self.manager.mark_reminder_resolved(1)

        self.assertEqual(result.status, ReminderStatusEnum.RESOLVED)
        self.assertIsNotNone(result.resolved_at)
        self.db.commit.assert_called_once()

    def test_get_pending_reminders_no_filter(self):
        """测试获取待处理提醒（无过滤）"""
        mock_records = [
            Mock(spec=TimesheetReminderRecord, id=1),
            Mock(spec=TimesheetReminderRecord, id=2)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        result = self.manager.get_pending_reminders()

        self.assertEqual(len(result), 2)

    def test_get_pending_reminders_with_filters(self):
        """测试获取待处理提醒（带过滤）"""
        mock_records = [Mock(spec=TimesheetReminderRecord, id=1)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        result = self.manager.get_pending_reminders(
            user_id=100,
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            limit=50
        )

        self.assertEqual(len(result), 1)

    def test_get_reminder_history_no_filter(self):
        """测试获取提醒历史（无过滤）"""
        mock_records = [
            Mock(spec=TimesheetReminderRecord, id=1),
            Mock(spec=TimesheetReminderRecord, id=2),
            Mock(spec=TimesheetReminderRecord, id=3)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.offset.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        records, total = self.manager.get_reminder_history()

        self.assertEqual(len(records), 3)
        self.assertEqual(total, 3)

    def test_get_reminder_history_with_filters(self):
        """测试获取提醒历史（带过滤）"""
        mock_records = [Mock(spec=TimesheetReminderRecord, id=1)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.offset.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        start_date = datetime(2026, 2, 20, 0, 0, 0)
        end_date = datetime(2026, 2, 21, 23, 59, 59)

        records, total = self.manager.get_reminder_history(
            user_id=100,
            reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
            start_date=start_date,
            end_date=end_date,
            limit=20,
            offset=10
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(total, 1)

    def test_check_reminder_limit_under_limit(self):
        """测试提醒次数限制检查（未超限）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        self.db.query.return_value = mock_query

        result = self.manager.check_reminder_limit(
            user_id=100,
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            max_per_day=5
        )

        self.assertTrue(result)

    def test_check_reminder_limit_at_limit(self):
        """测试提醒次数限制检查（达到上限）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        self.db.query.return_value = mock_query

        result = self.manager.check_reminder_limit(
            user_id=100,
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            max_per_day=5
        )

        self.assertFalse(result)

    def test_check_reminder_limit_over_limit(self):
        """测试提醒次数限制检查（超过上限）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 7
        self.db.query.return_value = mock_query

        result = self.manager.check_reminder_limit(
            user_id=100,
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            max_per_day=5
        )

        self.assertFalse(result)

    # ==================== 异常记录管理测试 ====================

    def test_create_anomaly_record_minimal(self):
        """测试创建异常记录（最小参数）"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            result = self.manager.create_anomaly_record(
                timesheet_id=1000,
                user_id=100,
                anomaly_type=AnomalyTypeEnum.DAILY_OVER_12,
                description='单日工时超过12小时'
            )

            saved_record = mock_save.call_args[0][1]
            self.assertIsInstance(saved_record, TimesheetAnomalyRecord)
            self.assertEqual(saved_record.timesheet_id, 1000)
            self.assertEqual(saved_record.user_id, 100)
            self.assertEqual(saved_record.anomaly_type, AnomalyTypeEnum.DAILY_OVER_12)
            self.assertEqual(saved_record.severity, 'WARNING')
            self.assertFalse(saved_record.is_resolved)

    def test_create_anomaly_record_full_parameters(self):
        """测试创建异常记录（完整参数）"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            result = self.manager.create_anomaly_record(
                timesheet_id=2000,
                user_id=200,
                anomaly_type=AnomalyTypeEnum.WEEKLY_OVER_60,
                description='周工时超过60小时',
                user_name='李四',
                anomaly_data={'weekly_hours': 65, 'week': '2026-W08'},
                severity='CRITICAL',
                reminder_id=500
            )

            saved_record = mock_save.call_args[0][1]
            self.assertEqual(saved_record.user_name, '李四')
            self.assertEqual(saved_record.anomaly_data, {'weekly_hours': 65, 'week': '2026-W08'})
            self.assertEqual(saved_record.severity, 'CRITICAL')
            self.assertEqual(saved_record.reminder_id, 500)

    def test_resolve_anomaly_success(self):
        """测试解决异常（成功）"""
        mock_record = Mock(spec=TimesheetAnomalyRecord)
        mock_record.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        self.db.query.return_value = mock_query

        result = self.manager.resolve_anomaly(
            anomaly_id=1,
            resolved_by=100,
            resolution_note='已补填工时说明'
        )

        self.assertTrue(result.is_resolved)
        self.assertEqual(result.resolved_by, 100)
        self.assertEqual(result.resolution_note, '已补填工时说明')
        self.assertIsNotNone(result.resolved_at)
        self.db.commit.assert_called_once()

    def test_resolve_anomaly_not_found(self):
        """测试解决异常（不存在）"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.manager.resolve_anomaly(
            anomaly_id=999,
            resolved_by=100
        )

        self.assertIsNone(result)
        self.db.commit.assert_not_called()

    def test_resolve_anomaly_without_note(self):
        """测试解决异常（无备注）"""
        mock_record = Mock(spec=TimesheetAnomalyRecord)
        mock_record.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        self.db.query.return_value = mock_query

        result = self.manager.resolve_anomaly(
            anomaly_id=1,
            resolved_by=100
        )

        self.assertTrue(result.is_resolved)
        self.assertEqual(result.resolution_note, None)

    def test_get_unresolved_anomalies_no_filter(self):
        """测试获取未解决异常（无过滤）"""
        mock_records = [
            Mock(spec=TimesheetAnomalyRecord, id=1),
            Mock(spec=TimesheetAnomalyRecord, id=2)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        result = self.manager.get_unresolved_anomalies()

        self.assertEqual(len(result), 2)

    def test_get_unresolved_anomalies_with_filters(self):
        """测试获取未解决异常（带过滤）"""
        mock_records = [Mock(spec=TimesheetAnomalyRecord, id=1)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        result = self.manager.get_unresolved_anomalies(
            user_id=100,
            anomaly_type=AnomalyTypeEnum.DAILY_OVER_12,
            limit=50
        )

        self.assertEqual(len(result), 1)

    # ==================== 工具方法测试 ====================

    def test_generate_reminder_no_missing_timesheet(self):
        """测试生成提醒编号（未填报工时）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        self.db.query.return_value = mock_query

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 2, 21, 14, 30, 45)
            mock_dt.now.return_value = mock_now

            result = self.manager._generate_reminder_no(ReminderTypeEnum.MISSING_TIMESHEET)

            self.assertTrue(result.startswith('RM20260221143045'))
            self.assertTrue(result.endswith('0006'))  # count + 1

    def test_generate_reminder_no_approval_timeout(self):
        """测试生成提醒编号（审批超时）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        self.db.query.return_value = mock_query

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 2, 21, 9, 15, 30)
            mock_dt.now.return_value = mock_now

            result = self.manager._generate_reminder_no(ReminderTypeEnum.APPROVAL_TIMEOUT)

            self.assertTrue(result.startswith('RA20260221091530'))
            self.assertTrue(result.endswith('0001'))

    def test_generate_reminder_no_anomaly_timesheet(self):
        """测试生成提醒编号（异常工时）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 99
        self.db.query.return_value = mock_query

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 2, 21, 16, 45, 20)
            mock_dt.now.return_value = mock_now

            result = self.manager._generate_reminder_no(ReminderTypeEnum.ANOMALY_TIMESHEET)

            self.assertTrue(result.startswith('RN20260221164520'))
            self.assertTrue(result.endswith('0100'))

    def test_generate_reminder_no_weekend_work(self):
        """测试生成提醒编号（周末工时）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        self.db.query.return_value = mock_query

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 2, 21, 12, 0, 0)
            mock_dt.now.return_value = mock_now

            result = self.manager._generate_reminder_no(ReminderTypeEnum.WEEKEND_WORK)

            self.assertTrue(result.startswith('RW20260221120000'))

    def test_generate_reminder_no_holiday_work(self):
        """测试生成提醒编号（节假日工时）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        self.db.query.return_value = mock_query

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 2, 21, 10, 10, 10)
            mock_dt.now.return_value = mock_now

            result = self.manager._generate_reminder_no(ReminderTypeEnum.HOLIDAY_WORK)

            self.assertTrue(result.startswith('RH20260221101010'))

    def test_generate_reminder_no_sync_failure(self):
        """测试生成提醒编号（同步失败）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        self.db.query.return_value = mock_query

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 2, 21, 18, 30, 0)
            mock_dt.now.return_value = mock_now

            result = self.manager._generate_reminder_no(ReminderTypeEnum.SYNC_FAILURE)

            self.assertTrue(result.startswith('RS20260221183000'))

    # ==================== 边界情况测试 ====================

    def test_check_user_applicable_department_none(self):
        """测试用户适用性（部门为None）"""
        config = Mock(spec=TimesheetReminderConfig)
        config.apply_to_users = []
        config.apply_to_departments = [1, 2]
        config.apply_to_roles = []

        result = self.manager.check_user_applicable(
            config=config,
            user_id=100,
            department_id=None
        )

        self.assertFalse(result)

    def test_check_user_applicable_roles_none(self):
        """测试用户适用性（角色为None）"""
        config = Mock(spec=TimesheetReminderConfig)
        config.apply_to_users = []
        config.apply_to_departments = []
        config.apply_to_roles = [10, 20]

        result = self.manager.check_user_applicable(
            config=config,
            user_id=100,
            role_ids=None
        )

        self.assertFalse(result)

    def test_check_user_applicable_empty_role_list(self):
        """测试用户适用性（空角色列表）"""
        config = Mock(spec=TimesheetReminderConfig)
        config.apply_to_users = []
        config.apply_to_departments = []
        config.apply_to_roles = [10, 20]

        result = self.manager.check_user_applicable(
            config=config,
            user_id=100,
            role_ids=[]
        )

        self.assertFalse(result)

    def test_update_reminder_config_ignore_none_values(self):
        """测试更新配置时忽略None值"""
        mock_config = Mock(spec=TimesheetReminderConfig)
        mock_config.id = 1
        mock_config.rule_name = '原始名称'
        mock_config.priority = 'NORMAL'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_config
        self.db.query.return_value = mock_query

        # 传入None值应该被忽略，非None值会被设置
        result = self.manager.update_reminder_config(
            config_id=1,
            rule_name='新名称',
            priority=None
        )

        # rule_name会被更新，priority保持原值（因为传入None）
        self.assertEqual(mock_config.rule_name, '新名称')
        self.assertEqual(mock_config.priority, 'NORMAL')

    def test_create_reminder_record_empty_extra_data(self):
        """测试创建提醒记录时空extra_data"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            with patch.object(self.manager, '_generate_reminder_no', return_value='RM20260221140001'):
                result = self.manager.create_reminder_record(
                    reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                    user_id=100,
                    title='测试',
                    content='内容'
                )

                saved_record = mock_save.call_args[0][1]
                self.assertEqual(saved_record.extra_data, {})

    def test_create_anomaly_record_empty_anomaly_data(self):
        """测试创建异常记录时空anomaly_data"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            result = self.manager.create_anomaly_record(
                timesheet_id=1000,
                user_id=100,
                anomaly_type=AnomalyTypeEnum.DAILY_OVER_12,
                description='测试'
            )

            saved_record = mock_save.call_args[0][1]
            self.assertEqual(saved_record.anomaly_data, {})


if __name__ == '__main__':
    unittest.main()
