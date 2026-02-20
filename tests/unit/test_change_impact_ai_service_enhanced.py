# -*- coding: utf-8 -*-
"""
变更影响AI分析服务增强单元测试
"""

import json
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import (
    ChangeImpactAnalysis,
    ChangeRequest,
    Project,
    ProjectMilestone,
    Task,
    TaskDependency,
)
from app.models.enums.workflow import ChangeTypeEnum, ChangeSourceEnum
from app.services.change_impact_ai_service import ChangeImpactAIService


class TestChangeImpactAIServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        service = ChangeImpactAIService(db=mock_db)
        self.assertEqual(service.db, mock_db)

    def test_init_db_attribute_exists(self):
        """测试db属性存在"""
        mock_db = MagicMock()
        service = ChangeImpactAIService(db=mock_db)
        self.assertTrue(hasattr(service, 'db'))


class TestAnalyzeChangeImpact(unittest.TestCase):
    """测试主分析方法"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)
        
        # 模拟变更请求
        self.mock_change = MagicMock(spec=ChangeRequest)
        self.mock_change.id = 1
        self.mock_change.project_id = 100
        self.mock_change.change_code = "CHG-001"
        self.mock_change.title = "测试变更"
        self.mock_change.description = "测试描述"
        self.mock_change.change_type = ChangeTypeEnum.REQUIREMENT
        self.mock_change.change_source = ChangeSourceEnum.CLIENT
        self.mock_change.time_impact = 5
        self.mock_change.cost_impact = Decimal("10000.00")
        
        # 模拟项目
        self.mock_project = MagicMock(spec=Project)
        self.mock_project.id = 100
        self.mock_project.project_code = "PROJ-001"
        self.mock_project.project_name = "测试项目"
        self.mock_project.status = "IN_PROGRESS"
        self.mock_project.budget_amount = Decimal("100000.00")
        self.mock_project.actual_cost = Decimal("50000.00")
        self.mock_project.plan_start = datetime(2024, 1, 1)
        self.mock_project.plan_end = datetime(2024, 12, 31)

    @pytest.mark.asyncio
    async def test_analyze_change_impact_success(self):
        """测试成功分析变更影响"""
        # 设置查询返回值
        change_query = MagicMock()
        change_query.filter.return_value.first.return_value = self.mock_change
        
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = self.mock_project
        
        self.mock_db.query.side_effect = [change_query, project_query, MagicMock(), MagicMock(), MagicMock()]
        
        # Mock所有分析方法
        with patch.object(self.service, '_gather_analysis_context', return_value={}), \
             patch.object(self.service, '_analyze_schedule_impact', new_callable=AsyncMock, return_value={
                 "level": "MEDIUM", "delay_days": 5, "affected_tasks_count": 3,
                 "critical_path_affected": False, "milestone_affected": True,
                 "description": "测试", "affected_tasks": [], "affected_milestones": []
             }), \
             patch.object(self.service, '_analyze_cost_impact', new_callable=AsyncMock, return_value={
                 "level": "LOW", "amount": 10000, "percentage": 10.0,
                 "breakdown": {}, "description": "测试", "budget_exceeded": False, "contingency_required": 12000
             }), \
             patch.object(self.service, '_analyze_quality_impact', new_callable=AsyncMock, return_value={
                 "level": "MEDIUM", "risk_areas": [], "testing_impact": "测试",
                 "acceptance_impact": "测试", "mitigation_required": True, "description": "测试"
             }), \
             patch.object(self.service, '_analyze_resource_impact', new_callable=AsyncMock, return_value={
                 "level": "LOW", "additional_required": [], "reallocation_needed": False,
                 "conflict_detected": False, "description": "测试", "affected_allocations": []
             }), \
             patch.object(self.service, '_identify_chain_reactions', return_value={
                 "detected": False, "depth": 0, "affected_projects": [],
                 "dependency_tree": {}, "critical_dependencies": []
             }), \
             patch.object(self.service, '_calculate_overall_risk', return_value={
                 "score": 45.5, "level": "MEDIUM", "recommended_action": "APPROVE",
                 "factors": [], "summary": "测试摘要", "confidence": 85
             }):
            
            result = await self.service.analyze_change_impact(
                change_request_id=1, user_id=1
            )
            
            self.assertIsInstance(result, ChangeImpactAnalysis)

    @pytest.mark.asyncio
    async def test_analyze_change_impact_change_not_found(self):
        """测试变更请求不存在"""
        change_query = MagicMock()
        change_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = change_query
        
        with self.assertRaises(ValueError) as context:
            await self.service.analyze_change_impact(
                change_request_id=999, user_id=1
            )
        self.assertIn("不存在", str(context.exception))

    @pytest.mark.asyncio
    async def test_analyze_change_impact_project_not_found(self):
        """测试项目不存在"""
        change_query = MagicMock()
        change_query.filter.return_value.first.return_value = self.mock_change
        
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = None
        
        self.mock_db.query.side_effect = [change_query, project_query]
        
        with self.assertRaises(ValueError) as context:
            await self.service.analyze_change_impact(
                change_request_id=1, user_id=1
            )
        self.assertIn("不存在", str(context.exception))

    @pytest.mark.asyncio
    async def test_analyze_change_impact_exception_handling(self):
        """测试分析过程中的异常处理"""
        change_query = MagicMock()
        change_query.filter.return_value.first.return_value = self.mock_change
        
        project_query = MagicMock()
        project_query.filter.return_value.first.return_value = self.mock_project
        
        self.mock_db.query.side_effect = [change_query, project_query, MagicMock()]
        
        with patch.object(self.service, '_gather_analysis_context', side_effect=Exception("测试异常")):
            with self.assertRaises(Exception):
                await self.service.analyze_change_impact(
                    change_request_id=1, user_id=1
                )


class TestGatherAnalysisContext(unittest.TestCase):
    """测试收集分析上下文"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)
        
        self.mock_change = MagicMock(spec=ChangeRequest)
        self.mock_change.id = 1
        self.mock_change.change_code = "CHG-001"
        self.mock_change.title = "测试变更"
        self.mock_change.description = "描述"
        self.mock_change.change_type = ChangeTypeEnum.REQUIREMENT
        self.mock_change.change_source = ChangeSourceEnum.CLIENT
        self.mock_change.time_impact = 5
        self.mock_change.cost_impact = Decimal("10000")
        
        self.mock_project = MagicMock(spec=Project)
        self.mock_project.id = 100
        self.mock_project.project_code = "PROJ-001"
        self.mock_project.project_name = "测试项目"
        self.mock_project.status = "IN_PROGRESS"
        self.mock_project.budget_amount = Decimal("100000")
        self.mock_project.plan_start = datetime(2024, 1, 1)
        self.mock_project.plan_end = datetime(2024, 12, 31)

    def test_gather_context_with_tasks(self):
        """测试收集包含任务的上下文"""
        mock_task = MagicMock(spec=Task)
        mock_task.id = 1
        mock_task.task_name = "任务1"
        mock_task.status = "IN_PROGRESS"
        mock_task.stage = "开发"
        mock_task.plan_start = datetime(2024, 2, 1)
        mock_task.plan_end = datetime(2024, 3, 1)
        mock_task.progress_percent = 50
        
        task_query = MagicMock()
        task_query.filter.return_value.all.return_value = [mock_task]
        
        dep_query = MagicMock()
        dep_query.filter.return_value.all.return_value = []
        
        milestone_query = MagicMock()
        milestone_query.filter.return_value.all.return_value = []
        
        self.mock_db.query.side_effect = [task_query, dep_query, milestone_query]
        
        result = self.service._gather_analysis_context(self.mock_change, self.mock_project)
        
        self.assertIn("change", result)
        self.assertIn("project", result)
        self.assertIn("tasks", result)
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["name"], "任务1")

    def test_gather_context_with_dependencies(self):
        """测试收集包含依赖关系的上下文"""
        mock_task = MagicMock(spec=Task)
        mock_task.id = 1
        
        mock_dep = MagicMock(spec=TaskDependency)
        mock_dep.task_id = 1
        mock_dep.depends_on_task_id = 2
        mock_dep.dependency_type = "FS"
        mock_dep.lag_days = 0
        
        task_query = MagicMock()
        task_query.filter.return_value.all.return_value = [mock_task]
        
        dep_query = MagicMock()
        dep_query.filter.return_value.all.return_value = [mock_dep]
        
        milestone_query = MagicMock()
        milestone_query.filter.return_value.all.return_value = []
        
        self.mock_db.query.side_effect = [task_query, dep_query, milestone_query]
        
        result = self.service._gather_analysis_context(self.mock_change, self.mock_project)
        
        self.assertIn("dependencies", result)
        self.assertEqual(len(result["dependencies"]), 1)
        self.assertEqual(result["dependencies"][0]["type"], "FS")

    def test_gather_context_with_milestones(self):
        """测试收集包含里程碑的上下文"""
        mock_milestone = MagicMock(spec=ProjectMilestone)
        mock_milestone.id = 1
        mock_milestone.milestone_name = "里程碑1"
        mock_milestone.plan_date = datetime(2024, 6, 1)
        mock_milestone.status = "PENDING"
        
        task_query = MagicMock()
        task_query.filter.return_value.all.return_value = []
        
        dep_query = MagicMock()
        dep_query.filter.return_value.all.return_value = []
        
        milestone_query = MagicMock()
        milestone_query.filter.return_value.all.return_value = [mock_milestone]
        
        self.mock_db.query.side_effect = [task_query, dep_query, milestone_query]
        
        result = self.service._gather_analysis_context(self.mock_change, self.mock_project)
        
        self.assertIn("milestones", result)
        self.assertEqual(len(result["milestones"]), 1)
        self.assertEqual(result["milestones"][0]["name"], "里程碑1")

    def test_gather_context_empty_project(self):
        """测试空项目的上下文收集"""
        task_query = MagicMock()
        task_query.filter.return_value.all.return_value = []
        
        dep_query = MagicMock()
        dep_query.filter.return_value.all.return_value = []
        
        milestone_query = MagicMock()
        milestone_query.filter.return_value.all.return_value = []
        
        self.mock_db.query.side_effect = [task_query, dep_query, milestone_query]
        
        result = self.service._gather_analysis_context(self.mock_change, self.mock_project)
        
        self.assertEqual(len(result["tasks"]), 0)
        self.assertEqual(len(result["dependencies"]), 0)
        self.assertEqual(len(result["milestones"]), 0)


class TestAnalyzeScheduleImpact(unittest.TestCase):
    """测试进度影响分析"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)
        
        self.mock_change = MagicMock(spec=ChangeRequest)
        self.mock_change.title = "测试变更"
        self.mock_change.description = "描述"
        self.mock_change.change_type = ChangeTypeEnum.REQUIREMENT
        self.mock_change.time_impact = 5
        
        self.mock_project = MagicMock(spec=Project)
        self.mock_project.project_name = "测试项目"
        self.mock_project.status = "IN_PROGRESS"
        
        self.context = {
            "change": {"time_impact": 5},
            "project": {"start_date": "2024-01-01", "end_date": "2024-12-31"},
            "tasks": [
                {"id": 1, "status": "IN_PROGRESS", "name": "任务1"},
                {"id": 2, "status": "TODO", "name": "任务2"}
            ],
            "milestones": []
        }

    @pytest.mark.asyncio
    async def test_schedule_impact_with_ai_response(self):
        """测试使用AI响应分析进度影响"""
        ai_response = json.dumps({
            "level": "HIGH",
            "delay_days": 5,
            "affected_tasks_count": 2,
            "critical_path_affected": True,
            "milestone_affected": False,
            "description": "严重延期"
        })
        
        with patch('app.services.change_impact_ai_service.call_glm_api', new_callable=AsyncMock, return_value=ai_response), \
             patch.object(self.service, '_find_affected_tasks', return_value=[]), \
             patch.object(self.service, '_find_affected_milestones', return_value=[]):
            
            result = await self.service._analyze_schedule_impact(
                self.mock_change, self.mock_project, self.context
            )
            
            self.assertEqual(result["level"], "HIGH")
            self.assertEqual(result["delay_days"], 5)

    @pytest.mark.asyncio
    async def test_schedule_impact_ai_failure(self):
        """测试AI调用失败时的降级处理"""
        with patch('app.services.change_impact_ai_service.call_glm_api', new_callable=AsyncMock, side_effect=Exception("AI错误")):
            
            result = await self.service._analyze_schedule_impact(
                self.mock_change, self.mock_project, self.context
            )
            
            self.assertEqual(result["level"], "MEDIUM")
            self.assertIn("异常", result["description"])

    @pytest.mark.asyncio
    async def test_schedule_impact_no_time_impact(self):
        """测试没有时间影响的情况"""
        self.mock_change.time_impact = 0
        self.context["change"]["time_impact"] = 0
        
        with patch('app.services.change_impact_ai_service.call_glm_api', new_callable=AsyncMock, return_value="{}"):
            
            result = await self.service._analyze_schedule_impact(
                self.mock_change, self.mock_project, self.context
            )
            
            self.assertEqual(result["delay_days"], 0)


class TestAnalyzeCostImpact(unittest.TestCase):
    """测试成本影响分析"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)
        
        self.mock_change = MagicMock(spec=ChangeRequest)
        self.mock_project = MagicMock(spec=Project)
        self.context = {}

    @pytest.mark.asyncio
    async def test_cost_impact_critical_level(self):
        """测试成本影响达到CRITICAL级别"""
        self.mock_change.cost_impact = Decimal("25000")
        self.mock_project.budget_amount = Decimal("100000")
        self.mock_project.actual_cost = Decimal("50000")
        
        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "CRITICAL")
        self.assertEqual(result["amount"], 25000)
        self.assertEqual(result["percentage"], 25.0)

    @pytest.mark.asyncio
    async def test_cost_impact_high_level(self):
        """测试成本影响HIGH级别"""
        self.mock_change.cost_impact = Decimal("15000")
        self.mock_project.budget_amount = Decimal("100000")
        self.mock_project.actual_cost = Decimal("50000")
        
        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "HIGH")
        self.assertGreater(result["percentage"], 10)

    @pytest.mark.asyncio
    async def test_cost_impact_medium_level(self):
        """测试成本影响MEDIUM级别"""
        self.mock_change.cost_impact = Decimal("7000")
        self.mock_project.budget_amount = Decimal("100000")
        self.mock_project.actual_cost = Decimal("50000")
        
        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "MEDIUM")

    @pytest.mark.asyncio
    async def test_cost_impact_low_level(self):
        """测试成本影响LOW级别"""
        self.mock_change.cost_impact = Decimal("1000")
        self.mock_project.budget_amount = Decimal("100000")
        self.mock_project.actual_cost = Decimal("50000")
        
        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "LOW")

    @pytest.mark.asyncio
    async def test_cost_impact_none_level(self):
        """测试无成本影响"""
        self.mock_change.cost_impact = None
        self.mock_project.budget_amount = Decimal("100000")
        
        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "NONE")
        self.assertEqual(result["amount"], 0)

    @pytest.mark.asyncio
    async def test_cost_impact_budget_exceeded(self):
        """测试预算超支检测"""
        self.mock_change.cost_impact = Decimal("60000")
        self.mock_project.budget_amount = Decimal("100000")
        self.mock_project.actual_cost = Decimal("50000")
        
        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertTrue(result["budget_exceeded"])

    @pytest.mark.asyncio
    async def test_cost_impact_breakdown(self):
        """测试成本分解"""
        self.mock_change.cost_impact = Decimal("10000")
        self.mock_project.budget_amount = Decimal("100000")
        
        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertIn("breakdown", result)
        self.assertIn("labor", result["breakdown"])
        self.assertIn("material", result["breakdown"])


class TestAnalyzeQualityImpact(unittest.TestCase):
    """测试质量影响分析"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)
        
        self.mock_change = MagicMock(spec=ChangeRequest)
        self.mock_project = MagicMock(spec=Project)
        self.context = {}

    @pytest.mark.asyncio
    async def test_quality_impact_requirement_change(self):
        """测试需求变更的质量影响"""
        self.mock_change.change_type = ChangeTypeEnum.REQUIREMENT
        
        result = await self.service._analyze_quality_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "MEDIUM")
        self.assertTrue(result["mitigation_required"])
        self.assertGreater(len(result["risk_areas"]), 0)

    @pytest.mark.asyncio
    async def test_quality_impact_technical_change(self):
        """测试技术变更的质量影响"""
        self.mock_change.change_type = ChangeTypeEnum.TECHNICAL
        
        result = await self.service._analyze_quality_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "HIGH")
        self.assertTrue(result["mitigation_required"])

    @pytest.mark.asyncio
    async def test_quality_impact_other_change(self):
        """测试其他类型变更的质量影响"""
        self.mock_change.change_type = ChangeTypeEnum.OTHER
        
        result = await self.service._analyze_quality_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "LOW")


class TestAnalyzeResourceImpact(unittest.TestCase):
    """测试资源影响分析"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)
        
        self.mock_change = MagicMock(spec=ChangeRequest)
        self.mock_project = MagicMock(spec=Project)
        self.context = {}

    @pytest.mark.asyncio
    async def test_resource_impact_high_time_cost(self):
        """测试高时间和成本影响的资源需求"""
        self.mock_change.time_impact = 25
        self.mock_change.cost_impact = Decimal("150000")
        
        result = await self.service._analyze_resource_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "HIGH")
        self.assertTrue(result["conflict_detected"])

    @pytest.mark.asyncio
    async def test_resource_impact_medium_impact(self):
        """测试中等影响的资源需求"""
        self.mock_change.time_impact = 15
        self.mock_change.cost_impact = Decimal("60000")
        
        result = await self.service._analyze_resource_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "MEDIUM")
        self.assertTrue(result["reallocation_needed"])
        self.assertGreater(len(result["additional_required"]), 0)

    @pytest.mark.asyncio
    async def test_resource_impact_low_impact(self):
        """测试低影响的资源需求"""
        self.mock_change.time_impact = 5
        self.mock_change.cost_impact = Decimal("5000")
        
        result = await self.service._analyze_resource_impact(
            self.mock_change, self.mock_project, self.context
        )
        
        self.assertEqual(result["level"], "NONE")


class TestIdentifyChainReactions(unittest.TestCase):
    """测试连锁反应识别"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)
        
        self.mock_change = MagicMock(spec=ChangeRequest)
        self.mock_project = MagicMock(spec=Project)

    def test_chain_reaction_no_dependencies(self):
        """测试无依赖关系的情况"""
        context = {
            "dependencies": [],
            "tasks": []
        }
        
        result = self.service._identify_chain_reactions(
            self.mock_change, self.mock_project, context
        )
        
        self.assertFalse(result["detected"])
        self.assertEqual(result["depth"], 0)

    def test_chain_reaction_with_dependencies(self):
        """测试有依赖关系的情况"""
        context = {
            "dependencies": [
                {"task_id": 2, "depends_on": 1, "type": "FS"},
                {"task_id": 3, "depends_on": 2, "type": "FS"}
            ],
            "tasks": [
                {"id": 1, "status": "TODO"},
                {"id": 2, "status": "TODO"},
                {"id": 3, "status": "TODO"}
            ]
        }
        
        result = self.service._identify_chain_reactions(
            self.mock_change, self.mock_project, context
        )
        
        self.assertTrue(result["detected"])
        self.assertGreater(result["depth"], 1)

    def test_chain_reaction_critical_dependencies(self):
        """测试关键依赖识别"""
        context = {
            "dependencies": [
                {"task_id": 2, "depends_on": 1, "type": "FS"},
                {"task_id": 3, "depends_on": 2, "type": "SS"}
            ],
            "tasks": []
        }
        
        result = self.service._identify_chain_reactions(
            self.mock_change, self.mock_project, context
        )
        
        self.assertGreater(len(result["critical_dependencies"]), 0)


class TestCalculateDependencyDepth(unittest.TestCase):
    """测试依赖深度计算"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)

    def test_dependency_depth_no_dependencies(self):
        """测试无依赖的深度"""
        dep_graph = {}
        depth = self.service._calculate_dependency_depth(1, dep_graph)
        self.assertEqual(depth, 1)

    def test_dependency_depth_single_level(self):
        """测试单层依赖"""
        dep_graph = {1: [2]}
        depth = self.service._calculate_dependency_depth(1, dep_graph)
        self.assertEqual(depth, 2)

    def test_dependency_depth_multi_level(self):
        """测试多层依赖"""
        dep_graph = {
            1: [2],
            2: [3],
            3: [4]
        }
        depth = self.service._calculate_dependency_depth(1, dep_graph)
        self.assertEqual(depth, 4)

    def test_dependency_depth_circular_reference(self):
        """测试循环依赖"""
        dep_graph = {
            1: [2],
            2: [1]
        }
        depth = self.service._calculate_dependency_depth(1, dep_graph)
        self.assertGreater(depth, 0)


class TestCalculateOverallRisk(unittest.TestCase):
    """测试综合风险计算"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)

    def test_overall_risk_critical(self):
        """测试CRITICAL风险级别"""
        result = self.service._calculate_overall_risk(
            schedule_impact={"level": "CRITICAL", "delay_days": 30},
            cost_impact={"level": "HIGH", "amount": 50000},
            quality_impact={"level": "HIGH", "mitigation_required": True},
            resource_impact={"level": "MEDIUM"},
            chain_reaction={"detected": True}
        )
        
        self.assertEqual(result["level"], "CRITICAL")
        self.assertEqual(result["recommended_action"], "ESCALATE")
        self.assertGreaterEqual(result["score"], 75)

    def test_overall_risk_high(self):
        """测试HIGH风险级别"""
        result = self.service._calculate_overall_risk(
            schedule_impact={"level": "HIGH", "delay_days": 15},
            cost_impact={"level": "MEDIUM", "amount": 20000},
            quality_impact={"level": "MEDIUM", "mitigation_required": True},
            resource_impact={"level": "LOW"},
            chain_reaction={"detected": False}
        )
        
        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["recommended_action"], "MODIFY")

    def test_overall_risk_medium(self):
        """测试MEDIUM风险级别"""
        result = self.service._calculate_overall_risk(
            schedule_impact={"level": "MEDIUM", "delay_days": 5},
            cost_impact={"level": "LOW", "amount": 5000},
            quality_impact={"level": "LOW", "mitigation_required": False},
            resource_impact={"level": "NONE"},
            chain_reaction={"detected": False}
        )
        
        self.assertEqual(result["level"], "MEDIUM")
        self.assertEqual(result["recommended_action"], "APPROVE")

    def test_overall_risk_low(self):
        """测试LOW风险级别"""
        result = self.service._calculate_overall_risk(
            schedule_impact={"level": "LOW", "delay_days": 1},
            cost_impact={"level": "NONE", "amount": 0},
            quality_impact={"level": "NONE", "mitigation_required": False},
            resource_impact={"level": "NONE"},
            chain_reaction={"detected": False}
        )
        
        self.assertEqual(result["level"], "LOW")
        self.assertLess(result["score"], 25)

    def test_overall_risk_factors(self):
        """测试风险因素列表"""
        result = self.service._calculate_overall_risk(
            schedule_impact={"level": "MEDIUM", "delay_days": 5},
            cost_impact={"level": "LOW", "amount": 5000},
            quality_impact={"level": "NONE", "mitigation_required": False},
            resource_impact={"level": "NONE"},
            chain_reaction={"detected": False}
        )
        
        self.assertIn("factors", result)
        self.assertGreater(len(result["factors"]), 0)


class TestFindAffectedTasks(unittest.TestCase):
    """测试查找受影响任务"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)

    def test_find_affected_tasks_in_progress(self):
        """测试查找进行中的受影响任务"""
        context = {
            "change": {"time_impact": 10},
            "tasks": [
                {"id": 1, "name": "任务1", "status": "IN_PROGRESS"},
                {"id": 2, "name": "任务2", "status": "TODO"},
                {"id": 3, "name": "任务3", "status": "COMPLETED"}
            ]
        }
        
        result = self.service._find_affected_tasks(context)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(t["task_id"] in [1, 2] for t in result))

    def test_find_affected_tasks_max_limit(self):
        """测试受影响任务数量限制"""
        tasks = [{"id": i, "name": f"任务{i}", "status": "TODO"} for i in range(20)]
        context = {
            "change": {"time_impact": 5},
            "tasks": tasks
        }
        
        result = self.service._find_affected_tasks(context)
        
        self.assertLessEqual(len(result), 10)


class TestFindAffectedMilestones(unittest.TestCase):
    """测试查找受影响里程碑"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)

    def test_find_affected_milestones_with_delay(self):
        """测试查找延期影响的里程碑"""
        context = {
            "milestones": [
                {
                    "id": 1,
                    "name": "里程碑1",
                    "plan_date": datetime(2024, 6, 1).isoformat()
                },
                {
                    "id": 2,
                    "name": "里程碑2",
                    "plan_date": datetime(2024, 12, 1).isoformat()
                }
            ]
        }
        
        result = self.service._find_affected_milestones(context, delay_days=10)
        
        self.assertEqual(len(result), 2)
        self.assertIn("new_date", result[0])

    def test_find_affected_milestones_no_milestones(self):
        """测试无里程碑情况"""
        context = {"milestones": []}
        
        result = self.service._find_affected_milestones(context, delay_days=5)
        
        self.assertEqual(len(result), 0)


class TestParseAIResponse(unittest.TestCase):
    """测试AI响应解析"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(db=self.mock_db)

    def test_parse_valid_json(self):
        """测试解析有效JSON"""
        response = '{"level": "HIGH", "score": 80}'
        default = {"level": "LOW", "score": 0}
        
        result = self.service._parse_ai_response(response, default)
        
        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["score"], 80)

    def test_parse_json_with_extra_text(self):
        """测试解析包含额外文本的JSON"""
        response = '这是一些文本 {"level": "MEDIUM"} 还有更多文本'
        default = {"level": "LOW"}
        
        result = self.service._parse_ai_response(response, default)
        
        self.assertEqual(result["level"], "MEDIUM")

    def test_parse_invalid_json(self):
        """测试解析无效JSON"""
        response = '这不是有效的JSON'
        default = {"level": "LOW", "score": 0}
        
        result = self.service._parse_ai_response(response, default)
        
        self.assertEqual(result, default)

    def test_parse_partial_json(self):
        """测试解析部分JSON（使用默认值补充）"""
        response = '{"level": "HIGH"}'
        default = {"level": "LOW", "score": 0, "description": "默认描述"}
        
        result = self.service._parse_ai_response(response, default)
        
        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["description"], "默认描述")


if __name__ == '__main__':
    unittest.main()
