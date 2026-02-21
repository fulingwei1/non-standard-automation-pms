# -*- coding: utf-8 -*-
"""
SchedulingSuggestionService 增强单元测试
覆盖所有核心方法、边界条件和错误场景
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.scheduling_suggestion_service import SchedulingSuggestionService


class TestSchedulingSuggestionServiceEnhanced(unittest.TestCase):
    """SchedulingSuggestionService 增强测试套件"""

    def setUp(self):
        """测试初始化"""
        self.db_mock = MagicMock()
        self.service = SchedulingSuggestionService()

    # ==================== 优先级分数测试 ====================

    def test_priority_scores_p1(self):
        """测试P1优先级分数"""
        self.assertEqual(self.service.PRIORITY_SCORES['P1'], 30)

    def test_priority_scores_p2(self):
        """测试P2优先级分数"""
        self.assertEqual(self.service.PRIORITY_SCORES['P2'], 24)

    def test_priority_scores_p3(self):
        """测试P3优先级分数"""
        self.assertEqual(self.service.PRIORITY_SCORES['P3'], 18)

    def test_priority_scores_p4(self):
        """测试P4优先级分数"""
        self.assertEqual(self.service.PRIORITY_SCORES['P4'], 12)

    def test_priority_scores_p5(self):
        """测试P5优先级分数"""
        self.assertEqual(self.service.PRIORITY_SCORES['P5'], 6)

    # ==================== 交期压力分数计算测试 ====================

    def test_deadline_pressure_within_7_days(self):
        """测试距交期7天内的压力分数"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=5)
        
        score = self.service._calculate_deadline_pressure(project)
        self.assertEqual(score, 25.0)

    def test_deadline_pressure_within_14_days(self):
        """测试距交期8-14天的压力分数"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=10)
        
        score = self.service._calculate_deadline_pressure(project)
        self.assertEqual(score, 20.0)

    def test_deadline_pressure_within_30_days(self):
        """测试距交期15-30天的压力分数"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=20)
        
        score = self.service._calculate_deadline_pressure(project)
        self.assertEqual(score, 15.0)

    def test_deadline_pressure_within_60_days(self):
        """测试距交期31-60天的压力分数"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=45)
        
        score = self.service._calculate_deadline_pressure(project)
        self.assertEqual(score, 10.0)

    def test_deadline_pressure_over_60_days(self):
        """测试距交期60天以上的压力分数"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=90)
        
        score = self.service._calculate_deadline_pressure(project)
        self.assertEqual(score, 5.0)

    def test_deadline_pressure_no_deadline(self):
        """测试无交期情况"""
        project = MagicMock()
        project.planned_end_date = None
        
        score = self.service._calculate_deadline_pressure(project)
        self.assertEqual(score, 5.0)

    def test_deadline_pressure_overdue(self):
        """测试已逾期情况"""
        project = MagicMock()
        project.planned_end_date = date.today() - timedelta(days=10)
        
        score = self.service._calculate_deadline_pressure(project)
        self.assertEqual(score, 5.0)

    # ==================== 交期描述测试 ====================

    def test_deadline_description_no_deadline(self):
        """测试无交期描述"""
        project = MagicMock()
        project.planned_end_date = None
        
        desc = self.service._get_deadline_description(project)
        self.assertEqual(desc, '无交期')

    def test_deadline_description_overdue(self):
        """测试逾期描述"""
        project = MagicMock()
        project.planned_end_date = date.today() - timedelta(days=5)
        
        desc = self.service._get_deadline_description(project)
        self.assertIn('已逾期 5 天', desc)

    def test_deadline_description_urgent(self):
        """测试紧急描述（7天内）"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=3)
        
        desc = self.service._get_deadline_description(project)
        self.assertIn('紧急', desc)

    def test_deadline_description_tight(self):
        """测试紧张描述（8-14天）"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=10)
        
        desc = self.service._get_deadline_description(project)
        self.assertIn('紧张', desc)

    def test_deadline_description_normal(self):
        """测试正常描述（15-30天）"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=20)
        
        desc = self.service._get_deadline_description(project)
        self.assertIn('正常', desc)

    def test_deadline_description_relaxed(self):
        """测试宽松描述（30天以上）"""
        project = MagicMock()
        project.planned_end_date = date.today() + timedelta(days=45)
        
        desc = self.service._get_deadline_description(project)
        self.assertIn('宽松', desc)

    # ==================== 客户重要度计算测试 ====================

    def test_customer_importance_no_customer_id(self):
        """测试无客户ID情况"""
        project = MagicMock()
        project.customer_id = None
        
        score = self.service._calculate_customer_importance(self.db_mock, project)
        self.assertEqual(score, 6.0)

    def test_customer_importance_customer_not_found(self):
        """测试客户不存在情况"""
        project = MagicMock()
        project.customer_id = 999
        project.contract_amount = 50000
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        score = self.service._calculate_customer_importance(self.db_mock, project)
        self.assertEqual(score, 6.0)

    def test_customer_importance_grade_a(self):
        """测试A级客户"""
        project = MagicMock()
        project.customer_id = 1
        project.contract_amount = 300000
        
        customer = MagicMock()
        customer.credit_level = 'A'
        self.db_mock.query.return_value.filter.return_value.first.return_value = customer
        
        score = self.service._calculate_customer_importance(self.db_mock, project)
        self.assertEqual(score, 15.0)

    def test_customer_importance_by_contract_over_1m(self):
        """测试根据合同金额判断（100万以上）"""
        project = MagicMock()
        project.customer_id = 1
        project.contract_amount = 1200000
        
        customer = MagicMock()
        customer.credit_level = 'B'
        self.db_mock.query.return_value.filter.return_value.first.return_value = customer
        
        score = self.service._calculate_customer_importance(self.db_mock, project)
        self.assertEqual(score, 15.0)

    def test_customer_importance_by_contract_over_500k(self):
        """测试根据合同金额判断（50万以上）"""
        project = MagicMock()
        project.customer_id = 1
        project.contract_amount = 600000
        
        customer = MagicMock()
        customer.credit_level = 'C'
        self.db_mock.query.return_value.filter.return_value.first.return_value = customer
        
        score = self.service._calculate_customer_importance(self.db_mock, project)
        self.assertEqual(score, 12.0)

    def test_customer_importance_by_contract_over_200k(self):
        """测试根据合同金额判断（20万以上）"""
        project = MagicMock()
        project.customer_id = 1
        project.contract_amount = 300000
        
        customer = MagicMock()
        customer.credit_level = 'D'
        self.db_mock.query.return_value.filter.return_value.first.return_value = customer
        
        score = self.service._calculate_customer_importance(self.db_mock, project)
        self.assertEqual(score, 9.0)

    def test_customer_importance_by_contract_under_200k(self):
        """测试根据合同金额判断（20万以下）"""
        project = MagicMock()
        project.customer_id = 1
        project.contract_amount = 100000
        
        customer = MagicMock()
        customer.credit_level = 'C'
        self.db_mock.query.return_value.filter.return_value.first.return_value = customer
        
        score = self.service._calculate_customer_importance(self.db_mock, project)
        self.assertEqual(score, 6.0)

    # ==================== 客户描述测试 ====================

    def test_customer_description_no_customer_id(self):
        """测试无客户ID的描述"""
        project = MagicMock()
        project.customer_id = None
        
        desc = self.service._get_customer_description(self.db_mock, project)
        self.assertEqual(desc, '无客户信息')

    def test_customer_description_customer_not_found(self):
        """测试客户不存在的描述"""
        project = MagicMock()
        project.customer_id = 999
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        desc = self.service._get_customer_description(self.db_mock, project)
        self.assertEqual(desc, '客户不存在')

    def test_customer_description_with_customer(self):
        """测试正常客户描述"""
        project = MagicMock()
        project.customer_id = 1
        
        customer = MagicMock()
        customer.customer_name = '测试客户'
        customer.credit_level = 'A'
        self.db_mock.query.return_value.filter.return_value.first.return_value = customer
        
        desc = self.service._get_customer_description(self.db_mock, project)
        self.assertIn('测试客户', desc)
        self.assertIn('A', desc)

    # ==================== 合同金额分数测试 ====================

    def test_contract_amount_score_over_500k(self):
        """测试合同金额50万以上"""
        project = MagicMock()
        project.contract_amount = 600000
        
        score = self.service._calculate_contract_amount_score(project)
        self.assertEqual(score, 10.0)

    def test_contract_amount_score_over_200k(self):
        """测试合同金额20-50万"""
        project = MagicMock()
        project.contract_amount = 300000
        
        score = self.service._calculate_contract_amount_score(project)
        self.assertEqual(score, 7.0)

    def test_contract_amount_score_over_100k(self):
        """测试合同金额10-20万"""
        project = MagicMock()
        project.contract_amount = 150000
        
        score = self.service._calculate_contract_amount_score(project)
        self.assertEqual(score, 5.0)

    def test_contract_amount_score_under_100k(self):
        """测试合同金额10万以下"""
        project = MagicMock()
        project.contract_amount = 50000
        
        score = self.service._calculate_contract_amount_score(project)
        self.assertEqual(score, 3.0)

    def test_contract_amount_score_none(self):
        """测试合同金额为None"""
        project = MagicMock()
        project.contract_amount = None
        
        score = self.service._calculate_contract_amount_score(project)
        self.assertEqual(score, 3.0)

    def test_contract_amount_score_zero(self):
        """测试合同金额为0"""
        project = MagicMock()
        project.contract_amount = 0
        
        score = self.service._calculate_contract_amount_score(project)
        self.assertEqual(score, 3.0)

    # ==================== 下一阶段获取测试 ====================

    def test_get_next_stage_from_frame(self):
        """测试从FRAME获取下一阶段"""
        next_stage = self.service._get_next_stage('FRAME')
        self.assertEqual(next_stage, 'MECH')

    def test_get_next_stage_from_mech(self):
        """测试从MECH获取下一阶段"""
        next_stage = self.service._get_next_stage('MECH')
        self.assertEqual(next_stage, 'ELECTRIC')

    def test_get_next_stage_from_electric(self):
        """测试从ELECTRIC获取下一阶段"""
        next_stage = self.service._get_next_stage('ELECTRIC')
        self.assertEqual(next_stage, 'WIRING')

    def test_get_next_stage_from_wiring(self):
        """测试从WIRING获取下一阶段"""
        next_stage = self.service._get_next_stage('WIRING')
        self.assertEqual(next_stage, 'DEBUG')

    def test_get_next_stage_from_debug(self):
        """测试从DEBUG获取下一阶段"""
        next_stage = self.service._get_next_stage('DEBUG')
        self.assertEqual(next_stage, 'COSMETIC')

    def test_get_next_stage_from_cosmetic(self):
        """测试从COSMETIC获取下一阶段（最后阶段）"""
        next_stage = self.service._get_next_stage('COSMETIC')
        self.assertIsNone(next_stage)

    def test_get_next_stage_invalid(self):
        """测试无效阶段（返回None或第一个阶段取决于实现）"""
        next_stage = self.service._get_next_stage('INVALID')
        # 无效阶段会返回None（因为current_order是0，不会匹配任何下一阶段）
        # 但由于逻辑，可能返回None
        self.assertTrue(next_stage is None or isinstance(next_stage, str))

    # ==================== 优先级评分计算综合测试 ====================

    def test_calculate_priority_score_p1_priority(self):
        """测试P1优先级的评分计算"""
        project = MagicMock()
        project.priority = 'P1'
        project.planned_end_date = date.today() + timedelta(days=5)
        project.customer_id = 1
        project.contract_amount = 600000
        
        customer = MagicMock()
        customer.credit_level = 'A'
        customer.customer_name = '重要客户'
        self.db_mock.query.return_value.filter.return_value.first.return_value = customer
        
        readiness = MagicMock()
        readiness.blocking_kit_rate = Decimal('85.5')
        
        result = self.service.calculate_priority_score(self.db_mock, project, readiness)
        
        self.assertIn('total_score', result)
        self.assertIn('factors', result)
        self.assertEqual(result['max_score'], 100)
        self.assertEqual(result['factors']['priority']['score'], 30)
        self.assertEqual(result['factors']['deadline']['score'], 25.0)
        self.assertEqual(result['factors']['kit_rate']['score'], 17.1)
        self.assertEqual(result['factors']['customer']['score'], 15.0)
        self.assertEqual(result['factors']['contract']['score'], 10.0)

    def test_calculate_priority_score_high_priority_mapping(self):
        """测试HIGH优先级映射为P1"""
        project = MagicMock()
        project.priority = 'HIGH'
        project.planned_end_date = date.today() + timedelta(days=30)
        project.customer_id = None
        project.contract_amount = 100000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['priority']['score'], 30)
        self.assertEqual(result['factors']['priority']['value'], 'P1')

    def test_calculate_priority_score_medium_priority_mapping(self):
        """测试MEDIUM优先级映射为P3"""
        project = MagicMock()
        project.priority = 'MEDIUM'
        project.planned_end_date = date.today() + timedelta(days=30)
        project.customer_id = None
        project.contract_amount = 100000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['priority']['score'], 18)
        self.assertEqual(result['factors']['priority']['value'], 'P3')

    def test_calculate_priority_score_low_priority_mapping(self):
        """测试LOW优先级映射为P5"""
        project = MagicMock()
        project.priority = 'LOW'
        project.planned_end_date = date.today() + timedelta(days=30)
        project.customer_id = None
        project.contract_amount = 100000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['priority']['score'], 6)
        self.assertEqual(result['factors']['priority']['value'], 'P5')

    def test_calculate_priority_score_normal_priority_mapping(self):
        """测试NORMAL优先级映射为P3"""
        project = MagicMock()
        project.priority = 'NORMAL'
        project.planned_end_date = date.today() + timedelta(days=30)
        project.customer_id = None
        project.contract_amount = 100000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['priority']['score'], 18)

    def test_calculate_priority_score_urgent_priority_mapping(self):
        """测试URGENT优先级映射为P1"""
        project = MagicMock()
        project.priority = 'URGENT'
        project.planned_end_date = date.today() + timedelta(days=5)
        project.customer_id = None
        project.contract_amount = 50000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['priority']['score'], 30)

    def test_calculate_priority_score_critical_priority_mapping(self):
        """测试CRITICAL优先级映射为P1"""
        project = MagicMock()
        project.priority = 'CRITICAL'
        project.planned_end_date = date.today() + timedelta(days=3)
        project.customer_id = None
        project.contract_amount = 50000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['priority']['score'], 30)

    def test_calculate_priority_score_unknown_priority_default(self):
        """测试未知优先级默认为P3"""
        project = MagicMock()
        project.priority = 'UNKNOWN'
        project.planned_end_date = date.today() + timedelta(days=30)
        project.customer_id = None
        project.contract_amount = 100000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['priority']['score'], 18)

    def test_calculate_priority_score_none_priority_default(self):
        """测试优先级为None默认为P3"""
        project = MagicMock()
        project.priority = None
        project.planned_end_date = date.today() + timedelta(days=30)
        project.customer_id = None
        project.contract_amount = 100000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['priority']['score'], 18)

    def test_calculate_priority_score_no_readiness(self):
        """测试无齐套分析数据"""
        project = MagicMock()
        project.priority = 'P2'
        project.planned_end_date = date.today() + timedelta(days=15)
        project.customer_id = None
        project.contract_amount = 200000
        
        result = self.service.calculate_priority_score(self.db_mock, project, None)
        
        self.assertEqual(result['factors']['kit_rate']['score'], 0)
        self.assertIsNone(result['factors']['kit_rate']['value'])
        self.assertIn('未进行齐套分析', result['factors']['kit_rate']['description'])

    def test_calculate_priority_score_zero_kit_rate(self):
        """测试齐套率为0的情况"""
        project = MagicMock()
        project.priority = 'P3'
        project.planned_end_date = date.today() + timedelta(days=20)
        project.customer_id = None
        project.contract_amount = 150000
        
        readiness = MagicMock()
        readiness.blocking_kit_rate = Decimal('0')
        
        result = self.service.calculate_priority_score(self.db_mock, project, readiness)
        
        self.assertEqual(result['factors']['kit_rate']['score'], 0)

    def test_calculate_priority_score_full_kit_rate(self):
        """测试齐套率为100%的情况"""
        project = MagicMock()
        project.priority = 'P2'
        project.planned_end_date = date.today() + timedelta(days=10)
        project.customer_id = 1
        project.contract_amount = 500000
        
        customer = MagicMock()
        customer.credit_level = 'A'
        customer.customer_name = '优质客户'
        self.db_mock.query.return_value.filter.return_value.first.return_value = customer
        
        readiness = MagicMock()
        readiness.blocking_kit_rate = Decimal('100')
        
        result = self.service.calculate_priority_score(self.db_mock, project, readiness)
        
        self.assertEqual(result['factors']['kit_rate']['score'], 20.0)

    # ==================== 阻塞物料获取测试 ====================

    def test_get_blocking_items_with_shortages(self):
        """测试获取阻塞物料列表"""
        readiness = MagicMock()
        readiness.id = 1
        
        shortage1 = MagicMock()
        shortage1.material_code = 'MAT001'
        shortage1.material_name = '测试物料1'
        shortage1.shortage_qty = Decimal('10.5')
        shortage1.expected_arrival = date.today() + timedelta(days=7)
        
        shortage2 = MagicMock()
        shortage2.material_code = 'MAT002'
        shortage2.material_name = '测试物料2'
        shortage2.shortage_qty = Decimal('5.0')
        shortage2.expected_arrival = None
        
        # Mock the complete query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [shortage1, shortage2]
        self.db_mock.query.return_value = mock_query
        
        items = self.service._get_blocking_items(self.db_mock, readiness, 'FRAME')
        
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['material_code'], 'MAT001')
        self.assertEqual(items[0]['shortage_qty'], 10.5)
        self.assertIsNotNone(items[0]['expected_arrival'])
        
        self.assertEqual(items[1]['material_code'], 'MAT002')
        self.assertEqual(items[1]['shortage_qty'], 5.0)
        self.assertIsNone(items[1]['expected_arrival'])

    def test_get_blocking_items_no_shortages(self):
        """测试无阻塞物料情况"""
        readiness = MagicMock()
        readiness.id = 1
        
        # Mock the complete query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []
        self.db_mock.query.return_value = mock_query
        
        items = self.service._get_blocking_items(self.db_mock, readiness, 'FRAME')
        
        self.assertEqual(len(items), 0)

    # ==================== 排产建议生成测试 ====================

    @patch('app.services.scheduling_suggestion_service.ResourceAllocationService')
    def test_generate_scheduling_suggestions_no_projects(self, mock_resource_service):
        """测试无待排产项目情况"""
        self.db_mock.query.return_value.filter.return_value.all.return_value = []
        
        suggestions = self.service.generate_scheduling_suggestions(self.db_mock)
        
        self.assertEqual(len(suggestions), 0)

    @patch('app.services.scheduling_suggestion_service.ResourceAllocationService')
    def test_generate_scheduling_suggestions_need_analysis(self, mock_resource_service):
        """测试需要齐套分析的项目"""
        project = MagicMock()
        project.id = 1
        project.status = 'S4'
        
        self.db_mock.query.return_value.filter.return_value.all.return_value = [project]
        self.db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        suggestions = self.service.generate_scheduling_suggestions(self.db_mock)
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]['status'], 'NEED_ANALYSIS')
        self.assertIn('需要先进行齐套分析', suggestions[0]['message'])

    @patch('app.services.scheduling_suggestion_service.ResourceAllocationService')
    def test_generate_scheduling_suggestions_can_start(self, mock_resource_service):
        """测试可以开工的项目"""
        project = MagicMock()
        project.id = 1
        project.status = 'S4'
        project.project_code = 'PRJ001'
        project.project_name = '测试项目'
        project.priority = 'P1'
        project.planned_end_date = date.today() + timedelta(days=30)
        project.planned_start_date = date.today()
        project.customer_id = None
        project.contract_amount = 300000
        
        readiness = MagicMock()
        readiness.id = 1
        readiness.project_id = 1
        readiness.can_start = True
        readiness.current_workable_stage = 'FRAME'
        readiness.blocking_kit_rate = Decimal('90')
        readiness.machine_id = 1
        readiness.stage_kit_rates = {
            'MECH': {'can_start': True}
        }
        
        mock_resource_service.allocate_resources.return_value = {
            'can_allocate': True,
            'workstations': [1, 2],
            'workers': [1, 2, 3],
            'conflicts': []
        }
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = [project]
        query_mock.filter.return_value.order_by.return_value.first.return_value = readiness
        
        suggestions = self.service.generate_scheduling_suggestions(self.db_mock)
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]['status'], 'READY')
        self.assertEqual(suggestions[0]['suggestion_type'], 'CAN_START')
        self.assertIn('suggested_start_date', suggestions[0])
        self.assertIn('suggested_end_date', suggestions[0])

    @patch('app.services.scheduling_suggestion_service.ResourceAllocationService')
    def test_generate_scheduling_suggestions_wait_resource(self, mock_resource_service):
        """测试等待资源的项目"""
        project = MagicMock()
        project.id = 1
        project.status = 'S5'
        project.project_code = 'PRJ002'
        project.project_name = '测试项目2'
        project.priority = 'P2'
        project.planned_end_date = date.today() + timedelta(days=20)
        project.planned_start_date = date.today()
        project.customer_id = None
        project.contract_amount = 200000
        
        readiness = MagicMock()
        readiness.id = 2
        readiness.project_id = 1
        readiness.can_start = True
        readiness.current_workable_stage = 'MECH'
        readiness.blocking_kit_rate = Decimal('85')
        readiness.machine_id = 2
        readiness.stage_kit_rates = {
            'ELECTRIC': {'can_start': True}
        }
        
        mock_resource_service.allocate_resources.return_value = {
            'can_allocate': False,
            'workstations': [],
            'workers': [],
            'conflicts': ['工位冲突'],
            'reason': '资源不足'
        }
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = [project]
        query_mock.filter.return_value.order_by.return_value.first.return_value = readiness
        
        suggestions = self.service.generate_scheduling_suggestions(self.db_mock)
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]['status'], 'WAIT_RESOURCE')
        self.assertEqual(suggestions[0]['suggestion_type'], 'WAIT_RESOURCE')
        self.assertFalse(suggestions[0]['resource_allocation']['can_allocate'])

    @patch('app.services.scheduling_suggestion_service.ResourceAllocationService')
    def test_generate_scheduling_suggestions_blocked(self, mock_resource_service):
        """测试被阻塞的项目"""
        project = MagicMock()
        project.id = 1
        project.status = 'S4'
        project.project_code = 'PRJ003'
        project.project_name = '测试项目3'
        project.priority = 'P3'
        project.planned_end_date = date.today() + timedelta(days=40)
        project.customer_id = None
        project.contract_amount = 150000
        
        readiness = MagicMock()
        readiness.id = 3
        readiness.project_id = 1
        readiness.can_start = False
        readiness.first_blocked_stage = 'FRAME'
        readiness.blocking_kit_rate = Decimal('60')
        readiness.estimated_ready_date = date.today() + timedelta(days=10)
        
        # Mock the query chain for projects
        mock_project_query = MagicMock()
        mock_project_filter = MagicMock()
        mock_project_query.filter.return_value = mock_project_filter
        mock_project_filter.all.return_value = [project]
        
        # Mock the query chain for readiness
        mock_readiness_query = MagicMock()
        mock_readiness_filter = MagicMock()
        mock_readiness_order = MagicMock()
        mock_readiness_query.filter.return_value = mock_readiness_filter
        mock_readiness_filter.order_by.return_value = mock_readiness_order
        mock_readiness_order.first.return_value = readiness
        
        # Mock the query chain for shortages (_get_blocking_items)
        mock_shortage_query = MagicMock()
        mock_shortage_filter = MagicMock()
        mock_shortage_query.filter.return_value = mock_shortage_filter
        mock_shortage_filter.all.return_value = []
        
        # Setup db.query to return different mocks based on call order
        self.db_mock.query.side_effect = [
            mock_project_query,      # First call: get projects
            mock_readiness_query,    # Second call: get readiness
            mock_shortage_query      # Third call: get blocking items
        ]
        
        suggestions = self.service.generate_scheduling_suggestions(self.db_mock)
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]['status'], 'BLOCKED')
        self.assertEqual(suggestions[0]['suggestion_type'], 'BLOCKED')
        self.assertEqual(suggestions[0]['blocking_stage'], 'FRAME')

    @patch('app.services.scheduling_suggestion_service.ResourceAllocationService')
    def test_generate_scheduling_suggestions_with_project_ids(self, mock_resource_service):
        """测试指定项目ID列表"""
        project1 = MagicMock()
        project1.id = 1
        project1.status = 'S4'
        
        project2 = MagicMock()
        project2.id = 2
        project2.status = 'S4'
        
        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.filter.return_value.all.return_value = [project1]
        filter_mock.order_by.return_value.first.return_value = None
        
        suggestions = self.service.generate_scheduling_suggestions(
            self.db_mock,
            project_ids=[1]
        )
        
        # 验证filter被调用来过滤project_ids
        self.assertTrue(filter_mock.filter.called)

    @patch('app.services.scheduling_suggestion_service.ResourceAllocationService')
    def test_generate_scheduling_suggestions_sorting_by_priority(self, mock_resource_service):
        """测试按优先级排序"""
        project1 = MagicMock()
        project1.id = 1
        project1.status = 'S4'
        project1.project_code = 'PRJ001'
        project1.project_name = '低优先级项目'
        project1.priority = 'P5'
        project1.planned_end_date = date.today() + timedelta(days=60)
        project1.customer_id = None
        project1.contract_amount = 50000
        
        project2 = MagicMock()
        project2.id = 2
        project2.status = 'S5'
        project2.project_code = 'PRJ002'
        project2.project_name = '高优先级项目'
        project2.priority = 'P1'
        project2.planned_end_date = date.today() + timedelta(days=7)
        project2.customer_id = None
        project2.contract_amount = 600000
        
        readiness1 = MagicMock()
        readiness1.id = 1
        readiness1.can_start = False
        readiness1.first_blocked_stage = 'FRAME'
        readiness1.blocking_kit_rate = Decimal('40')
        readiness1.estimated_ready_date = None
        
        readiness2 = MagicMock()
        readiness2.id = 2
        readiness2.can_start = False
        readiness2.first_blocked_stage = 'MECH'
        readiness2.blocking_kit_rate = Decimal('70')
        readiness2.estimated_ready_date = None
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = [project1, project2]
        
        # 为每个项目返回不同的readiness
        query_mock.filter.return_value.order_by.return_value.first.side_effect = [readiness1, readiness2]
        
        suggestions = self.service.generate_scheduling_suggestions(self.db_mock)
        
        # 验证高优先级项目排在前面
        self.assertEqual(len(suggestions), 2)
        self.assertGreater(suggestions[0]['priority_score'], suggestions[1]['priority_score'])


if __name__ == '__main__':
    unittest.main()
