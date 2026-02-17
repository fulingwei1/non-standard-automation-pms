# -*- coding: utf-8 -*-
"""
J1组单元测试 - project.py（聚合模块）
验证该模块正确地从子模块导出函数，并且各函数可调用
"""
import sys
from unittest.mock import MagicMock, patch

import pytest


MODULE = "app.utils.scheduled_tasks.project"


# ============================================================================
# 辅助
# ============================================================================

def make_mock_db_ctx():
    mock_session = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_session)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx, mock_session


# ============================================================================
# 测试：模块正确导出
# ============================================================================


@pytest.mark.unit
class TestProjectModuleImports:
    """project.py 聚合模块的导入测试"""

    def test_module_imports_successfully(self):
        """模块可以正常导入"""
        import app.utils.scheduled_tasks.project as project_module
        assert project_module is not None

    def test_calculate_project_health_exported(self):
        """calculate_project_health 从子模块导出"""
        import app.utils.scheduled_tasks.project as project_module
        assert hasattr(project_module, "calculate_project_health")
        assert callable(project_module.calculate_project_health)

    def test_daily_health_snapshot_exported(self):
        """daily_health_snapshot 从子模块导出"""
        import app.utils.scheduled_tasks.project as project_module
        assert hasattr(project_module, "daily_health_snapshot")
        assert callable(project_module.daily_health_snapshot)

    def test_check_overdue_issues_exported(self):
        """check_overdue_issues 从子模块导出"""
        import app.utils.scheduled_tasks.project as project_module
        assert hasattr(project_module, "check_overdue_issues")
        assert callable(project_module.check_overdue_issues)

    def test_check_blocking_issues_exported(self):
        """check_blocking_issues 从子模块导出"""
        import app.utils.scheduled_tasks.project as project_module
        assert hasattr(project_module, "check_blocking_issues")
        assert callable(project_module.check_blocking_issues)

    def test_check_timeout_issues_exported(self):
        """check_timeout_issues 从子模块导出"""
        import app.utils.scheduled_tasks.project as project_module
        assert hasattr(project_module, "check_timeout_issues")
        assert callable(project_module.check_timeout_issues)

    def test_daily_issue_statistics_snapshot_exported(self):
        """daily_issue_statistics_snapshot 从子模块导出"""
        import app.utils.scheduled_tasks.project as project_module
        assert hasattr(project_module, "daily_issue_statistics_snapshot")
        assert callable(project_module.daily_issue_statistics_snapshot)

    def test_all_exports_defined(self):
        """__all__ 中所有名称都已定义"""
        import app.utils.scheduled_tasks.project as project_module
        all_exports = project_module.__all__
        for name in all_exports:
            obj = getattr(project_module, name, None)
            # 允许 None（导入失败时为 None），但必须有该属性
            assert hasattr(project_module, name), f"模块缺少导出: {name}"


# ============================================================================
# 测试：通过聚合模块调用实际函数（端到端 smoke test）
# ============================================================================


@pytest.mark.unit
class TestProjectModuleFunctionCalls:
    """通过 project.py 调用函数的冒烟测试"""

    def test_calculate_project_health_callable_via_aggregation(self):
        """通过聚合模块调用 calculate_project_health"""
        import app.utils.scheduled_tasks.project as project_module

        with patch("app.utils.scheduled_tasks.project_health_tasks.get_db_session") as mock_db:
            mock_db.side_effect = Exception("mocked")
            result = project_module.calculate_project_health()

        assert "error" in result

    def test_daily_health_snapshot_callable_via_aggregation(self):
        """通过聚合模块调用 daily_health_snapshot"""
        import app.utils.scheduled_tasks.project as project_module

        with patch("app.utils.scheduled_tasks.project_health_tasks.get_db_session") as mock_db:
            mock_db.side_effect = Exception("mocked")
            result = project_module.daily_health_snapshot()

        assert "error" in result

    def test_check_overdue_issues_callable_via_aggregation(self):
        """通过聚合模块调用 check_overdue_issues（issue_tasks 版）"""
        import app.utils.scheduled_tasks.project as project_module

        with patch("app.utils.scheduled_tasks.issue_tasks.get_db_session") as mock_db:
            mock_db.side_effect = Exception("mocked")
            result = project_module.check_overdue_issues()

        assert "error" in result

    def test_check_blocking_issues_callable_via_aggregation(self):
        """通过聚合模块调用 check_blocking_issues"""
        import app.utils.scheduled_tasks.project as project_module

        with patch("app.utils.scheduled_tasks.issue_tasks.get_db_session") as mock_db:
            mock_db.side_effect = Exception("mocked")
            result = project_module.check_blocking_issues()

        assert "error" in result

    def test_check_timeout_issues_callable_via_aggregation(self):
        """通过聚合模块调用 check_timeout_issues"""
        import app.utils.scheduled_tasks.project as project_module

        with patch("app.utils.scheduled_tasks.issue_tasks.get_db_session") as mock_db:
            mock_db.side_effect = Exception("mocked")
            result = project_module.check_timeout_issues()

        assert "error" in result

    def test_daily_issue_statistics_snapshot_callable_via_aggregation(self):
        """通过聚合模块调用 daily_issue_statistics_snapshot"""
        import app.utils.scheduled_tasks.project as project_module

        with patch("app.utils.scheduled_tasks.issue_tasks.get_db_session") as mock_db:
            mock_db.side_effect = Exception("mocked")
            result = project_module.daily_issue_statistics_snapshot()

        assert "error" in result
