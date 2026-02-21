# -*- coding: utf-8 -*-
"""
成本过高分析服务增强单元测试
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService


class TestCostOverrunAnalysisServiceInit(unittest.TestCase):
    """测试初始化"""

    def test_init_creates_instance(self):
        """测试创建实例"""
        db = MagicMock()
        service = CostOverrunAnalysisService(db)
        self.assertIsNotNone(service)
        self.assertEqual(service.db, db)

    def test_init_creates_hourly_rate_service(self):
        """测试初始化时创建 HourlyRateService"""
        db = MagicMock()
        service = CostOverrunAnalysisService(db)
        self.assertIsNotNone(service.hourly_rate_service)


class TestCalculateActualHours(unittest.TestCase):
    """测试计算实际工时"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_calculate_actual_hours_with_data(self):
        """测试有工时数据时计算"""
        # Mock query chain
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = 120.5

        result = self.service._calculate_actual_hours(1)
        self.assertEqual(result, 120.5)

    def test_calculate_actual_hours_no_data(self):
        """测试无工时数据时返回0"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = None

        result = self.service._calculate_actual_hours(1)
        self.assertEqual(result, 0.0)

    def test_calculate_actual_hours_zero(self):
        """测试工时为0"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = 0

        result = self.service._calculate_actual_hours(1)
        self.assertEqual(result, 0.0)


class TestCalculateMaterialCost(unittest.TestCase):
    """测试计算物料成本"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_calculate_material_cost_with_data(self):
        """测试有物料成本数据"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = Decimal('5000.00')

        result = self.service._calculate_material_cost(1)
        self.assertEqual(result, Decimal('5000.00'))

    def test_calculate_material_cost_no_data(self):
        """测试无物料成本数据"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = None

        result = self.service._calculate_material_cost(1)
        self.assertEqual(result, Decimal('0'))

    def test_calculate_material_cost_multiple_types(self):
        """测试只统计MATERIAL类型"""
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = Decimal('3500.50')

        result = self.service._calculate_material_cost(1)
        self.assertIsInstance(result, Decimal)
        self.assertEqual(result, Decimal('3500.50'))


class TestCalculateLaborCost(unittest.TestCase):
    """测试计算工时成本"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_calculate_labor_cost_with_timesheets(self):
        """测试有工时记录时计算成本"""
        # 创建真实的Timesheet对象
        mock_timesheet1 = Mock()
        mock_timesheet1.user_id = 1
        mock_timesheet1.hours = 10.0
        mock_timesheet1.work_date = date(2024, 1, 15)

        mock_timesheet2 = Mock()
        mock_timesheet2.user_id = 2
        mock_timesheet2.hours = 15.5
        mock_timesheet2.work_date = date(2024, 1, 16)

        # Mock Timesheet query
        mock_ts_query = Mock()
        mock_ts_filter = Mock()
        mock_ts_filter.all.return_value = [mock_timesheet1, mock_timesheet2]
        mock_ts_query.filter.return_value = mock_ts_filter

        # Mock User query
        mock_user1 = Mock()
        mock_user1.id = 1
        mock_user2 = Mock()
        mock_user2.id = 2

        mock_user_query = Mock()
        mock_user_filter = Mock()
        mock_user_filter.first.side_effect = [mock_user1, mock_user2]
        mock_user_query.filter.return_value = mock_user_filter

        # 设置 query 返回不同的结果
        def query_side_effect(model):
            from app.models.timesheet import Timesheet
            from app.models.user import User
            if model.__name__ == 'Timesheet' or str(model) == str(Timesheet):
                return mock_ts_query
            elif model.__name__ == 'User' or str(model) == str(User):
                return mock_user_query
            return Mock()

        self.db.query.side_effect = query_side_effect

        # Mock hourly rate service
        self.service.hourly_rate_service.get_user_hourly_rate = Mock(
            side_effect=[Decimal('100'), Decimal('150')]
        )

        result = self.service._calculate_labor_cost(1)
        expected = Decimal('10.0') * Decimal('100') + Decimal('15.5') * Decimal('150')
        self.assertEqual(result, expected)

    def test_calculate_labor_cost_no_timesheets(self):
        """测试无工时记录时返回0"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        result = self.service._calculate_labor_cost(1)
        self.assertEqual(result, Decimal('0'))

    def test_calculate_labor_cost_user_not_found(self):
        """测试用户不存在时跳过该工时"""
        mock_timesheet = Mock()
        mock_timesheet.user_id = 1
        mock_timesheet.hours = 10.0
        mock_timesheet.work_date = date(2024, 1, 15)

        mock_ts_query = Mock()
        mock_ts_filter = Mock()
        mock_ts_filter.all.return_value = [mock_timesheet]
        mock_ts_query.filter.return_value = mock_ts_filter

        mock_user_query = Mock()
        mock_user_filter = Mock()
        mock_user_filter.first.return_value = None
        mock_user_query.filter.return_value = mock_user_filter

        def query_side_effect(model):
            from app.models.timesheet import Timesheet
            from app.models.user import User
            if model.__name__ == 'Timesheet' or str(model) == str(Timesheet):
                return mock_ts_query
            elif model.__name__ == 'User' or str(model) == str(User):
                return mock_user_query
            return Mock()

        self.db.query.side_effect = query_side_effect

        result = self.service._calculate_labor_cost(1)
        self.assertEqual(result, Decimal('0'))


class TestCalculateOutsourcingCost(unittest.TestCase):
    """测试计算外协成本"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_calculate_outsourcing_cost_with_orders(self):
        """测试有外协订单时计算成本"""
        mock_order1 = Mock()
        mock_order1.total_amount = Decimal('2000.00')

        mock_order2 = Mock()
        mock_order2.total_amount = Decimal('3500.50')

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [mock_order1, mock_order2]
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        result = self.service._calculate_outsourcing_cost(1)
        self.assertEqual(result, Decimal('5500.50'))

    def test_calculate_outsourcing_cost_no_orders(self):
        """测试无外协订单时返回0"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        result = self.service._calculate_outsourcing_cost(1)
        self.assertEqual(result, Decimal('0'))

    def test_calculate_outsourcing_cost_with_none_amount(self):
        """测试订单金额为None时的处理"""
        mock_order = Mock()
        mock_order.total_amount = None

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [mock_order]
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        result = self.service._calculate_outsourcing_cost(1)
        self.assertEqual(result, Decimal('0'))


class TestCalculateActualCost(unittest.TestCase):
    """测试计算项目实际成本"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_calculate_actual_cost_all_components(self):
        """测试计算包含所有成本组件"""
        # Mock各个成本计算方法
        self.service._calculate_material_cost = Mock(return_value=Decimal('5000'))
        self.service._calculate_labor_cost = Mock(return_value=Decimal('10000'))
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('3000'))

        # Mock其他成本查询
        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = Decimal('2000')

        result = self.service._calculate_actual_cost(1)
        expected = Decimal('5000') + Decimal('10000') + Decimal('3000') + Decimal('2000')
        self.assertEqual(result, expected)

    def test_calculate_actual_cost_no_other_costs(self):
        """测试无其他成本时"""
        self.service._calculate_material_cost = Mock(return_value=Decimal('5000'))
        self.service._calculate_labor_cost = Mock(return_value=Decimal('10000'))
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('3000'))

        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = None

        result = self.service._calculate_actual_cost(1)
        self.assertEqual(result, Decimal('18000'))

    def test_calculate_actual_cost_zero_costs(self):
        """测试所有成本为0"""
        self.service._calculate_material_cost = Mock(return_value=Decimal('0'))
        self.service._calculate_labor_cost = Mock(return_value=Decimal('0'))
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('0'))

        mock_query = self.db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = Decimal('0')

        result = self.service._calculate_actual_cost(1)
        self.assertEqual(result, Decimal('0'))


class TestAnalyzeProjectOverrun(unittest.TestCase):
    """测试分析单个项目的成本超支"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_analyze_project_no_overrun(self):
        """测试项目无超支"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = 'Test Project'
        mock_project.budget = Decimal('20000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        self.service._calculate_actual_cost = Mock(return_value=Decimal('15000'))
        self.service._calculate_actual_hours = Mock(return_value=80.0)

        result = self.service._analyze_project_overrun(mock_project)

        self.assertFalse(result['has_overrun'])
        self.assertEqual(result['project_id'], 1)
        self.assertEqual(result['budget'], 20000.0)
        self.assertEqual(result['actual_cost'], 15000.0)
        self.assertEqual(result['overrun_amount'], 0.0)
        self.assertEqual(result['reasons'], [])

    def test_analyze_project_with_overrun_hours(self):
        """测试工时超支"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = 'Test Project'
        mock_project.budget = Decimal('20000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        self.service._calculate_actual_cost = Mock(return_value=Decimal('25000'))
        self.service._calculate_actual_hours = Mock(return_value=150.0)
        self.service._calculate_material_cost = Mock(return_value=Decimal('5000'))
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('3000'))

        result = self.service._analyze_project_overrun(mock_project)

        self.assertTrue(result['has_overrun'])
        self.assertEqual(result['overrun_amount'], 5000.0)
        self.assertIn('工时超支', result['reasons'])

    def test_analyze_project_with_ecn(self):
        """测试有需求变更"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = 'Test Project'
        mock_project.budget = Decimal('20000')
        mock_project.plan_manhours = 100
        mock_project.ecns = [Mock()]  # 有ECN

        self.service._calculate_actual_cost = Mock(return_value=Decimal('25000'))
        self.service._calculate_actual_hours = Mock(return_value=90.0)
        self.service._calculate_material_cost = Mock(return_value=Decimal('5000'))
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('3000'))

        result = self.service._analyze_project_overrun(mock_project)

        self.assertTrue(result['has_overrun'])
        self.assertIn('需求变更导致成本增加', result['reasons'])

    def test_analyze_project_material_overrun(self):
        """测试物料成本超支"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = 'Test Project'
        mock_project.budget = Decimal('20000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        self.service._calculate_actual_cost = Mock(return_value=Decimal('25000'))
        self.service._calculate_actual_hours = Mock(return_value=90.0)
        self.service._calculate_material_cost = Mock(return_value=Decimal('15000'))  # 超过预算50%
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('2000'))

        result = self.service._analyze_project_overrun(mock_project)

        self.assertTrue(result['has_overrun'])
        self.assertIn('物料成本超支', result['reasons'])

    def test_analyze_project_outsourcing_overrun(self):
        """测试外协成本超支"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = 'Test Project'
        mock_project.budget = Decimal('20000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        self.service._calculate_actual_cost = Mock(return_value=Decimal('25000'))
        self.service._calculate_actual_hours = Mock(return_value=90.0)
        self.service._calculate_material_cost = Mock(return_value=Decimal('5000'))
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('8000'))  # 超过预算20%

        result = self.service._analyze_project_overrun(mock_project)

        self.assertTrue(result['has_overrun'])
        self.assertIn('外协成本超支', result['reasons'])

    def test_analyze_project_overrun_ratio_calculation(self):
        """测试超支比例计算"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = 'Test Project'
        mock_project.budget = Decimal('10000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        self.service._calculate_actual_cost = Mock(return_value=Decimal('12000'))
        self.service._calculate_actual_hours = Mock(return_value=90.0)
        self.service._calculate_material_cost = Mock(return_value=Decimal('5000'))
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('2000'))

        result = self.service._analyze_project_overrun(mock_project)

        self.assertTrue(result['has_overrun'])
        self.assertEqual(result['overrun_ratio'], 20.0)  # (12000-10000)/10000*100

    def test_analyze_project_zero_budget(self):
        """测试预算为0时的处理"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = 'Test Project'
        mock_project.budget = Decimal('0')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        self.service._calculate_actual_cost = Mock(return_value=Decimal('5000'))
        self.service._calculate_actual_hours = Mock(return_value=90.0)
        self.service._calculate_material_cost = Mock(return_value=Decimal('2000'))
        self.service._calculate_outsourcing_cost = Mock(return_value=Decimal('1000'))

        result = self.service._analyze_project_overrun(mock_project)

        self.assertTrue(result['has_overrun'])
        self.assertEqual(result['overrun_ratio'], 0.0)


class TestAnalyzeReasons(unittest.TestCase):
    """测试成本超支原因分析"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_analyze_reasons_no_projects(self):
        """测试无项目时"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        result = self.service.analyze_reasons()

        self.assertEqual(result['total_overrun_projects'], 0)
        self.assertEqual(result['reasons'], [])
        self.assertEqual(result['projects'], [])

    def test_analyze_reasons_with_project_filter(self):
        """测试按项目ID过滤"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.status = 'ST10'

        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.all.return_value = [mock_project]
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        self.db.query.return_value = mock_query

        self.service._analyze_project_overrun = Mock(return_value={
            'has_overrun': False,
            'project_id': 1,
            'overrun_amount': 0.0,
            'reasons': []
        })

        result = self.service.analyze_reasons(project_id=1)
        self.assertIsNotNone(result)

    def test_analyze_reasons_with_date_range(self):
        """测试按日期范围过滤"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.status = 'ST10'
        mock_project.created_at = datetime(2024, 1, 15)

        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter3 = Mock()
        mock_filter3.all.return_value = [mock_project]
        mock_filter2.filter.return_value = mock_filter3
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        self.db.query.return_value = mock_query

        self.service._analyze_project_overrun = Mock(return_value={
            'has_overrun': False,
            'project_id': 1,
            'overrun_amount': 0.0,
            'reasons': []
        })

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.analyze_reasons(start_date=start_date, end_date=end_date)

        self.assertEqual(result['analysis_period']['start_date'], '2024-01-01')
        self.assertEqual(result['analysis_period']['end_date'], '2024-01-31')

    def test_analyze_reasons_aggregates_by_reason(self):
        """测试按原因聚合统计"""
        mock_project1 = Mock()
        mock_project1.id = 1
        mock_project1.status = 'ST10'
        mock_project1.project_code = 'PRJ001'

        mock_project2 = Mock()
        mock_project2.id = 2
        mock_project2.status = 'ST20'
        mock_project2.project_code = 'PRJ002'

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [mock_project1, mock_project2]
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        self.service._analyze_project_overrun = Mock(side_effect=[
            {
                'has_overrun': True,
                'project_id': 1,
                'project_code': 'PRJ001',
                'overrun_amount': 5000.0,
                'reasons': ['工时超支', '物料成本超支']
            },
            {
                'has_overrun': True,
                'project_id': 2,
                'project_code': 'PRJ002',
                'overrun_amount': 3000.0,
                'reasons': ['工时超支']
            }
        ])

        result = self.service.analyze_reasons()

        self.assertEqual(result['total_overrun_projects'], 2)
        # 检查原因统计
        reasons = {r['reason']: r for r in result['reasons']}
        self.assertIn('工时超支', reasons)
        self.assertEqual(reasons['工时超支']['count'], 2)
        self.assertEqual(reasons['工时超支']['total_overrun'], 8000.0)


class TestAnalyzeAccountability(unittest.TestCase):
    """测试成本超支归责"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_analyze_accountability_empty(self):
        """测试无超支项目时"""
        self.service.analyze_reasons = Mock(return_value={
            'projects': []
        })

        result = self.service.analyze_accountability()

        self.assertEqual(len(result['by_person']), 0)

    def test_analyze_accountability_by_opportunity_owner(self):
        """测试归责到商机负责人"""
        mock_opp = Mock()
        mock_opp.owner_id = 1

        mock_project = Mock()
        mock_project.id = 1
        mock_project.opportunity_id = 1
        mock_project.opportunity = mock_opp
        mock_project.salesperson_id = None
        mock_project.pm_id = None

        mock_user = Mock()
        mock_user.id = 1
        mock_user.real_name = 'Zhang San'
        mock_user.username = 'zhangsan'
        mock_user.department = 'Sales'

        # Setup query mocks
        def query_side_effect(model):
            from app.models.project import Project
            from app.models.user import User
            if model.__name__ == 'Project' or str(model) == str(Project):
                mock_q = Mock()
                mock_f = Mock()
                mock_f.first.return_value = mock_project
                mock_q.filter.return_value = mock_f
                return mock_q
            elif model.__name__ == 'Timesheet':
                mock_q = Mock()
                mock_f = Mock()
                mock_f.all.return_value = []
                mock_q.filter.return_value = mock_f
                return mock_q
            elif model.__name__ == 'User' or str(model) == str(User):
                mock_q = Mock()
                mock_f = Mock()
                mock_f.first.return_value = mock_user
                mock_q.filter.return_value = mock_f
                return mock_q
            return Mock()

        self.db.query.side_effect = query_side_effect

        self.service.analyze_reasons = Mock(return_value={
            'projects': [{
                'project_id': 1,
                'overrun_amount': 5000.0
            }]
        })

        result = self.service.analyze_accountability()

        self.assertGreater(len(result['by_person']), 0)
        person = result['by_person'][0]
        self.assertEqual(person['person_name'], 'Zhang San')
        self.assertIn('报价不准确', person['reasons'])


class TestAnalyzeImpact(unittest.TestCase):
    """测试成本超支影响分析"""

    def setUp(self):
        self.db = MagicMock()
        self.service = CostOverrunAnalysisService(self.db)

    def test_analyze_impact_no_projects(self):
        """测试无超支项目时"""
        self.service.analyze_reasons = Mock(return_value={
            'projects': []
        })

        result = self.service.analyze_impact()

        self.assertEqual(result['summary']['total_overrun'], 0.0)
        self.assertEqual(result['summary']['total_contract_amount'], 0.0)
        self.assertEqual(len(result['affected_projects']), 0)

    def test_analyze_impact_calculates_margin_impact(self):
        """测试计算毛利率影响"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.contract_amount = Decimal('100000')
        mock_project.est_margin = Decimal('20')

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_project
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        self.service.analyze_reasons = Mock(return_value={
            'projects': [{
                'project_id': 1,
                'project_code': 'PRJ001',
                'overrun_amount': 10000.0
            }]
        })

        result = self.service.analyze_impact()

        self.assertEqual(result['summary']['total_overrun'], 10000.0)
        self.assertEqual(result['summary']['total_contract_amount'], 100000.0)
        self.assertGreater(len(result['affected_projects']), 0)
        affected = result['affected_projects'][0]
        self.assertEqual(affected['margin_impact'], 10.0)  # 20 - 10

    def test_analyze_impact_zero_contract_amount(self):
        """测试合同金额为0时的处理"""
        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.contract_amount = None
        mock_project.est_margin = Decimal('20')

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_project
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        self.service.analyze_reasons = Mock(return_value={
            'projects': [{
                'project_id': 1,
                'project_code': 'PRJ001',
                'overrun_amount': 10000.0
            }]
        })

        result = self.service.analyze_impact()

        self.assertEqual(result['summary']['overrun_ratio'], 0.0)

    def test_analyze_impact_with_date_range(self):
        """测试带日期范围的影响分析"""
        self.service.analyze_reasons = Mock(return_value={
            'projects': []
        })

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        result = self.service.analyze_impact(start_date=start_date, end_date=end_date)

        self.assertEqual(result['analysis_period']['start_date'], '2024-01-01')
        self.assertEqual(result['analysis_period']['end_date'], '2024-01-31')


if __name__ == '__main__':
    unittest.main()
