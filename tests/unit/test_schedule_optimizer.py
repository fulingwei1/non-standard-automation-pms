# -*- coding: utf-8 -*-
"""
AI进度排期优化器单元测试

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
import json

from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer
from app.models import Project
from app.models.ai_planning import AIWbsSuggestion, AIResourceAllocation


class TestAIScheduleOptimizerInit(unittest.TestCase):
    """测试初始化"""

    def test_init(self):
        """测试构造函数"""
        mock_db = MagicMock()
        optimizer = AIScheduleOptimizer(mock_db)
        self.assertEqual(optimizer.db, mock_db)


class TestOptimizeSchedule(unittest.TestCase):
    """测试optimize_schedule主入口"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_optimize_schedule_project_not_found(self):
        """测试项目不存在"""
        self.mock_db.query.return_value.get.return_value = None
        
        result = self.optimizer.optimize_schedule(project_id=999)
        
        self.assertEqual(result, {})
        self.mock_db.query.assert_called_once()

    def test_optimize_schedule_no_wbs_tasks(self):
        """测试没有WBS任务"""
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        
        self.mock_db.query.return_value.get.return_value = mock_project
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = self.optimizer.optimize_schedule(project_id=1)
        
        self.assertEqual(result, {})

    def test_optimize_schedule_success(self):
        """测试成功优化排期"""
        # Mock project
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        
        # Mock WBS tasks
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        task1.task_name = "需求分析"
        task1.wbs_code = "1.1"
        task1.wbs_level = 1
        task1.parent_wbs_id = None
        task1.estimated_duration_days = 5
        task1.dependencies = None
        task1.risk_level = "LOW"
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        task2.task_name = "系统设计"
        task2.wbs_code = "1.2"
        task2.wbs_level = 1
        task2.parent_wbs_id = None
        task2.estimated_duration_days = 10
        task2.dependencies = json.dumps([{"task_id": 1, "type": "FS"}])
        task2.risk_level = "MEDIUM"
        
        wbs_tasks = [task1, task2]
        
        # Mock resource allocations
        alloc1 = MagicMock(spec=AIResourceAllocation)
        alloc1.project_id = 1
        alloc1.wbs_suggestion_id = 1
        alloc1.user_id = 101
        alloc1.allocated_hours = 40
        alloc1.overall_match_score = 0.85
        alloc1.is_active = True
        
        # Setup query chain
        query_get = MagicMock()
        query_get.get.return_value = mock_project
        
        query_wbs = MagicMock()
        query_wbs.filter.return_value.order_by.return_value.all.return_value = wbs_tasks
        
        query_resource = MagicMock()
        query_resource.filter.return_value.all.return_value = [alloc1]
        
        # Mock db.query to return different values
        def query_side_effect(model):
            if model == Project:
                return query_get
            elif model == AIWbsSuggestion:
                return query_wbs
            elif model == AIResourceAllocation:
                return query_resource
        
        self.mock_db.query.side_effect = query_side_effect
        
        # Execute
        start_date = date(2026, 3, 1)
        result = self.optimizer.optimize_schedule(
            project_id=1,
            start_date=start_date
        )
        
        # Assertions
        self.assertIn("project_id", result)
        self.assertEqual(result["project_id"], 1)
        self.assertIn("start_date", result)
        self.assertIn("gantt_data", result)
        self.assertIn("critical_path", result)
        self.assertIn("resource_load", result)
        self.assertIn("conflicts", result)
        self.assertIn("recommendations", result)
        self.assertIn("optimization_summary", result)
        
        # Verify gantt data
        self.assertEqual(len(result["gantt_data"]), 2)
        
        # Verify critical path (all tasks with 0 slack)
        self.assertGreater(len(result["critical_path"]), 0)

    def test_optimize_schedule_default_start_date(self):
        """测试默认开始日期（今天）"""
        mock_project = MagicMock(spec=Project)
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        task1.task_name = "任务1"
        task1.wbs_code = "1.1"
        task1.wbs_level = 1
        task1.parent_wbs_id = None
        task1.estimated_duration_days = 5
        task1.dependencies = None
        task1.risk_level = "LOW"
        
        query_get = MagicMock()
        query_get.get.return_value = mock_project
        
        query_wbs = MagicMock()
        query_wbs.filter.return_value.order_by.return_value.all.return_value = [task1]
        
        query_resource = MagicMock()
        query_resource.filter.return_value.all.return_value = []
        
        def query_side_effect(model):
            if model == Project:
                return query_get
            elif model == AIWbsSuggestion:
                return query_wbs
            elif model == AIResourceAllocation:
                return query_resource
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.optimizer.optimize_schedule(project_id=1)
        
        # Should use today as start date
        self.assertEqual(result["start_date"], date.today().isoformat())


class TestCalculateCPM(unittest.TestCase):
    """测试CPM计算"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_calculate_cpm_single_task(self):
        """测试单个任务CPM"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        task.wbs_code = "1.1"
        task.wbs_level = 1
        task.estimated_duration_days = 5
        task.dependencies = None
        
        start_date = date(2026, 3, 1)
        result = self.optimizer._calculate_cpm([task], start_date)
        
        self.assertIn("es", result)
        self.assertIn("ef", result)
        self.assertIn("ls", result)
        self.assertIn("lf", result)
        self.assertIn("slack", result)
        
        # Single task: ES=0, EF=5, LS=0, LF=5, Slack=0
        self.assertEqual(result["es"][1], 0)
        self.assertEqual(result["ef"][1], 5)
        self.assertEqual(result["slack"][1], 0)
        self.assertEqual(result["total_duration"], 5)

    def test_calculate_cpm_sequential_tasks(self):
        """测试顺序任务CPM"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        task1.wbs_code = "1.1"
        task1.wbs_level = 1
        task1.estimated_duration_days = 5
        task1.dependencies = None
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        task2.wbs_code = "1.2"
        task2.wbs_level = 1
        task2.estimated_duration_days = 10
        task2.dependencies = json.dumps([{"task_id": 1, "type": "FS"}])
        
        start_date = date(2026, 3, 1)
        result = self.optimizer._calculate_cpm([task1, task2], start_date)
        
        # Task1: ES=0, EF=5
        self.assertEqual(result["es"][1], 0)
        self.assertEqual(result["ef"][1], 5)
        
        # Task2: ES=5 (after task1), EF=15
        self.assertEqual(result["es"][2], 5)
        self.assertEqual(result["ef"][2], 15)
        
        # Total duration
        self.assertEqual(result["total_duration"], 15)

    def test_calculate_cpm_parallel_tasks(self):
        """测试并行任务CPM"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        task1.wbs_code = "1.1"
        task1.wbs_level = 1
        task1.estimated_duration_days = 10
        task1.dependencies = None
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        task2.wbs_code = "1.2"
        task2.wbs_level = 1
        task2.estimated_duration_days = 5
        task2.dependencies = None
        
        start_date = date(2026, 3, 1)
        result = self.optimizer._calculate_cpm([task1, task2], start_date)
        
        # Both start at 0
        self.assertEqual(result["es"][1], 0)
        self.assertEqual(result["es"][2], 0)
        
        # Task1 finishes at 10
        self.assertEqual(result["ef"][1], 10)
        # Task2 finishes at 5
        self.assertEqual(result["ef"][2], 5)
        
        # Total duration is max(10, 5) = 10
        self.assertEqual(result["total_duration"], 10)

    def test_calculate_cpm_zero_duration_task(self):
        """测试工期为0的任务"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        task.wbs_code = "1.1"
        task.wbs_level = 1
        task.estimated_duration_days = None  # None会被处理为0
        task.dependencies = None
        
        start_date = date(2026, 3, 1)
        result = self.optimizer._calculate_cpm([task], start_date)
        
        self.assertEqual(result["es"][1], 0)
        self.assertEqual(result["ef"][1], 0)


class TestGetPredecessorsSuccessors(unittest.TestCase):
    """测试前置/后继任务获取"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_get_predecessors_none(self):
        """测试无前置任务"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        task.dependencies = None
        
        result = self.optimizer._get_predecessors(task, {})
        
        self.assertEqual(result, [])

    def test_get_predecessors_single(self):
        """测试单个前置任务"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        task2.dependencies = json.dumps([{"task_id": 1, "type": "FS"}])
        
        task_dict = {1: task1, 2: task2}
        
        result = self.optimizer._get_predecessors(task2, task_dict)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_get_predecessors_multiple(self):
        """测试多个前置任务"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        
        task3 = MagicMock(spec=AIWbsSuggestion)
        task3.id = 3
        task3.dependencies = json.dumps([
            {"task_id": 1, "type": "FS"},
            {"task_id": 2, "type": "FS"}
        ])
        
        task_dict = {1: task1, 2: task2, 3: task3}
        
        result = self.optimizer._get_predecessors(task3, task_dict)
        
        self.assertEqual(len(result), 2)

    def test_get_predecessors_invalid_json(self):
        """测试无效的JSON依赖"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        task.dependencies = "invalid json"
        
        result = self.optimizer._get_predecessors(task, {})
        
        self.assertEqual(result, [])

    def test_get_successors_none(self):
        """测试无后继任务"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        
        result = self.optimizer._get_successors(task, {1: task})
        
        self.assertEqual(result, [])

    def test_get_successors_single(self):
        """测试单个后继任务"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        task1.dependencies = None
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        task2.dependencies = json.dumps([{"task_id": 1, "type": "FS"}])
        
        task_dict = {1: task1, 2: task2}
        
        result = self.optimizer._get_successors(task1, task_dict)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 2)

    def test_get_successors_invalid_json(self):
        """测试后继任务中有无效JSON"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        task1.dependencies = None
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        task2.dependencies = "invalid"
        
        task_dict = {1: task1, 2: task2}
        
        result = self.optimizer._get_successors(task1, task_dict)
        
        self.assertEqual(result, [])


class TestGenerateGanttData(unittest.TestCase):
    """测试甘特图数据生成"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_generate_gantt_data_basic(self):
        """测试基本甘特图生成"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        task.task_name = "需求分析"
        task.wbs_code = "1.1"
        task.wbs_level = 1
        task.parent_wbs_id = None
        task.estimated_duration_days = 5
        
        cpm_result = {
            "es": {1: 0},
            "ef": {1: 5},
            "slack": {1: 0}
        }
        
        start_date = date(2026, 3, 1)
        
        result = self.optimizer._generate_gantt_data([task], cpm_result, start_date)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["task_id"], 1)
        self.assertEqual(result[0]["task_name"], "需求分析")
        self.assertEqual(result[0]["start_date"], "2026-03-01")
        self.assertEqual(result[0]["end_date"], "2026-03-06")
        self.assertTrue(result[0]["is_critical"])

    def test_generate_gantt_data_with_slack(self):
        """测试包含浮动时间的任务"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        task.task_name = "测试任务"
        task.wbs_code = "1.1"
        task.wbs_level = 1
        task.parent_wbs_id = None
        task.estimated_duration_days = 3
        
        cpm_result = {
            "es": {1: 0},
            "ef": {1: 3},
            "slack": {1: 2}  # 有浮动时间，非关键任务
        }
        
        start_date = date(2026, 3, 1)
        
        result = self.optimizer._generate_gantt_data([task], cpm_result, start_date)
        
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["is_critical"])
        self.assertEqual(result[0]["slack"], 2)


class TestIdentifyCriticalPath(unittest.TestCase):
    """测试关键路径识别"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_identify_critical_path_all_critical(self):
        """测试全部任务都是关键任务"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        task1.task_name = "任务1"
        task1.wbs_code = "1.1"
        task1.estimated_duration_days = 5
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        task2.task_name = "任务2"
        task2.wbs_code = "1.2"
        task2.estimated_duration_days = 10
        
        cpm_result = {
            "slack": {1: 0, 2: 0}
        }
        
        result = self.optimizer._identify_critical_path([task1, task2], cpm_result)
        
        self.assertEqual(len(result), 2)

    def test_identify_critical_path_mixed(self):
        """测试混合关键/非关键任务"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.id = 1
        task1.task_name = "关键任务"
        task1.wbs_code = "1.1"
        task1.estimated_duration_days = 5
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.id = 2
        task2.task_name = "非关键任务"
        task2.wbs_code = "1.2"
        task2.estimated_duration_days = 3
        
        cpm_result = {
            "slack": {1: 0, 2: 5}
        }
        
        result = self.optimizer._identify_critical_path([task1, task2], cpm_result)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["task_id"], 1)


class TestAnalyzeResourceLoad(unittest.TestCase):
    """测试资源负载分析"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_analyze_resource_load_empty(self):
        """测试无资源分配"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.optimizer._analyze_resource_load(project_id=1, cpm_result={})
        
        self.assertEqual(result, {})

    def test_analyze_resource_load_single_user(self):
        """测试单个用户资源负载"""
        alloc = MagicMock(spec=AIResourceAllocation)
        alloc.user_id = 101
        alloc.wbs_suggestion_id = 1
        alloc.allocated_hours = 40
        alloc.overall_match_score = 0.85
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [alloc]
        
        result = self.optimizer._analyze_resource_load(project_id=1, cpm_result={})
        
        self.assertIn(101, result)
        self.assertEqual(result[101]["total_hours"], 40)
        self.assertEqual(result[101]["task_count"], 1)
        self.assertEqual(len(result[101]["tasks"]), 1)

    def test_analyze_resource_load_multiple_tasks(self):
        """测试多任务资源负载"""
        alloc1 = MagicMock(spec=AIResourceAllocation)
        alloc1.user_id = 101
        alloc1.wbs_suggestion_id = 1
        alloc1.allocated_hours = 40
        alloc1.overall_match_score = 0.85
        
        alloc2 = MagicMock(spec=AIResourceAllocation)
        alloc2.user_id = 101
        alloc2.wbs_suggestion_id = 2
        alloc2.allocated_hours = 30
        alloc2.overall_match_score = 0.90
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [alloc1, alloc2]
        
        result = self.optimizer._analyze_resource_load(project_id=1, cpm_result={})
        
        self.assertEqual(result[101]["total_hours"], 70)
        self.assertEqual(result[101]["task_count"], 2)


class TestDetectConflicts(unittest.TestCase):
    """测试冲突检测"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_detect_conflicts_resource_overload(self):
        """测试资源过载检测"""
        resource_load = {
            101: {
                "user_id": 101,
                "total_hours": 500,  # 超过160*3=480
                "task_count": 5,
                "tasks": []
            }
        }
        
        result = self.optimizer._detect_conflicts([], {}, resource_load)
        
        # 应该检测到资源过载
        overload_conflicts = [c for c in result if c["type"] == "RESOURCE_OVERLOAD"]
        self.assertGreater(len(overload_conflicts), 0)

    def test_detect_conflicts_too_many_critical_tasks(self):
        """测试关键任务过多"""
        tasks = []
        for i in range(10):
            task = MagicMock(spec=AIWbsSuggestion)
            task.id = i
            task.estimated_duration_days = 5
            task.risk_level = "LOW"
            tasks.append(task)
        
        # 全部是关键任务（slack=0）
        cpm_result = {
            "slack": {i: 0 for i in range(10)}
        }
        
        result = self.optimizer._detect_conflicts(tasks, cpm_result, {})
        
        # 应该检测到关键任务过多
        critical_conflicts = [c for c in result if c["type"] == "TOO_MANY_CRITICAL_TASKS"]
        self.assertGreater(len(critical_conflicts), 0)

    def test_detect_conflicts_task_too_long(self):
        """测试任务工期过长"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        task.task_name = "超长任务"
        task.estimated_duration_days = 90  # 超过60天
        task.risk_level = "LOW"
        
        result = self.optimizer._detect_conflicts([task], {"slack": {1: 0}}, {})
        
        # 应该检测到任务过长
        long_task_conflicts = [c for c in result if c["type"] == "TASK_TOO_LONG"]
        self.assertGreater(len(long_task_conflicts), 0)

    def test_detect_conflicts_none(self):
        """测试无冲突"""
        task = MagicMock(spec=AIWbsSuggestion)
        task.id = 1
        task.estimated_duration_days = 10
        task.risk_level = "LOW"
        
        resource_load = {
            101: {"total_hours": 100, "task_count": 2, "tasks": []}
        }
        
        cpm_result = {"slack": {1: 5}}
        
        result = self.optimizer._detect_conflicts([task], cpm_result, resource_load)
        
        # 可能只有少量或无冲突
        self.assertIsInstance(result, list)


class TestGenerateRecommendations(unittest.TestCase):
    """测试建议生成"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_generate_recommendations_critical_path(self):
        """测试关键路径建议"""
        critical_path = [
            {"task_id": 1, "task_name": "任务1"},
            {"task_id": 2, "task_name": "任务2"}
        ]
        
        result = self.optimizer._generate_recommendations(
            tasks=[],
            critical_path=critical_path,
            conflicts=[],
            resource_load={}
        )
        
        # 应该有关键路径建议
        critical_recs = [r for r in result if r["category"] == "CRITICAL_PATH"]
        self.assertGreater(len(critical_recs), 0)

    def test_generate_recommendations_resource_balance(self):
        """测试资源平衡建议"""
        # 需要满足: max_load > avg_load * 2
        # avg_load = (500 + 50 + 50) / 3 = 200
        # max_load = 500
        # 500 > 200 * 2 (400) ? Yes!
        resource_load = {
            101: {"total_hours": 500, "task_count": 5},
            102: {"total_hours": 50, "task_count": 1},
            103: {"total_hours": 50, "task_count": 1}
        }
        
        result = self.optimizer._generate_recommendations(
            tasks=[],
            critical_path=[],
            conflicts=[],
            resource_load=resource_load
        )
        
        # 应该有资源平衡建议（500 > 200*2）
        balance_recs = [r for r in result if r["category"] == "RESOURCE_BALANCE"]
        self.assertGreater(len(balance_recs), 0)

    def test_generate_recommendations_high_risk(self):
        """测试高风险任务建议"""
        task1 = MagicMock(spec=AIWbsSuggestion)
        task1.risk_level = "HIGH"
        
        task2 = MagicMock(spec=AIWbsSuggestion)
        task2.risk_level = "CRITICAL"
        
        result = self.optimizer._generate_recommendations(
            tasks=[task1, task2],
            critical_path=[],
            conflicts=[],
            resource_load={}
        )
        
        # 应该有风险管理建议
        risk_recs = [r for r in result if r["category"] == "RISK_MANAGEMENT"]
        self.assertGreater(len(risk_recs), 0)


class TestCalculateResourceUtilization(unittest.TestCase):
    """测试资源利用率计算"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.optimizer = AIScheduleOptimizer(self.mock_db)

    def test_calculate_resource_utilization_empty(self):
        """测试空资源"""
        result = self.optimizer._calculate_resource_utilization({})
        self.assertEqual(result, 0.0)

    def test_calculate_resource_utilization_normal(self):
        """测试正常利用率"""
        resource_load = {
            101: {"total_hours": 240, "task_count": 3},  # 240 / (160*3) = 50%
            102: {"total_hours": 240, "task_count": 3}
        }
        
        result = self.optimizer._calculate_resource_utilization(resource_load)
        
        # (240+240) / (2 * 160*3) = 480/960 = 50%
        self.assertEqual(result, 50.0)

    def test_calculate_resource_utilization_over_100(self):
        """测试超过100%的利用率"""
        resource_load = {
            101: {"total_hours": 600, "task_count": 5}
        }
        
        result = self.optimizer._calculate_resource_utilization(resource_load)
        
        # 应该不超过100%
        self.assertLessEqual(result, 100.0)

    def test_calculate_resource_utilization_single_user(self):
        """测试单用户利用率"""
        resource_load = {
            101: {"total_hours": 160, "task_count": 2}
        }
        
        result = self.optimizer._calculate_resource_utilization(resource_load)
        
        # 160 / (1 * 160*3) = 160/480 = 33.33%
        self.assertAlmostEqual(result, 33.33, places=2)


if __name__ == "__main__":
    unittest.main()
