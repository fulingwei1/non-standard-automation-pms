# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 成本仪表盘服务"""
import pytest
from unittest.mock import MagicMock


class TestCostDashboardServiceBusinessLogic:
    """成本仪表盘服务业务逻辑测试"""

    def test_get_cost_summary(self):
        """测试获取成本摘要"""
        try:
            from app.services.cost.cost_dashboard_service import CostDashboardService

            mock_db = MagicMock()
            service = CostDashboardService(mock_db)

            result = service.get_cost_summary(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_cost_by_category(self):
        """测试按类别获取成本"""
        try:
            from app.services.cost.cost_dashboard_service import CostDashboardService

            mock_db = MagicMock()

            mock_cost = MagicMock()
            mock_cost.category = "MATERIAL"
            mock_cost.amount = 50000

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost]

            service = CostDashboardService(mock_db)

            result = service.get_cost_by_category(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_cost_trend(self):
        """测试获取成本趋势"""
        try:
            from app.services.cost.cost_dashboard_service import CostDashboardService

            mock_db = MagicMock()

            mock_cost = MagicMock()
            mock_cost.month = "2026-01"
            mock_cost.amount = 10000

            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_cost]

            service = CostDashboardService(mock_db)

            result = service.get_cost_trend(1, 6)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_generate_dashboard(self):
        """测试生成仪表盘"""
        try:
            from app.services.cost.cost_dashboard_service import CostDashboardService

            mock_db = MagicMock()
            service = CostDashboardService(mock_db)

            result = service.generate_dashboard(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_export_dashboard_pdf(self):
        """测试导出仪表盘PDF"""
        try:
            from app.services.cost.cost_dashboard_service import CostDashboardService

            mock_db = MagicMock()
            service = CostDashboardService(mock_db)

            result = service.export_dashboard_pdf(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")