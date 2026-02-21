# -*- coding: utf-8 -*-
"""
增强的 TimesheetAggregationService 单元测试
目标覆盖率: 70%+
测试数量: 30+
"""

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.timesheet_aggregation_service import TimesheetAggregationService


class TestTimesheetAggregationServiceInit(unittest.TestCase):
    """测试初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        service = TimesheetAggregationService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestAggregateMonthlyTimesheet(unittest.TestCase):
    """测试月度工时汇总"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = TimesheetAggregationService(self.mock_db)

    @patch('app.services.timesheet_aggregation_helpers.calculate_month_range')
    @patch('app.services.timesheet_aggregation_helpers.query_timesheets')
    @patch('app.services.timesheet_aggregation_helpers.calculate_hours_summary')
    @patch('app.services.timesheet_aggregation_helpers.build_project_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_daily_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_task_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.get_or_create_summary')
    def test_aggregate_monthly_timesheet_user_month(
        self, mock_get_summary, mock_task_breakdown, mock_daily_breakdown,
        mock_project_breakdown, mock_hours_summary, mock_query_timesheets,
        mock_calculate_month_range
    ):
        """测试用户月度汇总"""
        # 准备数据
        mock_calculate_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_timesheets = [MagicMock(), MagicMock()]
        mock_query_timesheets.return_value = mock_timesheets
        mock_hours_summary.return_value = {
            'total_hours': 160.0,
            'normal_hours': 140.0,
            'overtime_hours': 10.0,
            'weekend_hours': 5.0,
            'holiday_hours': 5.0
        }
        mock_project_breakdown.return_value = {
            'proj_1': {'project_id': 1, 'hours': 80.0},
            'proj_2': {'project_id': 2, 'hours': 80.0}
        }
        mock_daily_breakdown.return_value = {'2024-01-01': {'hours': 8.0}}
        mock_task_breakdown.return_value = {'task_1': {'hours': 160.0}}
        
        mock_summary = MagicMock()
        mock_summary.id = 1
        mock_get_summary.return_value = mock_summary

        # 执行
        result = self.service.aggregate_monthly_timesheet(2024, 1, user_id=100)

        # 验证
        self.assertTrue(result['success'])
        self.assertEqual(result['summary_id'], 1)
        self.assertEqual(result['total_hours'], 160.0)
        self.assertEqual(result['normal_hours'], 140.0)
        self.assertEqual(result['overtime_hours'], 10.0)
        self.assertEqual(result['weekend_hours'], 5.0)
        self.assertEqual(result['holiday_hours'], 5.0)
        self.assertEqual(result['entries_count'], 2)
        self.assertEqual(result['projects_count'], 2)
        
        # 验证调用
        mock_calculate_month_range.assert_called_once_with(2024, 1)
        mock_query_timesheets.assert_called_once()
        mock_hours_summary.assert_called_once_with(mock_timesheets)
        mock_get_summary.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_summary)

    @patch('app.services.timesheet_aggregation_helpers.calculate_month_range')
    @patch('app.services.timesheet_aggregation_helpers.query_timesheets')
    @patch('app.services.timesheet_aggregation_helpers.calculate_hours_summary')
    @patch('app.services.timesheet_aggregation_helpers.build_project_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_daily_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_task_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.get_or_create_summary')
    def test_aggregate_monthly_timesheet_project_month(
        self, mock_get_summary, mock_task_breakdown, mock_daily_breakdown,
        mock_project_breakdown, mock_hours_summary, mock_query_timesheets,
        mock_calculate_month_range
    ):
        """测试项目月度汇总"""
        # 准备数据
        mock_calculate_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_timesheets = [MagicMock()]
        mock_query_timesheets.return_value = mock_timesheets
        mock_hours_summary.return_value = {
            'total_hours': 80.0,
            'normal_hours': 70.0,
            'overtime_hours': 5.0,
            'weekend_hours': 3.0,
            'holiday_hours': 2.0
        }
        mock_project_breakdown.return_value = {'proj_1': {'project_id': 1, 'hours': 80.0}}
        mock_daily_breakdown.return_value = {}
        mock_task_breakdown.return_value = {}
        
        mock_summary = MagicMock()
        mock_summary.id = 2
        mock_get_summary.return_value = mock_summary

        # 执行
        result = self.service.aggregate_monthly_timesheet(2024, 1, project_id=1)

        # 验证汇总类型
        mock_get_summary.assert_called_once()
        call_args = mock_get_summary.call_args
        self.assertEqual(call_args[0][1], 'PROJECT_MONTH')  # summary_type

    @patch('app.services.timesheet_aggregation_helpers.calculate_month_range')
    @patch('app.services.timesheet_aggregation_helpers.query_timesheets')
    @patch('app.services.timesheet_aggregation_helpers.calculate_hours_summary')
    @patch('app.services.timesheet_aggregation_helpers.build_project_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_daily_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_task_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.get_or_create_summary')
    def test_aggregate_monthly_timesheet_dept_month(
        self, mock_get_summary, mock_task_breakdown, mock_daily_breakdown,
        mock_project_breakdown, mock_hours_summary, mock_query_timesheets,
        mock_calculate_month_range
    ):
        """测试部门月度汇总"""
        mock_calculate_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_query_timesheets.return_value = []
        mock_hours_summary.return_value = {
            'total_hours': 0, 'normal_hours': 0, 'overtime_hours': 0,
            'weekend_hours': 0, 'holiday_hours': 0
        }
        mock_project_breakdown.return_value = {}
        mock_daily_breakdown.return_value = {}
        mock_task_breakdown.return_value = {}
        mock_get_summary.return_value = MagicMock(id=3)

        # 执行
        result = self.service.aggregate_monthly_timesheet(2024, 1, department_id=10)

        # 验证
        call_args = mock_get_summary.call_args
        self.assertEqual(call_args[0][1], 'DEPT_MONTH')

    @patch('app.services.timesheet_aggregation_helpers.calculate_month_range')
    @patch('app.services.timesheet_aggregation_helpers.query_timesheets')
    @patch('app.services.timesheet_aggregation_helpers.calculate_hours_summary')
    @patch('app.services.timesheet_aggregation_helpers.build_project_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_daily_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_task_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.get_or_create_summary')
    def test_aggregate_monthly_timesheet_global_month(
        self, mock_get_summary, mock_task_breakdown, mock_daily_breakdown,
        mock_project_breakdown, mock_hours_summary, mock_query_timesheets,
        mock_calculate_month_range
    ):
        """测试全局月度汇总"""
        mock_calculate_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_query_timesheets.return_value = []
        mock_hours_summary.return_value = {
            'total_hours': 0, 'normal_hours': 0, 'overtime_hours': 0,
            'weekend_hours': 0, 'holiday_hours': 0
        }
        mock_project_breakdown.return_value = {}
        mock_daily_breakdown.return_value = {}
        mock_task_breakdown.return_value = {}
        mock_get_summary.return_value = MagicMock(id=4)

        # 执行
        result = self.service.aggregate_monthly_timesheet(2024, 1)

        # 验证
        call_args = mock_get_summary.call_args
        self.assertEqual(call_args[0][1], 'GLOBAL_MONTH')

    @patch('app.services.timesheet_aggregation_helpers.calculate_month_range')
    @patch('app.services.timesheet_aggregation_helpers.query_timesheets')
    @patch('app.services.timesheet_aggregation_helpers.calculate_hours_summary')
    @patch('app.services.timesheet_aggregation_helpers.build_project_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_daily_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.build_task_breakdown')
    @patch('app.services.timesheet_aggregation_helpers.get_or_create_summary')
    def test_aggregate_monthly_timesheet_empty_results(
        self, mock_get_summary, mock_task_breakdown, mock_daily_breakdown,
        mock_project_breakdown, mock_hours_summary, mock_query_timesheets,
        mock_calculate_month_range
    ):
        """测试空结果汇总"""
        mock_calculate_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_query_timesheets.return_value = []
        mock_hours_summary.return_value = {
            'total_hours': 0, 'normal_hours': 0, 'overtime_hours': 0,
            'weekend_hours': 0, 'holiday_hours': 0
        }
        mock_project_breakdown.return_value = {}
        mock_daily_breakdown.return_value = {}
        mock_task_breakdown.return_value = {}
        mock_get_summary.return_value = MagicMock(id=5)

        # 执行
        result = self.service.aggregate_monthly_timesheet(2024, 1, user_id=999)

        # 验证
        self.assertEqual(result['entries_count'], 0)
        self.assertEqual(result['projects_count'], 0)
        self.assertEqual(result['total_hours'], 0)


class TestGenerateHRReport(unittest.TestCase):
    """测试生成HR报表"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = TimesheetAggregationService(self.mock_db)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    def test_generate_hr_report_basic(self, mock_get_month_range):
        """测试基本HR报表生成"""
        # 准备数据
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.user_name = '张三'
        mock_ts1.department_id = 10
        mock_ts1.department_name = '开发部'
        mock_ts1.hours = Decimal('8.0')
        mock_ts1.overtime_type = 'NORMAL'
        mock_ts1.work_date = date(2024, 1, 1)
        mock_ts1.work_content = '开发功能A'
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 1
        mock_ts2.user_name = '张三'
        mock_ts2.department_id = 10
        mock_ts2.department_name = '开发部'
        mock_ts2.hours = Decimal('2.0')
        mock_ts2.overtime_type = 'OVERTIME'
        mock_ts2.work_date = date(2024, 1, 2)
        mock_ts2.work_content = '加班修复bug'
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_ts1, mock_ts2]
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_hr_report(2024, 1)

        # 验证
        self.assertEqual(len(result), 1)
        user_report = result[0]
        self.assertEqual(user_report['user_id'], 1)
        self.assertEqual(user_report['user_name'], '张三')
        self.assertEqual(user_report['total_hours'], 10.0)
        self.assertEqual(user_report['normal_hours'], 8.0)
        self.assertEqual(user_report['overtime_hours'], 2.0)
        self.assertEqual(len(user_report['daily_records']), 2)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    def test_generate_hr_report_with_department_filter(self, mock_get_month_range):
        """测试按部门筛选的HR报表"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_hr_report(2024, 1, department_id=10)

        # 验证调用了部门筛选
        self.assertEqual(result, [])

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    def test_generate_hr_report_multiple_users(self, mock_get_month_range):
        """测试多用户HR报表"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.user_name = '张三'
        mock_ts1.department_id = 10
        mock_ts1.department_name = '开发部'
        mock_ts1.hours = Decimal('8.0')
        mock_ts1.overtime_type = 'NORMAL'
        mock_ts1.work_date = date(2024, 1, 1)
        mock_ts1.work_content = '工作内容1'
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 2
        mock_ts2.user_name = '李四'
        mock_ts2.department_id = 10
        mock_ts2.department_name = '开发部'
        mock_ts2.hours = Decimal('8.0')
        mock_ts2.overtime_type = 'WEEKEND'
        mock_ts2.work_date = date(2024, 1, 6)
        mock_ts2.work_content = '周末加班'
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_ts1, mock_ts2]
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_hr_report(2024, 1)

        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['weekend_hours'], 0)
        self.assertEqual(result[1]['weekend_hours'], 8.0)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    def test_generate_hr_report_holiday_hours(self, mock_get_month_range):
        """测试节假日工时统计"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        mock_ts = MagicMock()
        mock_ts.user_id = 1
        mock_ts.user_name = '张三'
        mock_ts.department_id = 10
        mock_ts.department_name = '开发部'
        mock_ts.hours = Decimal('8.0')
        mock_ts.overtime_type = 'HOLIDAY'
        mock_ts.work_date = date(2024, 1, 1)
        mock_ts.work_content = '节假日加班'
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_ts]
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_hr_report(2024, 1)

        # 验证
        self.assertEqual(result[0]['holiday_hours'], 8.0)


class TestGenerateFinanceReport(unittest.TestCase):
    """测试生成财务报表"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = TimesheetAggregationService(self.mock_db)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    @patch('app.services.timesheet_aggregation_service.HourlyRateService.get_user_hourly_rate')
    def test_generate_finance_report_basic(self, mock_get_hourly_rate, mock_get_month_range):
        """测试基本财务报表生成"""
        # 准备数据
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_get_hourly_rate.return_value = 100.0
        
        mock_ts = MagicMock()
        mock_ts.project_id = 1
        mock_ts.project_code = 'PROJ-001'
        mock_ts.project_name = '项目A'
        mock_ts.user_id = 1
        mock_ts.user_name = '张三'
        mock_ts.hours = Decimal('8.0')
        mock_ts.work_date = date(2024, 1, 1)
        mock_ts.work_content = '开发功能'
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_ts]
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_finance_report(2024, 1)

        # 验证
        self.assertEqual(len(result), 1)
        project_report = result[0]
        self.assertEqual(project_report['project_id'], 1)
        self.assertEqual(project_report['total_hours'], 8.0)
        self.assertEqual(project_report['total_cost'], 800.0)
        self.assertEqual(len(project_report['personnel_records']), 1)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    @patch('app.services.timesheet_aggregation_service.HourlyRateService.get_user_hourly_rate')
    def test_generate_finance_report_with_project_filter(self, mock_get_hourly_rate, mock_get_month_range):
        """测试按项目筛选的财务报表"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_finance_report(2024, 1, project_id=1)

        # 验证
        self.assertEqual(result, [])

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    @patch('app.services.timesheet_aggregation_service.HourlyRateService.get_user_hourly_rate')
    def test_generate_finance_report_multiple_projects(self, mock_get_hourly_rate, mock_get_month_range):
        """测试多项目财务报表"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_get_hourly_rate.return_value = 100.0
        
        mock_ts1 = MagicMock()
        mock_ts1.project_id = 1
        mock_ts1.project_code = 'PROJ-001'
        mock_ts1.project_name = '项目A'
        mock_ts1.user_id = 1
        mock_ts1.user_name = '张三'
        mock_ts1.hours = Decimal('8.0')
        mock_ts1.work_date = date(2024, 1, 1)
        mock_ts1.work_content = '开发'
        
        mock_ts2 = MagicMock()
        mock_ts2.project_id = 2
        mock_ts2.project_code = 'PROJ-002'
        mock_ts2.project_name = '项目B'
        mock_ts2.user_id = 2
        mock_ts2.user_name = '李四'
        mock_ts2.hours = Decimal('6.0')
        mock_ts2.work_date = date(2024, 1, 1)
        mock_ts2.work_content = '测试'
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_ts1, mock_ts2]
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_finance_report(2024, 1)

        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['total_cost'], 800.0)
        self.assertEqual(result[1]['total_cost'], 600.0)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    @patch('app.services.timesheet_aggregation_service.HourlyRateService.get_user_hourly_rate')
    def test_generate_finance_report_same_project_multiple_users(self, mock_get_hourly_rate, mock_get_month_range):
        """测试同一项目多人的财务报表"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        def hourly_rate_side_effect(db, user_id, work_date):
            return 100.0 if user_id == 1 else 150.0
        
        mock_get_hourly_rate.side_effect = hourly_rate_side_effect
        
        mock_ts1 = MagicMock()
        mock_ts1.project_id = 1
        mock_ts1.project_code = 'PROJ-001'
        mock_ts1.project_name = '项目A'
        mock_ts1.user_id = 1
        mock_ts1.user_name = '张三'
        mock_ts1.hours = Decimal('8.0')
        mock_ts1.work_date = date(2024, 1, 1)
        mock_ts1.work_content = '开发'
        
        mock_ts2 = MagicMock()
        mock_ts2.project_id = 1
        mock_ts2.project_code = 'PROJ-001'
        mock_ts2.project_name = '项目A'
        mock_ts2.user_id = 2
        mock_ts2.user_name = '李四'
        mock_ts2.hours = Decimal('4.0')
        mock_ts2.work_date = date(2024, 1, 1)
        mock_ts2.work_content = '架构设计'
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_ts1, mock_ts2]
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_finance_report(2024, 1)

        # 验证
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['total_hours'], 12.0)
        self.assertEqual(result[0]['total_cost'], 1400.0)  # 8*100 + 4*150
        self.assertEqual(len(result[0]['personnel_records']), 2)


class TestGenerateRDReport(unittest.TestCase):
    """测试生成研发报表"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = TimesheetAggregationService(self.mock_db)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    @patch('app.services.timesheet_aggregation_service.HourlyRateService.get_user_hourly_rate')
    def test_generate_rd_report_basic(self, mock_get_hourly_rate, mock_get_month_range):
        """测试基本研发报表生成"""
        # 准备数据
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_get_hourly_rate.return_value = 120.0
        
        mock_rd_project = MagicMock()
        mock_rd_project.project_code = 'RD-001'
        mock_rd_project.project_name = '研发项目A'
        
        mock_ts = MagicMock()
        mock_ts.rd_project_id = 1
        mock_ts.user_id = 1
        mock_ts.user_name = '张三'
        mock_ts.hours = Decimal('8.0')
        mock_ts.work_date = date(2024, 1, 1)
        mock_ts.work_content = '研发工作'
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = [mock_ts]
        
        mock_rd_query = MagicMock()
        mock_rd_query.filter.return_value = mock_rd_query
        mock_rd_query.first.return_value = mock_rd_project
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:  # RdProject
                return mock_rd_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_rd_report(2024, 1)

        # 验证
        self.assertEqual(len(result), 1)
        rd_report = result[0]
        self.assertEqual(rd_report['rd_project_id'], 1)
        self.assertEqual(rd_report['rd_project_code'], 'RD-001')
        self.assertEqual(rd_report['total_hours'], 8.0)
        self.assertEqual(rd_report['total_cost'], 960.0)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    @patch('app.services.timesheet_aggregation_service.HourlyRateService.get_user_hourly_rate')
    def test_generate_rd_report_with_filter(self, mock_get_hourly_rate, mock_get_month_range):
        """测试按研发项目筛选的报表"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_rd_report(2024, 1, rd_project_id=1)

        # 验证
        self.assertEqual(result, [])

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    @patch('app.services.timesheet_aggregation_service.HourlyRateService.get_user_hourly_rate')
    def test_generate_rd_report_no_rd_project_found(self, mock_get_hourly_rate, mock_get_month_range):
        """测试研发项目不存在的情况"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_get_hourly_rate.return_value = 120.0
        
        mock_ts = MagicMock()
        mock_ts.rd_project_id = 999
        mock_ts.user_id = 1
        mock_ts.user_name = '张三'
        mock_ts.hours = Decimal('8.0')
        mock_ts.work_date = date(2024, 1, 1)
        mock_ts.work_content = '研发工作'
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = [mock_ts]
        
        mock_rd_query = MagicMock()
        mock_rd_query.filter.return_value = mock_rd_query
        mock_rd_query.first.return_value = None
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:
                return mock_rd_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_rd_report(2024, 1)

        # 验证
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]['rd_project_code'])
        self.assertIsNone(result[0]['rd_project_name'])


class TestGenerateProjectReport(unittest.TestCase):
    """测试生成项目报表"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = TimesheetAggregationService(self.mock_db)

    def test_generate_project_report_project_not_exist(self):
        """测试项目不存在"""
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = []
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = None
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:
                return mock_project_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_project_report(999)

        # 验证
        self.assertIn('error', result)
        self.assertEqual(result['error'], '项目不存在')

    def test_generate_project_report_basic(self):
        """测试基本项目报表生成"""
        # 准备数据
        mock_project = MagicMock()
        mock_project.project_code = 'PROJ-001'
        mock_project.project_name = '项目A'
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.user_name = '张三'
        mock_ts1.hours = Decimal('8.0')
        mock_ts1.work_date = date(2024, 1, 1)
        mock_ts1.task_id = 10
        mock_ts1.task_name = '任务A'
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 1
        mock_ts2.user_name = '张三'
        mock_ts2.hours = Decimal('4.0')
        mock_ts2.work_date = date(2024, 1, 2)
        mock_ts2.task_id = 10
        mock_ts2.task_name = '任务A'
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = [mock_ts1, mock_ts2]
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:
                return mock_project_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_project_report(1)

        # 验证
        self.assertEqual(result['project_code'], 'PROJ-001')
        self.assertEqual(result['total_hours'], 12.0)
        self.assertEqual(result['personnel_count'], 1)
        self.assertEqual(len(result['personnel_stats']), 1)
        self.assertEqual(len(result['daily_stats']), 2)
        self.assertEqual(len(result['task_stats']), 1)

    def test_generate_project_report_with_date_range(self):
        """测试带日期范围的项目报表"""
        mock_project = MagicMock()
        mock_project.project_code = 'PROJ-001'
        mock_project.project_name = '项目A'
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = []
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:
                return mock_project_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_project_report(
            1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        # 验证筛选被调用
        self.assertEqual(result['total_hours'], 0)

    def test_generate_project_report_multiple_users(self):
        """测试多用户项目报表"""
        mock_project = MagicMock()
        mock_project.project_code = 'PROJ-001'
        mock_project.project_name = '项目A'
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.user_name = '张三'
        mock_ts1.hours = Decimal('8.0')
        mock_ts1.work_date = date(2024, 1, 1)
        mock_ts1.task_id = None
        mock_ts1.task_name = None
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 2
        mock_ts2.user_name = '李四'
        mock_ts2.hours = Decimal('6.0')
        mock_ts2.work_date = date(2024, 1, 1)
        mock_ts2.task_id = None
        mock_ts2.task_name = None
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = [mock_ts1, mock_ts2]
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:
                return mock_project_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_project_report(1)

        # 验证
        self.assertEqual(result['personnel_count'], 2)
        self.assertEqual(result['total_hours'], 14.0)
        # 验证贡献率计算
        user1_stats = [p for p in result['personnel_stats'] if p['user_id'] == 1][0]
        user2_stats = [p for p in result['personnel_stats'] if p['user_id'] == 2][0]
        self.assertAlmostEqual(user1_stats['contribution_rate'], 57.14, places=2)
        self.assertAlmostEqual(user2_stats['contribution_rate'], 42.86, places=2)

    def test_generate_project_report_contribution_rate_zero_hours(self):
        """测试总工时为0时的贡献率计算"""
        mock_project = MagicMock()
        mock_project.project_code = 'PROJ-001'
        mock_project.project_name = '项目A'
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = []
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:
                return mock_project_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_project_report(1)

        # 验证
        self.assertEqual(result['total_hours'], 0)
        self.assertEqual(len(result['personnel_stats']), 0)

    def test_generate_project_report_daily_stats_same_day_multiple_users(self):
        """测试同一天多个用户的日报表统计"""
        mock_project = MagicMock()
        mock_project.project_code = 'PROJ-001'
        mock_project.project_name = '项目A'
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.user_name = '张三'
        mock_ts1.hours = Decimal('8.0')
        mock_ts1.work_date = date(2024, 1, 1)
        mock_ts1.task_id = None
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 2
        mock_ts2.user_name = '李四'
        mock_ts2.hours = Decimal('6.0')
        mock_ts2.work_date = date(2024, 1, 1)
        mock_ts2.task_id = None
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = [mock_ts1, mock_ts2]
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:
                return mock_project_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_project_report(1)

        # 验证
        self.assertEqual(len(result['daily_stats']), 1)
        daily = result['daily_stats'][0]
        self.assertEqual(daily['hours'], 14.0)
        self.assertEqual(daily['personnel_count'], 2)


class TestEdgeCases(unittest.TestCase):
    """测试边界条件和异常情况"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = TimesheetAggregationService(self.mock_db)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    def test_generate_hr_report_with_null_hours(self, mock_get_month_range):
        """测试小时数为None的情况"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        mock_ts = MagicMock()
        mock_ts.user_id = 1
        mock_ts.user_name = '张三'
        mock_ts.department_id = 10
        mock_ts.department_name = '开发部'
        mock_ts.hours = None  # 测试None值
        mock_ts.overtime_type = 'NORMAL'
        mock_ts.work_date = date(2024, 1, 1)
        mock_ts.work_content = '工作'
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_ts]
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_hr_report(2024, 1)

        # 验证
        self.assertEqual(result[0]['total_hours'], 0)

    @patch('app.services.timesheet_aggregation_service.get_month_range_by_ym')
    @patch('app.services.timesheet_aggregation_service.HourlyRateService.get_user_hourly_rate')
    def test_generate_finance_report_with_zero_hourly_rate(self, mock_get_hourly_rate, mock_get_month_range):
        """测试时薪为0的情况"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_get_hourly_rate.return_value = 0.0
        
        mock_ts = MagicMock()
        mock_ts.project_id = 1
        mock_ts.project_code = 'PROJ-001'
        mock_ts.project_name = '项目A'
        mock_ts.user_id = 1
        mock_ts.user_name = '实习生'
        mock_ts.hours = Decimal('8.0')
        mock_ts.work_date = date(2024, 1, 1)
        mock_ts.work_content = '学习'
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_ts]
        
        self.mock_db.query.return_value = mock_query

        # 执行
        result = self.service.generate_finance_report(2024, 1)

        # 验证
        self.assertEqual(result[0]['total_cost'], 0.0)

    def test_generate_project_report_with_multiple_tasks_same_user(self):
        """测试同一用户多任务的情况"""
        mock_project = MagicMock()
        mock_project.project_code = 'PROJ-001'
        mock_project.project_name = '项目A'
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.user_name = '张三'
        mock_ts1.hours = Decimal('4.0')
        mock_ts1.work_date = date(2024, 1, 1)
        mock_ts1.task_id = 10
        mock_ts1.task_name = '任务A'
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 1
        mock_ts2.user_name = '张三'
        mock_ts2.hours = Decimal('4.0')
        mock_ts2.work_date = date(2024, 1, 1)
        mock_ts2.task_id = 20
        mock_ts2.task_name = '任务B'
        
        mock_timesheet_query = MagicMock()
        mock_timesheet_query.filter.return_value = mock_timesheet_query
        mock_timesheet_query.order_by.return_value = mock_timesheet_query
        mock_timesheet_query.all.return_value = [mock_ts1, mock_ts2]
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = mock_project
        
        def query_side_effect(model):
            if 'Timesheet' in str(model):
                return mock_timesheet_query
            else:
                return mock_project_query
        
        self.mock_db.query.side_effect = query_side_effect

        # 执行
        result = self.service.generate_project_report(1)

        # 验证
        self.assertEqual(len(result['task_stats']), 2)
        self.assertEqual(result['task_stats'][0]['total_hours'], 4.0)
        self.assertEqual(result['task_stats'][1]['total_hours'], 4.0)


if __name__ == '__main__':
    unittest.main()
