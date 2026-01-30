# -*- coding: utf-8 -*-
"""
InventoryAnalysisService 综合单元测试

测试覆盖:
- get_turnover_rate_data: 获取库存周转率数据
- get_stale_materials_data: 获取呆滞物料数据
- get_safety_stock_compliance_data: 获取安全库存达标率数据
- get_abc_analysis_data: 获取物料ABC分类数据
- get_cost_occupancy_data: 获取库存成本占用数据
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestGetTurnoverRateData:
    """测试 get_turnover_rate_data 方法"""

    def test_returns_turnover_data_with_materials(self):
        """测试有物料时返回周转率数据"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        # Mock material data
        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = 1
        mock_material.category_name = "电气件"
        mock_material.current_stock = 100
        mock_material.standard_price = 50.0
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 500.0

        result = InventoryAnalysisService.get_turnover_rate_data(
            mock_db,
            date.today() - timedelta(days=30),
            date.today()
        )

        assert "summary" in result
        assert "category_breakdown" in result
        assert result["summary"]["total_materials"] == 1

    def test_returns_zero_turnover_when_no_inventory(self):
        """测试无库存时周转率为零"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 0

        result = InventoryAnalysisService.get_turnover_rate_data(
            mock_db,
            date.today() - timedelta(days=30),
            date.today()
        )

        assert result["summary"]["total_inventory_value"] == 0
        assert result["summary"]["turnover_rate"] == 0

    def test_filters_by_category_id(self):
        """测试按分类ID筛选"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 0

        result = InventoryAnalysisService.get_turnover_rate_data(
            mock_db,
            date.today() - timedelta(days=30),
            date.today(),
            category_id=1
        )

        assert result["summary"]["total_materials"] == 0

    def test_calculates_category_breakdown(self):
        """测试计算分类明细"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material1 = MagicMock()
        mock_material1.id = 1
        mock_material1.material_code = "MAT001"
        mock_material1.material_name = "物料1"
        mock_material1.category_id = 1
        mock_material1.category_name = "电气件"
        mock_material1.current_stock = 100
        mock_material1.standard_price = 50.0
        mock_material1.unit = "个"

        mock_material2 = MagicMock()
        mock_material2.id = 2
        mock_material2.material_code = "MAT002"
        mock_material2.material_name = "物料2"
        mock_material2.category_id = 2
        mock_material2.category_name = "机械件"
        mock_material2.current_stock = 50
        mock_material2.standard_price = 100.0
        mock_material2.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            mock_material1, mock_material2
        ]
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 100.0

        result = InventoryAnalysisService.get_turnover_rate_data(
            mock_db,
            date.today() - timedelta(days=30),
            date.today()
        )

        assert len(result["category_breakdown"]) == 2

    def test_handles_materials_without_category(self):
        """测试处理无分类的物料"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = None
        mock_material.category_name = None
        mock_material.current_stock = 100
        mock_material.standard_price = 50.0
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 0

        result = InventoryAnalysisService.get_turnover_rate_data(
            mock_db,
            date.today() - timedelta(days=30),
            date.today()
        )

        assert len(result["category_breakdown"]) == 1
        assert result["category_breakdown"][0]["category_name"] == "未分类"


class TestGetStaleMaterialsData:
    """测试 get_stale_materials_data 方法"""

    def test_returns_stale_materials(self):
        """测试返回呆滞物料"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "呆滞物料"
        mock_material.category_name = "电气件"
        mock_material.current_stock = 100
        mock_material.standard_price = 50.0
        mock_material.updated_at = datetime.now() - timedelta(days=100)
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]

        result = InventoryAnalysisService.get_stale_materials_data(mock_db, threshold_days=90)

        assert result["summary"]["stale_count"] == 1
        assert len(result["stale_materials"]) == 1

    def test_returns_empty_when_no_stale_materials(self):
        """测试无呆滞物料时返回空"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "活跃物料"
        mock_material.category_name = "电气件"
        mock_material.current_stock = 100
        mock_material.standard_price = 50.0
        mock_material.updated_at = datetime.now() - timedelta(days=10)
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]

        result = InventoryAnalysisService.get_stale_materials_data(mock_db, threshold_days=90)

        assert result["summary"]["stale_count"] == 0

    def test_calculates_age_distribution(self):
        """测试计算库龄分布"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        materials = []
        for days in [10, 45, 75, 120]:
            m = MagicMock()
            m.id = days
            m.material_code = f"MAT{days}"
            m.material_name = f"物料{days}"
            m.category_name = "电气件"
            m.current_stock = 10
            m.standard_price = 100.0
            m.updated_at = datetime.now() - timedelta(days=days)
            m.unit = "个"
            materials.append(m)

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = InventoryAnalysisService.get_stale_materials_data(mock_db, threshold_days=90)

        assert len(result["age_distribution"]) == 4

    def test_handles_material_without_updated_at(self):
        """测试处理无更新时间的物料"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "无更新时间物料"
        mock_material.category_name = "电气件"
        mock_material.current_stock = 100
        mock_material.standard_price = 50.0
        mock_material.updated_at = None
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]

        result = InventoryAnalysisService.get_stale_materials_data(mock_db, threshold_days=90)

        # 无更新时间视为长期呆滞
        assert result["summary"]["stale_count"] == 1

    def test_uses_custom_threshold(self):
        """测试使用自定义阈值"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "物料"
        mock_material.category_name = "电气件"
        mock_material.current_stock = 100
        mock_material.standard_price = 50.0
        mock_material.updated_at = datetime.now() - timedelta(days=50)
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]

        # 使用30天阈值，50天未更新应该算呆滞
        result = InventoryAnalysisService.get_stale_materials_data(mock_db, threshold_days=30)
        assert result["summary"]["stale_count"] == 1

        # 使用60天阈值，50天未更新不算呆滞
        result = InventoryAnalysisService.get_stale_materials_data(mock_db, threshold_days=60)
        assert result["summary"]["stale_count"] == 0


class TestGetSafetyStockComplianceData:
    """测试 get_safety_stock_compliance_data 方法"""

    def test_returns_compliance_data(self):
        """测试返回合规数据"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.category_name = "电气件"
        mock_material.current_stock = 100
        mock_material.safety_stock = 50
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]

        result = InventoryAnalysisService.get_safety_stock_compliance_data(mock_db)

        assert "summary" in result
        assert result["summary"]["compliant"] == 1

    def test_identifies_warning_materials(self):
        """测试识别警告物料"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "低库存物料"
        mock_material.category_name = "电气件"
        mock_material.current_stock = 30
        mock_material.safety_stock = 50
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]

        result = InventoryAnalysisService.get_safety_stock_compliance_data(mock_db)

        assert result["summary"]["warning"] == 1
        assert len(result["warning_materials"]) == 1

    def test_identifies_out_of_stock_materials(self):
        """测试识别缺货物料"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "缺货物料"
        mock_material.category_name = "电气件"
        mock_material.current_stock = 0
        mock_material.safety_stock = 50
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]

        result = InventoryAnalysisService.get_safety_stock_compliance_data(mock_db)

        assert result["summary"]["out_of_stock"] == 1
        assert len(result["out_of_stock_materials"]) == 1

    def test_handles_materials_without_safety_stock(self):
        """测试处理未设置安全库存的物料"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "无安全库存物料"
        mock_material.category_name = "电气件"
        mock_material.current_stock = 100
        mock_material.safety_stock = 0
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [mock_material]

        result = InventoryAnalysisService.get_safety_stock_compliance_data(mock_db)

        assert result["summary"]["no_safety_stock_set"] == 1

    def test_calculates_compliant_rate(self):
        """测试计算达标率"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        materials = []
        # 2个达标，1个警告，1个缺货
        for i, (stock, safety) in enumerate([(100, 50), (60, 60), (30, 50), (0, 50)]):
            m = MagicMock()
            m.id = i
            m.material_code = f"MAT{i}"
            m.material_name = f"物料{i}"
            m.category_name = "电气件"
            m.current_stock = stock
            m.safety_stock = safety
            m.unit = "个"
            materials.append(m)

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = InventoryAnalysisService.get_safety_stock_compliance_data(mock_db)

        assert result["summary"]["compliant"] == 2
        assert result["summary"]["warning"] == 1
        assert result["summary"]["out_of_stock"] == 1
        assert result["summary"]["compliant_rate"] == 50.0  # 2 out of 4


class TestGetAbcAnalysisData:
    """测试 get_abc_analysis_data 方法"""

    def test_returns_abc_classification(self):
        """测试返回ABC分类"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        # Mock query results
        mock_result = MagicMock()
        mock_result.material_code = "MAT001"
        mock_result.material_name = "高价值物料"
        mock_result.category_name = "电气件"
        mock_result.total_amount = 10000.0
        mock_result.order_count = 5

        mock_db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = [mock_result]

        result = InventoryAnalysisService.get_abc_analysis_data(
            mock_db,
            date.today() - timedelta(days=365),
            date.today()
        )

        assert "abc_materials" in result
        assert "abc_summary" in result
        assert result["total_materials"] == 1

    def test_returns_empty_when_no_data(self):
        """测试无数据时返回空"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = InventoryAnalysisService.get_abc_analysis_data(
            mock_db,
            date.today() - timedelta(days=365),
            date.today()
        )

        assert result["total_materials"] == 0
        assert result["total_amount"] == 0

    def test_classifies_materials_correctly(self):
        """测试正确分类物料"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        # 创建不同金额的物料，测试ABC分类
        materials = []
        for i, amount in enumerate([7000, 2000, 1000]):  # 70%, 20%, 10%
            m = MagicMock()
            m.material_code = f"MAT{i}"
            m.material_name = f"物料{i}"
            m.category_name = "电气件"
            m.total_amount = float(amount)
            m.order_count = 1
            materials.append(m)

        mock_db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = materials

        result = InventoryAnalysisService.get_abc_analysis_data(
            mock_db,
            date.today() - timedelta(days=365),
            date.today()
        )

        assert result["abc_summary"]["A"]["count"] == 1
        assert result["abc_summary"]["B"]["count"] == 1
        assert result["abc_summary"]["C"]["count"] == 1

    def test_calculates_cumulative_percentage(self):
        """测试计算累计百分比"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_result = MagicMock()
        mock_result.material_code = "MAT001"
        mock_result.material_name = "物料"
        mock_result.category_name = "电气件"
        mock_result.total_amount = 10000.0
        mock_result.order_count = 5

        mock_db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = [mock_result]

        result = InventoryAnalysisService.get_abc_analysis_data(
            mock_db,
            date.today() - timedelta(days=365),
            date.today()
        )

        # 单个物料应该是100%
        assert result["abc_materials"][0]["cumulative_percent"] == 100.0


class TestGetCostOccupancyData:
    """测试 get_cost_occupancy_data 方法"""

    def test_returns_cost_occupancy_data(self):
        """测试返回成本占用数据"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_category = MagicMock()
        mock_category.category_id = 1
        mock_category.category_name = "电气件"
        mock_category.inventory_value = 50000.0
        mock_category.material_count = 10

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = [mock_category]

        # Mock top materials query
        mock_material = MagicMock()
        mock_material.material_code = "MAT001"
        mock_material.material_name = "高库存物料"
        mock_material.category_name = "电气件"
        mock_material.inventory_value = 10000.0
        mock_material.current_stock = 100
        mock_material.unit = "个"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_material]

        result = InventoryAnalysisService.get_cost_occupancy_data(mock_db)

        assert "category_occupancy" in result
        assert "top_materials" in result
        assert "summary" in result

    def test_calculates_value_percentage(self):
        """测试计算价值百分比"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        categories = []
        for i, value in enumerate([30000, 20000]):
            c = MagicMock()
            c.category_id = i
            c.category_name = f"分类{i}"
            c.inventory_value = float(value)
            c.material_count = 5
            categories.append(c)

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = categories
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = InventoryAnalysisService.get_cost_occupancy_data(mock_db)

        # 总价值50000，第一个分类30000占60%
        assert result["category_occupancy"][0]["value_percentage"] == 60.0

    def test_returns_top_materials(self):
        """测试返回高库存占用物料"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = []

        materials = []
        for i in range(3):
            m = MagicMock()
            m.material_code = f"MAT{i}"
            m.material_name = f"物料{i}"
            m.category_name = "电气件"
            m.inventory_value = float((3 - i) * 10000)
            m.current_stock = 100
            m.unit = "个"
            materials.append(m)

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = materials

        result = InventoryAnalysisService.get_cost_occupancy_data(mock_db)

        assert len(result["top_materials"]) == 3

    def test_handles_empty_data(self):
        """测试处理空数据"""
        from app.services.inventory_analysis_service import InventoryAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = InventoryAnalysisService.get_cost_occupancy_data(mock_db)

        assert result["summary"]["total_inventory_value"] == 0
        assert result["summary"]["total_categories"] == 0


class TestInventoryAnalysisServiceSingleton:
    """测试单例模式"""

    def test_singleton_exists(self):
        """测试单例存在"""
        from app.services.inventory_analysis_service import inventory_analysis_service

        assert inventory_analysis_service is not None

    def test_singleton_is_instance(self):
        """测试单例是正确的实例"""
        from app.services.inventory_analysis_service import (
            InventoryAnalysisService,
            inventory_analysis_service,
        )

        assert isinstance(inventory_analysis_service, InventoryAnalysisService)
