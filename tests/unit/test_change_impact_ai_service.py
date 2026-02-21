# -*- coding: utf-8 -*-
"""
变更影响AI分析服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作，call_glm_api）
2. 让业务逻辑真正执行（不要mock业务方法）
3. 覆盖主要方法和边界情况
4. 所有测试必须通过

目标：覆盖率 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.change_impact_ai_service import ChangeImpactAIService
from app.models import (
    ChangeRequest,
    Project,
    Task,
    TaskDependency,
    ProjectMilestone,
    ChangeImpactAnalysis,
)


class TestChangeImpactAIServiceCore(unittest.IsolatedAsyncioTestCase):
    """测试核心业务逻辑"""

    async def asyncSetUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(self.mock_db)

        # 创建测试数据
        self.mock_change = self._create_mock_change()
        self.mock_project = self._create_mock_project()
        self.mock_tasks = self._create_mock_tasks()
        self.mock_dependencies = self._create_mock_dependencies()
        self.mock_milestones = self._create_mock_milestones()

    def _create_mock_change(self):
        """创建模拟变更请求"""
        change = MagicMock(spec=ChangeRequest)
        change.id = 1
        change.project_id = 100
        change.change_code = "CR-2024-001"
        change.title = "增加数据导出功能"
        change.description = "客户要求增加数据导出功能"
        change.change_type = MagicMock(value="REQUIREMENT")
        change.change_source = MagicMock(value="CUSTOMER")
        change.time_impact = 5
        change.cost_impact = Decimal("50000")
        return change

    def _create_mock_project(self):
        """创建模拟项目"""
        project = MagicMock(spec=Project)
        project.id = 100
        project.project_code = "PRJ-2024-001"
        project.project_name = "企业管理系统"
        project.status = "IN_PROGRESS"
        project.budget_amount = Decimal("500000")
        project.actual_cost = Decimal("200000")
        project.plan_start = datetime(2024, 1, 1)
        project.plan_end = datetime(2024, 6, 30)
        return project

    def _create_mock_tasks(self):
        """创建模拟任务列表"""
        tasks = []
        for i in range(5):
            task = MagicMock(spec=Task)
            task.id = i + 1
            task.project_id = 100
            task.task_name = f"任务{i+1}"
            task.status = "IN_PROGRESS" if i < 2 else "TODO"
            task.stage = "DEVELOPMENT"
            task.plan_start = datetime(2024, 1, 1) + timedelta(days=i * 10)
            task.plan_end = datetime(2024, 1, 10) + timedelta(days=i * 10)
            task.progress_percent = 50 if i < 2 else 0
            tasks.append(task)
        return tasks

    def _create_mock_dependencies(self):
        """创建模拟任务依赖"""
        deps = []
        dep1 = MagicMock(spec=TaskDependency)
        dep1.task_id = 2
        dep1.depends_on_task_id = 1
        dep1.dependency_type = "FS"
        dep1.lag_days = 0
        deps.append(dep1)

        dep2 = MagicMock(spec=TaskDependency)
        dep2.task_id = 3
        dep2.depends_on_task_id = 2
        dep2.dependency_type = "FS"
        dep2.lag_days = 0
        deps.append(dep2)
        return deps

    def _create_mock_milestones(self):
        """创建模拟里程碑"""
        milestones = []
        m1 = MagicMock(spec=ProjectMilestone)
        m1.id = 1
        m1.project_id = 100
        m1.milestone_name = "需求评审"
        m1.plan_date = datetime(2024, 2, 1)
        m1.status = "COMPLETED"
        milestones.append(m1)

        m2 = MagicMock(spec=ProjectMilestone)
        m2.id = 2
        m2.project_id = 100
        m2.milestone_name = "系统测试"
        m2.plan_date = datetime(2024, 5, 1)
        m2.status = "PENDING"
        milestones.append(m2)
        return milestones

    # ========== _gather_analysis_context() 测试 ==========

    def test_gather_analysis_context_basic(self):
        """测试基本的上下文收集"""
        # Mock查询结果
        self.mock_db.query.return_value.filter.return_value.all.side_effect = [
            self.mock_tasks,
            self.mock_dependencies,
            self.mock_milestones,
        ]

        context = self.service._gather_analysis_context(
            self.mock_change, self.mock_project
        )

        # 验证返回结构
        self.assertIn("change", context)
        self.assertIn("project", context)
        self.assertIn("tasks", context)
        self.assertIn("dependencies", context)
        self.assertIn("milestones", context)

        # 验证change数据
        self.assertEqual(context["change"]["id"], 1)
        self.assertEqual(context["change"]["code"], "CR-2024-001")
        self.assertEqual(context["change"]["type"], "REQUIREMENT")
        self.assertEqual(context["change"]["time_impact"], 5)
        self.assertEqual(context["change"]["cost_impact"], 50000)

        # 验证project数据
        self.assertEqual(context["project"]["id"], 100)
        self.assertEqual(context["project"]["name"], "企业管理系统")
        self.assertEqual(context["project"]["budget"], 500000)

        # 验证tasks数据
        self.assertEqual(len(context["tasks"]), 5)
        self.assertEqual(context["tasks"][0]["name"], "任务1")

        # 验证dependencies数据
        self.assertEqual(len(context["dependencies"]), 2)
        self.assertEqual(context["dependencies"][0]["task_id"], 2)

    def test_gather_analysis_context_no_tasks(self):
        """测试无任务的情况"""
        self.mock_db.query.return_value.filter.return_value.all.side_effect = [
            [],  # 无任务
            [],  # 无依赖
            [],  # 无里程碑
        ]

        context = self.service._gather_analysis_context(
            self.mock_change, self.mock_project
        )

        self.assertEqual(len(context["tasks"]), 0)
        self.assertEqual(len(context["dependencies"]), 0)
        self.assertEqual(len(context["milestones"]), 0)

    # ========== _analyze_cost_impact() 测试 ==========

    async def test_analyze_cost_impact_low(self):
        """测试低成本影响"""
        self.mock_change.cost_impact = Decimal("10000")  # 2% of budget
        context = self._build_basic_context()

        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "LOW")
        self.assertEqual(result["amount"], 10000)
        self.assertAlmostEqual(result["percentage"], 2.0, places=1)
        self.assertFalse(result["budget_exceeded"])

    async def test_analyze_cost_impact_medium(self):
        """测试中等成本影响"""
        self.mock_change.cost_impact = Decimal("30000")  # 6% of budget
        context = self._build_basic_context()

        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "MEDIUM")
        self.assertAlmostEqual(result["percentage"], 6.0, places=1)

    async def test_analyze_cost_impact_high(self):
        """测试高成本影响"""
        self.mock_change.cost_impact = Decimal("60000")  # 12% of budget
        context = self._build_basic_context()

        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "HIGH")
        self.assertAlmostEqual(result["percentage"], 12.0, places=1)

    async def test_analyze_cost_impact_critical(self):
        """测试严重成本影响"""
        self.mock_change.cost_impact = Decimal("120000")  # 24% of budget
        context = self._build_basic_context()

        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "CRITICAL")
        self.assertAlmostEqual(result["percentage"], 24.0, places=1)

    async def test_analyze_cost_impact_budget_exceeded(self):
        """测试超预算情况"""
        self.mock_change.cost_impact = Decimal("320000")
        self.mock_project.actual_cost = Decimal("200000")
        context = self._build_basic_context()

        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertTrue(result["budget_exceeded"])

    async def test_analyze_cost_impact_zero_budget(self):
        """测试预算为0的情况"""
        self.mock_project.budget_amount = None
        context = self._build_basic_context()

        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["percentage"], 0)
        # 预算为0时，无法计算百分比，影响级别为NONE
        self.assertEqual(result["level"], "NONE")

    async def test_analyze_cost_impact_breakdown(self):
        """测试成本分解"""
        self.mock_change.cost_impact = Decimal("100000")
        context = self._build_basic_context()

        result = await self.service._analyze_cost_impact(
            self.mock_change, self.mock_project, context
        )

        # 验证成本分解比例
        breakdown = result["breakdown"]
        self.assertAlmostEqual(breakdown["labor"], 60000, places=0)
        self.assertAlmostEqual(breakdown["material"], 30000, places=0)
        self.assertAlmostEqual(breakdown["outsourcing"], 10000, places=0)

    # ========== _analyze_quality_impact() 测试 ==========

    async def test_analyze_quality_impact_requirement_change(self):
        """测试需求变更的质量影响"""
        self.mock_change.change_type = MagicMock(value="REQUIREMENT")
        context = self._build_basic_context()

        result = await self.service._analyze_quality_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "MEDIUM")
        self.assertTrue(result["mitigation_required"])
        self.assertGreater(len(result["risk_areas"]), 0)
        self.assertIn("功能完整性", str(result["risk_areas"]))

    async def test_analyze_quality_impact_design_change(self):
        """测试设计变更的质量影响"""
        self.mock_change.change_type = MagicMock(value="DESIGN")
        context = self._build_basic_context()

        result = await self.service._analyze_quality_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "MEDIUM")
        self.assertTrue(result["mitigation_required"])

    async def test_analyze_quality_impact_technical_change(self):
        """测试技术变更的质量影响"""
        self.mock_change.change_type = MagicMock(value="TECHNICAL")
        context = self._build_basic_context()

        result = await self.service._analyze_quality_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "HIGH")
        self.assertTrue(result["mitigation_required"])
        self.assertIn("技术稳定性", str(result["risk_areas"]))

    async def test_analyze_quality_impact_other_change(self):
        """测试其他类型变更的质量影响"""
        self.mock_change.change_type = MagicMock(value="OTHER")
        context = self._build_basic_context()

        result = await self.service._analyze_quality_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "LOW")
        self.assertFalse(result["mitigation_required"])

    # ========== _analyze_resource_impact() 测试 ==========

    async def test_analyze_resource_impact_low(self):
        """测试低资源影响"""
        self.mock_change.time_impact = 3
        self.mock_change.cost_impact = Decimal("20000")
        context = self._build_basic_context()

        result = await self.service._analyze_resource_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "NONE")
        self.assertFalse(result["reallocation_needed"])
        self.assertFalse(result["conflict_detected"])

    async def test_analyze_resource_impact_medium(self):
        """测试中等资源影响"""
        self.mock_change.time_impact = 15
        self.mock_change.cost_impact = Decimal("60000")
        context = self._build_basic_context()

        result = await self.service._analyze_resource_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "MEDIUM")
        self.assertTrue(result["reallocation_needed"])
        self.assertGreater(len(result["additional_required"]), 0)

    async def test_analyze_resource_impact_high(self):
        """测试高资源影响"""
        self.mock_change.time_impact = 25
        self.mock_change.cost_impact = Decimal("150000")
        context = self._build_basic_context()

        result = await self.service._analyze_resource_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertEqual(result["level"], "HIGH")
        self.assertTrue(result["conflict_detected"])

    # ========== _identify_chain_reactions() 测试 ==========

    def test_identify_chain_reactions_no_dependencies(self):
        """测试无依赖的情况"""
        context = {
            "dependencies": [],
            "tasks": self.mock_tasks,
        }

        result = self.service._identify_chain_reactions(
            self.mock_change, self.mock_project, context
        )

        self.assertFalse(result["detected"])
        self.assertEqual(result["depth"], 0)
        self.assertEqual(len(result["affected_projects"]), 0)

    def test_identify_chain_reactions_with_dependencies(self):
        """测试有依赖的情况"""
        context = {
            "dependencies": [
                {"task_id": 2, "depends_on": 1, "type": "FS", "lag_days": 0},
                {"task_id": 3, "depends_on": 2, "type": "FS", "lag_days": 0},
                {"task_id": 4, "depends_on": 3, "type": "FS", "lag_days": 0},
            ],
            "tasks": [
                {"id": 1, "status": "TODO"},
                {"id": 2, "status": "TODO"},
                {"id": 3, "status": "TODO"},
                {"id": 4, "status": "TODO"},
            ],
        }

        result = self.service._identify_chain_reactions(
            self.mock_change, self.mock_project, context
        )

        self.assertTrue(result["detected"])
        self.assertGreater(result["depth"], 1)
        self.assertIn("dependency_tree", result)

    def test_identify_chain_reactions_critical_dependencies(self):
        """测试关键依赖识别"""
        context = {
            "dependencies": [
                {"task_id": 2, "depends_on": 1, "type": "FS", "lag_days": 0},
                {"task_id": 3, "depends_on": 2, "type": "SS", "lag_days": 0},
                {"task_id": 4, "depends_on": 3, "type": "FS", "lag_days": 1},
            ],
            "tasks": [
                {"id": i, "status": "TODO"} for i in range(1, 5)
            ],
        }

        result = self.service._identify_chain_reactions(
            self.mock_change, self.mock_project, context
        )

        # FS类型是关键依赖
        self.assertGreater(len(result["critical_dependencies"]), 0)
        fs_deps = [d for d in result["critical_dependencies"] if d["type"] == "FS"]
        self.assertGreater(len(fs_deps), 0)

    # ========== _calculate_dependency_depth() 测试 ==========

    def test_calculate_dependency_depth_no_dependencies(self):
        """测试无依赖的深度"""
        dep_graph = {}
        depth = self.service._calculate_dependency_depth(1, dep_graph)
        self.assertEqual(depth, 1)

    def test_calculate_dependency_depth_single_level(self):
        """测试单层依赖"""
        dep_graph = {2: [1]}
        depth = self.service._calculate_dependency_depth(2, dep_graph)
        self.assertEqual(depth, 2)

    def test_calculate_dependency_depth_multi_level(self):
        """测试多层依赖"""
        dep_graph = {
            2: [1],
            3: [2],
            4: [3],
        }
        depth = self.service._calculate_dependency_depth(4, dep_graph)
        self.assertEqual(depth, 4)

    def test_calculate_dependency_depth_circular(self):
        """测试循环依赖（应该防止无限递归）"""
        dep_graph = {
            1: [2],
            2: [1],
        }
        # 应该能处理循环依赖而不会无限递归
        depth = self.service._calculate_dependency_depth(1, dep_graph)
        # 循环依赖：1->2->1(停止)，深度为2
        self.assertEqual(depth, 2)

    # ========== _calculate_overall_risk() 测试 ==========

    def test_calculate_overall_risk_low(self):
        """测试低风险"""
        schedule_impact = {"level": "LOW", "delay_days": 2}
        cost_impact = {"level": "LOW", "amount": 5000}
        quality_impact = {"level": "LOW", "mitigation_required": False}
        resource_impact = {"level": "NONE"}
        chain_reaction = {"detected": False}

        result = self.service._calculate_overall_risk(
            schedule_impact, cost_impact, quality_impact,
            resource_impact, chain_reaction
        )

        self.assertEqual(result["level"], "LOW")
        self.assertEqual(result["recommended_action"], "APPROVE")
        self.assertLess(result["score"], 25)

    def test_calculate_overall_risk_medium(self):
        """测试中等风险"""
        schedule_impact = {"level": "MEDIUM", "delay_days": 10}
        cost_impact = {"level": "MEDIUM", "amount": 30000}
        quality_impact = {"level": "MEDIUM", "mitigation_required": True}
        resource_impact = {"level": "MEDIUM"}
        chain_reaction = {"detected": False}

        result = self.service._calculate_overall_risk(
            schedule_impact, cost_impact, quality_impact,
            resource_impact, chain_reaction
        )

        self.assertEqual(result["level"], "MEDIUM")
        self.assertEqual(result["recommended_action"], "APPROVE")
        self.assertGreaterEqual(result["score"], 25)
        self.assertLess(result["score"], 50)

    def test_calculate_overall_risk_high(self):
        """测试高风险"""
        schedule_impact = {"level": "HIGH", "delay_days": 20}
        cost_impact = {"level": "HIGH", "amount": 100000}
        quality_impact = {"level": "HIGH", "mitigation_required": True}
        resource_impact = {"level": "HIGH"}
        chain_reaction = {"detected": False}

        result = self.service._calculate_overall_risk(
            schedule_impact, cost_impact, quality_impact,
            resource_impact, chain_reaction
        )

        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["recommended_action"], "MODIFY")
        self.assertGreaterEqual(result["score"], 50)
        self.assertLess(result["score"], 75)

    def test_calculate_overall_risk_critical(self):
        """测试严重风险"""
        schedule_impact = {"level": "CRITICAL", "delay_days": 30}
        cost_impact = {"level": "CRITICAL", "amount": 200000}
        quality_impact = {"level": "HIGH", "mitigation_required": True}
        resource_impact = {"level": "HIGH"}
        chain_reaction = {"detected": True, "depth": 3}

        result = self.service._calculate_overall_risk(
            schedule_impact, cost_impact, quality_impact,
            resource_impact, chain_reaction
        )

        self.assertEqual(result["level"], "CRITICAL")
        self.assertEqual(result["recommended_action"], "ESCALATE")
        self.assertGreaterEqual(result["score"], 75)

    def test_calculate_overall_risk_with_chain_reaction(self):
        """测试包含连锁反应的风险"""
        schedule_impact = {"level": "MEDIUM", "delay_days": 10}
        cost_impact = {"level": "MEDIUM", "amount": 30000}
        quality_impact = {"level": "LOW", "mitigation_required": False}
        resource_impact = {"level": "LOW"}
        chain_reaction = {"detected": True, "depth": 2}

        result = self.service._calculate_overall_risk(
            schedule_impact, cost_impact, quality_impact,
            resource_impact, chain_reaction
        )

        # 连锁反应应该增加风险分数
        self.assertIn("factors", result)
        chain_factor = next(
            (f for f in result["factors"] if f["factor"] == "chain_reaction"),
            None
        )
        self.assertIsNotNone(chain_factor)
        self.assertEqual(chain_factor["score"], 50)

    def test_calculate_overall_risk_summary_generation(self):
        """测试摘要生成"""
        schedule_impact = {"level": "MEDIUM", "delay_days": 10}
        cost_impact = {"level": "MEDIUM", "amount": 50000}
        quality_impact = {"level": "MEDIUM", "mitigation_required": True}
        resource_impact = {"level": "LOW"}
        chain_reaction = {"detected": True, "depth": 2}

        result = self.service._calculate_overall_risk(
            schedule_impact, cost_impact, quality_impact,
            resource_impact, chain_reaction
        )

        # 验证摘要包含关键信息
        summary = result["summary"]
        self.assertIn("10天", summary)
        self.assertIn("50,000元", summary)
        self.assertIn("质量风险", summary)
        self.assertIn("连锁反应", summary)

    # ========== _find_affected_tasks() 测试 ==========

    def test_find_affected_tasks_basic(self):
        """测试查找受影响任务"""
        context = {
            "tasks": [
                {"id": 1, "name": "任务1", "status": "IN_PROGRESS"},
                {"id": 2, "name": "任务2", "status": "TODO"},
                {"id": 3, "name": "任务3", "status": "DONE"},
            ],
            "change": {"time_impact": 5}
        }

        result = self.service._find_affected_tasks(context)

        # 只有IN_PROGRESS和TODO的任务受影响
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["delay_days"], 5)

    def test_find_affected_tasks_max_limit(self):
        """测试最多返回10个任务"""
        context = {
            "tasks": [
                {"id": i, "name": f"任务{i}", "status": "TODO"}
                for i in range(1, 20)
            ],
            "change": {"time_impact": 3}
        }

        result = self.service._find_affected_tasks(context)
        self.assertEqual(len(result), 10)

    # ========== _find_affected_milestones() 测试 ==========

    def test_find_affected_milestones_basic(self):
        """测试查找受影响里程碑"""
        context = {
            "milestones": [
                {
                    "id": 1,
                    "name": "里程碑1",
                    "plan_date": "2024-05-01T00:00:00"
                },
                {
                    "id": 2,
                    "name": "里程碑2",
                    "plan_date": "2024-06-01T00:00:00"
                },
            ]
        }

        result = self.service._find_affected_milestones(context, 10)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["milestone_id"], 1)
        # 验证日期被延后了10天
        self.assertIn("2024-05-11", result[0]["new_date"])

    def test_find_affected_milestones_no_date(self):
        """测试没有计划日期的里程碑"""
        context = {
            "milestones": [
                {"id": 1, "name": "里程碑1", "plan_date": None},
            ]
        }

        result = self.service._find_affected_milestones(context, 10)
        self.assertEqual(len(result), 0)

    # ========== _parse_ai_response() 测试 ==========

    def test_parse_ai_response_valid_json(self):
        """测试解析有效JSON"""
        response = '{"level": "HIGH", "delay_days": 15}'
        default = {"level": "MEDIUM", "delay_days": 0}

        result = self.service._parse_ai_response(response, default)

        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["delay_days"], 15)

    def test_parse_ai_response_json_with_text(self):
        """测试提取文本中的JSON"""
        response = """
        根据分析，影响如下：
        {"level": "CRITICAL", "delay_days": 30, "description": "严重影响"}
        以上是分析结果。
        """
        default = {"level": "MEDIUM", "delay_days": 0}

        result = self.service._parse_ai_response(response, default)

        self.assertEqual(result["level"], "CRITICAL")
        self.assertEqual(result["delay_days"], 30)

    def test_parse_ai_response_invalid_json(self):
        """测试解析无效JSON（返回默认值）"""
        response = "这不是JSON格式"
        default = {"level": "MEDIUM", "delay_days": 0}

        result = self.service._parse_ai_response(response, default)

        self.assertEqual(result, default)

    def test_parse_ai_response_merge_with_default(self):
        """测试合并默认值"""
        response = '{"level": "HIGH"}'
        default = {"level": "MEDIUM", "delay_days": 0, "description": "默认"}

        result = self.service._parse_ai_response(response, default)

        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["delay_days"], 0)  # 来自默认值
        self.assertEqual(result["description"], "默认")  # 来自默认值

    # ========== 辅助方法 ==========

    def _build_basic_context(self):
        """构建基本的上下文数据"""
        return {
            "change": {
                "id": 1,
                "code": "CR-2024-001",
                "time_impact": 5,
                "cost_impact": 50000,
            },
            "project": {
                "id": 100,
                "budget": 500000,
            },
            "tasks": [],
            "dependencies": [],
            "milestones": [],
        }


class TestChangeImpactAIServiceIntegration(unittest.IsolatedAsyncioTestCase):
    """测试集成场景（需要mock AI调用）"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ChangeImpactAIService(self.mock_db)

        # 创建完整的mock对象
        self.mock_change = self._create_mock_change()
        self.mock_project = self._create_mock_project()
        self.mock_analysis = self._create_mock_analysis()

    def _create_mock_change(self):
        """创建模拟变更请求"""
        change = MagicMock(spec=ChangeRequest)
        change.id = 1
        change.project_id = 100
        change.change_code = "CR-2024-001"
        change.title = "增加数据导出功能"
        change.description = "客户要求增加数据导出功能"
        change.change_type = MagicMock(value="REQUIREMENT")
        change.change_source = MagicMock(value="CUSTOMER")
        change.time_impact = 10
        change.cost_impact = Decimal("80000")
        return change

    def _create_mock_project(self):
        """创建模拟项目"""
        project = MagicMock(spec=Project)
        project.id = 100
        project.project_code = "PRJ-2024-001"
        project.project_name = "企业管理系统"
        project.status = "IN_PROGRESS"
        project.budget_amount = Decimal("500000")
        project.actual_cost = Decimal("200000")
        project.plan_start = datetime(2024, 1, 1)
        project.plan_end = datetime(2024, 6, 30)
        return project

    def _create_mock_analysis(self):
        """创建模拟分析记录"""
        analysis = MagicMock(spec=ChangeImpactAnalysis)
        analysis.id = 1
        return analysis

    @patch('app.services.change_impact_ai_service.call_glm_api')
    async def test_analyze_change_impact_success(self, mock_glm_api):
        """测试完整的变更影响分析流程"""
        # Mock数据库查询
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.first.side_effect = [
            self.mock_change,
            self.mock_project,
        ]
        query_mock.filter.return_value.all.side_effect = [
            [],  # tasks
            [],  # dependencies
            [],  # milestones
        ]

        # Mock add操作返回分析对象
        self.mock_db.add.return_value = None
        self.mock_db.flush.return_value = None

        # 设置分析对象属性
        def add_side_effect(obj):
            obj.id = 1

        self.mock_db.add.side_effect = add_side_effect

        # Mock AI API响应
        mock_glm_api.return_value = '{"level": "MEDIUM", "delay_days": 10}'

        # 执行分析
        result = await self.service.analyze_change_impact(
            change_request_id=1,
            user_id=1
        )

        # 验证数据库操作
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()

        # 验证结果
        self.assertIsNotNone(result)

    @patch('app.services.change_impact_ai_service.call_glm_api')
    async def test_analyze_change_impact_change_not_found(self, mock_glm_api):
        """测试变更请求不存在的情况"""
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as cm:
            await self.service.analyze_change_impact(
                change_request_id=999,
                user_id=1
            )

        self.assertIn("不存在", str(cm.exception))

    @patch('app.services.change_impact_ai_service.call_glm_api')
    async def test_analyze_change_impact_project_not_found(self, mock_glm_api):
        """测试项目不存在的情况"""
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.first.side_effect = [
            self.mock_change,
            None,  # 项目不存在
        ]

        with self.assertRaises(ValueError) as cm:
            await self.service.analyze_change_impact(
                change_request_id=1,
                user_id=1
            )

        self.assertIn("项目", str(cm.exception))

    @patch('app.services.change_impact_ai_service.call_glm_api')
    async def test_analyze_schedule_impact_with_ai(self, mock_glm_api):
        """测试进度影响分析（包含AI调用）"""
        # Mock AI响应
        mock_glm_api.return_value = """
        {
            "level": "HIGH",
            "delay_days": 15,
            "critical_path_affected": true,
            "description": "影响关键路径"
        }
        """

        context = {
            "change": {"time_impact": 15},
            "project": {"start_date": "2024-01-01", "end_date": "2024-06-30"},
            "tasks": [
                {"id": 1, "status": "IN_PROGRESS", "name": "任务1"}
            ],
            "milestones": []
        }

        result = await self.service._analyze_schedule_impact(
            self.mock_change, self.mock_project, context
        )

        # 验证AI被调用
        mock_glm_api.assert_called_once()

        # 验证结果
        self.assertEqual(result["level"], "HIGH")
        self.assertTrue(result["critical_path_affected"])

    @patch('app.services.change_impact_ai_service.call_glm_api')
    async def test_analyze_schedule_impact_ai_error(self, mock_glm_api):
        """测试AI调用失败的情况"""
        # Mock AI抛出异常
        mock_glm_api.side_effect = Exception("API调用失败")

        context = {
            "change": {"time_impact": 5},
            "project": {"start_date": "2024-01-01", "end_date": "2024-06-30"},
            "tasks": [],
            "milestones": []
        }

        # 应该返回默认值而不是抛出异常
        result = await self.service._analyze_schedule_impact(
            self.mock_change, self.mock_project, context
        )

        self.assertIn("分析异常", result["description"])
        self.assertEqual(result["level"], "MEDIUM")


if __name__ == "__main__":
    unittest.main()
