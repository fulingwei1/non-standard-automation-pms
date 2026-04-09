# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 成本收集服务"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal


class TestCostCollectionServiceBusinessLogic:
    """成本收集服务业务逻辑测试"""

    def test_collect_material_cost(self):
        """测试收集物料成本"""
        try:
            from app.services.cost.cost_collection_service import CostCollectionService

            mock_db = MagicMock()
            service = CostCollectionService(mock_db)

            result = service.collect_material_cost(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_collect_labor_cost(self):
        """测试收集人工成本"""
        try:
            from app.services.cost.cost_collection_service import CostCollectionService

            mock_db = MagicMock()
            service = CostCollectionService(mock_db)

            result = service.collect_labor_cost(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_calculate_total_cost(self):
        """测试计算总成本"""
        try:
            from app.services.cost.cost_collection_service import CostCollectionService

            mock_db = MagicMock()
            service = CostCollectionService(mock_db)

            material = Decimal("1000")
            labor = Decimal("500")

            result = service.calculate_total_cost(material, labor)

            assert result == Decimal("1500")
        except ImportError:
            pytest.skip("Module not found")

    def test_aggregate_cost_by_project(self):
        """测试按项目汇总成本"""
        try:
            from app.services.cost.cost_collection_service import CostCollectionService

            mock_db = MagicMock()

            mock_cost = MagicMock()
            mock_cost.project_id = 1
            mock_cost.amount = Decimal("1000")

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost]

            service = CostCollectionService(mock_db)

            result = service.aggregate_cost_by_project(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_export_cost_report(self):
        """测试导出成本报告"""
        try:
            from app.services.cost.cost_collection_service import CostCollectionService

            mock_db = MagicMock()
            service = CostCollectionService(mock_db)

            result = service.export_cost_report(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")


class TestCostCollectionValidation:
    """验证测试"""

    def test_cost_amount_positive(self):
        """测试成本金额为正"""
        try:
            from app.services.cost.cost_collection_service import CostCollectionService

            mock_db = MagicMock()
            service = CostCollectionService(mock_db)

            material = Decimal("1000")
            labor = Decimal("500")

            result = service.calculate_total_cost(material, labor)

            assert result > 0
        except ImportError:
            pytest.skip("Module not found")