# -*- coding: utf-8 -*-
"""
测试成本分析服务
覆盖成本预测、超支预警、成本对比、趋势分析
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.cost_analysis_service import CostAnalysisService


class TestCostAnalysisService:
    """成本分析服务测试"""

    def setup_method(self):
        """每个测试前的设置"""
        self.db = MagicMock()
        self.service = CostAnalysisService(self.db)

    # ==================== 测试常量 ====================
    
    def test_warning_threshold(self):
        """测试预警阈值常量"""
        assert self.service.WARNING_THRESHOLD == 80
        assert self.service.CRITICAL_THRESHOLD == 100

    # ==================== 预测项目成本 ====================

    def test_predict_project_cost_project_not_found(self):
        """测试项目不存在的情况"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.predict_project_cost(999)
        assert 'error' in result
        assert result['error'] == '项目不存在'

    def test_predict_project_cost_no_budget(self):
        """测试无预算项目的成本预测"""
        # 模拟项目
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = None
        project.actual_cost = 5000

        # 模拟数据库查询
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.first.return_value = project
        query_mock.filter.return_value.all.return_value = []

        # 调用方法
        result = self.service.predict_project_cost(1)

        # 验证结果
        assert result['budget'] == 0
        assert result['actual_cost'] == 5000
        assert result['recorded_hours'] == 0
        assert result['is_over_budget'] is False

    def test_predict_project_cost_with_timesheets(self):
        """测试有工时记录的成本预测"""
        # 模拟项目
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 50000
        project.actual_cost = 10000

        # 模拟工时记录
        ts1 = MagicMock()
        ts1.hours = 10
        ts1.user_id = 1
        ts1.work_date = date.today()

        ts2 = MagicMock()
        ts2.hours = 15
        ts2.user_id = 2
        ts2.work_date = date.today()

        timesheets = [ts1, ts2]

        # 模拟任务
        task = MagicMock()
        task.estimated_hours = 20
        task.status = 'PENDING'
        tasks = [task]

        # 设置查询返回值
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = timesheets
            elif model.__name__ == 'Task':
                mock_query.filter.return_value.all.return_value = tasks
            return mock_query

        self.db.query.side_effect = query_side_effect

        # Mock HourlyRateService
        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_rate:
            mock_rate.get_user_hourly_rate.return_value = 100

            result = self.service.predict_project_cost(1)

            # 验证结果
            assert result['project_id'] == 1
            assert result['project_code'] == 'P001'
            assert result['budget'] == 50000
            assert result['actual_cost'] == 10000
            assert result['recorded_hours'] == 25  # 10 + 15
            assert result['recorded_labor_cost'] == 2500  # 25 * 100
            assert result['remaining_hours'] == 20
            assert result['predicted_remaining_cost'] == 2000  # 20 * 100
            assert result['predicted_total_cost'] == 12000  # 10000 + 2000

    def test_predict_project_cost_no_history_uses_default_rate(self):
        """测试无历史数据时使用默认时薪"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 50000
        project.actual_cost = 0

        # 模拟任务
        task = MagicMock()
        task.estimated_hours = 50
        task.status = 'PENDING'
        tasks = [task]

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = []
            elif model.__name__ == 'Task':
                mock_query.filter.return_value.all.return_value = tasks
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.predict_project_cost(1)

        # 验证默认时薪为100
        assert result['recorded_hours'] == 0
        assert result['remaining_hours'] == 50
        assert result['predicted_remaining_cost'] == 5000  # 50 * 100

    def test_predict_project_cost_over_budget(self):
        """测试预测超预算的情况"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 10000
        project.actual_cost = 8000

        task = MagicMock()
        task.estimated_hours = 50
        task.status = 'PENDING'

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = []
            elif model.__name__ == 'Task':
                mock_query.filter.return_value.all.return_value = [task]
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.predict_project_cost(1)

        # 预测总成本 = 8000 + 50*100 = 13000
        assert result['predicted_total_cost'] == 13000
        assert result['is_over_budget'] is True
        assert result['cost_variance'] == 3000  # 13000 - 10000
        assert result['cost_variance_rate'] == 30  # (3000/10000)*100

    def test_predict_project_cost_multiple_tasks(self):
        """测试多个任务的成本预测"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 50000
        project.actual_cost = 5000

        tasks = []
        for i in range(3):
            task = MagicMock()
            task.estimated_hours = 20
            task.status = 'PENDING'
            tasks.append(task)

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = []
            elif model.__name__ == 'Task':
                mock_query.filter.return_value.all.return_value = tasks
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.predict_project_cost(1)

        assert result['remaining_hours'] == 60  # 20 * 3
        assert result['predicted_remaining_cost'] == 6000  # 60 * 100

    # ==================== 成本超支预警 ====================

    def test_check_cost_overrun_alerts_no_projects(self):
        """测试无项目的情况"""
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = []

        alerts = self.service.check_cost_overrun_alerts()
        assert alerts == []

    def test_check_cost_overrun_alerts_no_budget_skip(self):
        """测试跳过无预算的项目"""
        project = MagicMock()
        project.id = 1
        project.budget_amount = None
        project.is_active = True

        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = [project]

        alerts = self.service.check_cost_overrun_alerts()
        assert alerts == []

    def test_check_cost_overrun_alerts_warning_level(self):
        """测试警告级别的预警（80-100%）"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 10000
        project.actual_cost = 8500  # 85%
        project.is_active = True

        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = [project]

        # Mock predict_project_cost
        with patch.object(self.service, 'predict_project_cost') as mock_predict:
            mock_predict.return_value = {'predicted_total_cost': 9000}

            alerts = self.service.check_cost_overrun_alerts()

            assert len(alerts) == 1
            assert alerts[0]['alert_level'] == 'WARNING'
            assert alerts[0]['cost_rate'] == 85.0
            assert alerts[0]['project_code'] == 'P001'

    def test_check_cost_overrun_alerts_critical_level(self):
        """测试严重级别的预警（>=100%）"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 10000
        project.actual_cost = 11000  # 110%
        project.is_active = True

        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = [project]

        with patch.object(self.service, 'predict_project_cost') as mock_predict:
            mock_predict.return_value = {'predicted_total_cost': 12000}

            alerts = self.service.check_cost_overrun_alerts()

            assert len(alerts) == 1
            assert alerts[0]['alert_level'] == 'CRITICAL'
            assert round(alerts[0]['cost_rate'], 1) == 110.0

    def test_check_cost_overrun_alerts_below_threshold(self):
        """测试未超过阈值的项目不生成预警"""
        project = MagicMock()
        project.id = 1
        project.budget_amount = 10000
        project.actual_cost = 7000  # 70%
        project.is_active = True

        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = [project]

        alerts = self.service.check_cost_overrun_alerts()
        assert alerts == []

    def test_check_cost_overrun_alerts_specific_project(self):
        """测试指定项目ID的预警检查"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 10000
        project.actual_cost = 9000  # 90%
        project.is_active = True

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.filter.return_value.all.return_value = [project]

        with patch.object(self.service, 'predict_project_cost') as mock_predict:
            mock_predict.return_value = {'predicted_total_cost': 9500}

            alerts = self.service.check_cost_overrun_alerts(project_id=1)

            assert len(alerts) == 1
            # 验证filter被调用了两次（is_active 和 project_id）
            assert filter_mock.filter.called

    def test_check_cost_overrun_alerts_message_format(self):
        """测试预警消息格式"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 10000
        project.actual_cost = 8500
        project.is_active = True

        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = [project]

        with patch.object(self.service, 'predict_project_cost') as mock_predict:
            mock_predict.return_value = {'predicted_total_cost': 9000}

            alerts = self.service.check_cost_overrun_alerts()

            assert '项目P001成本超支预警' in alerts[0]['message']
            assert '8500.00元' in alerts[0]['message']
            assert '10000.00元' in alerts[0]['message']
            assert '85.0%' in alerts[0]['message']

    # ==================== 项目成本对比 ====================

    def test_compare_project_costs_no_projects(self):
        """测试空项目列表的对比"""
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = []

        result = self.service.compare_project_costs([1, 2, 3])
        assert 'error' in result
        assert result['error'] == '项目不存在'

    def test_compare_project_costs_single_project(self):
        """测试单个项目的成本对比"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 10000
        project.actual_cost = 5000

        ts1 = MagicMock()
        ts1.hours = 20
        ts1.user_id = 1
        ts1.work_date = date.today()

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.all.return_value = [project]
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = [ts1]
            return mock_query

        self.db.query.side_effect = query_side_effect

        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_rate:
            mock_rate.get_user_hourly_rate.return_value = 100

            result = self.service.compare_project_costs([1])

            assert len(result['projects']) == 1
            assert result['projects'][0]['total_hours'] == 20
            assert result['projects'][0]['total_cost'] == 2000
            assert result['projects'][0]['avg_hourly_rate'] == 100
            assert result['projects'][0]['personnel_count'] == 1

    def test_compare_project_costs_multiple_projects(self):
        """测试多个项目的成本对比"""
        # 项目1
        p1 = MagicMock()
        p1.id = 1
        p1.project_code = 'P001'
        p1.project_name = '项目1'
        p1.budget_amount = 10000
        p1.actual_cost = 5000

        # 项目2
        p2 = MagicMock()
        p2.id = 2
        p2.project_code = 'P002'
        p2.project_name = '项目2'
        p2.budget_amount = 20000
        p2.actual_cost = 8000

        # 项目1的工时
        ts1 = MagicMock()
        ts1.hours = 30
        ts1.user_id = 1
        ts1.work_date = date.today()

        # 项目2的工时
        ts2 = MagicMock()
        ts2.hours = 50
        ts2.user_id = 2
        ts2.work_date = date.today()

        ts3 = MagicMock()
        ts3.hours = 30
        ts3.user_id = 3
        ts3.work_date = date.today()

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.all.return_value = [p1, p2]
            elif model.__name__ == 'Timesheet':
                filter_result = mock_query.filter.return_value
                # 根据项目返回不同的工时记录
                if hasattr(filter_result, '_project_id'):
                    if filter_result._project_id == 1:
                        filter_result.all.return_value = [ts1]
                    else:
                        filter_result.all.return_value = [ts2, ts3]
                else:
                    # 默认返回空列表，然后根据调用顺序返回不同结果
                    filter_result.all.side_effect = [[ts1], [ts2, ts3]]
            return mock_query

        self.db.query.side_effect = query_side_effect

        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_rate:
            mock_rate.get_user_hourly_rate.return_value = 100

            result = self.service.compare_project_costs([1, 2])

            assert len(result['projects']) == 2
            assert result['summary']['project_count'] == 2
            assert 'avg_total_cost' in result['summary']
            assert 'min_cost' in result['summary']
            assert 'max_cost' in result['summary']

    def test_compare_project_costs_personnel_count(self):
        """测试人员数量计算"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 10000
        project.actual_cost = 5000

        # 3个不同的用户
        ts1 = MagicMock()
        ts1.hours = 10
        ts1.user_id = 1
        ts1.work_date = date.today()

        ts2 = MagicMock()
        ts2.hours = 15
        ts2.user_id = 2
        ts2.work_date = date.today()

        ts3 = MagicMock()
        ts3.hours = 20
        ts3.user_id = 1  # 同一个用户
        ts3.work_date = date.today()

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.all.return_value = [project]
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = [ts1, ts2, ts3]
            return mock_query

        self.db.query.side_effect = query_side_effect

        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_rate:
            mock_rate.get_user_hourly_rate.return_value = 100

            result = self.service.compare_project_costs([1])

            assert result['projects'][0]['personnel_count'] == 2  # user_id 1 和 2
            assert result['projects'][0]['total_hours'] == 45  # 10 + 15 + 20
            assert result['projects'][0]['avg_hours_per_person'] == 22.5  # 45 / 2

    def test_compare_project_costs_zero_hours(self):
        """测试零工时的项目"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'
        project.budget_amount = 10000
        project.actual_cost = 0

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.all.return_value = [project]
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.compare_project_costs([1])

        assert result['projects'][0]['total_hours'] == 0
        assert result['projects'][0]['total_cost'] == 0
        assert result['projects'][0]['avg_hourly_rate'] == 0
        assert result['projects'][0]['avg_hours_per_person'] == 0

    # ==================== 成本趋势分析 ====================

    def test_analyze_cost_trend_project_not_found(self):
        """测试项目不存在的情况"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.analyze_cost_trend(999)
        assert 'error' in result
        assert result['error'] == '项目不存在'

    def test_analyze_cost_trend_default_months(self):
        """测试默认6个月的趋势分析"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.analyze_cost_trend(1)

        assert result['project_id'] == 1
        assert 'monthly_trend' in result
        assert 'total_cost' in result
        assert 'total_hours' in result

    def test_analyze_cost_trend_custom_months(self):
        """测试自定义月数的趋势分析"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.analyze_cost_trend(1, months=3)

        assert result['project_id'] == 1
        assert 'monthly_trend' in result

    def test_analyze_cost_trend_with_data(self):
        """测试有数据的趋势分析"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'

        # 创建不同月份的工时记录
        today = date.today()
        last_month = date(today.year, today.month - 1 if today.month > 1 else 12, 15)

        ts1 = MagicMock()
        ts1.hours = 20
        ts1.user_id = 1
        ts1.work_date = today

        ts2 = MagicMock()
        ts2.hours = 30
        ts2.user_id = 1
        ts2.work_date = last_month

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                filter_result = mock_query.filter.return_value
                filter_result.all.return_value = [ts1, ts2]
            return mock_query

        self.db.query.side_effect = query_side_effect

        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_rate:
            mock_rate.get_user_hourly_rate.return_value = 100

            result = self.service.analyze_cost_trend(1, months=2)

            assert result['total_hours'] > 0
            assert result['total_cost'] > 0
            assert len(result['monthly_trend']) > 0

    def test_analyze_cost_trend_month_calculation(self):
        """测试月份计算逻辑"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'

        # 创建1月份的工时记录（测试跨年逻辑）
        ts1 = MagicMock()
        ts1.hours = 10
        ts1.user_id = 1
        ts1.work_date = date(2026, 1, 15)

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                filter_result = mock_query.filter.return_value
                filter_result.all.return_value = [ts1]
            return mock_query

        self.db.query.side_effect = query_side_effect

        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_rate:
            mock_rate.get_user_hourly_rate.return_value = 100

            result = self.service.analyze_cost_trend(1, months=12)

            # 验证趋势数据已排序
            months = [item['month'] for item in result['monthly_trend']]
            assert months == sorted(months)

    def test_analyze_cost_trend_personnel_count_per_month(self):
        """测试每月人员数量计算"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'

        today = date.today()
        
        # 同一月份的两个用户
        ts1 = MagicMock()
        ts1.hours = 10
        ts1.user_id = 1
        ts1.work_date = today

        ts2 = MagicMock()
        ts2.hours = 15
        ts2.user_id = 2
        ts2.work_date = today

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                filter_result = mock_query.filter.return_value
                filter_result.all.return_value = [ts1, ts2]
            return mock_query

        self.db.query.side_effect = query_side_effect

        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_rate:
            mock_rate.get_user_hourly_rate.return_value = 100

            result = self.service.analyze_cost_trend(1, months=1)

            # 找到当前月份的数据
            current_month_key = today.strftime('%Y-%m')
            current_month_data = next(
                (item for item in result['monthly_trend'] if item['month'] == current_month_key),
                None
            )

            if current_month_data:
                assert current_month_data['hours'] == 25  # 10 + 15
                assert current_month_data['cost'] == 2500  # 25 * 100
                assert current_month_data['personnel_count'] == 2

    def test_analyze_cost_trend_empty_months(self):
        """测试空月份的数据"""
        project = MagicMock()
        project.id = 1
        project.project_code = 'P001'
        project.project_name = '测试项目'

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = project
            elif model.__name__ == 'Timesheet':
                filter_result = mock_query.filter.return_value
                filter_result.all.return_value = []  # 没有工时记录
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.service.analyze_cost_trend(1, months=3)

        # 验证所有月份都有数据，即使为0
        for month_data in result['monthly_trend']:
            assert month_data['hours'] == 0
            assert month_data['cost'] == 0
            assert month_data['personnel_count'] == 0

        assert result['total_hours'] == 0
        assert result['total_cost'] == 0
