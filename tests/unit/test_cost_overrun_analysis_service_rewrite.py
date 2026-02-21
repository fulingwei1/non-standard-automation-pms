# -*- coding: utf-8 -*-
"""
成本过高分析服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict

from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService


class TestCostOverrunAnalysisServiceCore(unittest.TestCase):
    """测试核心业务逻辑"""

    def setUp(self):
        """测试前置设置"""
        self.mock_db = MagicMock()
        self.service = CostOverrunAnalysisService(self.mock_db)
        # Mock hourly_rate_service
        self.service.hourly_rate_service = MagicMock()

    # ========== analyze_reasons() 测试 ==========

    def test_analyze_reasons_no_projects(self):
        """测试没有项目的情况"""
        # Mock查询返回空列表
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.service.analyze_reasons()

        self.assertEqual(result['total_overrun_projects'], 0)
        self.assertEqual(len(result['reasons']), 0)
        self.assertEqual(len(result['projects']), 0)

    def test_analyze_reasons_with_date_filters(self):
        """测试带日期过滤器"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        result = self.service.analyze_reasons(start_date=start_date, end_date=end_date)

        # 验证日期被正确传递
        self.assertEqual(result['analysis_period']['start_date'], '2024-01-01')
        self.assertEqual(result['analysis_period']['end_date'], '2024-12-31')

    def test_analyze_reasons_with_project_id(self):
        """测试带项目ID过滤"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.service.analyze_reasons(project_id=123)

        # 验证过滤条件被调用
        self.assertTrue(mock_query.filter.called)

    def test_analyze_reasons_with_overrun_projects(self):
        """测试有超支项目的情况"""
        # 创建mock项目
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = Decimal('10000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        # Mock查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_project]
        self.mock_db.query.return_value = mock_query

        # Mock _analyze_project_overrun返回超支信息
        with patch.object(self.service, '_analyze_project_overrun') as mock_analyze:
            mock_analyze.return_value = {
                'project_id': 1,
                'project_code': 'PRJ001',
                'project_name': '测试项目',
                'has_overrun': True,
                'budget': 10000.0,
                'actual_cost': 15000.0,
                'overrun_amount': 5000.0,
                'overrun_ratio': 50.0,
                'reasons': ['工时超支', '物料成本超支']
            }

            result = self.service.analyze_reasons()

        # 验证结果
        self.assertEqual(result['total_overrun_projects'], 1)
        self.assertEqual(len(result['reasons']), 2)
        # 验证原因统计
        reason_names = [r['reason'] for r in result['reasons']]
        self.assertIn('工时超支', reason_names)
        self.assertIn('物料成本超支', reason_names)

    def test_analyze_reasons_multiple_projects(self):
        """测试多个项目超支统计"""
        # 创建两个mock项目
        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.project_code = 'PRJ001'

        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.project_code = 'PRJ002'

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_project1, mock_project2]
        self.mock_db.query.return_value = mock_query

        # Mock两次调用
        with patch.object(self.service, '_analyze_project_overrun') as mock_analyze:
            mock_analyze.side_effect = [
                {
                    'project_id': 1,
                    'project_code': 'PRJ001',
                    'has_overrun': True,
                    'overrun_amount': 5000.0,
                    'reasons': ['工时超支']
                },
                {
                    'project_id': 2,
                    'project_code': 'PRJ002',
                    'has_overrun': True,
                    'overrun_amount': 3000.0,
                    'reasons': ['工时超支', '物料成本超支']
                }
            ]

            result = self.service.analyze_reasons()

        # 验证结果
        self.assertEqual(result['total_overrun_projects'], 2)
        # 工时超支应该有2次
        hours_reason = next((r for r in result['reasons'] if r['reason'] == '工时超支'), None)
        self.assertIsNotNone(hours_reason)
        self.assertEqual(hours_reason['count'], 2)
        self.assertEqual(hours_reason['total_overrun'], 8000.0)

    # ========== analyze_accountability() 测试 ==========

    def test_analyze_accountability_no_projects(self):
        """测试归责分析 - 无项目"""
        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': []
            }

            result = self.service.analyze_accountability()

        self.assertEqual(len(result['by_person']), 0)
        self.assertEqual(len(result['by_department']), 0)

    def test_analyze_accountability_with_opportunity_owner(self):
        """测试归责到报价人员"""
        # Mock项目数据
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.opportunity_id = 100
        mock_project.opportunity = MagicMock()
        mock_project.opportunity.owner_id = 10
        mock_project.salesperson_id = None
        mock_project.pm_id = None

        # Mock用户
        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.real_name = '张三'
        mock_user.username = 'zhangsan'
        mock_user.department = '销售部'

        # 设置查询mock
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Project':
                mock_q.first.return_value = mock_project
            elif model.__name__ == 'User':
                mock_q.first.return_value = mock_user
            elif model.__name__ == 'Timesheet':
                mock_q.all.return_value = []
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect

        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': [{
                    'project_id': 1,
                    'overrun_amount': 5000.0
                }]
            }

            result = self.service.analyze_accountability()

        # 验证结果
        self.assertEqual(len(result['by_person']), 1)
        person = result['by_person'][0]
        self.assertEqual(person['person_id'], 10)
        self.assertEqual(person['person_name'], '张三')
        self.assertEqual(person['total_overrun'], 5000.0)
        self.assertIn('报价不准确', person['reasons'])

    def test_analyze_accountability_with_salesperson(self):
        """测试归责到销售"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.opportunity_id = None
        mock_project.salesperson_id = 20
        mock_project.pm_id = None

        mock_user = MagicMock()
        mock_user.id = 20
        mock_user.real_name = '李四'
        mock_user.username = 'lisi'
        mock_user.department = '销售部'

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Project':
                mock_q.first.return_value = mock_project
            elif model.__name__ == 'User':
                mock_q.first.return_value = mock_user
            elif model.__name__ == 'Timesheet':
                mock_q.all.return_value = []
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect

        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': [{
                    'project_id': 1,
                    'overrun_amount': 3000.0
                }]
            }

            result = self.service.analyze_accountability()

        person = result['by_person'][0]
        self.assertEqual(person['person_id'], 20)
        self.assertIn('需求把握不准', person['reasons'])

    def test_analyze_accountability_with_pm(self):
        """测试归责到项目经理"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.opportunity_id = None
        mock_project.salesperson_id = None
        mock_project.pm_id = 30

        mock_user = MagicMock()
        mock_user.id = 30
        mock_user.real_name = '王五'
        mock_user.username = 'wangwu'
        mock_user.department = '项目部'

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Project':
                mock_q.first.return_value = mock_project
            elif model.__name__ == 'User':
                mock_q.first.return_value = mock_user
            elif model.__name__ == 'Timesheet':
                mock_q.all.return_value = []
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect

        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': [{
                    'project_id': 1,
                    'overrun_amount': 4000.0
                }]
            }

            result = self.service.analyze_accountability()

        person = result['by_person'][0]
        self.assertEqual(person['person_id'], 30)
        self.assertIn('成本控制不力', person['reasons'])

    def test_analyze_accountability_with_engineer_timesheet(self):
        """测试归责到工程师（工时超支）"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.opportunity_id = None
        mock_project.salesperson_id = None
        mock_project.pm_id = None

        # Mock timesheet
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 40
        mock_timesheet.hours = 10
        mock_timesheet.work_date = date(2024, 1, 15)

        mock_user = MagicMock()
        mock_user.id = 40
        mock_user.real_name = '赵六'
        mock_user.username = 'zhaoliu'
        mock_user.department = '研发部'

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Project':
                mock_q.first.return_value = mock_project
            elif model.__name__ == 'User':
                mock_q.first.return_value = mock_user
            elif model.__name__ == 'Timesheet':
                mock_q.all.return_value = [mock_timesheet]
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect

        # Mock hourly_rate_service
        self.service.hourly_rate_service.get_user_hourly_rate.return_value = Decimal('100')

        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': [{
                    'project_id': 1,
                    'overrun_amount': 2000.0
                }]
            }

            result = self.service.analyze_accountability()

        # 验证工程师被归责
        person = next((p for p in result['by_person'] if p['person_id'] == 40), None)
        self.assertIsNotNone(person)

    # ========== analyze_impact() 测试 ==========

    def test_analyze_impact_no_projects(self):
        """测试影响分析 - 无项目"""
        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {'projects': []}

            result = self.service.analyze_impact()

        self.assertEqual(result['summary']['total_overrun'], 0.0)
        self.assertEqual(result['summary']['total_contract_amount'], 0.0)
        self.assertEqual(result['summary']['overrun_ratio'], 0)

    def test_analyze_impact_with_projects(self):
        """测试影响分析 - 有超支项目"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.contract_amount = Decimal('100000')
        mock_project.est_margin = Decimal('20')

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        self.mock_db.query.return_value = mock_query

        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': [{
                    'project_id': 1,
                    'overrun_amount': 10000.0
                }]
            }

            result = self.service.analyze_impact()

        # 验证结果
        self.assertEqual(result['summary']['total_overrun'], 10000.0)
        self.assertEqual(result['summary']['total_contract_amount'], 100000.0)
        self.assertEqual(result['summary']['overrun_ratio'], 10.0)
        
        # 验证项目影响
        self.assertEqual(len(result['affected_projects']), 1)
        project = result['affected_projects'][0]
        self.assertEqual(project['project_id'], 1)
        self.assertEqual(project['overrun_amount'], 10000.0)
        self.assertEqual(project['original_margin'], 20.0)
        # 毛利率影响: 20 - (10000/100000 * 100) = 20 - 10 = 10
        self.assertEqual(project['affected_margin'], 10.0)

    def test_analyze_impact_zero_contract_amount(self):
        """测试合同金额为0的情况"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.contract_amount = Decimal('0')
        mock_project.est_margin = Decimal('0')

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        self.mock_db.query.return_value = mock_query

        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': [{
                    'project_id': 1,
                    'overrun_amount': 5000.0
                }]
            }

            result = self.service.analyze_impact()

        # 验证不会除以0
        self.assertEqual(result['summary']['overrun_ratio'], 0)

    # ========== _analyze_project_overrun() 测试 ==========

    def test_analyze_project_overrun_no_overrun(self):
        """测试项目无超支"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = Decimal('10000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        with patch.object(self.service, '_calculate_actual_cost') as mock_cost:
            mock_cost.return_value = Decimal('8000')

            result = self.service._analyze_project_overrun(mock_project)

        self.assertFalse(result['has_overrun'])
        self.assertEqual(result['budget'], 10000.0)
        self.assertEqual(result['actual_cost'], 8000.0)
        self.assertEqual(result['overrun_amount'], 0.0)
        self.assertEqual(len(result['reasons']), 0)

    def test_analyze_project_overrun_with_overrun(self):
        """测试项目有超支"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = Decimal('10000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        with patch.object(self.service, '_calculate_actual_cost') as mock_cost, \
             patch.object(self.service, '_calculate_actual_hours') as mock_hours, \
             patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_cost.return_value = Decimal('15000')
            mock_hours.return_value = 150.0  # 超过计划的100小时
            mock_material.return_value = Decimal('3000')
            mock_outsourcing.return_value = Decimal('1000')

            result = self.service._analyze_project_overrun(mock_project)

        self.assertTrue(result['has_overrun'])
        self.assertEqual(result['overrun_amount'], 5000.0)
        self.assertEqual(result['overrun_ratio'], 50.0)
        # 应该包含"工时超支"原因
        self.assertIn('工时超支', result['reasons'])

    def test_analyze_project_overrun_with_ecn(self):
        """测试有需求变更的超支"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = Decimal('10000')
        mock_project.plan_manhours = 100
        mock_project.ecns = [MagicMock()]  # 有ECN

        with patch.object(self.service, '_calculate_actual_cost') as mock_cost, \
             patch.object(self.service, '_calculate_actual_hours') as mock_hours, \
             patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_cost.return_value = Decimal('12000')
            mock_hours.return_value = 90.0  # 未超工时
            mock_material.return_value = Decimal('2000')
            mock_outsourcing.return_value = Decimal('500')

            result = self.service._analyze_project_overrun(mock_project)

        self.assertTrue(result['has_overrun'])
        self.assertIn('需求变更导致成本增加', result['reasons'])

    def test_analyze_project_overrun_material_cost_high(self):
        """测试物料成本超支"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = Decimal('10000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        with patch.object(self.service, '_calculate_actual_cost') as mock_cost, \
             patch.object(self.service, '_calculate_actual_hours') as mock_hours, \
             patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_cost.return_value = Decimal('12000')
            mock_hours.return_value = 90.0
            mock_material.return_value = Decimal('8000')  # 超过budget的50%
            mock_outsourcing.return_value = Decimal('500')

            result = self.service._analyze_project_overrun(mock_project)

        self.assertIn('物料成本超支', result['reasons'])

    def test_analyze_project_overrun_outsourcing_cost_high(self):
        """测试外协成本超支"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = Decimal('10000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        with patch.object(self.service, '_calculate_actual_cost') as mock_cost, \
             patch.object(self.service, '_calculate_actual_hours') as mock_hours, \
             patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_cost.return_value = Decimal('12000')
            mock_hours.return_value = 90.0
            mock_material.return_value = Decimal('2000')
            mock_outsourcing.return_value = Decimal('3000')  # 超过budget的20%

            result = self.service._analyze_project_overrun(mock_project)

        self.assertIn('外协成本超支', result['reasons'])

    def test_analyze_project_overrun_other_reasons(self):
        """测试其他原因"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = Decimal('10000')
        mock_project.plan_manhours = 100
        mock_project.ecns = []

        with patch.object(self.service, '_calculate_actual_cost') as mock_cost, \
             patch.object(self.service, '_calculate_actual_hours') as mock_hours, \
             patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_cost.return_value = Decimal('11000')
            mock_hours.return_value = 90.0  # 不超工时
            mock_material.return_value = Decimal('2000')  # 不超50%
            mock_outsourcing.return_value = Decimal('500')  # 不超20%

            result = self.service._analyze_project_overrun(mock_project)

        self.assertIn('其他原因', result['reasons'])

    # ========== _calculate_actual_cost() 测试 ==========

    def test_calculate_actual_cost(self):
        """测试计算实际成本"""
        with patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_labor_cost') as mock_labor, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_material.return_value = Decimal('5000')
            mock_labor.return_value = Decimal('8000')
            mock_outsourcing.return_value = Decimal('2000')

            # Mock其他成本
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.scalar.return_value = Decimal('1000')
            self.mock_db.query.return_value = mock_query

            result = self.service._calculate_actual_cost(1)

        self.assertEqual(result, Decimal('16000'))

    def test_calculate_actual_cost_no_other_costs(self):
        """测试计算实际成本 - 无其他成本"""
        with patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_labor_cost') as mock_labor, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_material.return_value = Decimal('5000')
            mock_labor.return_value = Decimal('8000')
            mock_outsourcing.return_value = Decimal('2000')

            # Mock其他成本为None
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.scalar.return_value = None
            self.mock_db.query.return_value = mock_query

            result = self.service._calculate_actual_cost(1)

        self.assertEqual(result, Decimal('15000'))

    # ========== _calculate_material_cost() 测试 ==========

    def test_calculate_material_cost(self):
        """测试计算物料成本"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = Decimal('5000')
        self.mock_db.query.return_value = mock_query

        result = self.service._calculate_material_cost(1)

        self.assertEqual(result, Decimal('5000'))

    def test_calculate_material_cost_none(self):
        """测试计算物料成本 - 返回None"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        self.mock_db.query.return_value = mock_query

        result = self.service._calculate_material_cost(1)

        self.assertEqual(result, Decimal('0'))

    # ========== _calculate_labor_cost() 测试 ==========

    def test_calculate_labor_cost(self):
        """测试计算工时成本"""
        # Mock timesheet
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.hours = 10
        mock_timesheet.work_date = date(2024, 1, 15)

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 1

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Timesheet':
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == 'User':
                mock_q.first.return_value = mock_user
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect
        self.service.hourly_rate_service.get_user_hourly_rate.return_value = Decimal('100')

        result = self.service._calculate_labor_cost(1)

        self.assertEqual(result, Decimal('1000'))

    def test_calculate_labor_cost_no_user(self):
        """测试计算工时成本 - 用户不存在"""
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.hours = 10
        mock_timesheet.work_date = date(2024, 1, 15)

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Timesheet':
                mock_q.all.return_value = [mock_timesheet]
            elif model.__name__ == 'User':
                mock_q.first.return_value = None  # 用户不存在
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service._calculate_labor_cost(1)

        self.assertEqual(result, Decimal('0'))

    def test_calculate_labor_cost_multiple_timesheets(self):
        """测试计算工时成本 - 多条记录"""
        mock_timesheet1 = MagicMock()
        mock_timesheet1.user_id = 1
        mock_timesheet1.hours = 10
        mock_timesheet1.work_date = date(2024, 1, 15)

        mock_timesheet2 = MagicMock()
        mock_timesheet2.user_id = 2
        mock_timesheet2.hours = 5
        mock_timesheet2.work_date = date(2024, 1, 16)

        mock_user1 = MagicMock()
        mock_user1.id = 1

        mock_user2 = MagicMock()
        mock_user2.id = 2

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Timesheet':
                mock_q.all.return_value = [mock_timesheet1, mock_timesheet2]
            elif model.__name__ == 'User':
                # 根据调用次数返回不同用户
                if not hasattr(mock_query_side_effect, 'call_count'):
                    mock_query_side_effect.call_count = 0
                mock_query_side_effect.call_count += 1
                if mock_query_side_effect.call_count <= 2:
                    mock_q.first.return_value = mock_user1
                else:
                    mock_q.first.return_value = mock_user2
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect
        self.service.hourly_rate_service.get_user_hourly_rate.return_value = Decimal('100')

        result = self.service._calculate_labor_cost(1)

        self.assertEqual(result, Decimal('1500'))

    # ========== _calculate_outsourcing_cost() 测试 ==========

    def test_calculate_outsourcing_cost(self):
        """测试计算外协成本"""
        mock_order = MagicMock()
        mock_order.total_amount = Decimal('3000')

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_order]
        self.mock_db.query.return_value = mock_query

        result = self.service._calculate_outsourcing_cost(1)

        self.assertEqual(result, Decimal('3000'))

    def test_calculate_outsourcing_cost_none(self):
        """测试计算外协成本 - 金额为None"""
        mock_order = MagicMock()
        mock_order.total_amount = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_order]
        self.mock_db.query.return_value = mock_query

        result = self.service._calculate_outsourcing_cost(1)

        self.assertEqual(result, Decimal('0'))

    def test_calculate_outsourcing_cost_multiple_orders(self):
        """测试计算外协成本 - 多个订单"""
        mock_order1 = MagicMock()
        mock_order1.total_amount = Decimal('3000')

        mock_order2 = MagicMock()
        mock_order2.total_amount = Decimal('2000')

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_order1, mock_order2]
        self.mock_db.query.return_value = mock_query

        result = self.service._calculate_outsourcing_cost(1)

        self.assertEqual(result, Decimal('5000'))

    # ========== _calculate_actual_hours() 测试 ==========

    def test_calculate_actual_hours(self):
        """测试计算实际工时"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 150.5
        self.mock_db.query.return_value = mock_query

        result = self.service._calculate_actual_hours(1)

        self.assertEqual(result, 150.5)

    def test_calculate_actual_hours_none(self):
        """测试计算实际工时 - 返回None"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        self.mock_db.query.return_value = mock_query

        result = self.service._calculate_actual_hours(1)

        self.assertEqual(result, 0)

    # ========== 边界情况测试 ==========

    def test_zero_budget_project(self):
        """测试预算为0的项目"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = Decimal('0')
        mock_project.plan_manhours = 0
        mock_project.ecns = []

        with patch.object(self.service, '_calculate_actual_cost') as mock_cost, \
             patch.object(self.service, '_calculate_actual_hours') as mock_hours, \
             patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_cost.return_value = Decimal('5000')
            mock_hours.return_value = 0.0
            mock_material.return_value = Decimal('0')
            mock_outsourcing.return_value = Decimal('0')

            result = self.service._analyze_project_overrun(mock_project)

        # 预算为0时，超支率应该为0
        self.assertTrue(result['has_overrun'])
        self.assertEqual(result['overrun_ratio'], 0.0)

    def test_none_values_handling(self):
        """测试None值处理"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = 'PRJ001'
        mock_project.project_name = '测试项目'
        mock_project.budget = None  # None预算
        mock_project.plan_manhours = None
        mock_project.ecns = []

        with patch.object(self.service, '_calculate_actual_cost') as mock_cost, \
             patch.object(self.service, '_calculate_actual_hours') as mock_hours, \
             patch.object(self.service, '_calculate_material_cost') as mock_material, \
             patch.object(self.service, '_calculate_outsourcing_cost') as mock_outsourcing:
            
            mock_cost.return_value = Decimal('5000')
            mock_hours.return_value = 0.0
            mock_material.return_value = Decimal('0')
            mock_outsourcing.return_value = Decimal('0')

            result = self.service._analyze_project_overrun(mock_project)

        # 应该将None转换为0
        self.assertTrue(result['has_overrun'])
        self.assertEqual(result['budget'], 0.0)

    def test_user_without_real_name(self):
        """测试用户无真实姓名"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.opportunity_id = None
        mock_project.salesperson_id = 20
        mock_project.pm_id = None

        mock_user = MagicMock()
        mock_user.id = 20
        mock_user.real_name = None
        mock_user.username = 'testuser'
        mock_user.department = '销售部'

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Project':
                mock_q.first.return_value = mock_project
            elif model.__name__ == 'User':
                mock_q.first.return_value = mock_user
            elif model.__name__ == 'Timesheet':
                mock_q.all.return_value = []
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect

        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': [{
                    'project_id': 1,
                    'overrun_amount': 3000.0
                }]
            }

            result = self.service.analyze_accountability()

        person = result['by_person'][0]
        # 应该使用username
        self.assertEqual(person['person_name'], 'testuser')

    def test_user_not_found_fallback(self):
        """测试用户不存在时的降级处理"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.opportunity_id = None
        mock_project.salesperson_id = 999  # 不存在的用户
        mock_project.pm_id = None

        def mock_query_side_effect(model):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            if model.__name__ == 'Project':
                mock_q.first.return_value = mock_project
            elif model.__name__ == 'User':
                mock_q.first.return_value = None  # 用户不存在
            elif model.__name__ == 'Timesheet':
                mock_q.all.return_value = []
            return mock_q

        self.mock_db.query.side_effect = mock_query_side_effect

        with patch.object(self.service, 'analyze_reasons') as mock_reasons:
            mock_reasons.return_value = {
                'projects': [{
                    'project_id': 1,
                    'overrun_amount': 3000.0
                }]
            }

            result = self.service.analyze_accountability()

        person = result['by_person'][0]
        # 应该使用User_{id}格式
        self.assertEqual(person['person_name'], 'User_999')


if __name__ == "__main__":
    unittest.main()
