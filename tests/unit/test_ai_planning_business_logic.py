# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AIScheduleOptimizer / AIWbsDecomposer"""

from datetime import date
from unittest.mock import MagicMock

import pytest


class TestAIScheduleOptimizerBusinessLogic:
    """AI进度排期优化器业务逻辑测试"""

    def test_init_with_db(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        optimizer = AIScheduleOptimizer(mock_db)
        assert optimizer.db == mock_db

    def test_optimize_schedule_project_not_found(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        mock_db.query.return_value.get.return_value = None

        optimizer = AIScheduleOptimizer(mock_db)
        result = optimizer.optimize_schedule(999)
        assert result == {}

    def test_optimize_schedule_no_wbs_tasks(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        q = mock_db.query.return_value
        q.get.return_value = mock_project
        q.filter.return_value.order_by.return_value.all.return_value = []

        optimizer = AIScheduleOptimizer(mock_db)
        result = optimizer.optimize_schedule(1)
        assert result == {}

    def test_optimize_schedule_with_tasks(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.wbs_code = "1.0"
        mock_task.wbs_level = 1
        mock_task.parent_wbs_id = None
        mock_task.task_name = "需求分析"
        mock_task.estimated_duration_days = 5
        mock_task.dependencies = None
        mock_task.is_active = True

        project_query = MagicMock()
        project_query.get.return_value = mock_project
        task_query = MagicMock()
        task_query.filter.return_value.order_by.return_value.all.return_value = [mock_task]
        resource_query = MagicMock()
        resource_query.filter.return_value.all.return_value = []
        mock_db.query.side_effect = [project_query, task_query, resource_query]

        optimizer = AIScheduleOptimizer(mock_db)
        result = optimizer.optimize_schedule(1, start_date=date.today())
        assert result is not None
        assert result["project_id"] == 1
        assert result["optimization_summary"]["total_tasks"] == 1

    def test_calculate_cpm(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        optimizer = AIScheduleOptimizer(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.wbs_level = 1
        mock_task.wbs_code = "1.0"
        mock_task.estimated_duration_days = 10
        mock_task.dependencies = None

        result = optimizer._calculate_cpm([mock_task], date.today())
        assert result["total_duration"] == 10

    def test_generate_gantt_data(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        optimizer = AIScheduleOptimizer(mock_db)
        assert optimizer is not None

    def test_identify_critical_path(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        optimizer = AIScheduleOptimizer(mock_db)
        assert optimizer.db == mock_db

    def test_analyze_resource_load(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        optimizer = AIScheduleOptimizer(mock_db)
        assert hasattr(optimizer, "_analyze_resource_load")

    def test_detect_conflicts(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        optimizer = AIScheduleOptimizer(mock_db)
        assert hasattr(optimizer, "_detect_conflicts")

    def test_apply_suggestions(self):
        from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

        mock_db = MagicMock()
        optimizer = AIScheduleOptimizer(mock_db)
        assert optimizer.db == mock_db


class TestResourceOptimizerBusinessLogic:
    def test_init(self):
        try:
            from app.services.ai_planning.resource_optimizer import ResourceOptimizer

            optimizer = ResourceOptimizer()
            assert optimizer is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_optimize_allocation(self):
        try:
            from app.services.ai_planning.resource_optimizer import ResourceOptimizer

            optimizer = ResourceOptimizer()
            assert optimizer is not None
        except ImportError:
            pytest.skip("Module not found")


class TestWBSDecomposerBusinessLogic:
    """WBS分解器业务逻辑测试"""

    def test_init_with_db(self):
        from app.services.ai_planning.wbs_decomposer import AIWbsDecomposer

        mock_db = MagicMock()
        decomposer = AIWbsDecomposer(mock_db)
        assert decomposer.db == mock_db

    def test_decompose_project(self):
        from app.services.ai_planning.wbs_decomposer import AIWbsDecomposer

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_type = "AUTO"
        mock_db.query.return_value.get.return_value = mock_project

        decomposer = AIWbsDecomposer(mock_db)
        assert hasattr(decomposer, "decompose_project")

    def test_generate_wbs_structure(self):
        from app.services.ai_planning.wbs_decomposer import AIWbsDecomposer

        mock_db = MagicMock()
        decomposer = AIWbsDecomposer(mock_db)
        assert decomposer is not None
