# -*- coding: utf-8 -*-
"""
ReminderManager 增强单元测试
覆盖所有核心方法和边界条件
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from app.models.timesheet_reminder import (
    AnomalyTypeEnum,
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetAnomalyRecord,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
)
from app.services.timesheet_reminder.reminder_manager import TimesheetReminderManager


class TestTimesheetReminderManager(unittest.TestCase):
    """ReminderManager 测试套件"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.manager = TimesheetReminderManager(self.db)

    def tearDown(self):
        """测试后清理"""
        self.db.reset_mock()

    # ==================== 规则配置管理测试 ====================

    def test_create_reminder_config_with_minimal_params(self):
        """测试创建提醒规则配置 - 最小参数"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            config = self.manager.create_reminder_config(
                rule_code='TEST001',
                rule_name='测试规则',
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                rule_parameters={'key': 'value'}
            )

            self.assertIsNotNone(config)
            self.assertEqual(config.rule_code, 'TEST001')
            self.assertEqual(config.rule_name, '测试规则')
            self.assertEqual(config.reminder_type, ReminderTypeEnum.MISSING_TIMESHEET)
            self.assertEqual(config.rule_parameters, {'key': 'value'})
            self.assertEqual(config.apply_to_departments, [])
            self.assertEqual(config.apply_to_roles, [])
            self.assertEqual(config.apply_to_users, [])
            self.assertEqual(config.notification_channels, ['SYSTEM'])
            self.assertEqual(config.remind_frequency, 'ONCE_DAILY')
            self.assertEqual(config.max_reminders_per_day, 1)
            self.assertEqual(config.priority, 'NORMAL')
            self.assertTrue(config.is_active)
            mock_save.assert_called_once_with(self.db, config)

    def test_create_reminder_config_with_full_params(self):
        """测试创建提醒规则配置 - 完整参数"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            config = self.manager.create_reminder_config(
                rule_code='TEST002',
                rule_name='完整测试规则',
                reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
                rule_parameters={'timeout': 24},
                apply_to_departments=[1, 2, 3],
                apply_to_roles=[10, 20],
                apply_to_users=[100, 200],
                notification_channels=['EMAIL', 'SMS'],
                notification_template='模板内容',
                remind_frequency='HOURLY',
                max_reminders_per_day=5,
                priority='HIGH',
                created_by=999
            )

            self.assertEqual(config.apply_to_departments, [1, 2, 3])
            self.assertEqual(config.apply_to_roles, [10, 20])
            self.assertEqual(config.apply_to_users, [100, 200])
            self.assertEqual(config.notification_channels, ['EMAIL', 'SMS'])
            self.assertEqual(config.notification_template, '模板内容')
            self.assertEqual(config.remind_frequency, 'HOURLY')
            self.assertEqual(config.max_reminders_per_day, 5)
            self.assertEqual(config.priority, 'HIGH')
            self.assertEqual(config.created_by, 999)

    def test_update_reminder_config_success(self):
        """测试更新提醒规则配置 - 成功"""
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        mock_config.rule_code = 'OLD_CODE'
        mock_config.priority = 'NORMAL'
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_config

        result = self.manager.update_reminder_config(
            config_id=1,
            priority='HIGH',
            is_active=False,
            rule_name='更新后的名称'
        )

        self.assertEqual(result, mock_config)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_config)

    def test_update_reminder_config_not_found(self):
        """测试更新提醒规则配置 - 配置不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.manager.update_reminder_config(config_id=999, priority='HIGH')

        self.assertIsNone(result)
        self.db.commit.assert_not_called()

    def test_update_reminder_config_ignore_none_values(self):
        """测试更新提醒规则配置 - 忽略None值"""
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        mock_config.priority = 'NORMAL'
        self.db.query.return_value.filter.return_value.first.return_value = mock_config

        result = self.manager.update_reminder_config(
            config_id=1,
            priority='HIGH',
            rule_name=None  # 应该被忽略
        )

        # 验证只设置了非None的值
        self.assertEqual(result, mock_config)

    def test_get_reminder_config_exists(self):
        """测试获取提醒规则配置 - 存在"""
        mock_config = MagicMock(spec=TimesheetReminderConfig)
        self.db.query.return_value.filter.return_value.first.return_value = mock_config

        result = self.manager.get_reminder_config(1)

        self.assertEqual(result, mock_config)

    def test_get_reminder_config_not_exists(self):
        """测试获取提醒规则配置 - 不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.manager.get_reminder_config(999)

        self.assertIsNone(result)

    def test_get_active_configs_by_type(self):
        """测试获取指定类型的活跃配置"""
        mock_configs = [MagicMock(), MagicMock()]
        self.db.query.return_value.filter.return_value.all.return_value = mock_configs

        result = self.manager.get_active_configs_by_type(ReminderTypeEnum.MISSING_TIMESHEET)

        self.assertEqual(result, mock_configs)
        self.assertEqual(len(result), 2)

    def test_check_user_applicable_no_restrictions(self):
        """测试检查用户适用性 - 无限制（适用所有用户）"""
        config = TimesheetReminderConfig(
            rule_code='TEST',
            rule_name='Test',
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            rule_parameters={},
            apply_to_users=[],
            apply_to_departments=[],
            apply_to_roles=[]
        )

        result = self.manager.check_user_applicable(config, user_id=100)

        self.assertTrue(result)

    def test_check_user_applicable_by_user_id(self):
        """测试检查用户适用性 - 通过用户ID"""
        config = TimesheetReminderConfig(
            rule_code='TEST',
            rule_name='Test',
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            rule_parameters={},
            apply_to_users=[100, 200, 300],
            apply_to_departments=[],
            apply_to_roles=[]
        )

        self.assertTrue(self.manager.check_user_applicable(config, user_id=100))
        self.assertTrue(self.manager.check_user_applicable(config, user_id=200))
        self.assertFalse(self.manager.check_user_applicable(config, user_id=999))

    def test_check_user_applicable_by_department(self):
        """测试检查用户适用性 - 通过部门"""
        config = TimesheetReminderConfig(
            rule_code='TEST',
            rule_name='Test',
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            rule_parameters={},
            apply_to_users=[],
            apply_to_departments=[10, 20],
            apply_to_roles=[]
        )

        self.assertTrue(self.manager.check_user_applicable(config, user_id=100, department_id=10))
        self.assertFalse(self.manager.check_user_applicable(config, user_id=100, department_id=99))
        self.assertFalse(self.manager.check_user_applicable(config, user_id=100, department_id=None))

    def test_check_user_applicable_by_role(self):
        """测试检查用户适用性 - 通过角色"""
        config = TimesheetReminderConfig(
            rule_code='TEST',
            rule_name='Test',
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            rule_parameters={},
            apply_to_users=[],
            apply_to_departments=[],
            apply_to_roles=[5, 6, 7]
        )

        self.assertTrue(self.manager.check_user_applicable(config, user_id=100, role_ids=[5, 8]))
        self.assertTrue(self.manager.check_user_applicable(config, user_id=100, role_ids=[6]))
        self.assertFalse(self.manager.check_user_applicable(config, user_id=100, role_ids=[1, 2]))
        self.assertFalse(self.manager.check_user_applicable(config, user_id=100, role_ids=None))

    def test_check_user_applicable_multiple_conditions(self):
        """测试检查用户适用性 - 多重条件（任一满足即可）"""
        config = TimesheetReminderConfig(
            rule_code='TEST',
            rule_name='Test',
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            rule_parameters={},
            apply_to_users=[100],
            apply_to_departments=[10],
            apply_to_roles=[5]
        )

        # 满足用户ID
        self.assertTrue(self.manager.check_user_applicable(config, user_id=100, department_id=99, role_ids=[99]))
        # 满足部门
        self.assertTrue(self.manager.check_user_applicable(config, user_id=999, department_id=10, role_ids=[99]))
        # 满足角色
        self.assertTrue(self.manager.check_user_applicable(config, user_id=999, department_id=99, role_ids=[5]))
        # 都不满足
        self.assertFalse(self.manager.check_user_applicable(config, user_id=999, department_id=99, role_ids=[99]))

    # ==================== 提醒记录管理测试 ====================

    def test_create_reminder_record_minimal(self):
        """测试创建提醒记录 - 最小参数"""
        with patch.object(self.manager, '_generate_reminder_no', return_value='RM202601010001'):
            with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
                record = self.manager.create_reminder_record(
                    reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                    user_id=100,
                    title='测试提醒',
                    content='提醒内容'
                )

                self.assertEqual(record.reminder_no, 'RM202601010001')
                self.assertEqual(record.reminder_type, ReminderTypeEnum.MISSING_TIMESHEET)
                self.assertEqual(record.user_id, 100)
                self.assertEqual(record.title, '测试提醒')
                self.assertEqual(record.content, '提醒内容')
                self.assertEqual(record.status, ReminderStatusEnum.PENDING)
                self.assertEqual(record.priority, 'NORMAL')
                self.assertEqual(record.notification_channels, ['SYSTEM'])
                self.assertEqual(record.extra_data, {})
                mock_save.assert_called_once()

    def test_create_reminder_record_full(self):
        """测试创建提醒记录 - 完整参数"""
        with patch.object(self.manager, '_generate_reminder_no', return_value='RA202601010001'):
            with patch('app.services.timesheet_reminder.reminder_manager.save_obj'):
                record = self.manager.create_reminder_record(
                    reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
                    user_id=100,
                    title='审批超时',
                    content='您有待审批的工时单已超时',
                    user_name='张三',
                    config_id=5,
                    source_type='TIMESHEET',
                    source_id=1000,
                    extra_data={'days': 3},
                    priority='HIGH',
                    notification_channels=['EMAIL', 'SMS']
                )

                self.assertEqual(record.user_name, '张三')
                self.assertEqual(record.config_id, 5)
                self.assertEqual(record.source_type, 'TIMESHEET')
                self.assertEqual(record.source_id, 1000)
                self.assertEqual(record.extra_data, {'days': 3})
                self.assertEqual(record.priority, 'HIGH')
                self.assertEqual(record.notification_channels, ['EMAIL', 'SMS'])

    def test_mark_reminder_sent_success(self):
        """测试标记提醒已发送 - 成功"""
        mock_record = MagicMock(spec=TimesheetReminderRecord)
        mock_record.reminder_no = 'RM202601010001'
        self.db.query.return_value.filter.return_value.first.return_value = mock_record

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 1, 1, 12, 0, 0)
            mock_dt.now.return_value = mock_now

            result = self.manager.mark_reminder_sent(reminder_id=1, channels=['EMAIL', 'SMS'])

            self.assertEqual(result, mock_record)
            self.assertEqual(mock_record.status, ReminderStatusEnum.SENT)
            self.assertEqual(mock_record.sent_at, mock_now)
            self.assertEqual(mock_record.notification_channels, ['EMAIL', 'SMS'])
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once_with(mock_record)

    def test_mark_reminder_sent_not_found(self):
        """测试标记提醒已发送 - 记录不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.manager.mark_reminder_sent(reminder_id=999, channels=['EMAIL'])

        self.assertIsNone(result)
        self.db.commit.assert_not_called()

    def test_mark_reminder_read_success(self):
        """测试标记提醒已读 - 成功"""
        mock_record = MagicMock(spec=TimesheetReminderRecord)
        self.db.query.return_value.filter.return_value.first.return_value = mock_record

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 1, 1, 13, 0, 0)
            mock_dt.now.return_value = mock_now

            result = self.manager.mark_reminder_read(reminder_id=1)

            self.assertEqual(result, mock_record)
            self.assertEqual(mock_record.status, ReminderStatusEnum.READ)
            self.assertEqual(mock_record.read_at, mock_now)
            self.db.commit.assert_called_once()

    def test_mark_reminder_read_not_found(self):
        """测试标记提醒已读 - 记录不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.manager.mark_reminder_read(reminder_id=999)

        self.assertIsNone(result)

    def test_dismiss_reminder_success(self):
        """测试忽略提醒 - 成功"""
        mock_record = MagicMock(spec=TimesheetReminderRecord)
        mock_record.reminder_no = 'RM202601010001'
        self.db.query.return_value.filter.return_value.first.return_value = mock_record

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 1, 1, 14, 0, 0)
            mock_dt.now.return_value = mock_now

            result = self.manager.dismiss_reminder(
                reminder_id=1,
                dismissed_by=200,
                reason='误报'
            )

            self.assertEqual(result, mock_record)
            self.assertEqual(mock_record.status, ReminderStatusEnum.DISMISSED)
            self.assertEqual(mock_record.dismissed_at, mock_now)
            self.assertEqual(mock_record.dismissed_by, 200)
            self.assertEqual(mock_record.dismissed_reason, '误报')
            self.db.commit.assert_called_once()

    def test_dismiss_reminder_without_reason(self):
        """测试忽略提醒 - 无原因"""
        mock_record = MagicMock(spec=TimesheetReminderRecord)
        self.db.query.return_value.filter.return_value.first.return_value = mock_record

        with patch('app.services.timesheet_reminder.reminder_manager.datetime'):
            result = self.manager.dismiss_reminder(reminder_id=1, dismissed_by=200)

            self.assertEqual(result, mock_record)
            self.assertEqual(mock_record.dismissed_reason, None)

    def test_dismiss_reminder_not_found(self):
        """测试忽略提醒 - 记录不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.manager.dismiss_reminder(reminder_id=999, dismissed_by=200)

        self.assertIsNone(result)

    def test_mark_reminder_resolved_success(self):
        """测试标记提醒已解决 - 成功"""
        mock_record = MagicMock(spec=TimesheetReminderRecord)
        mock_record.reminder_no = 'RM202601010001'
        self.db.query.return_value.filter.return_value.first.return_value = mock_record

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 1, 1, 15, 0, 0)
            mock_dt.now.return_value = mock_now

            result = self.manager.mark_reminder_resolved(reminder_id=1)

            self.assertEqual(result, mock_record)
            self.assertEqual(mock_record.status, ReminderStatusEnum.RESOLVED)
            self.assertEqual(mock_record.resolved_at, mock_now)
            self.db.commit.assert_called_once()

    def test_mark_reminder_resolved_not_found(self):
        """测试标记提醒已解决 - 记录不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.manager.mark_reminder_resolved(reminder_id=999)

        self.assertIsNone(result)

    def test_get_pending_reminders_all(self):
        """测试获取待处理提醒列表 - 所有"""
        mock_records = [MagicMock(), MagicMock(), MagicMock()]
        self.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records

        result = self.manager.get_pending_reminders()

        self.assertEqual(result, mock_records)
        self.assertEqual(len(result), 3)

    def test_get_pending_reminders_by_user(self):
        """测试获取待处理提醒列表 - 按用户筛选"""
        mock_records = [MagicMock()]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records
        self.db.query.return_value.filter.return_value = mock_query

        result = self.manager.get_pending_reminders(user_id=100)

        self.assertEqual(result, mock_records)

    def test_get_pending_reminders_by_type(self):
        """测试获取待处理提醒列表 - 按类型筛选"""
        mock_records = [MagicMock()]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records
        self.db.query.return_value.filter.return_value = mock_query

        result = self.manager.get_pending_reminders(reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT)

        self.assertEqual(result, mock_records)

    def test_get_pending_reminders_with_limit(self):
        """测试获取待处理提醒列表 - 自定义限制"""
        mock_records = [MagicMock()] * 50
        mock_query = MagicMock()
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_records
        self.db.query.return_value.filter.return_value = mock_query

        result = self.manager.get_pending_reminders(limit=50)

        self.assertEqual(len(result), 50)

    def test_get_reminder_history_all(self):
        """测试获取提醒历史 - 所有"""
        mock_records = [MagicMock()] * 10
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        records, total = self.manager.get_reminder_history()

        self.assertEqual(len(records), 10)
        self.assertEqual(total, 100)

    def test_get_reminder_history_with_filters(self):
        """测试获取提醒历史 - 带筛选条件"""
        mock_records = [MagicMock()] * 5
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 25
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 1, 31)

        records, total = self.manager.get_reminder_history(
            user_id=100,
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            start_date=start_date,
            end_date=end_date,
            limit=5,
            offset=10
        )

        self.assertEqual(len(records), 5)
        self.assertEqual(total, 25)

    def test_get_reminder_history_pagination(self):
        """测试获取提醒历史 - 分页"""
        mock_records = [MagicMock()] * 20
        mock_query = MagicMock()
        mock_query.count.return_value = 200
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = mock_records
        self.db.query.return_value = mock_query

        records, total = self.manager.get_reminder_history(limit=20, offset=40)

        self.assertEqual(len(records), 20)
        self.assertEqual(total, 200)

    def test_check_reminder_limit_within_limit(self):
        """测试检查提醒次数限制 - 未超限"""
        self.db.query.return_value.filter.return_value.count.return_value = 2

        result = self.manager.check_reminder_limit(
            user_id=100,
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            max_per_day=5
        )

        self.assertTrue(result)

    def test_check_reminder_limit_at_limit(self):
        """测试检查提醒次数限制 - 达到限制"""
        self.db.query.return_value.filter.return_value.count.return_value = 5

        result = self.manager.check_reminder_limit(
            user_id=100,
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            max_per_day=5
        )

        self.assertFalse(result)

    def test_check_reminder_limit_exceeded(self):
        """测试检查提醒次数限制 - 超限"""
        self.db.query.return_value.filter.return_value.count.return_value = 10

        result = self.manager.check_reminder_limit(
            user_id=100,
            reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
            max_per_day=5
        )

        self.assertFalse(result)

    # ==================== 异常记录管理测试 ====================

    def test_create_anomaly_record_minimal(self):
        """测试创建异常记录 - 最小参数"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj') as mock_save:
            with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
                mock_now = datetime(2026, 1, 1, 10, 0, 0)
                mock_dt.now.return_value = mock_now

                record = self.manager.create_anomaly_record(
                    timesheet_id=1000,
                    user_id=100,
                    anomaly_type=AnomalyTypeEnum.DAILY_OVER_12,
                    description='工时异常超时'
                )

                self.assertEqual(record.timesheet_id, 1000)
                self.assertEqual(record.user_id, 100)
                self.assertEqual(record.anomaly_type, AnomalyTypeEnum.DAILY_OVER_12)
                self.assertEqual(record.description, '工时异常超时')
                self.assertEqual(record.severity, 'WARNING')
                self.assertEqual(record.detected_at, mock_now)
                self.assertFalse(record.is_resolved)
                self.assertEqual(record.anomaly_data, {})
                mock_save.assert_called_once()

    def test_create_anomaly_record_full(self):
        """测试创建异常记录 - 完整参数"""
        with patch('app.services.timesheet_reminder.reminder_manager.save_obj'):
            with patch('app.services.timesheet_reminder.reminder_manager.datetime'):
                record = self.manager.create_anomaly_record(
                    timesheet_id=1000,
                    user_id=100,
                    anomaly_type=AnomalyTypeEnum.NO_REST_7DAYS,
                    description='缺少休息时间',
                    user_name='李四',
                    anomaly_data={'hours': 12, 'breaks': 0},
                    severity='ERROR',
                    reminder_id=500
                )

                self.assertEqual(record.user_name, '李四')
                self.assertEqual(record.anomaly_data, {'hours': 12, 'breaks': 0})
                self.assertEqual(record.severity, 'ERROR')
                self.assertEqual(record.reminder_id, 500)

    def test_resolve_anomaly_success(self):
        """测试解决异常 - 成功"""
        mock_record = MagicMock(spec=TimesheetAnomalyRecord)
        self.db.query.return_value.filter.return_value.first.return_value = mock_record

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_now = datetime(2026, 1, 2, 10, 0, 0)
            mock_dt.now.return_value = mock_now

            result = self.manager.resolve_anomaly(
                anomaly_id=1,
                resolved_by=200,
                resolution_note='已修正工时'
            )

            self.assertEqual(result, mock_record)
            self.assertTrue(mock_record.is_resolved)
            self.assertEqual(mock_record.resolved_at, mock_now)
            self.assertEqual(mock_record.resolved_by, 200)
            self.assertEqual(mock_record.resolution_note, '已修正工时')
            self.db.commit.assert_called_once()

    def test_resolve_anomaly_without_note(self):
        """测试解决异常 - 无备注"""
        mock_record = MagicMock(spec=TimesheetAnomalyRecord)
        self.db.query.return_value.filter.return_value.first.return_value = mock_record

        with patch('app.services.timesheet_reminder.reminder_manager.datetime'):
            result = self.manager.resolve_anomaly(anomaly_id=1, resolved_by=200)

            self.assertEqual(result, mock_record)
            self.assertEqual(mock_record.resolution_note, None)

    def test_resolve_anomaly_not_found(self):
        """测试解决异常 - 记录不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.manager.resolve_anomaly(anomaly_id=999, resolved_by=200)

        self.assertIsNone(result)

    def test_get_unresolved_anomalies_all(self):
        """测试获取未解决的异常列表 - 所有"""
        mock_records = [MagicMock(), MagicMock()]
        self.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records

        result = self.manager.get_unresolved_anomalies()

        self.assertEqual(result, mock_records)
        self.assertEqual(len(result), 2)

    def test_get_unresolved_anomalies_by_user(self):
        """测试获取未解决的异常列表 - 按用户筛选"""
        mock_records = [MagicMock()]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records
        self.db.query.return_value.filter.return_value = mock_query

        result = self.manager.get_unresolved_anomalies(user_id=100)

        self.assertEqual(result, mock_records)

    def test_get_unresolved_anomalies_by_type(self):
        """测试获取未解决的异常列表 - 按类型筛选"""
        mock_records = [MagicMock()]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records
        self.db.query.return_value.filter.return_value = mock_query

        result = self.manager.get_unresolved_anomalies(anomaly_type=AnomalyTypeEnum.DAILY_OVER_12)

        self.assertEqual(result, mock_records)

    def test_get_unresolved_anomalies_with_limit(self):
        """测试获取未解决的异常列表 - 自定义限制"""
        mock_records = [MagicMock()] * 50
        mock_query = MagicMock()
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_records
        self.db.query.return_value.filter.return_value = mock_query

        result = self.manager.get_unresolved_anomalies(limit=50)

        self.assertEqual(len(result), 50)

    # ==================== 工具方法测试 ====================

    def test_generate_reminder_no_missing_timesheet(self):
        """测试生成提醒编号 - 缺失工时"""
        self.db.query.return_value.filter.return_value.count.return_value = 5

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 15, 14, 30, 45)

            reminder_no = self.manager._generate_reminder_no(ReminderTypeEnum.MISSING_TIMESHEET)

            self.assertTrue(reminder_no.startswith('RM20260115143045'))
            self.assertTrue(reminder_no.endswith('0006'))

    def test_generate_reminder_no_approval_timeout(self):
        """测试生成提醒编号 - 审批超时"""
        self.db.query.return_value.filter.return_value.count.return_value = 0

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 20, 9, 15, 30)

            reminder_no = self.manager._generate_reminder_no(ReminderTypeEnum.APPROVAL_TIMEOUT)

            self.assertTrue(reminder_no.startswith('RA20260220091530'))
            self.assertTrue(reminder_no.endswith('0001'))

    def test_generate_reminder_no_anomaly_timesheet(self):
        """测试生成提醒编号 - 异常工时"""
        self.db.query.return_value.filter.return_value.count.return_value = 99

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 3, 1, 0, 0, 0)

            reminder_no = self.manager._generate_reminder_no(ReminderTypeEnum.ANOMALY_TIMESHEET)

            self.assertTrue(reminder_no.startswith('RN20260301000000'))
            self.assertTrue(reminder_no.endswith('0100'))

    def test_generate_reminder_no_weekend_work(self):
        """测试生成提醒编号 - 周末工作"""
        self.db.query.return_value.filter.return_value.count.return_value = 2

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 5, 18, 0, 0)

            reminder_no = self.manager._generate_reminder_no(ReminderTypeEnum.WEEKEND_WORK)

            self.assertTrue(reminder_no.startswith('RW20260405180000'))
            self.assertTrue(reminder_no.endswith('0003'))

    def test_generate_reminder_no_holiday_work(self):
        """测试生成提醒编号 - 假日工作"""
        self.db.query.return_value.filter.return_value.count.return_value = 0

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 1, 12, 0, 0)

            reminder_no = self.manager._generate_reminder_no(ReminderTypeEnum.HOLIDAY_WORK)

            self.assertTrue(reminder_no.startswith('RH20260501120000'))
            self.assertTrue(reminder_no.endswith('0001'))

    def test_generate_reminder_no_sync_failure(self):
        """测试生成提醒编号 - 同步失败"""
        self.db.query.return_value.filter.return_value.count.return_value = 10

        with patch('app.services.timesheet_reminder.reminder_manager.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 15, 23, 59, 59)

            reminder_no = self.manager._generate_reminder_no(ReminderTypeEnum.SYNC_FAILURE)

            self.assertTrue(reminder_no.startswith('RS20260615235959'))
            self.assertTrue(reminder_no.endswith('0011'))


if __name__ == '__main__':
    unittest.main()
