# -*- coding: utf-8 -*-
"""
inventory_analysis_service 单元测试

测试库存分析服务的各个方法：
- 库存周转率
- 呆滞物料分析
- 安全库存达标率
- ABC分类
- 成本占用分析
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.inventory_analysis_service import InventoryAnalysisService


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_material(
    material_id=1,
    material_code="M001",
    material_name="测试物料",
    category_id=1,
    category_name="电子元件",
    current_stock=100,
    safety_stock=50,
    standard_price=10.0,
    unit="个",
    is_active=True,
    updated_at=None,
):
    """创建模拟的物料对象"""
    mock = MagicMock()
    mock.id = material_id
    mock.material_code = material_code
    mock.material_name = material_name
    mock.category_id = category_id
    mock.category_name = category_name
    mock.current_stock = current_stock
    mock.safety_stock = safety_stock
    mock.standard_price = standard_price
    mock.unit = unit
    mock.is_active = is_active
    mock.updated_at = updated_at or datetime.now()
    return mock


@pytest.mark.unit
class TestGetTurnoverRateData:
    """测试 get_turnover_rate_data 方法"""

    def test_returns_empty_summary_for_no_materials(self):
        """测试无物料时返回空汇总"""
        db = create_mock_db_session()
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            []
        )
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = (
            0
        )

        result = InventoryAnalysisService.get_turnover_rate_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )

        assert result["summary"]["total_materials"] == 0
        assert result["summary"]["total_inventory_value"] == 0

    def test_calculates_inventory_value(self):
        """测试计算库存价值"""
        db = create_mock_db_session()
        materials = [
            create_mock_material(current_stock=100, standard_price=10.0),  # 1000
            create_mock_material(current_stock=50, standard_price=20.0),  # 1000
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            materials
        )
        db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.all.return_value = (
            materials
        )
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = (
            0
        )

        result = InventoryAnalysisService.get_turnover_rate_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )

        assert result["summary"]["total_inventory_value"] == 2000.0
        assert result["summary"]["total_materials"] == 2

    def test_groups_by_category(self):
        """测试按分类分组"""
        db = create_mock_db_session()
        materials = [
            create_mock_material(
                category_name="电子元件", current_stock=100, standard_price=10.0
            ),
            create_mock_material(
                category_name="机械件", current_stock=50, standard_price=20.0
            ),
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            materials
        )
        db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.all.return_value = (
            materials
        )
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = (
            0
        )

        result = InventoryAnalysisService.get_turnover_rate_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )

        assert len(result["category_breakdown"]) == 2

    def test_handles_none_price_values(self):
        """测试处理空价格值"""
        db = create_mock_db_session()
        # 有库存但价格为None的情况
        material = create_mock_material(current_stock=10, standard_price=None)
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            material
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.all.return_value = [
            material
        ]
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = (
            0
        )

        result = InventoryAnalysisService.get_turnover_rate_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )

        # 价格为None时，库存价值应该为0
        assert result["summary"]["total_inventory_value"] == 0


@pytest.mark.unit
class TestGetStaleMaterialsData:
    """测试 get_stale_materials_data 方法"""

    def test_returns_empty_for_no_materials(self):
        """测试无物料时返回空"""
        db = create_mock_db_session()
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            []
        )

        result = InventoryAnalysisService.get_stale_materials_data(db)

        assert result["stale_materials"] == []
        assert result["summary"]["stale_count"] == 0

    def test_identifies_stale_materials(self):
        """测试识别呆滞物料"""
        db = create_mock_db_session()
        # 120天前更新 - 呆滞
        stale_material = create_mock_material(
            material_code="M001",
            current_stock=100,
            standard_price=10.0,
            updated_at=datetime.now() - timedelta(days=120),
        )
        # 30天前更新 - 不呆滞
        fresh_material = create_mock_material(
            material_code="M002",
            current_stock=50,
            standard_price=20.0,
            updated_at=datetime.now() - timedelta(days=30),
        )
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            stale_material,
            fresh_material,
        ]

        result = InventoryAnalysisService.get_stale_materials_data(db, threshold_days=90)

        assert result["summary"]["stale_count"] == 1
        assert result["stale_materials"][0]["material_code"] == "M001"

    def test_calculates_age_distribution(self):
        """测试计算库龄分布"""
        db = create_mock_db_session()
        materials = [
            create_mock_material(
                updated_at=datetime.now() - timedelta(days=10),
                current_stock=100,
                standard_price=10.0,
            ),  # 30天以内
            create_mock_material(
                updated_at=datetime.now() - timedelta(days=45),
                current_stock=100,
                standard_price=10.0,
            ),  # 30-60天
            create_mock_material(
                updated_at=datetime.now() - timedelta(days=75),
                current_stock=100,
                standard_price=10.0,
            ),  # 60-90天
            create_mock_material(
                updated_at=datetime.now() - timedelta(days=100),
                current_stock=100,
                standard_price=10.0,
            ),  # 90天以上
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            materials
        )

        result = InventoryAnalysisService.get_stale_materials_data(db)

        age_dist = {d["age_range"]: d["value"] for d in result["age_distribution"]}
        assert age_dist["30天以内"] == 1000.0
        assert age_dist["30-60天"] == 1000.0
        assert age_dist["60-90天"] == 1000.0
        assert age_dist["90天以上"] == 1000.0

    def test_sorts_by_inventory_value(self):
        """测试按库存金额排序"""
        db = create_mock_db_session()
        materials = [
            create_mock_material(
                material_code="M001",
                current_stock=10,
                standard_price=10.0,
                updated_at=datetime.now() - timedelta(days=100),
            ),  # 100
            create_mock_material(
                material_code="M002",
                current_stock=100,
                standard_price=10.0,
                updated_at=datetime.now() - timedelta(days=100),
            ),  # 1000
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            materials
        )

        result = InventoryAnalysisService.get_stale_materials_data(db)

        assert result["stale_materials"][0]["material_code"] == "M002"  # 高价值优先


@pytest.mark.unit
class TestGetSafetyStockComplianceData:
    """测试 get_safety_stock_compliance_data 方法"""

    def test_returns_empty_for_no_materials(self):
        """测试无物料时返回空"""
        db = create_mock_db_session()
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            []
        )

        result = InventoryAnalysisService.get_safety_stock_compliance_data(db)

        assert result["summary"]["total_materials"] == 0
        assert result["summary"]["compliant_rate"] == 0

    def test_counts_compliant_materials(self):
        """测试统计达标物料"""
        db = create_mock_db_session()
        materials = [
            create_mock_material(current_stock=100, safety_stock=50),  # 达标
            create_mock_material(current_stock=100, safety_stock=100),  # 达标
            create_mock_material(current_stock=30, safety_stock=50),  # 预警
            create_mock_material(current_stock=0, safety_stock=50),  # 缺货
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            materials
        )

        result = InventoryAnalysisService.get_safety_stock_compliance_data(db)

        assert result["summary"]["compliant"] == 2
        assert result["summary"]["warning"] == 1
        assert result["summary"]["out_of_stock"] == 1

    def test_excludes_no_safety_stock_from_rate(self):
        """测试达标率排除未设安全库存"""
        db = create_mock_db_session()
        materials = [
            create_mock_material(current_stock=100, safety_stock=50),  # 达标
            create_mock_material(current_stock=0, safety_stock=0),  # 未设安全库存
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = (
            materials
        )

        result = InventoryAnalysisService.get_safety_stock_compliance_data(db)

        assert result["summary"]["no_safety_stock_set"] == 1
        assert result["summary"]["compliant_rate"] == 100.0  # 1/1 = 100%

    def test_calculates_shortage_qty(self):
        """测试计算缺货数量"""
        db = create_mock_db_session()
        material = create_mock_material(current_stock=30, safety_stock=50)
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            material
        ]

        result = InventoryAnalysisService.get_safety_stock_compliance_data(db)

        assert result["warning_materials"][0]["shortage_qty"] == 20


@pytest.mark.unit
class TestGetAbcAnalysisData:
    """测试 get_abc_analysis_data 方法"""

    def test_returns_empty_for_no_data(self):
        """测试无数据时返回空"""
        db = create_mock_db_session()
        db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = (
            []
        )

        result = InventoryAnalysisService.get_abc_analysis_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )

        assert result["abc_materials"] == []
        assert result["total_materials"] == 0

    def test_classifies_abc_correctly(self):
        """测试正确分类ABC"""
        db = create_mock_db_session()
        # 创建10个物料，金额递减
        results = []
        for i in range(10):
            mock = MagicMock()
            mock.material_code = f"M{i:03d}"
            mock.material_name = f"物料{i}"
            mock.category_name = "测试分类"
            mock.total_amount = 1000 - i * 100  # 1000, 900, 800, ...
            mock.order_count = 1
            results.append(mock)

        db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = (
            results
        )

        result = InventoryAnalysisService.get_abc_analysis_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )

        # 验证A类累计占比约70%
        a_materials = [m for m in result["abc_materials"] if m["abc_class"] == "A"]
        assert len(a_materials) > 0

        # 验证汇总
        assert result["abc_summary"]["A"]["count"] > 0
        assert result["abc_summary"]["B"]["count"] >= 0
        assert result["abc_summary"]["C"]["count"] >= 0

    def test_calculates_cumulative_percent(self):
        """测试计算累计百分比"""
        db = create_mock_db_session()
        results = []
        for i in range(3):
            mock = MagicMock()
            mock.material_code = f"M{i:03d}"
            mock.material_name = f"物料{i}"
            mock.category_name = "测试分类"
            mock.total_amount = 100  # 各100，共300
            mock.order_count = 1
            results.append(mock)

        db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = (
            results
        )

        result = InventoryAnalysisService.get_abc_analysis_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )

        # 每个约33.33%
        assert result["abc_materials"][0]["amount_percent"] == pytest.approx(33.33, 0.1)
        assert result["abc_materials"][2]["cumulative_percent"] == pytest.approx(100.0, 0.1)


@pytest.mark.unit
class TestGetCostOccupancyData:
    """测试 get_cost_occupancy_data 方法"""

    def test_returns_empty_for_no_categories(self):
        """测试无分类时返回空"""
        db = create_mock_db_session()
        db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = (
            []
        )
        db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = InventoryAnalysisService.get_cost_occupancy_data(db)

        assert result["category_occupancy"] == []
        assert result["summary"]["total_inventory_value"] == 0

    def test_groups_by_category(self):
        """测试按分类分组"""
        db = create_mock_db_session()
        categories = [
            MagicMock(
                category_id=1,
                category_name="电子元件",
                inventory_value=10000,
                material_count=50,
            ),
            MagicMock(
                category_id=2,
                category_name="机械件",
                inventory_value=5000,
                material_count=30,
            ),
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = (
            categories
        )
        db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = InventoryAnalysisService.get_cost_occupancy_data(db)

        assert len(result["category_occupancy"]) == 2
        assert result["summary"]["total_inventory_value"] == 15000.0

    def test_calculates_value_percentage(self):
        """测试计算价值占比"""
        db = create_mock_db_session()
        categories = [
            MagicMock(
                category_id=1,
                category_name="电子元件",
                inventory_value=7000,
                material_count=50,
            ),
            MagicMock(
                category_id=2,
                category_name="机械件",
                inventory_value=3000,
                material_count=30,
            ),
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = (
            categories
        )
        db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = InventoryAnalysisService.get_cost_occupancy_data(db)

        # 7000/10000 = 70%
        assert result["category_occupancy"][0]["value_percentage"] == 70.0

    def test_returns_top_materials(self):
        """测试返回TOP物料"""
        db = create_mock_db_session()
        db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = (
            []
        )

        top_materials = [
            MagicMock(
                material_code="M001",
                material_name="高价值物料",
                category_name="电子元件",
                inventory_value=5000,
                current_stock=100,
                unit="个",
            )
        ]
        db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            top_materials
        )

        result = InventoryAnalysisService.get_cost_occupancy_data(db)

        assert len(result["top_materials"]) == 1
        assert result["top_materials"][0]["material_code"] == "M001"
