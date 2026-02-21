# -*- coding: utf-8 -*-
"""
工时分析服务增强单元测试
覆盖所有核心方法和边界条件
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List, Any

from app.services.timesheet_analytics_service import TimesheetAnalyticsService


class TestTimesheetAnalyticsServiceInit(unittest.TestCase):
    """测试初始化"""
    
    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        db = MagicMock()
        service = TimesheetAnalyticsService(db)
        self.assertEqual(service.db, db)


class TestAnalyzeTrend(unittest.TestCase):
    """测试工时趋势分析"""
    
    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def _create_mock_result(self, work_date, total_hours, normal_hours, overtime_hours):
        """创建模拟查询结果"""
        result = MagicMock()
        result.work_date = work_date
        result.total_hours = Decimal(str(total_hours))
        result.normal_hours = Decimal(str(normal_hours))
        result.overtime_hours = Decimal(str(overtime_hours))
        return result
    
    def test_analyze_trend_daily_basic(self):
        """测试日趋势分析基本功能"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 3)
        
        # Mock查询结果
        mock_results = [
            self._create_mock_result(date(2024, 1, 1), 10, 8, 2),
            self._create_mock_result(date(2024, 1, 2), 12, 10, 2),
            self._create_mock_result(date(2024, 1, 3), 15, 12, 3),
        ]
        
        # 正确设置mock链
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_trend(
            period_type='DAILY',
            start_date=start_date,
            end_date=end_date
        )
        
        self.assertEqual(result.period_type, 'DAILY')
        self.assertEqual(result.start_date, start_date)
        self.assertEqual(result.end_date, end_date)
        self.assertEqual(result.total_hours, Decimal('37'))
        self.assertGreater(result.average_hours, 0)
    
    def test_analyze_trend_weekly(self):
        """测试周趋势分析"""
        mock_results = [
            self._create_mock_result(date(2024, 1, 1), 40, 32, 8),
            self._create_mock_result(date(2024, 1, 8), 45, 36, 9),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_trend(
            period_type='WEEKLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 14)
        )
        
        self.assertEqual(result.period_type, 'WEEKLY')
        self.assertEqual(result.total_hours, Decimal('85'))
    
    def test_analyze_trend_monthly(self):
        """测试月趋势分析"""
        mock_results = [
            self._create_mock_result(date(2024, 1, 15), 160, 140, 20),
            self._create_mock_result(date(2024, 2, 15), 170, 145, 25),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_trend(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 2, 29)
        )
        
        self.assertEqual(result.period_type, 'MONTHLY')
        self.assertEqual(result.total_hours, Decimal('330'))
    
    def test_analyze_trend_quarterly(self):
        """测试季度趋势分析"""
        mock_results = [
            self._create_mock_result(date(2024, 1, 15), 500, 400, 100),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_trend(
            period_type='QUARTERLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31)
        )
        
        self.assertEqual(result.period_type, 'QUARTERLY')
        self.assertEqual(result.total_hours, Decimal('500'))
    
    def test_analyze_trend_yearly(self):
        """测试年趋势分析"""
        mock_results = [
            self._create_mock_result(date(2024, 6, 15), 2000, 1600, 400),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_trend(
            period_type='YEARLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        self.assertEqual(result.period_type, 'YEARLY')
        self.assertEqual(result.total_hours, Decimal('2000'))
    
    def test_analyze_trend_with_filters(self):
        """测试带过滤条件的趋势分析"""
        mock_results = [
            self._create_mock_result(date(2024, 1, 1), 8, 8, 0),
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_trend(
            period_type='DAILY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            user_ids=[1, 2],
            project_ids=[10],
            department_ids=[5]
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.total_hours, Decimal('8'))
    
    def test_analyze_trend_empty_results(self):
        """测试空结果的趋势分析"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.analyze_trend(
            period_type='DAILY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1)
        )
        
        self.assertEqual(result.total_hours, Decimal('0'))
        self.assertEqual(result.average_hours, Decimal('0'))


class TestCalculateTrend(unittest.TestCase):
    """测试趋势计算"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def test_calculate_trend_increasing(self):
        """测试递增趋势"""
        results = []
        for i in range(10):
            result = MagicMock()
            result.total_hours = Decimal(str(10 + i * 2))
            results.append(result)
        
        trend, change_rate = self.service._calculate_trend(results)
        
        self.assertEqual(trend, 'INCREASING')
        self.assertGreater(change_rate, 5)
    
    def test_calculate_trend_decreasing(self):
        """测试递减趋势"""
        results = []
        for i in range(10):
            result = MagicMock()
            result.total_hours = Decimal(str(30 - i * 2))
            results.append(result)
        
        trend, change_rate = self.service._calculate_trend(results)
        
        self.assertEqual(trend, 'DECREASING')
        self.assertLess(change_rate, -5)
    
    def test_calculate_trend_stable(self):
        """测试稳定趋势"""
        results = []
        for i in range(10):
            result = MagicMock()
            result.total_hours = Decimal('20')
            results.append(result)
        
        trend, change_rate = self.service._calculate_trend(results)
        
        self.assertEqual(trend, 'STABLE')
        self.assertLessEqual(abs(change_rate), 5)
    
    def test_calculate_trend_less_than_two_results(self):
        """测试结果少于2条"""
        result = MagicMock()
        result.total_hours = Decimal('10')
        results = [result]
        
        trend, change_rate = self.service._calculate_trend(results)
        
        self.assertEqual(trend, 'STABLE')
        self.assertEqual(change_rate, 0.0)
    
    def test_calculate_trend_zero_first_half(self):
        """测试前半部分为0"""
        results = []
        for i in range(10):
            result = MagicMock()
            result.total_hours = Decimal('0') if i < 5 else Decimal('20')
            results.append(result)
        
        trend, change_rate = self.service._calculate_trend(results)
        
        self.assertEqual(change_rate, 0.0)


class TestGenerateTrendChart(unittest.TestCase):
    """测试趋势图生成"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def test_generate_trend_chart_daily(self):
        """测试日趋势图"""
        results = []
        for i in range(3):
            result = MagicMock()
            result.work_date = date(2024, 1, 1) + timedelta(days=i)
            result.total_hours = Decimal(str(10 + i))
            result.normal_hours = Decimal(str(8 + i))
            result.overtime_hours = Decimal('2')
            results.append(result)
        
        chart_data = self.service._generate_trend_chart(results, 'DAILY')
        
        self.assertEqual(len(chart_data.labels), 3)
        self.assertEqual(len(chart_data.datasets), 3)
        self.assertEqual(chart_data.labels[0], '2024-01-01')
    
    def test_generate_trend_chart_monthly(self):
        """测试月趋势图"""
        results = []
        for i in range(2):
            result = MagicMock()
            result.work_date = date(2024, 1 + i, 15)
            result.total_hours = Decimal('160')
            result.normal_hours = Decimal('140')
            result.overtime_hours = Decimal('20')
            results.append(result)
        
        chart_data = self.service._generate_trend_chart(results, 'MONTHLY')
        
        self.assertEqual(len(chart_data.labels), 2)
        self.assertTrue('2024-01' in chart_data.labels[0])
    
    def test_generate_trend_chart_yearly(self):
        """测试年趋势图"""
        result = MagicMock()
        result.work_date = date(2024, 6, 15)
        result.total_hours = Decimal('2000')
        result.normal_hours = Decimal('1600')
        result.overtime_hours = Decimal('400')
        results = [result]
        
        chart_data = self.service._generate_trend_chart(results, 'YEARLY')
        
        self.assertEqual(len(chart_data.labels), 1)
        self.assertEqual(chart_data.labels[0], '2024')


class TestAnalyzeWorkload(unittest.TestCase):
    """测试人员负荷分析"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def test_analyze_workload_basic(self):
        """测试基本负荷分析"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        
        mock_results = []
        for day in range(5):
            for user_id in [1, 2]:
                result = MagicMock()
                result.user_id = user_id
                result.user_name = f'User {user_id}'
                result.department_name = f'Dept {user_id}'
                result.work_date = start_date + timedelta(days=day)
                result.daily_hours = Decimal('9')
                mock_results.append(result)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_workload(
            period_type='DAILY',
            start_date=start_date,
            end_date=end_date
        )
        
        self.assertEqual(result.period_type, 'DAILY')
        self.assertEqual(result.start_date, start_date)
        self.assertEqual(result.end_date, end_date)
    
    def test_analyze_workload_with_filters(self):
        """测试带过滤条件的负荷分析"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.analyze_workload(
            period_type='DAILY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
            user_ids=[1, 2],
            department_ids=[5]
        )
        
        self.assertIsNotNone(result)


class TestAnalyzeEfficiency(unittest.TestCase):
    """测试工时效率分析"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def test_analyze_efficiency_basic(self):
        """测试基本效率分析"""
        mock_result = MagicMock()
        mock_result.actual_hours = Decimal('100')
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        
        result = self.service.analyze_efficiency(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(result.period_type, 'MONTHLY')
        self.assertGreater(result.actual_hours, 0)
        self.assertGreater(result.planned_hours, 0)
    
    def test_analyze_efficiency_with_filters(self):
        """测试带过滤条件的效率分析"""
        mock_result = MagicMock()
        mock_result.actual_hours = Decimal('50')
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        
        result = self.service.analyze_efficiency(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            project_ids=[1, 2],
            user_ids=[5]
        )
        
        self.assertIsNotNone(result)
    
    def test_analyze_efficiency_zero_hours(self):
        """测试零工时情况"""
        mock_result = MagicMock()
        mock_result.actual_hours = None
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        
        result = self.service.analyze_efficiency(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(result.actual_hours, Decimal('0'))


class TestAnalyzeOvertime(unittest.TestCase):
    """测试加班统计分析"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def test_analyze_overtime_basic(self):
        """测试基本加班分析"""
        mock_result = MagicMock()
        mock_result.total_overtime = Decimal('50')
        mock_result.weekend_hours = Decimal('20')
        mock_result.holiday_hours = Decimal('10')
        mock_result.total_hours = Decimal('200')
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        mock_query.scalar.return_value = 5
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.analyze_overtime(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(result.period_type, 'MONTHLY')
        self.assertEqual(result.total_overtime_hours, Decimal('50'))
        self.assertGreater(result.overtime_rate, 0)
    
    def test_analyze_overtime_with_filters(self):
        """测试带过滤条件的加班分析"""
        mock_result = MagicMock()
        mock_result.total_overtime = Decimal('20')
        mock_result.weekend_hours = Decimal('10')
        mock_result.holiday_hours = Decimal('5')
        mock_result.total_hours = Decimal('100')
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        mock_query.scalar.return_value = 3
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.analyze_overtime(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            user_ids=[1, 2],
            department_ids=[5]
        )
        
        self.assertIsNotNone(result)
    
    def test_analyze_overtime_zero_hours(self):
        """测试零加班情况"""
        mock_result = MagicMock()
        mock_result.total_overtime = None
        mock_result.weekend_hours = None
        mock_result.holiday_hours = None
        mock_result.total_hours = Decimal('100')
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        mock_query.scalar.return_value = 5
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.analyze_overtime(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(result.total_overtime_hours, Decimal('0'))


class TestAnalyzeDepartmentComparison(unittest.TestCase):
    """测试部门工时对比"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def test_analyze_department_comparison_basic(self):
        """测试基本部门对比"""
        mock_results = []
        for dept_id in range(1, 4):
            result = MagicMock()
            result.department_id = dept_id
            result.department_name = f'Department {dept_id}'
            result.total_hours = Decimal(str(100 + dept_id * 20))
            result.normal_hours = Decimal(str(80 + dept_id * 15))
            result.overtime_hours = Decimal(str(20 + dept_id * 5))
            result.user_count = 10 + dept_id
            result.entry_count = 50 + dept_id * 10
            mock_results.append(result)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_department_comparison(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(result.period_type, 'MONTHLY')
    
    def test_analyze_department_comparison_with_filter(self):
        """测试带部门过滤的对比"""
        mock_results = [
            MagicMock(
                department_id=1,
                department_name='Tech',
                total_hours=Decimal('200'),
                normal_hours=Decimal('160'),
                overtime_hours=Decimal('40'),
                user_count=15,
                entry_count=100
            )
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_department_comparison(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            department_ids=[1]
        )
        
        self.assertIsNotNone(result)
    
    def test_analyze_department_comparison_empty(self):
        """测试空部门列表"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.analyze_department_comparison(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertIsNotNone(result)


class TestAnalyzeProjectDistribution(unittest.TestCase):
    """测试项目工时分布"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def test_analyze_project_distribution_basic(self):
        """测试基本项目分布"""
        mock_results = []
        for proj_id in range(1, 4):
            result = MagicMock()
            result.project_id = proj_id
            result.project_name = f'Project {proj_id}'
            result.total_hours = Decimal(str(100 * proj_id))
            result.user_count = 5 + proj_id
            result.entry_count = 30 + proj_id * 10
            mock_results.append(result)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_project_distribution(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(result.period_type, 'MONTHLY')
        self.assertEqual(result.total_projects, 3)
        self.assertEqual(result.total_hours, Decimal('600'))
    
    def test_analyze_project_distribution_with_filters(self):
        """测试带过滤条件的项目分布"""
        mock_results = [
            MagicMock(
                project_id=1,
                project_name='Project Alpha',
                total_hours=Decimal('150'),
                user_count=8,
                entry_count=60
            )
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_project_distribution(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            project_ids=[1],
            user_ids=[5, 6]
        )
        
        self.assertEqual(result.total_projects, 1)
        self.assertEqual(result.total_hours, Decimal('150'))
    
    def test_analyze_project_distribution_empty(self):
        """测试空项目列表"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.analyze_project_distribution(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(result.total_projects, 0)
        self.assertEqual(result.total_hours, Decimal('0'))


class TestEdgeCases(unittest.TestCase):
    """测试边界条件"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = TimesheetAnalyticsService(self.db)
    
    def test_large_dataset(self):
        """测试大数据集"""
        mock_results = []
        for i in range(1000):
            result = MagicMock()
            result.work_date = date(2024, 1, 1)
            result.total_hours = Decimal('8')
            result.normal_hours = Decimal('8')
            result.overtime_hours = Decimal('0')
            mock_results.append(result)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_trend(
            period_type='DAILY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1)
        )
        
        self.assertGreater(result.total_hours, 0)
    
    def test_single_day_period(self):
        """测试单日周期"""
        mock_results = [
            MagicMock(
                work_date=date(2024, 1, 1),
                total_hours=Decimal('8'),
                normal_hours=Decimal('8'),
                overtime_hours=Decimal('0')
            )
        ]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.service.analyze_trend(
            period_type='DAILY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1)
        )
        
        self.assertEqual(result.total_hours, Decimal('8'))
    
    def test_decimal_precision(self):
        """测试小数精度"""
        mock_result = MagicMock()
        mock_result.actual_hours = Decimal('100.12345')
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        
        result = self.service.analyze_efficiency(
            period_type='MONTHLY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertIsInstance(result.actual_hours, Decimal)
        self.assertGreater(result.actual_hours, Decimal('100'))


if __name__ == '__main__':
    unittest.main()
