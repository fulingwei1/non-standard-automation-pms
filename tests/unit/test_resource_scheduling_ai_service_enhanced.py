# -*- coding: utf-8 -*-
"""
资源调度AI服务增强单元测试
完整覆盖所有核心方法和边界条件
"""

import json
import sys
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, PropertyMock

from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService


class TestResourceSchedulingAIServiceEnhanced(unittest.TestCase):
    """资源调度AI服务增强测试套件"""

    def setUp(self):
        """初始化测试环境"""
        self.db_mock = MagicMock()
        self.service = ResourceSchedulingAIService(self.db_mock)
        
        # Mock AI客户端
        self.ai_client_mock = MagicMock()
        self.service.ai_client = self.ai_client_mock
        
        # Mock内部导入的类
        self.mock_pmo_allocation = MagicMock()
        self.mock_timesheet = MagicMock()
        self.mock_project = MagicMock()
        
        # 将mock注入到sys.modules中
        sys.modules['app.models.finance'].PMOResourceAllocation = self.mock_pmo_allocation
        sys.modules['app.models.finance'].Timesheet = self.mock_timesheet

    def tearDown(self):
        """清理测试环境"""
        self.db_mock.reset_mock()
        self.ai_client_mock.reset_mock()

    # ========================================================================
    # 1. 资源冲突检测测试 (detect_resource_conflicts)
    # ========================================================================

    def test_detect_resource_conflicts_no_conflicts(self):
        """测试无冲突场景"""
        # Mock查询返回空列表
        self.db_mock.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        
        conflicts = self.service.detect_resource_conflicts(
            resource_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(len(conflicts), 0)

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_detect_resource_conflicts_with_overlap(self, mock_save):
        """测试存在时间重叠的资源分配"""
        # Mock分配记录
        alloc1 = Mock()
        alloc1.id = 1
        alloc1.resource_id = 1
        alloc1.project_id = 10
        alloc1.start_date = date(2024, 1, 1)
        alloc1.end_date = date(2024, 1, 31)
        alloc1.allocation_percent = Decimal('60')
        alloc1.resource_name = "张三"
        alloc1.resource_dept = "研发部"
        alloc1.planned_hours = Decimal('100')
        alloc1.status = "PLANNED"
        
        alloc2 = Mock()
        alloc2.id = 2
        alloc2.resource_id = 1
        alloc2.project_id = 20
        alloc2.start_date = date(2024, 1, 15)
        alloc2.end_date = date(2024, 2, 15)
        alloc2.allocation_percent = Decimal('50')
        alloc2.resource_name = "张三"
        alloc2.resource_dept = "研发部"
        alloc2.planned_hours = Decimal('80')
        alloc2.status = "PLANNED"
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [alloc1, alloc2]
        
        # Mock项目查询
        project_mock = Mock()
        project_mock.project_code = "PRJ-001"
        project_mock.project_name = "测试项目"
        self.db_mock.query.return_value.filter.return_value.first.return_value = project_mock
        
        # Mock AI评估
        with patch.object(self.service, '_ai_assess_conflict') as mock_ai:
            mock_ai.return_value = (
                ["风险1", "风险2"],
                {"schedule_impact": "高"},
                Decimal("0.85")
            )
            
            conflicts = self.service.detect_resource_conflicts(resource_id=1)
            
            self.assertEqual(len(conflicts), 1)

    def test_detect_resource_conflicts_no_overlap(self):
        """测试无时间重叠的场景"""
        # 两个分配没有时间重叠
        alloc1 = Mock()
        alloc1.id = 1
        alloc1.resource_id = 1
        alloc1.project_id = 10
        alloc1.start_date = date(2024, 1, 1)
        alloc1.end_date = date(2024, 1, 15)
        alloc1.allocation_percent = Decimal('60')
        alloc1.status = "PLANNED"
        
        alloc2 = Mock()
        alloc2.id = 2
        alloc2.resource_id = 1
        alloc2.project_id = 20
        alloc2.start_date = date(2024, 2, 1)
        alloc2.end_date = date(2024, 2, 28)
        alloc2.allocation_percent = Decimal('50')
        alloc2.status = "PLANNED"
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [alloc1, alloc2]
        
        conflicts = self.service.detect_resource_conflicts(resource_id=1)
        
        self.assertEqual(len(conflicts), 0)

    def test_detect_resource_conflicts_under_100_percent(self):
        """测试总分配比例未超过100%的场景"""
        # 两个分配有重叠但总比例未超过100%
        alloc1 = Mock()
        alloc1.id = 1
        alloc1.resource_id = 1
        alloc1.project_id = 10
        alloc1.start_date = date(2024, 1, 1)
        alloc1.end_date = date(2024, 1, 31)
        alloc1.allocation_percent = Decimal('40')
        alloc1.status = "PLANNED"
        
        alloc2 = Mock()
        alloc2.id = 2
        alloc2.resource_id = 1
        alloc2.project_id = 20
        alloc2.start_date = date(2024, 1, 15)
        alloc2.end_date = date(2024, 2, 15)
        alloc2.allocation_percent = Decimal('50')
        alloc2.status = "PLANNED"
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [alloc1, alloc2]
        
        conflicts = self.service.detect_resource_conflicts(resource_id=1)
        
        # 总分配90%，不应产生冲突
        self.assertEqual(len(conflicts), 0)

    def test_detect_resource_conflicts_with_filters(self):
        """测试带过滤条件的冲突检测"""
        query_mock = self.db_mock.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.filter.return_value = filter_mock
        filter_mock.all.return_value = []
        
        self.service.detect_resource_conflicts(
            resource_id=1,
            resource_type="PERSON",
            project_id=10,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证查询被调用
        self.assertTrue(query_mock.filter.called)

    # ========================================================================
    # 2. _create_conflict_record 测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_create_conflict_record_basic(self, mock_save):
        """测试创建冲突记录"""
        alloc_a = Mock()
        alloc_a.id = 1
        alloc_a.project_id = 10
        alloc_a.allocation_percent = Decimal('60')
        alloc_a.start_date = date(2024, 1, 1)
        alloc_a.end_date = date(2024, 1, 31)
        alloc_a.resource_name = "张三"
        alloc_a.resource_dept = "研发部"
        alloc_a.planned_hours = Decimal('100')
        
        alloc_b = Mock()
        alloc_b.id = 2
        alloc_b.project_id = 20
        alloc_b.allocation_percent = Decimal('50')
        alloc_b.start_date = date(2024, 1, 15)
        alloc_b.end_date = date(2024, 2, 15)
        alloc_b.planned_hours = Decimal('80')
        
        project_mock = Mock()
        project_mock.project_code = "PRJ-001"
        project_mock.project_name = "测试项目"
        self.db_mock.query.return_value.filter.return_value.first.return_value = project_mock
        
        # Mock AI评估
        with patch.object(self.service, '_ai_assess_conflict') as mock_ai:
            mock_ai.return_value = (
                ["风险1", "风险2"],
                {"schedule_impact": "高"},
                Decimal("0.85")
            )
            
            conflict = self.service._create_conflict_record(
                resource_id=1,
                resource_type="PERSON",
                alloc_a=alloc_a,
                alloc_b=alloc_b,
                overlap_start=date(2024, 1, 15),
                overlap_end=date(2024, 1, 31),
                total_allocation=Decimal('110')
            )
            
            self.assertIsNotNone(conflict)
            self.assertEqual(conflict.resource_id, 1)
            self.assertEqual(conflict.over_allocation, Decimal('10'))
            mock_save.assert_called_once()

    # ========================================================================
    # 3. _calculate_severity 测试
    # ========================================================================

    def test_calculate_severity_critical_high_over_allocation(self):
        """测试严重过度分配 (>= 50%)"""
        severity = self.service._calculate_severity(Decimal('50'), 10)
        self.assertEqual(severity, "CRITICAL")
        
        severity = self.service._calculate_severity(Decimal('60'), 5)
        self.assertEqual(severity, "CRITICAL")

    def test_calculate_severity_critical_long_overlap(self):
        """测试长时间重叠 (>= 30天)"""
        severity = self.service._calculate_severity(Decimal('10'), 30)
        self.assertEqual(severity, "CRITICAL")
        
        severity = self.service._calculate_severity(Decimal('5'), 35)
        self.assertEqual(severity, "CRITICAL")

    def test_calculate_severity_high(self):
        """测试高严重程度"""
        severity = self.service._calculate_severity(Decimal('30'), 10)
        self.assertEqual(severity, "HIGH")
        
        severity = self.service._calculate_severity(Decimal('20'), 14)
        self.assertEqual(severity, "HIGH")

    def test_calculate_severity_medium(self):
        """测试中等严重程度"""
        severity = self.service._calculate_severity(Decimal('10'), 5)
        self.assertEqual(severity, "MEDIUM")
        
        severity = self.service._calculate_severity(Decimal('15'), 7)
        self.assertEqual(severity, "MEDIUM")

    def test_calculate_severity_low(self):
        """测试低严重程度"""
        severity = self.service._calculate_severity(Decimal('5'), 3)
        self.assertEqual(severity, "LOW")
        
        severity = self.service._calculate_severity(Decimal('8'), 5)
        self.assertEqual(severity, "LOW")

    # ========================================================================
    # 4. _calculate_priority_score 测试
    # ========================================================================

    def test_calculate_priority_score_critical(self):
        """测试紧急优先级分数"""
        score = self.service._calculate_priority_score("CRITICAL", 20)
        self.assertGreaterEqual(score, 95)
        self.assertLessEqual(score, 100)

    def test_calculate_priority_score_high(self):
        """测试高优先级分数"""
        score = self.service._calculate_priority_score("HIGH", 10)
        self.assertGreaterEqual(score, 75)
        self.assertLessEqual(score, 100)

    def test_calculate_priority_score_medium(self):
        """测试中等优先级分数"""
        score = self.service._calculate_priority_score("MEDIUM", 5)
        self.assertGreaterEqual(score, 50)

    def test_calculate_priority_score_low(self):
        """测试低优先级分数"""
        score = self.service._calculate_priority_score("LOW", 2)
        self.assertGreaterEqual(score, 30)

    def test_calculate_priority_score_max_capped(self):
        """测试分数上限为100"""
        score = self.service._calculate_priority_score("CRITICAL", 50)
        self.assertEqual(score, 100)

    # ========================================================================
    # 5. _ai_assess_conflict 测试
    # ========================================================================

    def test_ai_assess_conflict_success(self):
        """测试AI评估成功场景"""
        project_mock = Mock()
        project_mock.project_name = "测试项目"
        
        ai_response = {
            "content": json.dumps({
                "risk_factors": ["资源超负荷", "项目延期"],
                "impact_analysis": {
                    "schedule_impact": "严重",
                    "quality_impact": "中等"
                },
                "confidence": 0.85
            })
        }
        self.ai_client_mock.generate_solution.return_value = ai_response
        
        risk_factors, impact_analysis, confidence = self.service._ai_assess_conflict(
            resource_id=1,
            project_a=project_mock,
            project_b=project_mock,
            over_allocation=Decimal('20'),
            overlap_days=15
        )
        
        self.assertEqual(len(risk_factors), 2)
        self.assertIn("schedule_impact", impact_analysis)
        self.assertEqual(confidence, Decimal("0.85"))

    def test_ai_assess_conflict_failure_returns_default(self):
        """测试AI评估失败返回默认值"""
        project_mock = Mock()
        project_mock.project_name = "测试项目"
        
        # 模拟AI调用失败
        self.ai_client_mock.generate_solution.side_effect = Exception("AI服务错误")
        
        risk_factors, impact_analysis, confidence = self.service._ai_assess_conflict(
            resource_id=1,
            project_a=project_mock,
            project_b=project_mock,
            over_allocation=Decimal('20'),
            overlap_days=15
        )
        
        # 应返回默认值
        self.assertIsInstance(risk_factors, list)
        self.assertIsInstance(impact_analysis, dict)
        self.assertEqual(confidence, Decimal("0.6"))

    def test_ai_assess_conflict_invalid_json(self):
        """测试AI返回无效JSON"""
        project_mock = Mock()
        project_mock.project_name = "测试项目"
        
        ai_response = {
            "content": "这不是JSON"
        }
        self.ai_client_mock.generate_solution.return_value = ai_response
        
        risk_factors, impact_analysis, confidence = self.service._ai_assess_conflict(
            resource_id=1,
            project_a=project_mock,
            project_b=project_mock,
            over_allocation=Decimal('20'),
            overlap_days=15
        )
        
        # 应返回默认值
        self.assertIsInstance(risk_factors, list)
        self.assertIsInstance(impact_analysis, dict)

    # ========================================================================
    # 6. generate_scheduling_suggestions 测试
    # ========================================================================

    def test_generate_scheduling_suggestions_conflict_not_found(self):
        """测试冲突不存在时抛出异常"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.generate_scheduling_suggestions(conflict_id=999)
        
        self.assertIn("not found", str(context.exception))

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_generate_scheduling_suggestions_success(self, mock_save):
        """测试成功生成调度方案"""
        conflict_mock = Mock()
        conflict_mock.id = 1
        conflict_mock.resource_name = "张三"
        conflict_mock.department_name = "研发部"
        conflict_mock.project_a_name = "项目A"
        conflict_mock.project_b_name = "项目B"
        conflict_mock.allocation_a_percent = Decimal('60')
        conflict_mock.allocation_b_percent = Decimal('50')
        conflict_mock.start_date_a = date(2024, 1, 1)
        conflict_mock.end_date_a = date(2024, 1, 31)
        conflict_mock.start_date_b = date(2024, 1, 15)
        conflict_mock.end_date_b = date(2024, 2, 15)
        conflict_mock.overlap_start = date(2024, 1, 15)
        conflict_mock.overlap_end = date(2024, 1, 31)
        conflict_mock.overlap_days = 17
        conflict_mock.over_allocation = Decimal('10')
        conflict_mock.severity = "HIGH"
        conflict_mock.project_b_id = 20
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = conflict_mock
        
        # Mock AI生成方案
        with patch.object(self.service, '_ai_generate_solutions') as mock_ai:
            mock_ai.return_value = [{
                "solution_type": "REALLOCATE",
                "strategy_name": "调整分配",
                "strategy_description": "降低项目B分配",
                "adjustments": {},
                "pros": ["快速"],
                "cons": ["影响进度"],
                "risks": ["需要沟通"],
                "affected_projects": [],
                "timeline_impact_days": 3,
                "cost_impact": 0,
                "quality_impact": "LOW",
                "execution_steps": ["步骤1"],
                "estimated_duration_days": 2,
                "feasibility_score": 85,
                "impact_score": 25,
                "cost_score": 10,
                "risk_score": 20,
                "efficiency_score": 80,
                "ai_reasoning": "推荐理由",
                "ai_tokens_used": 500
            }]
            
            suggestions = self.service.generate_scheduling_suggestions(conflict_id=1)
            
            self.assertEqual(len(suggestions), 1)
            self.assertTrue(conflict_mock.has_ai_suggestion)
            self.assertEqual(conflict_mock.status, "ANALYZING")

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_generate_scheduling_suggestions_multiple_suggestions(self, mock_save):
        """测试生成多个方案"""
        conflict_mock = Mock()
        conflict_mock.id = 1
        conflict_mock.project_b_id = 20
        # 设置其他必需属性...
        for attr in ['resource_name', 'department_name', 'project_a_name', 'project_b_name',
                     'allocation_a_percent', 'allocation_b_percent', 'start_date_a', 'end_date_a',
                     'start_date_b', 'end_date_b', 'overlap_start', 'overlap_end',
                     'overlap_days', 'over_allocation', 'severity']:
            setattr(conflict_mock, attr, Mock())
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = conflict_mock
        
        with patch.object(self.service, '_ai_generate_solutions') as mock_ai:
            mock_ai.return_value = [{
                "solution_type": f"TYPE_{i}",
                "strategy_name": f"方案{i}",
                "feasibility_score": 80 - i * 5,
                "impact_score": 20,
                "cost_score": 10,
                "risk_score": 15,
                "efficiency_score": 75,
            } for i in range(3)]
            
            suggestions = self.service.generate_scheduling_suggestions(
                conflict_id=1,
                max_suggestions=3
            )
            
            self.assertEqual(len(suggestions), 3)

    # ========================================================================
    # 7. _ai_generate_solutions 测试
    # ========================================================================

    def test_ai_generate_solutions_success(self):
        """测试AI成功生成方案"""
        conflict_mock = Mock()
        conflict_mock.resource_name = "张三"
        conflict_mock.department_name = "研发部"
        conflict_mock.project_a_name = "项目A"
        conflict_mock.project_b_name = "项目B"
        conflict_mock.allocation_a_percent = Decimal('60')
        conflict_mock.allocation_b_percent = Decimal('50')
        conflict_mock.start_date_a = date(2024, 1, 1)
        conflict_mock.end_date_a = date(2024, 1, 31)
        conflict_mock.start_date_b = date(2024, 1, 15)
        conflict_mock.end_date_b = date(2024, 2, 15)
        conflict_mock.overlap_start = date(2024, 1, 15)
        conflict_mock.overlap_end = date(2024, 1, 31)
        conflict_mock.overlap_days = 17
        conflict_mock.over_allocation = Decimal('10')
        conflict_mock.severity = "HIGH"
        conflict_mock.project_b_id = 20
        
        ai_response = {
            "content": json.dumps([{
                "solution_type": "REALLOCATE",
                "strategy_name": "调整分配",
                "feasibility_score": 85
            }]),
            "tokens_used": 1000
        }
        self.ai_client_mock.generate_solution.return_value = ai_response
        
        solutions = self.service._ai_generate_solutions(conflict_mock, max_suggestions=1)
        
        self.assertEqual(len(solutions), 1)
        self.assertIn("ai_tokens_used", solutions[0])
        self.assertIn("ai_generated_at", solutions[0])

    def test_ai_generate_solutions_failure_returns_default(self):
        """测试AI失败返回默认方案"""
        conflict_mock = Mock()
        conflict_mock.allocation_a_percent = Decimal('60')
        conflict_mock.project_b_id = 20
        
        self.ai_client_mock.generate_solution.side_effect = Exception("AI错误")
        
        solutions = self.service._ai_generate_solutions(conflict_mock, max_suggestions=3)
        
        # 应返回默认方案
        self.assertIsInstance(solutions, list)
        self.assertGreater(len(solutions), 0)
        self.assertEqual(solutions[0]["solution_type"], "REALLOCATE")

    # ========================================================================
    # 8. _create_suggestion_record 测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_create_suggestion_record_basic(self, mock_save):
        """测试创建方案记录"""
        conflict_mock = Mock()
        conflict_mock.id = 1
        
        ai_suggestion = {
            "solution_type": "REALLOCATE",
            "strategy_name": "调整分配",
            "strategy_description": "降低项目B分配",
            "adjustments": {"project_a": {"allocation_percent": 60}},
            "pros": ["快速"],
            "cons": ["影响进度"],
            "risks": ["需要沟通"],
            "affected_projects": [],
            "affected_resources": [],
            "timeline_impact_days": 3,
            "cost_impact": 0,
            "quality_impact": "LOW",
            "execution_steps": ["步骤1"],
            "estimated_duration_days": 2,
            "prerequisites": [],
            "feasibility_score": 85,
            "impact_score": 25,
            "cost_score": 10,
            "risk_score": 20,
            "efficiency_score": 80,
            "ai_reasoning": "推荐理由",
            "ai_tokens_used": 500
        }
        
        suggestion = self.service._create_suggestion_record(
            conflict=conflict_mock,
            ai_suggestion=ai_suggestion,
            rank=1,
            is_recommended=True
        )
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.solution_type, "REALLOCATE")
        self.assertEqual(suggestion.rank_order, 1)
        self.assertTrue(suggestion.is_recommended)
        mock_save.assert_called_once()

    def test_create_suggestion_record_calculates_ai_score(self):
        """测试AI综合评分计算"""
        with patch('app.services.resource_scheduling_ai_service.save_obj'):
            conflict_mock = Mock()
            conflict_mock.id = 1
            
            ai_suggestion = {
                "feasibility_score": 80,
                "impact_score": 30,
                "cost_score": 20,
                "risk_score": 25,
                "efficiency_score": 75,
            }
            
            suggestion = self.service._create_suggestion_record(
                conflict=conflict_mock,
                ai_suggestion=ai_suggestion,
                rank=1,
                is_recommended=False
            )
            
            # 验证评分计算
            self.assertIsNotNone(suggestion.ai_score)
            self.assertGreater(suggestion.ai_score, 0)

    # ========================================================================
    # 9. forecast_resource_demand 测试 (Mock整个方法的Project访问)
    # ========================================================================

    def test_forecast_resource_demand_1month(self):
        """测试1个月预测"""
        # Mock整个查询链
        project_mock = Mock()
        project_mock.project_name = "测试项目"
        project_mock.start_date = date.today()
        project_mock.end_date = date.today() + timedelta(days=30)
        project_mock.stage = "EXECUTING"
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [project_mock]
        
        with patch.object(self.service, '_ai_forecast_demand') as mock_ai:
            mock_ai.return_value = {
                "predicted_demand": 10,
                "demand_gap": 2,
                "gap_severity": "SHORTAGE",
                "predicted_utilization": 85,
                "ai_confidence": 0.75
            }
            
            with patch('app.services.resource_scheduling_ai_service.save_obj'):
                forecasts = self.service.forecast_resource_demand(
                    forecast_period="1MONTH",
                    resource_type="PERSON"
                )
                
                self.assertEqual(len(forecasts), 1)

    # ========================================================================
    # 10. _ai_forecast_demand 测试
    # ========================================================================

    def test_ai_forecast_demand_success(self):
        """测试AI预测成功"""
        project_mock = Mock()
        project_mock.project_name = "测试项目"
        project_mock.start_date = date.today()
        project_mock.end_date = date.today() + timedelta(days=90)
        project_mock.stage = "EXECUTING"
        
        ai_response = {
            "content": json.dumps({
                "predicted_demand": 15,
                "demand_gap": 3,
                "gap_severity": "SHORTAGE",
                "predicted_total_hours": 5400,
                "predicted_utilization": 85,
                "ai_confidence": 0.78
            })
        }
        self.ai_client_mock.generate_solution.return_value = ai_response
        
        result = self.service._ai_forecast_demand(
            projects=[project_mock],
            forecast_period="3MONTH",
            resource_type="PERSON",
            skill_category="开发"
        )
        
        self.assertEqual(result["predicted_demand"], 15)
        self.assertEqual(result["demand_gap"], 3)

    def test_ai_forecast_demand_failure_returns_default(self):
        """测试AI预测失败返回默认值"""
        self.ai_client_mock.generate_solution.side_effect = Exception("AI错误")
        
        result = self.service._ai_forecast_demand(
            projects=[],
            forecast_period="3MONTH",
            resource_type="PERSON",
            skill_category=None
        )
        
        self.assertIn("predicted_demand", result)
        self.assertEqual(result["predicted_demand"], 10)

    # ========================================================================
    # 11. _create_forecast_record 测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_create_forecast_record_basic(self, mock_save):
        """测试创建预测记录"""
        forecast_start = date.today()
        forecast_end = date.today() + timedelta(days=90)
        
        ai_forecast = {
            "predicted_demand": 15,
            "demand_gap": 3,
            "gap_severity": "SHORTAGE",
            "predicted_total_hours": 5400,
            "predicted_peak_hours": 240,
            "predicted_utilization": 85,
            "driving_projects": [{"project_id": 1, "impact": "高"}],
            "recommendations": ["招聘2名工程师"],
            "hiring_suggestion": {"role": "高级工程师", "count": 2},
            "estimated_cost": 150000,
            "risk_level": "MEDIUM",
            "ai_confidence": 0.78
        }
        
        forecast = self.service._create_forecast_record(
            forecast_start=forecast_start,
            forecast_end=forecast_end,
            forecast_period="3MONTH",
            resource_type="PERSON",
            skill_category="开发",
            ai_forecast=ai_forecast
        )
        
        self.assertIsNotNone(forecast)
        self.assertEqual(forecast.predicted_demand, 15)
        self.assertEqual(forecast.demand_gap, 3)
        mock_save.assert_called_once()

    # ========================================================================
    # 12. analyze_resource_utilization 测试
    # ========================================================================

    def test_analyze_resource_utilization_basic(self):
        """测试基本利用率分析"""
        # Mock工时记录
        ts1 = Mock()
        ts1.hours = Decimal('8')
        ts2 = Mock()
        ts2.hours = Decimal('7.5')
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [ts1, ts2]
        
        with patch.object(self.service, '_ai_analyze_utilization') as mock_ai:
            mock_ai.return_value = {
                "key_insights": ["利用率正常"],
                "optimization_suggestions": []
            }
            
            with patch('app.services.resource_scheduling_ai_service.save_obj'):
                analysis = self.service.analyze_resource_utilization(
                    resource_id=1,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 7),
                    analysis_period="WEEKLY"
                )
                
                self.assertIsNotNone(analysis)
                self.assertEqual(analysis.resource_id, 1)

    def test_analyze_resource_utilization_zero_available_hours(self):
        """测试可用工时为零的场景"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []
        
        with patch.object(self.service, '_ai_analyze_utilization') as mock_ai:
            mock_ai.return_value = {}
            
            with patch('app.services.resource_scheduling_ai_service.save_obj'):
                # 同一天的日期范围
                analysis = self.service.analyze_resource_utilization(
                    resource_id=1,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 1)
                )
                
                self.assertIsNotNone(analysis)

    # ========================================================================
    # 13. _determine_utilization_status 测试
    # ========================================================================

    def test_determine_utilization_status_underutilized(self):
        """测试利用不足状态"""
        status = self.service._determine_utilization_status(Decimal('30'))
        self.assertEqual(status, "UNDERUTILIZED")
        
        status = self.service._determine_utilization_status(Decimal('49'))
        self.assertEqual(status, "UNDERUTILIZED")

    def test_determine_utilization_status_normal(self):
        """测试正常状态"""
        status = self.service._determine_utilization_status(Decimal('50'))
        self.assertEqual(status, "NORMAL")
        
        status = self.service._determine_utilization_status(Decimal('75'))
        self.assertEqual(status, "NORMAL")
        
        status = self.service._determine_utilization_status(Decimal('90'))
        self.assertEqual(status, "NORMAL")

    def test_determine_utilization_status_overutilized(self):
        """测试过度利用状态"""
        status = self.service._determine_utilization_status(Decimal('91'))
        self.assertEqual(status, "OVERUTILIZED")
        
        status = self.service._determine_utilization_status(Decimal('110'))
        self.assertEqual(status, "OVERUTILIZED")

    def test_determine_utilization_status_critical(self):
        """测试严重过载状态"""
        status = self.service._determine_utilization_status(Decimal('111'))
        self.assertEqual(status, "CRITICAL")
        
        status = self.service._determine_utilization_status(Decimal('150'))
        self.assertEqual(status, "CRITICAL")

    # ========================================================================
    # 14. _ai_analyze_utilization 测试
    # ========================================================================

    def test_ai_analyze_utilization_success(self):
        """测试AI分析利用率成功"""
        ai_response = {
            "content": json.dumps({
                "key_insights": ["洞察1", "洞察2"],
                "optimization_suggestions": ["建议1"],
                "reallocation_opportunities": []
            })
        }
        self.ai_client_mock.generate_solution.return_value = ai_response
        
        result = self.service._ai_analyze_utilization(
            resource_id=1,
            utilization_rate=Decimal('85'),
            total_hours=Decimal('168'),
            period_days=30
        )
        
        self.assertIn("key_insights", result)
        self.assertEqual(len(result["key_insights"]), 2)

    def test_ai_analyze_utilization_failure_returns_default(self):
        """测试AI分析失败返回默认值"""
        self.ai_client_mock.generate_solution.side_effect = Exception("AI错误")
        
        result = self.service._ai_analyze_utilization(
            resource_id=1,
            utilization_rate=Decimal('85'),
            total_hours=Decimal('168'),
            period_days=30
        )
        
        self.assertIn("key_insights", result)
        self.assertIsInstance(result["optimization_suggestions"], list)

    # ========================================================================
    # 15. 边界条件和异常处理测试
    # ========================================================================

    def test_detect_conflicts_empty_resource_id(self):
        """测试空资源ID"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []
        
        conflicts = self.service.detect_resource_conflicts()
        self.assertEqual(len(conflicts), 0)

    def test_severity_with_zero_values(self):
        """测试零值严重程度"""
        severity = self.service._calculate_severity(Decimal('0'), 0)
        self.assertEqual(severity, "LOW")

    def test_priority_score_with_unknown_severity(self):
        """测试未知严重程度的优先级分数"""
        score = self.service._calculate_priority_score("UNKNOWN", 5)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_create_suggestion_with_missing_fields(self, mock_save):
        """测试创建方案时缺少某些字段"""
        conflict_mock = Mock()
        conflict_mock.id = 1
        
        # 最小化的AI建议
        ai_suggestion = {}
        
        suggestion = self.service._create_suggestion_record(
            conflict=conflict_mock,
            ai_suggestion=ai_suggestion,
            rank=1,
            is_recommended=False
        )
        
        self.assertIsNotNone(suggestion)
        mock_save.assert_called_once()


if __name__ == '__main__':
    unittest.main()
