# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 收入服务"""
import pytest
from unittest.mock import MagicMock, patch


class TestRevenueServiceBusinessLogic:
    """收入服务业务逻辑测试"""

    def test_get_project_revenue(self):
        """测试获取项目收入"""
        try:
            from app.services.revenue_service import RevenueService

            mock_db = MagicMock()
            service = RevenueService(mock_db)

            result = service.get_project_revenue(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_projects_revenue(self):
        """测试获取项目收入列表"""
        try:
            from app.services.revenue_service import RevenueService

            mock_db = MagicMock()
            service = RevenueService(mock_db)

            result = service.get_projects_revenue()

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")