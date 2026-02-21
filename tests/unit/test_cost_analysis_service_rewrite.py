# -*- coding: utf-8 -*-
"""
成本分析服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作, HourlyRateService）
2. 测试核心业务逻辑
3. 达到70%+覆盖率（305行）
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime, timedelta

from app.services.cost_analysis_service import CostAnalysisService


class TestCostAnalysisServiceCore(unittest.TestCase):
    """测试成本分析服务核心功能"""

    def setUp(self):
        """每个测试前的准备"""
        self.mock_db = MagicMock()
        self.service = CostAnalysisService(self.mock_db)

    # ========== predict_project_cost() 测试 ==========

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_predict_project_cost_basic(self, mock_hourly_rate):
        """测试基本的成本预测"""
        # Mock数据准备
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = 100000.0
        mock_project.actual_cost = 50000.0

        # Mock工时记录
        mock_timesheet1 = MagicMock()
        mock_timesheet1.user_id = 1
        mock_timesheet1.hours = 40.0
        mock_timesheet1.work_date = date(2024, 1, 1)

        mock_timesheet2 = MagicMock()
        mock_timesheet2.user_id = 2
        mock_timesheet2.hours = 30.0
        mock_timesheet2.work_date = date(2024, 1, 2)

        # Mock任务
        mock_task1 = MagicMock()
        mock_task1.estimated_hours = 50.0
        mock_task2 = MagicMock()
        mock_task2.estimated_hours = 30.0

        # 配置数据库查询返回值
        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        
        # 第一次查询：Project
        query_mock.filter.return_value.first.return_value = mock_project
        
        # 第二次查询：Timesheet
        timesheet_query = MagicMock()
        timesheet_query.filter.return_value.all.return_value = [mock_timesheet1, mock_timesheet2]
        
        # 第三次查询：Task
        task_query = MagicMock()
        task_query.filter.return_value.all.return_value = [mock_task1, mock_task2]
        
        # 配置query的side_effect来返回不同的结果
        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            from app.models.progress import Task
            
            if model == Project:
                return query_mock
            elif model == Timesheet:
                return timesheet_query
            elif model == Task:
                return task_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect

        # Mock时薪
        mock_hourly_rate.return_value = 150

        # 执行测试
        result = self.service.predict_project_cost(1)

        # 验证结果
        self.assertEqual(result['project_id'], 1)
        self.assertEqual(result['project_code'], "PRJ001")
        self.assertEqual(result['project_name'], "测试项目")
        self.assertEqual(result['budget'], 100000.0)
        self.assertEqual(result['actual_cost'], 50000.0)
        self.assertEqual(result['recorded_hours'], 70.0)  # 40 + 30
        self.assertEqual(result['recorded_labor_cost'], 10500.0)  # 70 * 150
        self.assertEqual(result['remaining_hours'], 80.0)  # 50 + 30
        self.assertEqual(result['predicted_remaining_cost'], 12000.0)  # 80 * 150
        self.assertEqual(result['predicted_total_cost'], 62000.0)  # 50000 + 12000
        self.assertEqual(result['cost_variance'], -38000.0)  # 62000 - 100000
        self.assertEqual(result['cost_variance_rate'], -38.0)
        self.assertFalse(result['is_over_budget'])

    def test_predict_project_cost_not_found(self):
        """测试项目不存在"""
        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None

        result = self.service.predict_project_cost(999)

        self.assertIn('error', result)
        self.assertEqual(result['error'], '项目不存在')

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_predict_project_cost_no_history(self, mock_hourly_rate):
        """测试没有历史工时数据的项目（使用默认时薪）"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ002"
        mock_project.project_name = "新项目"
        mock_project.budget_amount = 50000
        mock_project.actual_cost = 0

        mock_task = MagicMock()
        mock_task.estimated_hours = 100

        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        
        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            from app.models.progress import Task
            
            if model == Project:
                result = MagicMock()
                result.filter.return_value.first.return_value = mock_project
                return result
            elif model == Timesheet:
                result = MagicMock()
                result.filter.return_value.all.return_value = []
                return result
            elif model == Task:
                result = MagicMock()
                result.filter.return_value.all.return_value = [mock_task]
                return result
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect

        result = self.service.predict_project_cost(1)

        # 验证使用默认时薪100
        self.assertEqual(result['recorded_hours'], 0)
        self.assertEqual(result['recorded_labor_cost'], 0)
        self.assertEqual(result['remaining_hours'], 100.0)
        self.assertEqual(result['predicted_remaining_cost'], 10000.0)  # 100 * 100

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_predict_project_cost_over_budget(self, mock_hourly_rate):
        """测试预算超支的情况"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ003"
        mock_project.project_name = "超支项目"
        mock_project.budget_amount = 10000
        mock_project.actual_cost = 8000

        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.hours = 50
        mock_timesheet.work_date = date(2024, 1, 1)

        mock_task = MagicMock()
        mock_task.estimated_hours = 50

        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            from app.models.progress import Task
            
            if model == Project:
                result = MagicMock()
                result.filter.return_value.first.return_value = mock_project
                return result
            elif model == Timesheet:
                result = MagicMock()
                result.filter.return_value.all.return_value = [mock_timesheet]
                return result
            elif model == Task:
                result = MagicMock()
                result.filter.return_value.all.return_value = [mock_task]
                return result
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        mock_hourly_rate.return_value = 100

        result = self.service.predict_project_cost(1)

        # 验证超支
        self.assertEqual(result['predicted_total_cost'], 13000.0)  # 8000 + 5000
        self.assertTrue(result['is_over_budget'])
        self.assertEqual(result['cost_variance'], 3000.0)
        self.assertEqual(result['cost_variance_rate'], 30.0)

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_predict_project_cost_no_budget(self, mock_hourly_rate):
        """测试没有预算的项目"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ004"
        mock_project.project_name = "无预算项目"
        mock_project.budget_amount = None
        mock_project.actual_cost = 5000

        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            from app.models.progress import Task
            
            if model == Project:
                result = MagicMock()
                result.filter.return_value.first.return_value = mock_project
                return result
            elif model == Timesheet:
                result = MagicMock()
                result.filter.return_value.all.return_value = []
                return result
            elif model == Task:
                result = MagicMock()
                result.filter.return_value.all.return_value = []
                return result
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect

        result = self.service.predict_project_cost(1)

        # 验证无预算时的处理
        self.assertEqual(result['budget'], 0)
        self.assertEqual(result['cost_variance'], 0)
        self.assertEqual(result['cost_variance_rate'], 0)
        self.assertFalse(result['is_over_budget'])

    # ========== check_cost_overrun_alerts() 测试 ==========

    @patch.object(CostAnalysisService, 'predict_project_cost')
    def test_check_cost_overrun_alerts_critical(self, mock_predict):
        """测试严重超支预警（>=100%）"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "严重超支项目"
        mock_project.budget_amount = 10000
        mock_project.actual_cost = 11000
        mock_project.is_active = True

        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        query_mock.filter.return_value.all.return_value = [mock_project]

        mock_predict.return_value = {'predicted_total_cost': 12000.0}

        result = self.service.check_cost_overrun_alerts()

        self.assertEqual(len(result), 1)
        alert = result[0]
        self.assertEqual(alert['project_id'], 1)
        self.assertEqual(alert['alert_level'], 'CRITICAL')
        self.assertAlmostEqual(alert['cost_rate'], 110.0, places=1)
        self.assertIn('成本超支预警', alert['message'])

    @patch.object(CostAnalysisService, 'predict_project_cost')
    def test_check_cost_overrun_alerts_warning(self, mock_predict):
        """测试警告预警（80% <= x < 100%）"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ002"
        mock_project.project_name = "警告项目"
        mock_project.budget_amount = 10000
        mock_project.actual_cost = 8500
        mock_project.is_active = True

        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        query_mock.filter.return_value.all.return_value = [mock_project]

        mock_predict.return_value = {'predicted_total_cost': 9000.0}

        result = self.service.check_cost_overrun_alerts()

        self.assertEqual(len(result), 1)
        alert = result[0]
        self.assertEqual(alert['alert_level'], 'WARNING')
        self.assertEqual(alert['cost_rate'], 85.0)

    def test_check_cost_overrun_alerts_no_warning(self):
        """测试无预警情况（<80%）"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ003"
        mock_project.project_name = "正常项目"
        mock_project.budget_amount = 10000
        mock_project.actual_cost = 5000
        mock_project.is_active = True

        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        query_mock.filter.return_value.all.return_value = [mock_project]

        result = self.service.check_cost_overrun_alerts()

        self.assertEqual(len(result), 0)

    def test_check_cost_overrun_alerts_no_budget(self):
        """测试没有预算的项目（跳过）"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = None
        mock_project.is_active = True

        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        query_mock.filter.return_value.all.return_value = [mock_project]

        result = self.service.check_cost_overrun_alerts()

        self.assertEqual(len(result), 0)

    @patch.object(CostAnalysisService, 'predict_project_cost')
    def test_check_cost_overrun_alerts_specific_project(self, mock_predict):
        """测试检查指定项目的预警"""
        mock_project = MagicMock()
        mock_project.id = 5
        mock_project.project_code = "PRJ005"
        mock_project.project_name = "指定项目"
        mock_project.budget_amount = 10000
        mock_project.actual_cost = 9000
        mock_project.is_active = True

        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        query_mock.filter.return_value.filter.return_value.all.return_value = [mock_project]

        mock_predict.return_value = {'predicted_total_cost': 9500.0}

        result = self.service.check_cost_overrun_alerts(project_id=5)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['project_id'], 5)

    # ========== compare_project_costs() 测试 ==========

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_compare_project_costs_basic(self, mock_hourly_rate):
        """测试基本的项目成本对比"""
        # 项目1
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.project_code = "PRJ001"
        mock_project1.project_name = "项目1"
        mock_project1.budget_amount = 100000
        mock_project1.actual_cost = 50000

        # 项目2
        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.project_code = "PRJ002"
        mock_project2.project_name = "项目2"
        mock_project2.budget_amount = 80000
        mock_project2.actual_cost = 40000

        # 项目1的工时
        ts1_p1 = MagicMock()
        ts1_p1.user_id = 1
        ts1_p1.hours = 40
        ts1_p1.work_date = date(2024, 1, 1)

        ts2_p1 = MagicMock()
        ts2_p1.user_id = 2
        ts2_p1.hours = 30
        ts2_p1.work_date = date(2024, 1, 2)

        # 项目2的工时
        ts1_p2 = MagicMock()
        ts1_p2.user_id = 3
        ts1_p2.hours = 50
        ts1_p2.work_date = date(2024, 1, 1)

        project_query = MagicMock()
        project_query.filter.return_value.all.return_value = [mock_project1, mock_project2]

        # 使用计数器跟踪Timesheet查询次数
        timesheet_call_count = [0]
        
        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            
            if model == Project:
                return project_query
            elif model == Timesheet:
                result = MagicMock()
                timesheet_call_count[0] += 1
                
                # 第一次调用返回项目1的工时，第二次返回项目2的工时
                if timesheet_call_count[0] == 1:
                    result.filter.return_value.all.return_value = [ts1_p1, ts2_p1]
                else:
                    result.filter.return_value.all.return_value = [ts1_p2]
                return result
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        mock_hourly_rate.return_value = 150

        result = self.service.compare_project_costs([1, 2])

        # 验证结果
        self.assertEqual(len(result['projects']), 2)
        
        # 项目1：70小时 * 150 = 10500
        project1_data = result['projects'][0]
        self.assertEqual(project1_data['project_id'], 1)
        self.assertEqual(project1_data['total_hours'], 70.0)
        self.assertEqual(project1_data['total_cost'], 10500.0)
        self.assertEqual(project1_data['personnel_count'], 2)
        
        # 项目2：50小时 * 150 = 7500
        project2_data = result['projects'][1]
        self.assertEqual(project2_data['project_id'], 2)
        self.assertEqual(project2_data['total_hours'], 50.0)
        self.assertEqual(project2_data['total_cost'], 7500.0)
        self.assertEqual(project2_data['personnel_count'], 1)

        # 汇总统计
        summary = result['summary']
        self.assertEqual(summary['project_count'], 2)
        self.assertEqual(summary['avg_total_cost'], 9000.0)  # (10500 + 7500) / 2
        self.assertEqual(summary['avg_total_hours'], 60.0)  # (70 + 50) / 2
        self.assertEqual(summary['min_cost'], 7500.0)
        self.assertEqual(summary['max_cost'], 10500.0)

    def test_compare_project_costs_not_found(self):
        """测试项目不存在"""
        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        query_mock.filter.return_value.all.return_value = []

        result = self.service.compare_project_costs([999])

        self.assertIn('error', result)
        self.assertEqual(result['error'], '项目不存在')

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_compare_project_costs_no_timesheets(self, mock_hourly_rate):
        """测试没有工时记录的项目对比"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "项目1"
        mock_project.budget_amount = 100000
        mock_project.actual_cost = 0

        project_query = MagicMock()
        project_query.filter.return_value.all.return_value = [mock_project]

        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            
            if model == Project:
                return project_query
            elif model == Timesheet:
                result = MagicMock()
                result.filter.return_value.all.return_value = []
                return result
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect

        result = self.service.compare_project_costs([1])

        project_data = result['projects'][0]
        self.assertEqual(project_data['total_hours'], 0)
        self.assertEqual(project_data['total_cost'], 0)
        self.assertEqual(project_data['avg_hourly_rate'], 0)
        self.assertEqual(project_data['personnel_count'], 0)
        self.assertEqual(project_data['avg_hours_per_person'], 0)

    # ========== analyze_cost_trend() 测试 ==========

    @patch('app.services.cost_analysis_service.date')
    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_analyze_cost_trend_basic(self, mock_hourly_rate, mock_date):
        """测试基本的成本趋势分析"""
        # Mock today()使其返回2024年3月1日
        mock_date.today.return_value = date(2024, 3, 1)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "项目1"

        # 工时记录（跨月）
        ts1 = MagicMock()
        ts1.user_id = 1
        ts1.hours = 40.0
        ts1.work_date = date(2024, 1, 15)

        ts2 = MagicMock()
        ts2.user_id = 2
        ts2.hours = 30.0
        ts2.work_date = date(2024, 2, 10)

        ts3 = MagicMock()
        ts3.user_id = 1
        ts3.hours = 20.0
        ts3.work_date = date(2024, 2, 20)

        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = mock_project

        timesheet_query = MagicMock()
        # Timesheet查询使用多个filter参数，需要正确设置mock
        filter_result = MagicMock()
        filter_result.all.return_value = [ts1, ts2, ts3]
        timesheet_query.filter.return_value = filter_result

        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            
            if model == Project:
                return project_query
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        mock_hourly_rate.return_value = 150

        result = self.service.analyze_cost_trend(1, months=3)

        # 验证结果
        self.assertEqual(result['project_id'], 1)
        self.assertEqual(result['project_code'], "PRJ001")
        self.assertIn('monthly_trend', result)
        
        # 验证月度数据
        trend_data = result['monthly_trend']
        
        # 找到2024-01和2024-02的数据
        jan_data = [d for d in trend_data if d['month'] == '2024-01']
        feb_data = [d for d in trend_data if d['month'] == '2024-02']
        
        if jan_data:
            self.assertEqual(jan_data[0]['hours'], 40.0)
            self.assertEqual(jan_data[0]['cost'], 6000.0)  # 40 * 150
        
        if feb_data:
            self.assertEqual(feb_data[0]['hours'], 50.0)  # 30 + 20
            self.assertEqual(feb_data[0]['cost'], 7500.0)  # 50 * 150

        # 验证总计
        self.assertEqual(result['total_hours'], 90.0)
        self.assertEqual(result['total_cost'], 13500.0)

    def test_analyze_cost_trend_not_found(self):
        """测试项目不存在"""
        query_mock = MagicMock()
        self.mock_db.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None

        result = self.service.analyze_cost_trend(999)

        self.assertIn('error', result)
        self.assertEqual(result['error'], '项目不存在')

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_analyze_cost_trend_no_data(self, mock_hourly_rate):
        """测试没有工时数据的趋势分析"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "项目1"

        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = mock_project

        timesheet_query = MagicMock()
        timesheet_query.filter.return_value.all.return_value = []

        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            
            if model == Project:
                return project_query
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect

        result = self.service.analyze_cost_trend(1, months=3)

        # 验证所有月份数据为0
        for month_data in result['monthly_trend']:
            self.assertEqual(month_data['hours'], 0)
            self.assertEqual(month_data['cost'], 0)
        
        self.assertEqual(result['total_hours'], 0)
        self.assertEqual(result['total_cost'], 0)

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_analyze_cost_trend_personnel_count(self, mock_hourly_rate):
        """测试人员数量统计"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "项目1"

        # 同一月多个人
        ts1 = MagicMock()
        ts1.user_id = 1
        ts1.hours = 40
        ts1.work_date = date(2024, 1, 15)

        ts2 = MagicMock()
        ts2.user_id = 2
        ts2.hours = 30
        ts2.work_date = date(2024, 1, 20)

        ts3 = MagicMock()
        ts3.user_id = 3
        ts3.hours = 20
        ts3.work_date = date(2024, 1, 25)

        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = mock_project

        timesheet_query = MagicMock()
        timesheet_query.filter.return_value.all.return_value = [ts1, ts2, ts3]

        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            
            if model == Project:
                return project_query
            elif model == Timesheet:
                return timesheet_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        mock_hourly_rate.return_value = 150

        result = self.service.analyze_cost_trend(1, months=2)

        # 验证人员数量
        jan_data = [d for d in result['monthly_trend'] if d['month'] == '2024-01']
        if jan_data:
            self.assertEqual(jan_data[0]['personnel_count'], 3)

    # ========== 边界情况测试 ==========

    def test_warning_threshold_constant(self):
        """测试预警阈值常量"""
        self.assertEqual(CostAnalysisService.WARNING_THRESHOLD, 80)
        self.assertEqual(CostAnalysisService.CRITICAL_THRESHOLD, 100)

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_predict_cost_zero_budget(self, mock_hourly_rate):
        """测试预算为0的边界情况"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "零预算项目"
        mock_project.budget_amount = 0
        mock_project.actual_cost = 5000

        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            from app.models.progress import Task
            
            if model == Project:
                result = MagicMock()
                result.filter.return_value.first.return_value = mock_project
                return result
            elif model == Timesheet:
                result = MagicMock()
                result.filter.return_value.all.return_value = []
                return result
            elif model == Task:
                result = MagicMock()
                result.filter.return_value.all.return_value = []
                return result
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect

        result = self.service.predict_project_cost(1)

        # 预算为0时不应该计算偏差率
        self.assertEqual(result['cost_variance'], 0)
        self.assertEqual(result['cost_variance_rate'], 0)
        self.assertFalse(result['is_over_budget'])

    @patch('app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_compare_costs_single_project(self, mock_hourly_rate):
        """测试单个项目的成本对比"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "单个项目"
        mock_project.budget_amount = 10000
        mock_project.actual_cost = 5000

        ts = MagicMock()
        ts.user_id = 1
        ts.hours = 40
        ts.work_date = date(2024, 1, 1)

        project_query = MagicMock()
        project_query.filter.return_value.all.return_value = [mock_project]

        def query_side_effect(model):
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            
            if model == Project:
                return project_query
            elif model == Timesheet:
                result = MagicMock()
                result.filter.return_value.all.return_value = [ts]
                return result
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        mock_hourly_rate.return_value = 150

        result = self.service.compare_project_costs([1])

        # 单个项目时平均值应该等于该项目的值
        self.assertEqual(result['summary']['project_count'], 1)
        self.assertEqual(result['summary']['avg_total_cost'], 6000.0)
        self.assertEqual(result['summary']['min_cost'], 6000.0)
        self.assertEqual(result['summary']['max_cost'], 6000.0)


if __name__ == "__main__":
    unittest.main()
