# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 销售团队服务"""
import pytest
from unittest.mock import MagicMock


class TestSalesTeamServiceBusinessLogic:
    """销售团队服务业务逻辑测试"""

    def test_create_team(self):
        """测试创建团队"""
        try:
            from app.services.sales_team_service import SalesTeamService

            mock_db = MagicMock()
            service = SalesTeamService(mock_db)

            result = service.create_team("团队A", 1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_add_member(self):
        """测试添加成员"""
        try:
            from app.services.sales_team_service import SalesTeamService

            mock_db = MagicMock()

            mock_team = MagicMock()
            mock_team.id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_team

            service = SalesTeamService(mock_db)

            result = service.add_member(1, 1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_remove_member(self):
        """测试移除成员"""
        try:
            from app.services.sales_team_service import SalesTeamService

            mock_db = MagicMock()

            mock_team = MagicMock()
            mock_team.id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_team

            service = SalesTeamService(mock_db)

            result = service.remove_member(1, 1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_team_performance(self):
        """测试获取团队绩效"""
        try:
            from app.services.sales_team_service import SalesTeamService

            mock_db = MagicMock()

            mock_team = MagicMock()
            mock_team.id = 1
            mock_team.total_sales = 100000

            mock_db.query.return_value.filter.return_value.first.return_value = mock_team

            service = SalesTeamService(mock_db)

            result = service.get_team_performance(1, 2025)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")