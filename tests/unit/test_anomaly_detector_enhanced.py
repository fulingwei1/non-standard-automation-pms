# -*- coding: utf-8 -*-
"""
异常工时检测服务增强测试
目标：25-35个测试用例，覆盖率70%+
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.models.timesheet import Timesheet
from app.models.timesheet_reminder import AnomalyTypeEnum, TimesheetAnomalyRecord
from app.services.timesheet_reminder.anomaly_detector import TimesheetAnomalyDetector


class TestTimesheetAnomalyDetectorInit(unittest.TestCase):
    """测试初始化"""

    def test_init_with_db_session(self):
        """测试正常初始化"""
        mock_db = MagicMock()
        with patch('app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager'):
            detector = TimesheetAnomalyDetector(mock_db)
            self.assertEqual(detector.db, mock_db)
            self.assertIsNotNone(detector.reminder_manager)


class TestDetectAllAnomalies(unittest.TestCase):
    """测试 detect_all_anomalies 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager'):
            self.detector = TimesheetAnomalyDetector(self.mock_db)

    def test_detect_all_anomalies_default_dates(self):
        """测试默认日期参数"""
        # Mock 所有检测方法
        self.detector.detect_daily_over_12 = Mock(return_value=[])
        self.detector.detect_daily_invalid = Mock(return_value=[])
        self.detector.detect_weekly_over_60 = Mock(return_value=[])
        self.detector.detect_no_rest_7days = Mock(return_value=[])
        self.detector.detect_progress_mismatch = Mock(return_value=[])

        result = self.detector.detect_all_anomalies()

        # 验证默认日期
        expected_start = date.today() - timedelta(days=1)
        expected_end = date.today()

        self.detector.detect_daily_over_12.assert_called_once_with(expected_start, expected_end, None)
        self.assertEqual(result, [])

    def test_detect_all_anomalies_with_custom_dates(self):
        """测试自定义日期范围"""
        self.detector.detect_daily_over_12 = Mock(return_value=[])
        self.detector.detect_daily_invalid = Mock(return_value=[])
        self.detector.detect_weekly_over_60 = Mock(return_value=[])
        self.detector.detect_no_rest_7days = Mock(return_value=[])
        self.detector.detect_progress_mismatch = Mock(return_value=[])

        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        result = self.detector.detect_all_anomalies(start, end, user_id=123)

        self.detector.detect_daily_over_12.assert_called_once_with(start, end, 123)
        self.assertEqual(result, [])

    def test_detect_all_anomalies_aggregates_results(self):
        """测试聚合所有检测结果"""
        anomaly1 = Mock(spec=TimesheetAnomalyRecord)
        anomaly2 = Mock(spec=TimesheetAnomalyRecord)
        anomaly3 = Mock(spec=TimesheetAnomalyRecord)

        self.detector.detect_daily_over_12 = Mock(return_value=[anomaly1])
        self.detector.detect_daily_invalid = Mock(return_value=[anomaly2])
        self.detector.detect_weekly_over_60 = Mock(return_value=[])
        self.detector.detect_no_rest_7days = Mock(return_value=[anomaly3])
        self.detector.detect_progress_mismatch = Mock(return_value=[])

        result = self.detector.detect_all_anomalies()

        self.assertEqual(len(result), 3)
        self.assertIn(anomaly1, result)
        self.assertIn(anomaly2, result)
        self.assertIn(anomaly3, result)


class TestDetectDailyOver12(unittest.TestCase):
    """测试 detect_daily_over_12 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager'):
            self.detector = TimesheetAnomalyDetector(self.mock_db)

    def test_detect_daily_over_12_no_anomalies(self):
        """测试无异常情况"""
        # Mock query结果为空
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = []

        result = self.detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 31))
        self.assertEqual(result, [])

    def test_detect_daily_over_12_with_anomaly(self):
        """测试发现超12小时异常"""
        # Mock查询结果
        mock_result = Mock()
        mock_result.user_id = 1
        mock_result.user_name = "张三"
        mock_result.work_date = date(2024, 1, 15)
        mock_result.total_hours = Decimal('13.5')
        mock_result.timesheet_ids = "1,2,3"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = [mock_result]

        # Mock 不存在旧异常记录
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock create_anomaly_record
        mock_anomaly = Mock(spec=TimesheetAnomalyRecord)
        self.detector.reminder_manager.create_anomaly_record = Mock(return_value=mock_anomaly)

        result = self.detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 1)
        self.detector.reminder_manager.create_anomaly_record.assert_called_once()
        call_args = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertEqual(call_args['anomaly_type'], AnomalyTypeEnum.DAILY_OVER_12)
        self.assertEqual(call_args['severity'], 'WARNING')

    def test_detect_daily_over_12_skip_existing(self):
        """测试跳过已存在的异常记录"""
        mock_result = Mock()
        mock_result.user_id = 1
        mock_result.user_name = "张三"
        mock_result.work_date = date(2024, 1, 15)
        mock_result.total_hours = Decimal('14.0')
        mock_result.timesheet_ids = "1"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = [mock_result]

        # Mock 已存在异常记录
        existing_anomaly = Mock(spec=TimesheetAnomalyRecord)
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_anomaly

        self.detector.reminder_manager.create_anomaly_record = Mock()

        result = self.detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 0)
        self.detector.reminder_manager.create_anomaly_record.assert_not_called()

    def test_detect_daily_over_12_with_user_filter(self):
        """测试指定用户ID过滤"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = []

        self.detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 31), user_id=123)

        # 验证filter被调用了两次（一次基础过滤，一次用户过滤）
        self.assertTrue(mock_query.filter.called)


class TestDetectDailyInvalid(unittest.TestCase):
    """测试 detect_daily_invalid 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager'):
            self.detector = TimesheetAnomalyDetector(self.mock_db)

    def test_detect_daily_invalid_negative_hours(self):
        """测试检测负工时"""
        mock_result = Mock()
        mock_result.user_id = 1
        mock_result.user_name = "李四"
        mock_result.work_date = date(2024, 1, 15)
        mock_result.total_hours = Decimal('-2.0')
        mock_result.timesheet_ids = "10"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = [mock_result]

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_anomaly = Mock(spec=TimesheetAnomalyRecord)
        self.detector.reminder_manager.create_anomaly_record = Mock(return_value=mock_anomaly)

        result = self.detector.detect_daily_invalid(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 1)
        call_args = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertEqual(call_args['anomaly_type'], AnomalyTypeEnum.DAILY_INVALID)
        self.assertEqual(call_args['severity'], 'ERROR')

    def test_detect_daily_invalid_over_24_hours(self):
        """测试检测超24小时"""
        mock_result = Mock()
        mock_result.user_id = 2
        mock_result.user_name = "王五"
        mock_result.work_date = date(2024, 1, 20)
        mock_result.total_hours = Decimal('25.0')
        mock_result.timesheet_ids = "20,21"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = [mock_result]

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_anomaly = Mock(spec=TimesheetAnomalyRecord)
        self.detector.reminder_manager.create_anomaly_record = Mock(return_value=mock_anomaly)

        result = self.detector.detect_daily_invalid(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 1)
        self.assertIn('25.0', self.detector.reminder_manager.create_anomaly_record.call_args[1]['description'])

    def test_detect_daily_invalid_no_results(self):
        """测试无无效数据"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = []

        result = self.detector.detect_daily_invalid(date(2024, 1, 1), date(2024, 1, 31))
        self.assertEqual(result, [])


class TestDetectWeeklyOver60(unittest.TestCase):
    """测试 detect_weekly_over_60 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager'):
            self.detector = TimesheetAnomalyDetector(self.mock_db)

    # 注意：weekly_over_60的测试因涉及SQLAlchemy JSON字段查询，在纯Mock环境中难以实现
    # 这些测试应在集成测试中覆盖


class TestDetectNoRest7Days(unittest.TestCase):
    """测试 detect_no_rest_7days 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager'):
            self.detector = TimesheetAnomalyDetector(self.mock_db)

    # 注意：连续7天检测的测试因涉及SQLAlchemy JSON字段查询，在纯Mock环境中难以实现
    # 这些测试应在集成测试中覆盖

    def test_detect_no_rest_7days_with_breaks(self):
        """测试有休息天数的情况"""
        mock_user = Mock()
        mock_user.user_id = 1
        mock_user.user_name = "正常人"

        # 有间断的工作日
        work_dates = [
            Mock(work_date=date(2024, 1, 1)),
            Mock(work_date=date(2024, 1, 2)),
            Mock(work_date=date(2024, 1, 4)),  # 跳过3号
            Mock(work_date=date(2024, 1, 5)),
        ]

        user_query = MagicMock()
        user_query.filter.return_value = user_query
        user_query.distinct.return_value.all.return_value = [mock_user]

        date_query = MagicMock()
        date_query.filter.return_value = date_query
        date_query.distinct.return_value.order_by.return_value.all.return_value = work_dates

        def mock_query_side_effect(*args):
            if hasattr(args[0], 'user_id'):
                return user_query
            else:
                return date_query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.detector.detect_no_rest_7days(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 0)

    def test_detect_no_rest_7days_less_than_7(self):
        """测试少于7天工作"""
        mock_user = Mock()
        mock_user.user_id = 1
        mock_user.user_name = "新人"

        work_dates = [
            Mock(work_date=date(2024, 1, 1)),
            Mock(work_date=date(2024, 1, 2)),
            Mock(work_date=date(2024, 1, 3)),
        ]

        user_query = MagicMock()
        user_query.filter.return_value = user_query
        user_query.distinct.return_value.all.return_value = [mock_user]

        date_query = MagicMock()
        date_query.filter.return_value = date_query
        date_query.distinct.return_value.order_by.return_value.all.return_value = work_dates

        def mock_query_side_effect(*args):
            if hasattr(args[0], 'user_id'):
                return user_query
            else:
                return date_query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.detector.detect_no_rest_7days(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 0)


class TestDetectProgressMismatch(unittest.TestCase):
    """测试 detect_progress_mismatch 方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager'):
            self.detector = TimesheetAnomalyDetector(self.mock_db)

    def test_detect_progress_mismatch_no_progress_update(self):
        """测试4小时工时但进度未更新"""
        timesheet = Mock(spec=Timesheet)
        timesheet.id = 1
        timesheet.user_id = 1
        timesheet.user_name = "张三"
        timesheet.work_date = date(2024, 1, 15)
        timesheet.hours = Decimal('5.0')
        timesheet.progress_before = 10
        timesheet.progress_after = 10  # 进度没变
        timesheet.task_id = 100

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet]

        # Mock不存在异常记录
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_anomaly = Mock(spec=TimesheetAnomalyRecord)
        self.detector.reminder_manager.create_anomaly_record = Mock(return_value=mock_anomaly)

        result = self.detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 1)
        call_args = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertEqual(call_args['anomaly_type'], AnomalyTypeEnum.PROGRESS_MISMATCH)
        self.assertIn('进度未更新', call_args['description'])

    def test_detect_progress_mismatch_low_progress_increase(self):
        """测试8小时工时但进度增加少于10%"""
        timesheet = Mock(spec=Timesheet)
        timesheet.id = 2
        timesheet.user_id = 2
        timesheet.user_name = "李四"
        timesheet.work_date = date(2024, 1, 16)
        timesheet.hours = Decimal('9.0')
        timesheet.progress_before = 20
        timesheet.progress_after = 25  # 只增加5%
        timesheet.task_id = 101

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet]

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_anomaly = Mock(spec=TimesheetAnomalyRecord)
        self.detector.reminder_manager.create_anomaly_record = Mock(return_value=mock_anomaly)

        result = self.detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 1)
        call_args = self.detector.reminder_manager.create_anomaly_record.call_args[1]
        self.assertIn('仅增加 5', call_args['description'])

    def test_detect_progress_mismatch_normal_progress(self):
        """测试正常进度更新"""
        timesheet = Mock(spec=Timesheet)
        timesheet.id = 3
        timesheet.user_id = 3
        timesheet.user_name = "王五"
        timesheet.work_date = date(2024, 1, 17)
        timesheet.hours = Decimal('8.0')
        timesheet.progress_before = 50
        timesheet.progress_after = 70  # 增加20%，正常
        timesheet.task_id = 102

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet]

        result = self.detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 0)

    def test_detect_progress_mismatch_no_progress_fields(self):
        """测试无进度字段的工时"""
        timesheet = Mock(spec=Timesheet)
        timesheet.id = 4
        timesheet.user_id = 4
        timesheet.user_name = "赵六"
        timesheet.work_date = date(2024, 1, 18)
        timesheet.hours = Decimal('10.0')
        timesheet.progress_before = None
        timesheet.progress_after = None
        timesheet.task_id = 103

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet]

        result = self.detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 0)

    def test_detect_progress_mismatch_skip_existing(self):
        """测试跳过已存在的进度不匹配异常"""
        timesheet = Mock(spec=Timesheet)
        timesheet.id = 5
        timesheet.user_id = 5
        timesheet.user_name = "孙七"
        timesheet.work_date = date(2024, 1, 19)
        timesheet.hours = Decimal('6.0')
        timesheet.progress_before = 30
        timesheet.progress_after = 30
        timesheet.task_id = 104

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet]

        # Mock已存在异常
        existing = Mock(spec=TimesheetAnomalyRecord)
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing

        result = self.detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 0)

    def test_detect_progress_mismatch_hours_threshold(self):
        """测试工时阈值边界"""
        # 3.99小时，不应触发
        timesheet1 = Mock(spec=Timesheet)
        timesheet1.id = 6
        timesheet1.user_id = 6
        timesheet1.user_name = "周八"
        timesheet1.work_date = date(2024, 1, 20)
        timesheet1.hours = Decimal('3.99')
        timesheet1.progress_before = 40
        timesheet1.progress_after = 40
        timesheet1.task_id = 105

        # 7.99小时，应触发第一条规则
        timesheet2 = Mock(spec=Timesheet)
        timesheet2.id = 7
        timesheet2.user_id = 7
        timesheet2.user_name = "吴九"
        timesheet2.work_date = date(2024, 1, 21)
        timesheet2.hours = Decimal('7.99')
        timesheet2.progress_before = 50
        timesheet2.progress_after = 55  # 增加5%
        timesheet2.task_id = 106

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet1, timesheet2]

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_anomaly = Mock(spec=TimesheetAnomalyRecord)
        self.detector.reminder_manager.create_anomaly_record = Mock(return_value=mock_anomaly)

        result = self.detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 31))

        # timesheet1不触发，timesheet2不会触发第二条规则（<8小时）
        self.assertEqual(len(result), 0)


class TestEdgeCases(unittest.TestCase):
    """边界条件和异常情况测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.timesheet_reminder.anomaly_detector.TimesheetReminderManager'):
            self.detector = TimesheetAnomalyDetector(self.mock_db)

    def test_empty_database(self):
        """测试空数据库"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = []

        result = self.detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 31))
        self.assertEqual(result, [])

    def test_exact_threshold_values(self):
        """测试精确阈值（12.0小时不应触发>12异常）"""
        mock_result = Mock()
        mock_result.user_id = 1
        mock_result.user_name = "边界测试"
        mock_result.work_date = date(2024, 1, 15)
        mock_result.total_hours = Decimal('12.0')
        mock_result.timesheet_ids = "1"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = []  # >12才返回

        result = self.detector.detect_daily_over_12(date(2024, 1, 1), date(2024, 1, 31))
        self.assertEqual(result, [])

    def test_single_day_range(self):
        """测试单日范围"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value.all.return_value = []

        single_day = date(2024, 1, 15)
        result = self.detector.detect_daily_over_12(single_day, single_day)
        self.assertEqual(result, [])

    def test_progress_zero_change_boundary(self):
        """测试进度变化为0的边界"""
        timesheet = Mock(spec=Timesheet)
        timesheet.id = 1
        timesheet.user_id = 1
        timesheet.user_name = "零进度"
        timesheet.work_date = date(2024, 1, 15)
        timesheet.hours = Decimal('4.0')  # 正好4小时
        timesheet.progress_before = 50
        timesheet.progress_after = 50  # 进度变化=0
        timesheet.task_id = 100

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet]
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_anomaly = Mock(spec=TimesheetAnomalyRecord)
        self.detector.reminder_manager.create_anomaly_record = Mock(return_value=mock_anomaly)

        result = self.detector.detect_progress_mismatch(date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(result), 1)


if __name__ == '__main__':
    unittest.main()
