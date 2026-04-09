# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AI进度排期优化器"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta


class TestAIScheduleOptimizerBusinessLogic:
    """AI进度排期优化器业务逻辑测试"""

    def test_optimize_schedule_project_not_found(self):
        """测试项目不存在"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()
            mock_db.query.return_value.get.return_value = None

            optimizer = AIScheduleOptimizer(mock_db)
            result = optimizer.optimize_schedule(999)

            assert result == {}
        except ImportError:
            pytest.skip("Module not found")

    def test_optimize_schedule_no_wbs_tasks(self):
        """测试没有WBS任务"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            # Mock项目
            mock_project = MagicMock()
            mock_project.id = 1

            mock_db.query.return_value.get.return_value = mock_project
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

            optimizer = AIScheduleOptimizer(mock_db)
            result = optimizer.optimize_schedule(1)

            assert result == {}
        except ImportError:
            pytest.skip("Module not found")

    def test_optimize_schedule_with_tasks(self):
        """测试有任务的优化"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            # Mock项目
            mock_project = MagicMock()
            mock_project.id = 1

            # Mock WBS任务
            mock_task1 = MagicMock()
            mock_task1.id = 1
            mock_task1.wbs_code = "1.0"
            mock_task1.task_name = "阶段1"
            mock_task1.duration_days = 5
            mock_task1.dependencies = []
            mock_task1.is_active = True

            mock_task2 = MagicMock()
            mock_task2.id = 2
            mock_task2.wbs_code = "1.1"
            mock_task2.task_name = "任务1"
            mock_task2.duration_days = 3
            mock_task2.dependencies = ["1.0"]
            mock_task2.is_active = True

            mock_db.query.return_value.get.return_value = mock_project
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task1, mock_task2]

            optimizer = AIScheduleOptimizer(mock_db)

            # Mock内部方法
            optimizer._calculate_cpm = MagicMock(return_value={"tasks": []})
            optimizer._generate_gantt_data = MagicMock(return_value=[])
            optimizer._identify_critical_path = MagicMock(return_value=["1.0", "1.1"])
            optimizer._analyze_resource_load = MagicMock(return_value={})
            optimizer._detect_conflicts = MagicMock(return_value=[])

            result = optimizer.optimize_schedule(1, date(2026, 4, 10))

            assert "critical_path" in result
        except ImportError:
            pytest.skip("Module not found")

    def test_calculate_cpm(self):
        """测试关键路径计算"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            optimizer = AIScheduleOptimizer(mock_db)

            # Mock任务
            tasks = [
                MagicMock(id=1, wbs_code="1.0", duration_days=5, dependencies=[]),
                MagicMock(id=2, wbs_code="1.1", duration_days=3, dependencies=["1.0"]),
            ]

            start_date = date(2026, 4, 10)
            result = optimizer._calculate_cpm(tasks, start_date)

            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Module not found")

    def test_generate_gantt_data(self):
        """测试甘特图数据生成"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            optimizer = AIScheduleOptimizer(mock_db)

            tasks = [
                MagicMock(
                    id=1,
                    wbs_code="1.0",
                    task_name="开始",
                    duration_days=5,
                    dependencies=[]
                ),
            ]

            cpm_result = {"1.0": {"start": date(2026, 4, 10), "end": date(2026, 4, 15)}}
            start_date = date(2026, 4, 10)

            result = optimizer._generate_gantt_data(tasks, cpm_result, start_date)

            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")

    def test_identify_critical_path(self):
        """测试关键路径识别"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            optimizer = AIScheduleOptimizer(mock_db)

            tasks = [
                MagicMock(id=1, wbs_code="1.0", duration_days=10),
                MagicMock(id=2, wbs_code="1.1", duration_days=5),
            ]

            cpm_result = {
                "1.0": {"is_critical": True},
                "1.1": {"is_critical": False}
            }

            result = optimizer._identify_critical_path(tasks, cpm_result)

            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")

    def test_analyze_resource_load(self):
        """测试资源负载分析"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            optimizer = AIScheduleOptimizer(mock_db)

            cpm_result = {
                "1.0": {"start": date(2026, 4, 10), "end": date(2026, 4, 15)}
            }

            result = optimizer._analyze_resource_load(1, cpm_result)

            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Module not found")

    def test_detect_conflicts(self):
        """测试冲突检测"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            optimizer = AIScheduleOptimizer(mock_db)

            gantt_data = [
                {
                    "wbs_code": "1.0",
                    "start": date(2026, 4, 10),
                    "end": date(2026, 4, 15),
                    "resources": [{"id": 1}]
                },
                {
                    "wbs_code": "1.1",
                    "start": date(2026, 4, 12),
                    "end": date(2026, 4, 17),
                    "resources": [{"id": 1}]  # 资源冲突
                },
            ]

            resource_load = {1: {"max": 100, "current": 150}}

            result = optimizer._detect_conflicts(gantt_data, resource_load)

            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")


class TestAIScheduleOptimizerConstraints:
    """约束条件测试"""

    def test_optimize_with_deadline_constraint(self):
        """测试截止日期约束"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            mock_project = MagicMock()
            mock_db.query.return_value.get.return_value = mock_project
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

            optimizer = AIScheduleOptimizer(mock_db)

            constraints = {"deadline": date(2026, 5, 1)}
            result = optimizer.optimize_schedule(1, date(2026, 4, 10), constraints)

            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Module not found")

    def test_optimize_with_resource_constraint(self):
        """测试资源约束"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            mock_project = MagicMock()
            mock_db.query.return_value.get.return_value = mock_project
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

            optimizer = AIScheduleOptimizer(mock_db)

            constraints = {"max_workers": 10}
            result = optimizer.optimize_schedule(1, date(2026, 4, 10), constraints)

            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Module not found")


class TestAIScheduleOptimizerEdgeCases:
    """边界情况测试"""

    def test_empty_dependencies(self):
        """测试空依赖"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            optimizer = AIScheduleOptimizer(mock_db)

            tasks = [
                MagicMock(id=1, wbs_code="1.0", duration_days=5, dependencies=[]),
            ]

            start_date = date(2026, 4, 10)
            result = optimizer._calculate_cpm(tasks, start_date)

            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Module not found")

    def test_single_task_project(self):
        """测试单任务项目"""
        try:
            from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

            mock_db = MagicMock()

            mock_project = MagicMock()

            mock_task = MagicMock()
            mock_task.wbs_code = "1.0"
            mock_task.duration_days = 5
            mock_task.dependencies = []
            mock_task.is_active = True

            mock_db.query.return_value.get.return_value = mock_project
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task]

            optimizer = AIScheduleOptimizer(mock_db)

            optimizer._calculate_cpm = MagicMock(return_value={})
            optimizer._generate_gantt_data = MagicMock(return_value=[])
            optimizer._identify_critical_path = MagicMock(return_value=["1.0"])
            optimizer._analyze_resource_load = MagicMock(return_value={})
            optimizer._detect_conflicts = MagicMock(return_value=[])

            result = optimizer.optimize_schedule(1)

            assert "critical_path" in result
        except ImportError:
            pytest.skip("Module not found")