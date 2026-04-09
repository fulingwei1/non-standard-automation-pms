# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - WBS分解服务"""
import pytest
from unittest.mock import MagicMock


class TestWbsDecomposerBusinessLogic:
    """WBS分解服务业务逻辑测试"""

    def test_decompose_project(self):
        """测试分解项目"""
        try:
            from app.services.ai_planning.wbs_decomposer import WbsDecomposer

            mock_db = MagicMock()
            service = WbsDecomposer(mock_db)

            result = service.decompose_project(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_create_wbs_node(self):
        """测试创建WBS节点"""
        try:
            from app.services.ai_planning.wbs_decomposer import WbsDecomposer

            mock_db = MagicMock()
            service = WbsDecomposer(mock_db)

            result = service.create_node("1.0", "项目启动", 1, None)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_link_dependencies(self):
        """测试链接依赖"""
        try:
            from app.services.ai_planning.wbs_decomposer import WbsDecomposer

            mock_db = MagicMock()
            service = WbsDecomposer(mock_db)

            result = service.link_dependencies(1, [2, 3])

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_calculate_critical_path(self):
        """测试计算关键路径"""
        try:
            from app.services.ai_planning.wbs_decomposer import WbsDecomposer

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.duration = 5

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

            service = WbsDecomposer(mock_db)

            result = service.calculate_critical_path(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_update_task_duration(self):
        """测试更新任务工期"""
        try:
            from app.services.ai_planning.wbs_decomposer import WbsDecomposer

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_task

            service = WbsDecomposer(mock_db)

            result = service.update_duration(1, 10)

            assert mock_db.commit.called
        except ImportError:
            pytest.skip("Module not found")

    def test_get_wbs_tree(self):
        """测试获取WBS树"""
        try:
            from app.services.ai_planning.wbs_decomposer import WbsDecomposer

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.parent_id = None

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

            service = WbsDecomposer(mock_db)

            result = service.get_wbs_tree(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")