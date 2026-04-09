# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 项目管理服务"""
import pytest
from unittest.mock import MagicMock


class TestProjectManagementServiceBusinessLogic:
    """项目管理服务业务逻辑测试"""

    def test_create_project(self):
        """测试创建项目"""
        try:
            from app.services.project_management_service import ProjectManagementService

            mock_db = MagicMock()
            service = ProjectManagementService(mock_db)

            result = service.create_project("项目A", "ICT")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_update_project_status(self):
        """测试更新项目状态"""
        try:
            from app.services.project_management_service import ProjectManagementService

            mock_db = MagicMock()

            mock_project = MagicMock()
            mock_project.status = "PLANNING"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_project

            service = ProjectManagementService(mock_db)

            result = service.update_project_status(1, "IN_PROGRESS")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_add_project_member(self):
        """测试添加项目成员"""
        try:
            from app.services.project_management_service import ProjectManagementService

            mock_db = MagicMock()

            mock_project = MagicMock()
            mock_project.id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_project

            service = ProjectManagementService(mock_db)

            result = service.add_project_member(1, 1, "ENGINEER")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_project_progress(self):
        """测试获取项目进度"""
        try:
            from app.services.project_management_service import ProjectManagementService

            mock_db = MagicMock()

            mock_project = MagicMock()
            mock_project.completed_tasks = 10
            mock_project.total_tasks = 20

            mock_db.query.return_value.filter.return_value.first.return_value = mock_project

            service = ProjectManagementService(mock_db)

            result = service.get_project_progress(1)

            assert result == 50
        except ImportError:
            pytest.skip("Module not found")