# -*- coding: utf-8 -*-
"""
资源调度AI服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, AI API调用等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal
import json

from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService


class TestResourceSchedulingAIService(unittest.TestCase):
    """测试资源调度AI服务"""

    def setUp(self):
        """测试前设置"""
        # Mock数据库session
        self.db = MagicMock()
        self.service = ResourceSchedulingAIService(self.db)
        
        # Mock AI客户端
        self.service.ai_client = MagicMock()

    # ========================================================================
    # 1. 资源冲突检测测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_detect_resource_conflicts_no_conflicts(self, mock_save):
        """测试无冲突场景"""
        # 准备数据：两个分配没有时间重叠
        alloc1 = MagicMock()
        alloc1.resource_id = 1
        alloc1.project_id = 10
        alloc1.allocation_percent = 50
        alloc1.start_date = date(2024, 1, 1)
        alloc1.end_date = date(2024, 1, 15)
        
        alloc2 = MagicMock()
        alloc2.resource_id = 1
        alloc2.project_id = 20
        alloc2.allocation_percent = 50
        alloc2.start_date = date(2024, 1, 16)  # 不重叠
        alloc2.end_date = date(2024, 1, 31)
        
        # Mock查询
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.filter.return_value.all.return_value = [alloc1, alloc2]
        
        # 执行
        conflicts = self.service.detect_resource_conflicts(
            resource_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        
        # 验证：无冲突
        self.assertEqual(len(conflicts), 0)

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_detect_resource_conflicts_with_overlap(self, mock_save):
        """测试有冲突场景"""
        # 准备数据：两个分配时间重叠且超100%
        alloc1 = MagicMock()
        alloc1.id = 101
        alloc1.resource_id = 1
        alloc1.resource_name = "张三"
        alloc1.resource_dept = "研发部"
        alloc1.project_id = 10
        alloc1.allocation_percent = Decimal("60")
        alloc1.start_date = date(2024, 1, 1)
        alloc1.end_date = date(2024, 1, 20)
        alloc1.planned_hours = Decimal("100")
        alloc1.status = "PLANNED"  # 添加status字段
        
        alloc2 = MagicMock()
        alloc2.id = 102
        alloc2.resource_id = 1
        alloc2.resource_name = "张三"
        alloc2.resource_dept = "研发部"
        alloc2.project_id = 20
        alloc2.allocation_percent = Decimal("50")
        alloc2.start_date = date(2024, 1, 10)  # 重叠
        alloc2.end_date = date(2024, 1, 30)
        alloc2.planned_hours = Decimal("80")
        alloc2.status = "PLANNED"  # 添加status字段
        
        # Mock项目查询
        project_a = MagicMock()
        project_a.project_code = "PRJ001"
        project_a.project_name = "项目A"
        
        project_b = MagicMock()
        project_b.project_code = "PRJ002"
        project_b.project_name = "项目B"
        
        # Mock分配查询 - 模拟filter链: filter(resource_id).filter(date_range).filter(status)
        mock_filter_final = MagicMock()
        mock_filter_final.all.return_value = [alloc1, alloc2]
        
        mock_filter_date = MagicMock()
        mock_filter_date.filter.return_value = mock_filter_final  # filter(status)
        
        mock_filter_resource = MagicMock()
        mock_filter_resource.filter.return_value = mock_filter_date  # filter(date_range)
        
        mock_alloc_query = MagicMock()
        mock_alloc_query.filter.return_value = mock_filter_resource  # filter(resource_id)
        
        # Mock项目查询
        mock_project_query_a = MagicMock()
        mock_project_query_a.filter.return_value.first.return_value = project_a
        
        mock_project_query_b = MagicMock()
        mock_project_query_b.filter.return_value.first.return_value = project_b
        
        self.db.query.side_effect = [
            mock_alloc_query,  # 第一次调用：分配查询
            mock_project_query_a,  # project_a
            mock_project_query_b,  # project_b
        ]
        
        # Mock AI评估
        self.service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "risk_factors": ["资源超负荷", "项目进度风险"],
                "impact_analysis": {
                    "schedule_impact": "延期风险高",
                    "quality_impact": "质量可能下降",
                    "cost_impact": "成本增加"
                },
                "confidence": 0.85
            })
        }
        
        # 执行
        conflicts = self.service.detect_resource_conflicts(
            resource_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        
        # 验证
        self.assertEqual(len(conflicts), 1)
        conflict = conflicts[0]
        self.assertEqual(conflict.resource_id, 1)
        self.assertEqual(conflict.total_allocation, Decimal("110"))
        self.assertEqual(conflict.over_allocation, Decimal("10"))
        self.assertEqual(conflict.overlap_days, 11)  # 1月10-20日
        self.assertIsNotNone(conflict.severity)

    def test_calculate_severity_critical(self):
        """测试严重程度计算 - CRITICAL"""
        # 过度分配50%以上
        severity = self.service._calculate_severity(Decimal("60"), 10)
        self.assertEqual(severity, "CRITICAL")
        
        # 或冲突30天以上
        severity = self.service._calculate_severity(Decimal("20"), 35)
        self.assertEqual(severity, "CRITICAL")

    def test_calculate_severity_high(self):
        """测试严重程度计算 - HIGH"""
        severity = self.service._calculate_severity(Decimal("35"), 15)
        self.assertEqual(severity, "HIGH")

    def test_calculate_severity_medium(self):
        """测试严重程度计算 - MEDIUM"""
        severity = self.service._calculate_severity(Decimal("15"), 8)
        self.assertEqual(severity, "MEDIUM")

    def test_calculate_severity_low(self):
        """测试严重程度计算 - LOW"""
        severity = self.service._calculate_severity(Decimal("5"), 3)
        self.assertEqual(severity, "LOW")

    def test_calculate_priority_score(self):
        """测试优先级评分计算"""
        # CRITICAL + 30天
        score = self.service._calculate_priority_score("CRITICAL", 30)
        self.assertEqual(score, 100)  # min(95+30, 100)
        
        # HIGH + 10天
        score = self.service._calculate_priority_score("HIGH", 10)
        self.assertEqual(score, 85)  # 75 + 10
        
        # MEDIUM + 5天
        score = self.service._calculate_priority_score("MEDIUM", 5)
        self.assertEqual(score, 55)  # 50 + 5
        
        # LOW + 3天
        score = self.service._calculate_priority_score("LOW", 3)
        self.assertEqual(score, 33)  # 30 + 3

    def test_ai_assess_conflict_success(self):
        """测试AI评估冲突 - 成功场景"""
        project_a = MagicMock()
        project_a.project_name = "项目A"
        
        project_b = MagicMock()
        project_b.project_name = "项目B"
        
        # Mock AI响应
        self.service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "risk_factors": ["风险1", "风险2", "风险3"],
                "impact_analysis": {
                    "schedule_impact": "延期2周",
                    "quality_impact": "质量风险中等",
                    "cost_impact": "成本增加10%"
                },
                "confidence": 0.92
            })
        }
        
        risk_factors, impact_analysis, confidence = self.service._ai_assess_conflict(
            resource_id=1,
            project_a=project_a,
            project_b=project_b,
            over_allocation=Decimal("30"),
            overlap_days=15,
        )
        
        # 验证
        self.assertEqual(len(risk_factors), 3)
        self.assertIn("风险1", risk_factors)
        self.assertEqual(impact_analysis["schedule_impact"], "延期2周")
        self.assertEqual(confidence, Decimal("0.92"))

    def test_ai_assess_conflict_failure(self):
        """测试AI评估冲突 - 失败场景（返回默认值）"""
        # Mock AI抛出异常
        self.service.ai_client.generate_solution.side_effect = Exception("AI调用失败")
        
        risk_factors, impact_analysis, confidence = self.service._ai_assess_conflict(
            resource_id=1,
            project_a=None,
            project_b=None,
            over_allocation=Decimal("20"),
            overlap_days=10,
        )
        
        # 验证返回默认值
        self.assertIn("资源超负荷", risk_factors)
        self.assertIn("项目进度风险", risk_factors)
        self.assertIn("schedule_impact", impact_analysis)
        self.assertEqual(confidence, Decimal("0.6"))

    # ========================================================================
    # 2. AI生成调度方案测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_generate_scheduling_suggestions_success(self, mock_save):
        """测试生成调度方案 - 成功"""
        # 准备冲突数据
        conflict = MagicMock()
        conflict.id = 1
        conflict.resource_name = "张三"
        conflict.department_name = "研发部"
        conflict.project_a_id = 10
        conflict.project_a_name = "项目A"
        conflict.allocation_a_percent = Decimal("60")
        conflict.start_date_a = date(2024, 1, 1)
        conflict.end_date_a = date(2024, 1, 20)
        conflict.project_b_id = 20
        conflict.project_b_name = "项目B"
        conflict.allocation_b_percent = Decimal("50")
        conflict.start_date_b = date(2024, 1, 10)
        conflict.end_date_b = date(2024, 1, 30)
        conflict.overlap_start = date(2024, 1, 10)
        conflict.overlap_end = date(2024, 1, 20)
        conflict.overlap_days = 11
        conflict.over_allocation = Decimal("10")
        conflict.severity = "MEDIUM"
        
        # Mock查询
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.first.return_value = conflict
        
        # Mock AI生成方案
        self.service.ai_client.generate_solution.return_value = {
            "content": json.dumps([
                {
                    "solution_type": "REALLOCATE",
                    "strategy_name": "调整资源分配比例",
                    "strategy_description": "降低项目B的资源占用",
                    "adjustments": {
                        "project_a": {"action": "KEEP", "allocation_percent": 60},
                        "project_b": {"action": "REDUCE", "allocation_percent": 40}
                    },
                    "pros": ["快速实施", "成本低"],
                    "cons": ["影响项目B进度"],
                    "risks": ["需要沟通"],
                    "affected_projects": [{"project_id": 20, "impact": "轻微延期"}],
                    "timeline_impact_days": 5,
                    "cost_impact": 0,
                    "quality_impact": "LOW",
                    "execution_steps": ["沟通", "调整", "确认"],
                    "estimated_duration_days": 2,
                    "feasibility_score": 85,
                    "impact_score": 25,
                    "cost_score": 10,
                    "risk_score": 20,
                    "efficiency_score": 80,
                    "ai_reasoning": "该方案通过降低项目B的资源占用..."
                },
                {
                    "solution_type": "RESCHEDULE",
                    "strategy_name": "重新安排时间",
                    "strategy_description": "调整项目B的时间",
                    "adjustments": {},
                    "pros": ["彻底解决冲突"],
                    "cons": ["需要协调"],
                    "risks": ["客户可能不同意"],
                    "affected_projects": [{"project_id": 20, "impact": "延期2周"}],
                    "timeline_impact_days": 14,
                    "cost_impact": 5000,
                    "quality_impact": "NONE",
                    "execution_steps": ["沟通客户", "调整计划"],
                    "estimated_duration_days": 7,
                    "feasibility_score": 70,
                    "impact_score": 40,
                    "cost_score": 30,
                    "risk_score": 35,
                    "efficiency_score": 65,
                    "ai_reasoning": "时间调整方案..."
                }
            ]),
            "tokens_used": 1000
        }
        
        # 执行
        suggestions = self.service.generate_scheduling_suggestions(
            conflict_id=1,
            max_suggestions=2,
        )
        
        # 验证
        self.assertEqual(len(suggestions), 2)
        
        # 第一个方案（推荐）
        sug1 = suggestions[0]
        self.assertEqual(sug1.solution_type, "REALLOCATE")
        self.assertEqual(sug1.rank_order, 1)
        self.assertTrue(sug1.is_recommended)
        self.assertEqual(sug1.feasibility_score, Decimal("85"))
        
        # 第二个方案
        sug2 = suggestions[1]
        self.assertEqual(sug2.solution_type, "RESCHEDULE")
        self.assertEqual(sug2.rank_order, 2)
        self.assertFalse(sug2.is_recommended)
        
        # 验证冲突更新
        self.assertTrue(conflict.has_ai_suggestion)
        self.assertEqual(conflict.suggested_solution_id, suggestions[0].id)
        self.assertEqual(conflict.status, "ANALYZING")

    def test_generate_scheduling_suggestions_not_found(self):
        """测试生成调度方案 - 冲突不存在"""
        # Mock查询返回None
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.generate_scheduling_suggestions(conflict_id=999)
        
        self.assertIn("not found", str(context.exception))

    def test_ai_generate_solutions_failure(self):
        """测试AI生成方案失败 - 返回默认方案"""
        conflict = MagicMock()
        conflict.id = 1
        conflict.resource_name = "张三"
        conflict.department_name = "研发部"
        conflict.project_a_name = "项目A"
        conflict.project_b_name = "项目B"
        conflict.project_b_id = 20
        conflict.allocation_a_percent = Decimal("60")
        conflict.allocation_b_percent = Decimal("50")
        conflict.start_date_a = date(2024, 1, 1)
        conflict.end_date_a = date(2024, 1, 20)
        conflict.start_date_b = date(2024, 1, 10)
        conflict.end_date_b = date(2024, 1, 30)
        conflict.overlap_start = date(2024, 1, 10)
        conflict.overlap_end = date(2024, 1, 20)
        conflict.overlap_days = 11
        conflict.over_allocation = Decimal("10")
        conflict.severity = "MEDIUM"
        
        # Mock AI抛出异常
        self.service.ai_client.generate_solution.side_effect = Exception("AI调用失败")
        
        # 执行
        suggestions = self.service._ai_generate_solutions(conflict, max_suggestions=3)
        
        # 验证返回默认方案
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        self.assertEqual(suggestions[0]["solution_type"], "REALLOCATE")

    def test_get_default_suggestions(self):
        """测试获取默认方案"""
        conflict = MagicMock()
        conflict.id = 1
        conflict.project_b_id = 20
        conflict.allocation_a_percent = Decimal("60")
        
        suggestions = self.service._get_default_suggestions(conflict)
        
        # 验证
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["solution_type"], "REALLOCATE")
        self.assertIn("adjustments", suggestions[0])

    # ========================================================================
    # 3. 资源需求预测测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_forecast_resource_demand_3month(self, mock_save):
        """测试资源需求预测 - 3个月"""
        # 准备项目数据
        project1 = MagicMock()
        project1.project_name = "项目1"
        project1.start_date = date.today()
        project1.end_date = date.today() + timedelta(days=60)
        project1.stage = "EXECUTION"
        
        project2 = MagicMock()
        project2.project_name = "项目2"
        project2.start_date = date.today() + timedelta(days=30)
        project2.end_date = date.today() + timedelta(days=120)
        project2.stage = "PLANNING"
        
        # Mock查询
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = [project1, project2]
        
        # Mock AI预测
        self.service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "predicted_demand": 15,
                "demand_gap": 3,
                "gap_severity": "SHORTAGE",
                "predicted_total_hours": 5400,
                "predicted_peak_hours": 240,
                "predicted_utilization": 85,
                "driving_projects": [{"project_id": 1, "impact": "高"}],
                "recommendations": ["招聘2名高级工程师"],
                "hiring_suggestion": {"role": "高级工程师", "count": 2, "timeline": "1个月内"},
                "estimated_cost": 150000,
                "risk_level": "MEDIUM",
                "ai_confidence": 0.78
            })
        }
        
        # 执行
        forecasts = self.service.forecast_resource_demand(
            forecast_period="3MONTH",
            resource_type="PERSON",
            skill_category="开发",
        )
        
        # 验证
        self.assertEqual(len(forecasts), 1)
        forecast = forecasts[0]
        self.assertEqual(forecast.forecast_period, "3MONTH")
        self.assertEqual(forecast.predicted_demand, 15)
        self.assertEqual(forecast.demand_gap, 3)
        self.assertEqual(forecast.gap_severity, "SHORTAGE")
        self.assertEqual(forecast.predicted_utilization, Decimal("85"))
        self.assertEqual(forecast.risk_level, "MEDIUM")

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_forecast_resource_demand_1year(self, mock_save):
        """测试资源需求预测 - 1年"""
        # Mock查询
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = []
        
        # Mock AI预测
        self.service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "predicted_demand": 20,
                "demand_gap": -2,
                "gap_severity": "SURPLUS",
                "predicted_utilization": 65,
                "ai_confidence": 0.65
            })
        }
        
        # 执行
        forecasts = self.service.forecast_resource_demand(
            forecast_period="1YEAR",
            resource_type="PERSON",
        )
        
        # 验证
        self.assertEqual(len(forecasts), 1)
        forecast = forecasts[0]
        self.assertEqual(forecast.forecast_period, "1YEAR")
        self.assertEqual(forecast.demand_gap, -2)
        self.assertEqual(forecast.gap_severity, "SURPLUS")

    def test_ai_forecast_demand_failure(self):
        """测试AI预测失败 - 返回默认值"""
        # Mock AI抛出异常
        self.service.ai_client.generate_solution.side_effect = Exception("AI调用失败")
        
        # 执行
        result = self.service._ai_forecast_demand(
            projects=[],
            forecast_period="3MONTH",
            resource_type="PERSON",
            skill_category=None,
        )
        
        # 验证返回默认值
        self.assertEqual(result["predicted_demand"], 10)
        self.assertEqual(result["demand_gap"], 0)
        self.assertEqual(result["gap_severity"], "BALANCED")
        self.assertEqual(result["ai_confidence"], 0.5)

    # ========================================================================
    # 4. 资源利用率分析测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_analyze_resource_utilization_normal(self, mock_save):
        """测试资源利用率分析 - 正常利用"""
        # 准备工时数据
        timesheet1 = MagicMock()
        timesheet1.hours = 8
        
        timesheet2 = MagicMock()
        timesheet2.hours = 7.5
        
        timesheet3 = MagicMock()
        timesheet3.hours = 8
        
        # Mock查询（3天，24小时工时）
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet1, timesheet2, timesheet3]
        
        # Mock AI洞察
        self.service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "key_insights": ["利用率健康", "工作负载适中"],
                "optimization_suggestions": ["保持当前节奏"],
                "reallocation_opportunities": []
            })
        }
        
        # 执行（7天周期）
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        analysis = self.service.analyze_resource_utilization(
            resource_id=1,
            start_date=start_date,
            end_date=end_date,
            analysis_period="WEEKLY",
        )
        
        # 验证
        self.assertEqual(analysis.resource_id, 1)
        self.assertEqual(analysis.period_days, 7)
        self.assertEqual(analysis.total_actual_hours, Decimal("23.5"))
        
        # 可用工时 = 7天 * 5/7 * 8小时 = 40小时
        # 利用率 = 23.5 / 40 * 100 = 58.75%
        self.assertGreater(analysis.utilization_rate, 50)
        self.assertLess(analysis.utilization_rate, 70)
        self.assertEqual(analysis.utilization_status, "NORMAL")
        self.assertFalse(analysis.is_idle_resource)
        self.assertFalse(analysis.is_overloaded)

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_analyze_resource_utilization_underutilized(self, mock_save):
        """测试资源利用率分析 - 利用不足"""
        # Mock查询（少量工时）
        timesheet = MagicMock()
        timesheet.hours = 2
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = [timesheet]
        
        # Mock AI洞察
        self.service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "key_insights": ["利用率偏低"],
                "optimization_suggestions": ["考虑增加任务分配"]
            })
        }
        
        # 执行
        analysis = self.service.analyze_resource_utilization(
            resource_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        
        # 验证
        self.assertEqual(analysis.utilization_status, "UNDERUTILIZED")
        self.assertTrue(analysis.is_idle_resource)

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_analyze_resource_utilization_overloaded(self, mock_save):
        """测试资源利用率分析 - 超负荷"""
        # Mock查询（大量工时）
        timesheets = [MagicMock(hours=12) for _ in range(7)]
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = timesheets
        
        # Mock AI洞察
        self.service.ai_client.generate_solution.side_effect = Exception("AI调用失败")
        
        # 执行
        analysis = self.service.analyze_resource_utilization(
            resource_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        
        # 验证：7天*12小时 = 84小时，可用40小时，利用率210%
        self.assertGreater(analysis.utilization_rate, 100)
        self.assertEqual(analysis.utilization_status, "CRITICAL")
        self.assertTrue(analysis.is_overloaded)

    def test_determine_utilization_status_ranges(self):
        """测试利用率状态判定"""
        # UNDERUTILIZED: < 50%
        status = self.service._determine_utilization_status(Decimal("30"))
        self.assertEqual(status, "UNDERUTILIZED")
        
        # NORMAL: 50-90%
        status = self.service._determine_utilization_status(Decimal("75"))
        self.assertEqual(status, "NORMAL")
        
        # OVERUTILIZED: 90-110%
        status = self.service._determine_utilization_status(Decimal("95"))
        self.assertEqual(status, "OVERUTILIZED")
        
        # CRITICAL: > 110%
        status = self.service._determine_utilization_status(Decimal("120"))
        self.assertEqual(status, "CRITICAL")
        
        # 边界值测试
        status = self.service._determine_utilization_status(Decimal("50"))
        self.assertEqual(status, "NORMAL")
        
        status = self.service._determine_utilization_status(Decimal("90"))
        self.assertEqual(status, "NORMAL")
        
        status = self.service._determine_utilization_status(Decimal("110"))
        self.assertEqual(status, "OVERUTILIZED")

    def test_ai_analyze_utilization_failure(self):
        """测试AI分析失败 - 返回默认值"""
        # Mock AI抛出异常
        self.service.ai_client.generate_solution.side_effect = Exception("AI调用失败")
        
        # 执行
        result = self.service._ai_analyze_utilization(
            resource_id=1,
            utilization_rate=Decimal("75"),
            total_hours=Decimal("60"),
            period_days=7,
        )
        
        # 验证返回默认值
        self.assertIn("key_insights", result)
        self.assertIn("optimization_suggestions", result)

    # ========================================================================
    # 5. 边界情况和异常处理测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_detect_conflicts_empty_allocations(self, mock_save):
        """测试冲突检测 - 无分配记录"""
        # Mock查询返回空列表
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        
        conflicts = self.service.detect_resource_conflicts(resource_id=1)
        
        # 验证
        self.assertEqual(len(conflicts), 0)

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_detect_conflicts_single_allocation(self, mock_save):
        """测试冲突检测 - 单个分配（无冲突）"""
        alloc = MagicMock()
        alloc.resource_id = 1
        alloc.allocation_percent = 80
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.filter.return_value.all.return_value = [alloc]
        
        conflicts = self.service.detect_resource_conflicts(resource_id=1)
        
        # 验证
        self.assertEqual(len(conflicts), 0)

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_detect_conflicts_under_100_percent(self, mock_save):
        """测试冲突检测 - 重叠但未超100%（无冲突）"""
        alloc1 = MagicMock()
        alloc1.resource_id = 1
        alloc1.allocation_percent = Decimal("40")
        alloc1.start_date = date(2024, 1, 1)
        alloc1.end_date = date(2024, 1, 20)
        
        alloc2 = MagicMock()
        alloc2.resource_id = 1
        alloc2.allocation_percent = Decimal("30")
        alloc2.start_date = date(2024, 1, 10)
        alloc2.end_date = date(2024, 1, 30)
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.filter.return_value.all.return_value = [alloc1, alloc2]
        
        conflicts = self.service.detect_resource_conflicts(resource_id=1)
        
        # 验证：总分配70%，不算冲突
        self.assertEqual(len(conflicts), 0)

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_analyze_utilization_zero_hours(self, mock_save):
        """测试利用率分析 - 零工时"""
        # Mock查询返回空
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = []
        
        # Mock AI
        self.service.ai_client.generate_solution.return_value = {
            "content": "{}"
        }
        
        analysis = self.service.analyze_resource_utilization(
            resource_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        
        # 验证
        self.assertEqual(analysis.total_actual_hours, Decimal("0"))
        self.assertEqual(analysis.utilization_rate, 0)
        self.assertTrue(analysis.is_idle_resource)

    def test_create_forecast_record_minimal_data(self):
        """测试创建预测记录 - 最小数据"""
        with patch('app.services.resource_scheduling_ai_service.save_obj'):
            forecast = self.service._create_forecast_record(
                forecast_start=date.today(),
                forecast_end=date.today() + timedelta(days=90),
                forecast_period="3MONTH",
                resource_type="PERSON",
                skill_category=None,
                ai_forecast={},  # 空预测数据
            )
            
            # 验证使用默认值
            self.assertEqual(forecast.predicted_demand, 10)
            self.assertEqual(forecast.demand_gap, 0)

    # ========================================================================
    # 6. 综合场景测试
    # ========================================================================

    @patch('app.services.resource_scheduling_ai_service.save_obj')
    def test_full_workflow_detect_and_suggest(self, mock_save):
        """测试完整工作流 - 检测冲突 + 生成方案"""
        # Step 1: 检测冲突
        alloc1 = MagicMock()
        alloc1.id = 101
        alloc1.resource_id = 1
        alloc1.resource_name = "测试人员"
        alloc1.resource_dept = "研发部"
        alloc1.project_id = 10
        alloc1.allocation_percent = Decimal("70")
        alloc1.start_date = date(2024, 1, 1)
        alloc1.end_date = date(2024, 1, 31)
        alloc1.planned_hours = Decimal("120")
        
        alloc2 = MagicMock()
        alloc2.id = 102
        alloc2.resource_id = 1
        alloc2.resource_name = "测试人员"
        alloc2.resource_dept = "研发部"
        alloc2.project_id = 20
        alloc2.allocation_percent = Decimal("60")
        alloc2.start_date = date(2024, 1, 15)
        alloc2.end_date = date(2024, 2, 15)
        alloc2.planned_hours = Decimal("100")
        
        project_a = MagicMock()
        project_a.project_code = "PRJ001"
        project_a.project_name = "项目A"
        
        project_b = MagicMock()
        project_b.project_code = "PRJ002"
        project_b.project_name = "项目B"
        
        # Mock第一次查询：分配
        mock_alloc_query = MagicMock()
        mock_alloc_query.filter.return_value.filter.return_value.all.return_value = [alloc1, alloc2]
        
        # 设置side_effect依次返回：分配查询、项目A、项目B、冲突查询、冲突查询
        self.db.query.side_effect = [
            mock_alloc_query,  # detect时的分配查询
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=project_a)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=project_b)))),
        ]
        
        # Mock AI评估
        self.service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "risk_factors": ["资源超负荷"],
                "impact_analysis": {"schedule_impact": "延期"},
                "confidence": 0.8
            })
        }
        
        conflicts = self.service.detect_resource_conflicts(resource_id=1)
        
        # 验证冲突检测结果
        self.assertGreater(len(conflicts), 0)


if __name__ == "__main__":
    unittest.main()
