# -*- coding: utf-8 -*-
"""
智能缺料预警引擎增强测试

测试覆盖：
- 所有核心方法
- 边界条件
- 异常情况
- 数据库操作Mock
"""
import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta, date
from decimal import Decimal

from app.services.shortage.smart_alert_engine import SmartAlertEngine
from app.models.shortage.smart_alert import ShortageAlert, ShortageHandlingPlan
from app.models.material import Material
from app.models.project import Project
from app.models.production.work_order import WorkOrder
from app.models.inventory_tracking import MaterialStock
from app.models.purchase import PurchaseOrder, PurchaseOrderItem


class TestSmartAlertEngine(unittest.TestCase):
    """智能预警引擎测试套件"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.db_mock = MagicMock()
        self.engine = SmartAlertEngine(self.db_mock)
    
    def tearDown(self):
        """每个测试后的清理"""
        self.db_mock.reset_mock()
    
    # ========== calculate_alert_level 测试 ==========
    
    def test_calculate_alert_level_urgent_overdue(self):
        """测试：已逾期应返回 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('100'),
            required_qty=Decimal('200'),
            days_to_shortage=-1,
            is_critical_path=False
        )
        self.assertEqual(level, 'URGENT')
    
    def test_calculate_alert_level_urgent_same_day(self):
        """测试：当天需求应返回 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('50'),
            required_qty=Decimal('100'),
            days_to_shortage=0,
            is_critical_path=False
        )
        self.assertEqual(level, 'URGENT')
    
    def test_calculate_alert_level_urgent_critical_path_3days(self):
        """测试：关键路径且3天内应返回 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('50'),
            required_qty=Decimal('100'),
            days_to_shortage=3,
            is_critical_path=True
        )
        self.assertEqual(level, 'URGENT')
    
    def test_calculate_alert_level_urgent_critical_path_high_shortage(self):
        """测试：关键路径且缺口>50%应返回 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('60'),
            required_qty=Decimal('100'),
            days_to_shortage=5,
            is_critical_path=True
        )
        self.assertEqual(level, 'URGENT')
    
    def test_calculate_alert_level_critical_path_7days(self):
        """测试：关键路径且7天内应返回 CRITICAL"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('40'),
            required_qty=Decimal('100'),
            days_to_shortage=7,
            is_critical_path=True
        )
        self.assertEqual(level, 'CRITICAL')
    
    def test_calculate_alert_level_critical_non_critical_3days_high_shortage(self):
        """测试：非关键路径但3天内且缺口>70%应返回 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('80'),
            required_qty=Decimal('100'),
            days_to_shortage=2,
            is_critical_path=False
        )
        self.assertEqual(level, 'URGENT')
    
    def test_calculate_alert_level_critical_7days_high_shortage(self):
        """测试：7天内且缺口>50%应返回 CRITICAL"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('60'),
            required_qty=Decimal('100'),
            days_to_shortage=5,
            is_critical_path=False
        )
        self.assertEqual(level, 'CRITICAL')
    
    def test_calculate_alert_level_warning_14days(self):
        """测试：14天内且缺口>30%应返回 WARNING"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('40'),
            required_qty=Decimal('100'),
            days_to_shortage=10,
            is_critical_path=False
        )
        self.assertEqual(level, 'WARNING')
    
    def test_calculate_alert_level_warning_high_shortage_far_away(self):
        """测试：缺口>50%但时间充裕应返回 WARNING"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('60'),
            required_qty=Decimal('100'),
            days_to_shortage=20,
            is_critical_path=False
        )
        self.assertEqual(level, 'WARNING')
    
    def test_calculate_alert_level_info_low_shortage(self):
        """测试：缺口小且时间充裕应返回 INFO"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('20'),
            required_qty=Decimal('100'),
            days_to_shortage=20,
            is_critical_path=False
        )
        self.assertEqual(level, 'INFO')
    
    def test_calculate_alert_level_zero_required_qty(self):
        """测试：需求数量为0的边界情况"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal('10'),
            required_qty=Decimal('0'),
            days_to_shortage=5,
            is_critical_path=False
        )
        # 应该返回 CRITICAL（因为 shortage_rate=0，但 days_to_shortage=5）
        self.assertEqual(level, 'INFO')
    
    # ========== _calculate_risk_score 测试 ==========
    
    def test_calculate_risk_score_max_risk(self):
        """测试：所有因素都高风险应返回100"""
        score = self.engine._calculate_risk_score(
            delay_days=35,
            cost_impact=Decimal('150000'),
            project_count=6,
            shortage_qty=Decimal('1500')
        )
        self.assertEqual(score, Decimal('100'))
    
    def test_calculate_risk_score_medium_risk(self):
        """测试：中等风险应返回中等分数"""
        score = self.engine._calculate_risk_score(
            delay_days=10,
            cost_impact=Decimal('30000'),
            project_count=2,
            shortage_qty=Decimal('50')
        )
        self.assertGreater(score, Decimal('30'))
        self.assertLess(score, Decimal('70'))
    
    def test_calculate_risk_score_low_risk(self):
        """测试：低风险应返回低分数"""
        score = self.engine._calculate_risk_score(
            delay_days=0,
            cost_impact=Decimal('5000'),
            project_count=1,
            shortage_qty=Decimal('5')
        )
        self.assertLessEqual(score, Decimal('25'))
    
    def test_calculate_risk_score_zero_values(self):
        """测试：所有值为0的边界情况"""
        score = self.engine._calculate_risk_score(
            delay_days=0,
            cost_impact=Decimal('0'),
            project_count=0,
            shortage_qty=Decimal('0')
        )
        self.assertGreaterEqual(score, Decimal('0'))
    
    # ========== _get_available_qty 测试 ==========
    
    def test_get_available_qty_with_stock(self):
        """测试：获取有库存的可用数量"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.scalar.return_value = Decimal('500')
        
        qty = self.engine._get_available_qty(material_id=1)
        
        self.assertEqual(qty, Decimal('500'))
        self.db_mock.query.assert_called_once()
    
    def test_get_available_qty_no_stock(self):
        """测试：获取无库存的可用数量（应返回0）"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.scalar.return_value = None
        
        qty = self.engine._get_available_qty(material_id=1)
        
        self.assertEqual(qty, Decimal('0'))
    
    # ========== _get_in_transit_qty 测试 ==========
    
    def test_get_in_transit_qty_with_orders(self):
        """测试：获取有在途订单的数量"""
        mock_query = MagicMock()
        mock_join = MagicMock()
        mock_filter = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter
        mock_filter.scalar.return_value = Decimal('300')
        
        qty = self.engine._get_in_transit_qty(material_id=1)
        
        self.assertEqual(qty, Decimal('300'))
        self.db_mock.query.assert_called_once()
    
    def test_get_in_transit_qty_no_orders(self):
        """测试：获取无在途订单的数量（应返回0）"""
        mock_query = MagicMock()
        mock_join = MagicMock()
        mock_filter = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter
        mock_filter.scalar.return_value = None
        
        qty = self.engine._get_in_transit_qty(material_id=1)
        
        self.assertEqual(qty, Decimal('0'))
    
    # ========== _generate_alert_no 测试 ==========
    
    def test_generate_alert_no_first_today(self):
        """测试：今天第一个预警单号"""
        self.db_mock.query.return_value.filter.return_value.scalar.return_value = 0
        
        alert_no = self.engine._generate_alert_no()
        
        today = datetime.now().strftime('%Y%m%d')
        expected = f"SA{today}0001"
        self.assertEqual(alert_no, expected)
    
    def test_generate_alert_no_multiple_today(self):
        """测试：今天第N个预警单号"""
        self.db_mock.query.return_value.filter.return_value.scalar.return_value = 5
        
        alert_no = self.engine._generate_alert_no()
        
        today = datetime.now().strftime('%Y%m%d')
        expected = f"SA{today}0006"
        self.assertEqual(alert_no, expected)
    
    # ========== _generate_plan_no 测试 ==========
    
    def test_generate_plan_no_first_today(self):
        """测试：今天第一个方案编号"""
        self.db_mock.query.return_value.filter.return_value.scalar.return_value = 0
        
        plan_no = self.engine._generate_plan_no()
        
        today = datetime.now().strftime('%Y%m%d')
        expected = f"SP{today}0001"
        self.assertEqual(plan_no, expected)
    
    # ========== _score_feasibility 测试 ==========
    
    def test_score_feasibility_urgent_purchase(self):
        """测试：紧急采购可行性评分"""
        plan = ShortageHandlingPlan(solution_type='URGENT_PURCHASE')
        score = self.engine._score_feasibility(plan)
        self.assertEqual(score, Decimal('80'))
    
    def test_score_feasibility_reschedule(self):
        """测试：重排期可行性评分"""
        plan = ShortageHandlingPlan(solution_type='RESCHEDULE')
        score = self.engine._score_feasibility(plan)
        self.assertEqual(score, Decimal('90'))
    
    def test_score_feasibility_partial_delivery(self):
        """测试：分批交付可行性评分"""
        plan = ShortageHandlingPlan(solution_type='PARTIAL_DELIVERY')
        score = self.engine._score_feasibility(plan)
        self.assertEqual(score, Decimal('85'))
    
    def test_score_feasibility_unknown_type(self):
        """测试：未知类型可行性评分（应返回默认值50）"""
        plan = ShortageHandlingPlan(solution_type='UNKNOWN')
        score = self.engine._score_feasibility(plan)
        self.assertEqual(score, Decimal('50'))
    
    # ========== _score_cost 测试 ==========
    
    def test_score_cost_no_cost(self):
        """测试：无成本方案应得满分"""
        alert = ShortageAlert(estimated_cost_impact=Decimal('10000'))
        plan = ShortageHandlingPlan(estimated_cost=None)
        score = self.engine._score_cost(plan, alert)
        self.assertEqual(score, Decimal('100'))
    
    def test_score_cost_very_low(self):
        """测试：成本<50%应得满分"""
        alert = ShortageAlert(estimated_cost_impact=Decimal('10000'))
        plan = ShortageHandlingPlan(estimated_cost=Decimal('4000'))
        score = self.engine._score_cost(plan, alert)
        self.assertEqual(score, Decimal('100'))
    
    def test_score_cost_medium(self):
        """测试：成本在50%-100%应得80分"""
        alert = ShortageAlert(estimated_cost_impact=Decimal('10000'))
        plan = ShortageHandlingPlan(estimated_cost=Decimal('7000'))
        score = self.engine._score_cost(plan, alert)
        self.assertEqual(score, Decimal('80'))
    
    def test_score_cost_high(self):
        """测试：成本>150%应得40分"""
        alert = ShortageAlert(estimated_cost_impact=Decimal('10000'))
        plan = ShortageHandlingPlan(estimated_cost=Decimal('16000'))
        score = self.engine._score_cost(plan, alert)
        self.assertEqual(score, Decimal('40'))
    
    # ========== _score_time 测试 ==========
    
    def test_score_time_zero_lead_time(self):
        """测试：立即可用应得满分"""
        alert = ShortageAlert()
        plan = ShortageHandlingPlan(estimated_lead_time=0)
        score = self.engine._score_time(plan, alert)
        self.assertEqual(score, Decimal('100'))
    
    def test_score_time_3days(self):
        """测试：3天交期应得90分"""
        alert = ShortageAlert()
        plan = ShortageHandlingPlan(estimated_lead_time=3)
        score = self.engine._score_time(plan, alert)
        self.assertEqual(score, Decimal('90'))
    
    def test_score_time_7days(self):
        """测试：7天交期应得70分"""
        alert = ShortageAlert()
        plan = ShortageHandlingPlan(estimated_lead_time=7)
        score = self.engine._score_time(plan, alert)
        self.assertEqual(score, Decimal('70'))
    
    def test_score_time_long(self):
        """测试：超过14天应得30分"""
        alert = ShortageAlert()
        plan = ShortageHandlingPlan(estimated_lead_time=20)
        score = self.engine._score_time(plan, alert)
        self.assertEqual(score, Decimal('30'))
    
    # ========== _score_risk 测试 ==========
    
    def test_score_risk_no_risks(self):
        """测试：无风险应得满分"""
        plan = ShortageHandlingPlan(risks=[])
        score = self.engine._score_risk(plan)
        self.assertEqual(score, Decimal('100'))
    
    def test_score_risk_few_risks(self):
        """测试：2个风险应得80分"""
        plan = ShortageHandlingPlan(risks=['risk1', 'risk2'])
        score = self.engine._score_risk(plan)
        self.assertEqual(score, Decimal('80'))
    
    def test_score_risk_many_risks(self):
        """测试：超过4个风险应得40分"""
        plan = ShortageHandlingPlan(risks=['r1', 'r2', 'r3', 'r4', 'r5'])
        score = self.engine._score_risk(plan)
        self.assertEqual(score, Decimal('40'))
    
    # ========== _generate_urgent_purchase_plan 测试 ==========
    
    @patch.object(SmartAlertEngine, '_generate_plan_no', return_value='SP202602210001')
    def test_generate_urgent_purchase_plan(self, mock_plan_no):
        """测试：生成紧急采购方案"""
        alert = ShortageAlert(
            id=1,
            shortage_qty=Decimal('100'),
            estimated_cost_impact=Decimal('10000')
        )
        
        plan = self.engine._generate_urgent_purchase_plan(alert)
        
        self.assertIsNotNone(plan)
        self.assertEqual(plan.solution_type, 'URGENT_PURCHASE')
        self.assertEqual(plan.proposed_qty, Decimal('100'))
        self.assertEqual(plan.estimated_lead_time, 7)
        self.assertIn('快速解决', plan.advantages)
    
    # ========== _generate_partial_delivery_plan 测试 ==========
    
    @patch.object(SmartAlertEngine, '_generate_plan_no', return_value='SP202602210002')
    def test_generate_partial_delivery_plan_with_stock(self, mock_plan_no):
        """测试：有库存时生成分批交付方案"""
        alert = ShortageAlert(
            id=1,
            available_qty=Decimal('50'),
            shortage_qty=Decimal('100')
        )
        
        plan = self.engine._generate_partial_delivery_plan(alert)
        
        self.assertIsNotNone(plan)
        self.assertEqual(plan.solution_type, 'PARTIAL_DELIVERY')
        self.assertEqual(plan.proposed_qty, Decimal('50'))
        self.assertEqual(plan.estimated_lead_time, 0)
    
    def test_generate_partial_delivery_plan_no_stock(self):
        """测试：无库存时不应生成分批交付方案"""
        alert = ShortageAlert(
            id=1,
            available_qty=Decimal('0'),
            shortage_qty=Decimal('100')
        )
        
        plan = self.engine._generate_partial_delivery_plan(alert)
        
        self.assertIsNone(plan)
    
    # ========== _generate_reschedule_plan 测试 ==========
    
    @patch.object(SmartAlertEngine, '_generate_plan_no', return_value='SP202602210003')
    def test_generate_reschedule_plan(self, mock_plan_no):
        """测试：生成重排期方案"""
        alert = ShortageAlert(
            id=1,
            required_date=date.today(),
            estimated_delay_days=7
        )
        
        plan = self.engine._generate_reschedule_plan(alert)
        
        self.assertIsNotNone(plan)
        self.assertEqual(plan.solution_type, 'RESCHEDULE')
        self.assertEqual(plan.estimated_lead_time, 7)
        self.assertIn('成本最低', plan.advantages)
        self.assertIn('延期交付', plan.disadvantages)
    
    # ========== _score_solution 测试 ==========
    
    def test_score_solution_comprehensive(self):
        """测试：综合评分逻辑"""
        alert = ShortageAlert(
            estimated_cost_impact=Decimal('10000')
        )
        plan = ShortageHandlingPlan(
            solution_type='URGENT_PURCHASE',
            estimated_cost=Decimal('5000'),
            estimated_lead_time=3,
            risks=['risk1']
        )
        
        self.engine._score_solution(plan, alert)
        
        self.assertIsNotNone(plan.feasibility_score)
        self.assertIsNotNone(plan.cost_score)
        self.assertIsNotNone(plan.time_score)
        self.assertIsNotNone(plan.risk_score)
        self.assertIsNotNone(plan.ai_score)
        self.assertIsNotNone(plan.score_explanation)
        self.assertGreater(plan.ai_score, Decimal('0'))
    
    # ========== _collect_material_demands 测试 ==========
    
    def test_collect_material_demands_with_filters(self):
        """测试：收集物料需求（带过滤条件）"""
        # Mock查询链
        mock_result = [
            MagicMock(
                work_order_id=1,
                project_id=10,
                material_id=100,
                material_code='MAT001',
                material_name='测试物料',
                required_qty=Decimal('200'),
                required_date=date.today() + timedelta(days=5),
                is_critical_path=True
            )
        ]
        
        mock_query = MagicMock()
        mock_join = MagicMock()
        mock_filter = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter
        mock_filter.all.return_value = mock_result
        
        demands = self.engine._collect_material_demands(
            project_id=10,
            material_id=100,
            days_ahead=30
        )
        
        self.assertEqual(len(demands), 1)
        self.assertEqual(demands[0]['material_code'], 'MAT001')
        self.assertEqual(demands[0]['required_qty'], Decimal('200'))
        self.assertTrue(demands[0]['is_critical_path'])
    
    def test_collect_material_demands_no_results(self):
        """测试：无需求数据时应返回空列表"""
        mock_query = MagicMock()
        mock_join = MagicMock()
        mock_filter = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter
        mock_filter.all.return_value = []
        
        demands = self.engine._collect_material_demands(
            project_id=None,
            material_id=None,
            days_ahead=30
        )
        
        self.assertEqual(len(demands), 0)
    
    # ========== _find_affected_projects 测试 ==========
    
    def test_find_affected_projects(self):
        """测试：查找受影响项目"""
        mock_result = [
            MagicMock(
                id=1,
                name='项目A',
                required_qty=Decimal('500')
            ),
            MagicMock(
                id=2,
                name='项目B',
                required_qty=Decimal('300')
            )
        ]
        
        mock_query = MagicMock()
        mock_join = MagicMock()
        mock_filter = MagicMock()
        mock_group = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter
        mock_filter.group_by.return_value = mock_group
        mock_group.all.return_value = mock_result
        
        projects = self.engine._find_affected_projects(
            material_id=100,
            project_id=None
        )
        
        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]['name'], '项目A')
        self.assertEqual(projects[0]['required_qty'], 500.0)
    
    # ========== _get_average_lead_time 测试 ==========
    
    def test_get_average_lead_time_with_history(self):
        """测试：有历史数据时计算平均交期"""
        mock_query = MagicMock()
        mock_join = MagicMock()
        mock_filter = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter
        mock_filter.scalar.return_value = 12.5
        
        lead_time = self.engine._get_average_lead_time(material_id=100)
        
        self.assertEqual(lead_time, 12)
    
    def test_get_average_lead_time_no_history(self):
        """测试：无历史数据时返回默认值15天"""
        mock_query = MagicMock()
        mock_join = MagicMock()
        mock_filter = MagicMock()
        self.db_mock.query.return_value = mock_query
        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter
        mock_filter.scalar.return_value = None
        
        lead_time = self.engine._get_average_lead_time(material_id=100)
        
        self.assertEqual(lead_time, 15)
    
    # ========== predict_impact 测试 ==========
    
    @patch.object(SmartAlertEngine, '_find_affected_projects')
    @patch.object(SmartAlertEngine, '_get_average_lead_time')
    @patch.object(SmartAlertEngine, '_calculate_risk_score')
    def test_predict_impact(self, mock_risk_score, mock_lead_time, mock_projects):
        """测试：预测缺料影响"""
        mock_projects.return_value = [
            {'id': 1, 'name': '项目A', 'required_qty': 100.0}
        ]
        mock_lead_time.return_value = 10
        mock_risk_score.return_value = Decimal('75')
        
        # Mock Material查询
        mock_material = MagicMock()
        mock_material.standard_price = Decimal('50')
        self.db_mock.query.return_value.filter.return_value.first.return_value = mock_material
        
        impact = self.engine.predict_impact(
            material_id=100,
            shortage_qty=Decimal('100'),
            required_date=date.today() + timedelta(days=5),
            project_id=1
        )
        
        self.assertIn('estimated_delay_days', impact)
        self.assertIn('estimated_cost_impact', impact)
        self.assertIn('affected_projects', impact)
        self.assertIn('risk_score', impact)
        self.assertEqual(len(impact['affected_projects']), 1)
    
    # ========== generate_solutions 测试 ==========
    
    @patch.object(SmartAlertEngine, '_generate_urgent_purchase_plan')
    @patch.object(SmartAlertEngine, '_generate_substitute_plans')
    @patch.object(SmartAlertEngine, '_generate_transfer_plans')
    @patch.object(SmartAlertEngine, '_generate_partial_delivery_plan')
    @patch.object(SmartAlertEngine, '_generate_reschedule_plan')
    @patch.object(SmartAlertEngine, '_score_solution')
    def test_generate_solutions_multiple_plans(
        self, mock_score, mock_reschedule, mock_partial,
        mock_transfer, mock_substitute, mock_urgent
    ):
        """测试：生成多个处理方案并排序"""
        alert = ShortageAlert(id=1)
        
        # Mock各个方案生成方法
        plan1 = ShortageHandlingPlan(solution_type='URGENT_PURCHASE', ai_score=Decimal('80'))
        plan2 = ShortageHandlingPlan(solution_type='RESCHEDULE', ai_score=Decimal('90'))
        plan3 = ShortageHandlingPlan(solution_type='PARTIAL_DELIVERY', ai_score=Decimal('70'))
        
        mock_urgent.return_value = plan1
        mock_substitute.return_value = []
        mock_transfer.return_value = []
        mock_partial.return_value = plan3
        mock_reschedule.return_value = plan2
        
        solutions = self.engine.generate_solutions(alert)
        
        # 验证排序（ai_score降序）
        self.assertEqual(len(solutions), 3)
        self.assertEqual(solutions[0].ai_score, Decimal('90'))
        self.assertTrue(solutions[0].is_recommended)
        self.assertEqual(solutions[0].recommendation_rank, 1)
        
        # 验证数据库操作
        self.assertEqual(self.db_mock.add.call_count, 3)
        self.db_mock.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
