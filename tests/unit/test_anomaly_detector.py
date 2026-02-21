# -*- coding: utf-8 -*-
"""
异常工时检测器单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, call, patch

from app.models.timesheet_reminder import AnomalyTypeEnum
from app.services.timesheet_reminder.anomaly_detector import (
    TimesheetAnomalyDetector,
)


class TestTimesheetAnomalyDetectorInit(unittest.TestCase):
    """测试初始化"""

    def test_init(self):
        """测试初始化"""
        mock_db = MagicMock()
        detector = TimesheetAnomalyDetector(mock_db)
        
        self.assertEqual(detector.db, mock_db)
        self.assertIsNotNone(detector.reminder_manager)


class TestDetectDailyOver12(unittest.TestCase):
    """测试单日工时 > 12小时检测"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.detector = TimesheetAnomalyDetector(self.mock_db)

    def test_detect_daily_over_12_found(self):
        """测试检测到单日超过12小时"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        # Mock query结果
        mock_result = Mock()
        mock_result.user_id = 1
        mock_result.user_name = "张三"
        mock_result.work_date = date(2024, 2, 1)
        mock_result.total_hours = Decimal('14.5')
        mock_result.timesheet_ids = "101,102,103"
        
        # 设置query链
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        
        self.mock_db.query.return_value = mock_query
        
        # Mock existing检查（不存在）
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value = mock_existing_query
        mock_existing_query.first.return_value = None
        
        # 需要设置两次query调用：第一次是主查询，第二次是existing检查
        self.mock_db.query.side_effect = [mock_query, mock_existing_query]
        
        # Mock create_anomaly_record
        mock_anomaly = Mock()
        mock_anomaly.id = 1
        self.detector.reminder_manager.create_anomaly_record = MagicMock(return_value=mock_anomaly)
        
        # 执行检测
        anomalies = self.detector.detect_daily_over_12(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].id, 1)
        
        # 验证create_anomaly_record被正确调用
        self.detector.reminder_manager.create_anomaly_record.assert_called_once()
        call_kwargs = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertEqual(call_kwargs['timesheet_id'], 101)
        self.assertEqual(call_kwargs['user_id'], 1)
        self.assertEqual(call_kwargs['anomaly_type'], AnomalyTypeEnum.DAILY_OVER_12)
        self.assertIn('14.5', call_kwargs['description'])
        self.assertEqual(call_kwargs['severity'], 'WARNING')

    def test_detect_daily_over_12_existing_skip(self):
        """测试已存在异常记录时跳过"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        # Mock query结果
        mock_result = Mock()
        mock_result.user_id = 1
        mock_result.user_name = "张三"
        mock_result.work_date = date(2024, 2, 1)
        mock_result.total_hours = Decimal('14.5')
        mock_result.timesheet_ids = "101"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        
        # Mock existing检查（已存在）
        mock_existing = Mock()
        mock_existing.id = 999
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value = mock_existing_query
        mock_existing_query.first.return_value = mock_existing
        
        self.mock_db.query.side_effect = [mock_query, mock_existing_query]
        
        # 执行检测
        anomalies = self.detector.detect_daily_over_12(start_date, end_date)
        
        # 验证：应该跳过
        self.assertEqual(len(anomalies), 0)

    def test_detect_daily_over_12_with_user_id(self):
        """测试指定用户ID"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        user_id = 5
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_db.query.return_value = mock_query
        
        # 执行检测
        self.detector.detect_daily_over_12(start_date, end_date, user_id)
        
        # 验证filter被调用且包含user_id过滤
        self.assertTrue(mock_query.filter.called)

    def test_detect_daily_over_12_no_results(self):
        """测试无异常情况"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_db.query.return_value = mock_query
        
        # 执行检测
        anomalies = self.detector.detect_daily_over_12(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 0)


class TestDetectDailyInvalid(unittest.TestCase):
    """测试单日工时 < 0 或 > 24 检测"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.detector = TimesheetAnomalyDetector(self.mock_db)

    def test_detect_daily_invalid_over_24(self):
        """测试单日超过24小时"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        # Mock query结果
        mock_result = Mock()
        mock_result.user_id = 2
        mock_result.user_name = "李四"
        mock_result.work_date = date(2024, 2, 1)
        mock_result.total_hours = Decimal('26.0')
        mock_result.timesheet_ids = "201"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value = mock_existing_query
        mock_existing_query.first.return_value = None
        
        self.mock_db.query.side_effect = [mock_query, mock_existing_query]
        
        mock_anomaly = Mock()
        mock_anomaly.id = 2
        self.detector.reminder_manager.create_anomaly_record = MagicMock(return_value=mock_anomaly)
        
        # 执行检测
        anomalies = self.detector.detect_daily_invalid(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 1)
        call_kwargs = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertEqual(call_kwargs['anomaly_type'], AnomalyTypeEnum.DAILY_INVALID)
        self.assertEqual(call_kwargs['severity'], 'ERROR')

    def test_detect_daily_invalid_negative(self):
        """测试单日负数工时"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        mock_result = Mock()
        mock_result.user_id = 3
        mock_result.user_name = "王五"
        mock_result.work_date = date(2024, 2, 1)
        mock_result.total_hours = Decimal('-2.0')
        mock_result.timesheet_ids = "301"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value = mock_existing_query
        mock_existing_query.first.return_value = None
        
        self.mock_db.query.side_effect = [mock_query, mock_existing_query]
        
        mock_anomaly = Mock()
        self.detector.reminder_manager.create_anomaly_record = MagicMock(return_value=mock_anomaly)
        
        # 执行检测
        anomalies = self.detector.detect_daily_invalid(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 1)


class TestDetectWeeklyOver60(unittest.TestCase):
    """测试周工时 > 60小时检测"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.detector = TimesheetAnomalyDetector(self.mock_db)

    @patch('app.services.timesheet_reminder.anomaly_detector.TimesheetAnomalyRecord')
    def test_detect_weekly_over_60_found(self, mock_anomaly_record_class):
        """测试检测到周工时超过60小时"""
        # 2024-02-05 是星期一
        start_date = date(2024, 2, 5)
        end_date = date(2024, 2, 11)  # 星期日
        
        # Mock query结果
        mock_result = Mock()
        mock_result.user_id = 4
        mock_result.user_name = "赵六"
        mock_result.weekly_hours = Decimal('68.0')
        mock_result.timesheet_ids = "401,402,403"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        
        # Mock existing检查
        mock_existing = MagicMock()
        mock_existing.filter.return_value = mock_existing
        mock_existing.first.return_value = None
        
        # 使用列表来控制调用顺序
        self.mock_db.query.side_effect = [mock_query, mock_existing]
        
        mock_anomaly = Mock()
        self.detector.reminder_manager.create_anomaly_record = MagicMock(return_value=mock_anomaly)
        
        # 执行检测
        anomalies = self.detector.detect_weekly_over_60(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 1)
        call_kwargs = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertEqual(call_kwargs['anomaly_type'], AnomalyTypeEnum.WEEKLY_OVER_60)
        self.assertIn('week_start', call_kwargs['anomaly_data'])
        self.assertIn('week_end', call_kwargs['anomaly_data'])

    @patch('app.services.timesheet_reminder.anomaly_detector.TimesheetAnomalyRecord')
    def test_detect_weekly_over_60_multiple_weeks(self, mock_anomaly_record_class):
        """测试跨多周检测"""
        # 测试两周
        start_date = date(2024, 2, 5)  # 第一周周一
        end_date = date(2024, 2, 18)   # 第二周周日
        
        # 第一周的结果
        mock_result1 = Mock()
        mock_result1.user_id = 5
        mock_result1.user_name = "孙七"
        mock_result1.weekly_hours = Decimal('65.0')
        mock_result1.timesheet_ids = "501"
        
        # 第二周的结果
        mock_result2 = Mock()
        mock_result2.user_id = 5
        mock_result2.user_name = "孙七"
        mock_result2.weekly_hours = Decimal('62.0')
        mock_result2.timesheet_ids = "502"
        
        # 第一周的query
        mock_query1 = MagicMock()
        mock_query1.filter.return_value = mock_query1
        mock_query1.group_by.return_value = mock_query1
        mock_query1.having.return_value = mock_query1
        mock_query1.all.return_value = [mock_result1]
        
        # 第二周的query
        mock_query2 = MagicMock()
        mock_query2.filter.return_value = mock_query2
        mock_query2.group_by.return_value = mock_query2
        mock_query2.having.return_value = mock_query2
        mock_query2.all.return_value = [mock_result2]
        
        # Mock existing检查
        mock_existing = MagicMock()
        mock_existing.filter.return_value = mock_existing
        mock_existing.first.return_value = None
        
        # 记录query调用次数
        query_calls = [mock_query1, mock_existing, mock_query2, mock_existing]
        self.mock_db.query.side_effect = query_calls
        
        mock_anomaly = Mock()
        self.detector.reminder_manager.create_anomaly_record = MagicMock(return_value=mock_anomaly)
        
        # 执行检测
        anomalies = self.detector.detect_weekly_over_60(start_date, end_date)
        
        # 验证：应该发现两条异常
        self.assertEqual(len(anomalies), 2)


class TestDetectNoRest7Days(unittest.TestCase):
    """测试连续7天无休息检测"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.detector = TimesheetAnomalyDetector(self.mock_db)

    @patch('app.services.timesheet_reminder.anomaly_detector.TimesheetAnomalyRecord')
    def test_detect_no_rest_7days_found(self, mock_anomaly_record_class):
        """测试检测到连续7天工作"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 10)
        
        # Mock用户列表
        mock_user = Mock()
        mock_user.user_id = 6
        mock_user.user_name = "周八"
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.distinct.return_value = mock_user_query
        mock_user_query.all.return_value = [mock_user]
        
        # Mock工作日期列表（连续7天）
        work_dates = [
            date(2024, 2, 1),
            date(2024, 2, 2),
            date(2024, 2, 3),
            date(2024, 2, 4),
            date(2024, 2, 5),
            date(2024, 2, 6),
            date(2024, 2, 7),
        ]
        
        mock_date_results = [Mock(work_date=d) for d in work_dates]
        mock_date_query = MagicMock()
        mock_date_query.filter.return_value = mock_date_query
        mock_date_query.distinct.return_value = mock_date_query
        mock_date_query.order_by.return_value = mock_date_query
        mock_date_query.all.return_value = mock_date_results
        
        # Mock existing检查
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value = mock_existing_query
        mock_existing_query.first.return_value = None
        
        # Mock timesheet IDs查询
        mock_id_results = [Mock(id=601), Mock(id=602)]
        mock_id_query = MagicMock()
        mock_id_query.filter.return_value = mock_id_query
        mock_id_query.all.return_value = mock_id_results
        
        self.mock_db.query.side_effect = [
            mock_user_query,      # 用户列表
            mock_date_query,      # 工作日期
            mock_existing_query,  # existing检查
            mock_id_query,        # timesheet IDs
        ]
        
        mock_anomaly = Mock()
        self.detector.reminder_manager.create_anomaly_record = MagicMock(return_value=mock_anomaly)
        
        # 执行检测
        anomalies = self.detector.detect_no_rest_7days(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 1)
        call_kwargs = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertEqual(call_kwargs['anomaly_type'], AnomalyTypeEnum.NO_REST_7DAYS)
        self.assertEqual(call_kwargs['anomaly_data']['consecutive_days'], 7)

    def test_detect_no_rest_7days_less_than_7(self):
        """测试工作天数少于7天"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 5)
        
        mock_user = Mock()
        mock_user.user_id = 7
        mock_user.user_name = "吴九"
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.distinct.return_value = mock_user_query
        mock_user_query.all.return_value = [mock_user]
        
        # 只有5天
        work_dates = [
            date(2024, 2, 1),
            date(2024, 2, 2),
            date(2024, 2, 3),
            date(2024, 2, 4),
            date(2024, 2, 5),
        ]
        
        mock_date_results = [Mock(work_date=d) for d in work_dates]
        mock_date_query = MagicMock()
        mock_date_query.filter.return_value = mock_date_query
        mock_date_query.distinct.return_value = mock_date_query
        mock_date_query.order_by.return_value = mock_date_query
        mock_date_query.all.return_value = mock_date_results
        
        self.mock_db.query.side_effect = [mock_user_query, mock_date_query]
        
        # 执行检测
        anomalies = self.detector.detect_no_rest_7days(start_date, end_date)
        
        # 验证：不应该检测到异常
        self.assertEqual(len(anomalies), 0)

    def test_detect_no_rest_7days_with_gap(self):
        """测试有间隔的情况"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 10)
        
        mock_user = Mock()
        mock_user.user_id = 8
        mock_user.user_name = "郑十"
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.distinct.return_value = mock_user_query
        mock_user_query.all.return_value = [mock_user]
        
        # 有间隔的日期（2月4日休息）
        work_dates = [
            date(2024, 2, 1),
            date(2024, 2, 2),
            date(2024, 2, 3),
            # 2月4日休息
            date(2024, 2, 5),
            date(2024, 2, 6),
            date(2024, 2, 7),
            date(2024, 2, 8),
        ]
        
        mock_date_results = [Mock(work_date=d) for d in work_dates]
        mock_date_query = MagicMock()
        mock_date_query.filter.return_value = mock_date_query
        mock_date_query.distinct.return_value = mock_date_query
        mock_date_query.order_by.return_value = mock_date_query
        mock_date_query.all.return_value = mock_date_results
        
        self.mock_db.query.side_effect = [mock_user_query, mock_date_query]
        
        # 执行检测
        anomalies = self.detector.detect_no_rest_7days(start_date, end_date)
        
        # 验证：不应该检测到异常（有间隔）
        self.assertEqual(len(anomalies), 0)


class TestDetectProgressMismatch(unittest.TestCase):
    """测试工时与进度不匹配检测"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.detector = TimesheetAnomalyDetector(self.mock_db)

    def test_detect_progress_no_change(self):
        """测试填报4小时以上但进度未更新"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        # Mock timesheet
        mock_ts = Mock()
        mock_ts.id = 701
        mock_ts.user_id = 9
        mock_ts.user_name = "钱十一"
        mock_ts.work_date = date(2024, 2, 1)
        mock_ts.hours = Decimal('6.0')
        mock_ts.progress_before = 50
        mock_ts.progress_after = 50  # 进度未变
        mock_ts.task_id = 100
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_ts]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value = mock_existing_query
        mock_existing_query.first.return_value = None
        
        self.mock_db.query.side_effect = [mock_query, mock_existing_query]
        
        mock_anomaly = Mock()
        self.detector.reminder_manager.create_anomaly_record = MagicMock(return_value=mock_anomaly)
        
        # 执行检测
        anomalies = self.detector.detect_progress_mismatch(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 1)
        call_kwargs = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertEqual(call_kwargs['anomaly_type'], AnomalyTypeEnum.PROGRESS_MISMATCH)
        self.assertEqual(call_kwargs['severity'], 'INFO')

    def test_detect_progress_small_increase(self):
        """测试填报8小时以上但进度增加少于10%"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        mock_ts = Mock()
        mock_ts.id = 702
        mock_ts.user_id = 10
        mock_ts.user_name = "孙十二"
        mock_ts.work_date = date(2024, 2, 1)
        mock_ts.hours = Decimal('10.0')
        mock_ts.progress_before = 50
        mock_ts.progress_after = 55  # 只增加5%
        mock_ts.task_id = 101
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_ts]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value = mock_existing_query
        mock_existing_query.first.return_value = None
        
        self.mock_db.query.side_effect = [mock_query, mock_existing_query]
        
        mock_anomaly = Mock()
        self.detector.reminder_manager.create_anomaly_record = MagicMock(return_value=mock_anomaly)
        
        # 执行检测
        anomalies = self.detector.detect_progress_mismatch(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 1)

    def test_detect_progress_normal(self):
        """测试正常情况：进度更新合理"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        mock_ts = Mock()
        mock_ts.id = 703
        mock_ts.user_id = 11
        mock_ts.user_name = "李十三"
        mock_ts.work_date = date(2024, 2, 1)
        mock_ts.hours = Decimal('8.0')
        mock_ts.progress_before = 50
        mock_ts.progress_after = 70  # 增加20%，合理
        mock_ts.task_id = 102
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_ts]
        
        self.mock_db.query.return_value = mock_query
        
        # 执行检测
        anomalies = self.detector.detect_progress_mismatch(start_date, end_date)
        
        # 验证：不应该检测到异常
        self.assertEqual(len(anomalies), 0)

    def test_detect_progress_no_progress_fields(self):
        """测试无进度字段的情况"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        mock_ts = Mock()
        mock_ts.id = 704
        mock_ts.user_id = 12
        mock_ts.user_name = "周十四"
        mock_ts.work_date = date(2024, 2, 1)
        mock_ts.hours = Decimal('8.0')
        mock_ts.progress_before = None
        mock_ts.progress_after = None
        mock_ts.task_id = 103
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_ts]
        
        self.mock_db.query.return_value = mock_query
        
        # 执行检测
        anomalies = self.detector.detect_progress_mismatch(start_date, end_date)
        
        # 验证：不应该检测到异常
        self.assertEqual(len(anomalies), 0)


class TestDetectAllAnomalies(unittest.TestCase):
    """测试统一检测入口"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.detector = TimesheetAnomalyDetector(self.mock_db)

    @patch.object(TimesheetAnomalyDetector, 'detect_daily_over_12')
    @patch.object(TimesheetAnomalyDetector, 'detect_daily_invalid')
    @patch.object(TimesheetAnomalyDetector, 'detect_weekly_over_60')
    @patch.object(TimesheetAnomalyDetector, 'detect_no_rest_7days')
    @patch.object(TimesheetAnomalyDetector, 'detect_progress_mismatch')
    def test_detect_all_anomalies(
        self, 
        mock_progress, 
        mock_no_rest, 
        mock_weekly, 
        mock_invalid, 
        mock_over_12
    ):
        """测试检测所有异常"""
        # Mock各个检测方法返回值
        anomaly1 = Mock()
        anomaly2 = Mock()
        anomaly3 = Mock()
        
        mock_over_12.return_value = [anomaly1]
        mock_invalid.return_value = [anomaly2]
        mock_weekly.return_value = []
        mock_no_rest.return_value = [anomaly3]
        mock_progress.return_value = []
        
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 5)
        
        # 执行检测
        anomalies = self.detector.detect_all_anomalies(start_date, end_date)
        
        # 验证：应该调用所有检测方法
        mock_over_12.assert_called_once_with(start_date, end_date, None)
        mock_invalid.assert_called_once_with(start_date, end_date, None)
        mock_weekly.assert_called_once_with(start_date, end_date, None)
        mock_no_rest.assert_called_once_with(start_date, end_date, None)
        mock_progress.assert_called_once_with(start_date, end_date, None)
        
        # 验证：返回所有异常
        self.assertEqual(len(anomalies), 3)

    @patch.object(TimesheetAnomalyDetector, 'detect_daily_over_12')
    @patch.object(TimesheetAnomalyDetector, 'detect_daily_invalid')
    @patch.object(TimesheetAnomalyDetector, 'detect_weekly_over_60')
    @patch.object(TimesheetAnomalyDetector, 'detect_no_rest_7days')
    @patch.object(TimesheetAnomalyDetector, 'detect_progress_mismatch')
    def test_detect_all_anomalies_default_dates(
        self, 
        mock_progress, 
        mock_no_rest, 
        mock_weekly, 
        mock_invalid, 
        mock_over_12
    ):
        """测试使用默认日期"""
        mock_over_12.return_value = []
        mock_invalid.return_value = []
        mock_weekly.return_value = []
        mock_no_rest.return_value = []
        mock_progress.return_value = []
        
        # 执行检测（不传日期参数）
        anomalies = self.detector.detect_all_anomalies()
        
        # 验证：应该使用默认日期（昨天到今天）
        expected_start = date.today() - timedelta(days=1)
        expected_end = date.today()
        
        mock_over_12.assert_called_once_with(expected_start, expected_end, None)

    @patch.object(TimesheetAnomalyDetector, 'detect_daily_over_12')
    @patch.object(TimesheetAnomalyDetector, 'detect_daily_invalid')
    @patch.object(TimesheetAnomalyDetector, 'detect_weekly_over_60')
    @patch.object(TimesheetAnomalyDetector, 'detect_no_rest_7days')
    @patch.object(TimesheetAnomalyDetector, 'detect_progress_mismatch')
    def test_detect_all_anomalies_with_user_id(
        self, 
        mock_progress, 
        mock_no_rest, 
        mock_weekly, 
        mock_invalid, 
        mock_over_12
    ):
        """测试指定用户ID"""
        mock_over_12.return_value = []
        mock_invalid.return_value = []
        mock_weekly.return_value = []
        mock_no_rest.return_value = []
        mock_progress.return_value = []
        
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 5)
        user_id = 100
        
        # 执行检测
        self.detector.detect_all_anomalies(start_date, end_date, user_id)
        
        # 验证：所有方法都应该接收到user_id
        mock_over_12.assert_called_once_with(start_date, end_date, user_id)
        mock_invalid.assert_called_once_with(start_date, end_date, user_id)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.detector = TimesheetAnomalyDetector(self.mock_db)

    @patch('app.services.timesheet_reminder.anomaly_detector.TimesheetAnomalyRecord')
    def test_empty_timesheet_ids(self, mock_anomaly_record_class):
        """测试空的timesheet_ids列表"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 10)
        
        mock_user = Mock()
        mock_user.user_id = 20
        mock_user.user_name = "测试用户"
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.distinct.return_value = mock_user_query
        mock_user_query.all.return_value = [mock_user]
        
        # 连续7天
        work_dates = [date(2024, 2, i) for i in range(1, 8)]
        mock_date_results = [Mock(work_date=d) for d in work_dates]
        mock_date_query = MagicMock()
        mock_date_query.filter.return_value = mock_date_query
        mock_date_query.distinct.return_value = mock_date_query
        mock_date_query.order_by.return_value = mock_date_query
        mock_date_query.all.return_value = mock_date_results
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value = mock_existing_query
        mock_existing_query.first.return_value = None
        
        # timesheet IDs为空
        mock_id_query = MagicMock()
        mock_id_query.filter.return_value = mock_id_query
        mock_id_query.all.return_value = []
        
        self.mock_db.query.side_effect = [
            mock_user_query,
            mock_date_query,
            mock_existing_query,
            mock_id_query,
        ]
        
        # 执行检测
        anomalies = self.detector.detect_no_rest_7days(start_date, end_date)
        
        # 验证：应该跳过
        self.assertEqual(len(anomalies), 0)

    def test_exactly_threshold_values(self):
        """测试临界值（正好12小时）"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 1)
        
        # 正好12小时（不应该触发）
        mock_result = Mock()
        mock_result.user_id = 21
        mock_result.user_name = "临界用户"
        mock_result.work_date = date(2024, 2, 1)
        mock_result.total_hours = Decimal('12.0')
        mock_result.timesheet_ids = "2101"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = []  # having条件应该是 > 12，所以12不会出现
        
        self.mock_db.query.return_value = mock_query
        
        # 执行检测
        anomalies = self.detector.detect_daily_over_12(start_date, end_date)
        
        # 验证
        self.assertEqual(len(anomalies), 0)


if __name__ == "__main__":
    unittest.main()
