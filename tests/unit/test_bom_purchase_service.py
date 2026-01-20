# -*- coding: utf-8 -*-
"""
BOM采购订单服务单元测试
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.models.material import BomHeader, BomItem, Material

from app.services.purchase_order_from_bom_service import (
    build_order_items,
    calculate_order_item,
    calculate_summary,
    create_order_preview,
    determine_supplier_for_item,
    get_purchase_items_from_bom,
    group_items_by_supplier,
)


@pytest.mark.unit
class TestCalculateOrderItem:
    """测试计算订单明细"""

    def test_calculate_order_item_with_price(self):
        """测试有价格的订单明细计算"""
        item = Mock()
        item.quantity = Decimal("10")
        item.purchased_qty = Decimal("2")
        item.unit_price = Decimal("100")
        item.unit = "个"
        item.material_id = 1
        item.bom_item_id = 1
        item.material_code = "MAT001"
        item.material_name = "物料1"
        item.specification = "规格A"
        item.required_date = date(2026, 1, 20)

        remaining_qty = item.quantity - item.purchased_qty

        result = calculate_order_item(item, 1, remaining_qty)

        assert result["item_no"] == 1
        assert result["quantity"] == Decimal("8")
        assert result["unit_price"] == Decimal("100")
        assert result["amount"] == Decimal("800")
        assert result["tax_rate"] == Decimal("13")
        assert result["tax_amount"] == Decimal("104")
        assert result["amount_with_tax"] == Decimal("904")
        assert result["unit"] == "个"
        assert result["required_date"] == date(2026, 1, 20)

    def test_calculate_order_item_no_price(self):
        """测试没有价格的订单明细计算"""
        item = Mock()
        item.quantity = Decimal("5")
        item.purchased_qty = Decimal("0")
        item.unit_price = None
        item.unit = "个"
        item.material_id = 1
        item.bom_item_id = 1
        item.material_code = "MAT001"
        item.material_name = "物料1"
        item.specification = "规格A"

        result = calculate_order_item(item, 1, item.quantity)

        assert result["unit_price"] == Decimal("0")
        assert result["amount"] == Decimal("0")
        assert result["tax_amount"] == Decimal("0")
        assert result["amount_with_tax"] == Decimal("0")

    def test_calculate_order_item_default_unit(self):
        """测试默认单位"""
        item = Mock()
        item.quantity = Decimal("10")
        item.purchased_qty = Decimal("0")
        item.unit_price = Decimal("100")
        item.unit = None
        item.material_id = 1
        item.bom_item_id = 1
        item.material_code = "MAT001"
        item.material_name = "物料1"
        item.specification = "规格A"

        result = calculate_order_item(item, 1, item.quantity)

        assert result["unit"] == "件"

    def test_calculate_order_item_fractional_qty(self):
        """测试小数数量计算"""
        item = Mock()
        item.quantity = Decimal("10.5")
        item.purchased_qty = Decimal("3.2")
        item.unit_price = Decimal("50")
        item.unit = "个"
        item.material_id = 1
        item.bom_item_id = 1
        item.material_code = "MAT001"
        item.material_name = "物料1"
        item.specification = "规格A"

        remaining_qty = item.quantity - item.purchased_qty

        result = calculate_order_item(item, 1, remaining_qty)

        assert result["quantity"] == Decimal("7.3")
        assert result["amount"] == Decimal("365")
        assert result["tax_amount"] == Decimal("47.45")

    def test_calculate_order_item_large_tax_calculation(self):
        """测试大额税额计算"""
        item = Mock()
        item.quantity = Decimal("1000")
        item.purchased_qty = Decimal("0")
        item.unit_price = Decimal("999.99")
        item.unit = "个"
        item.material_id = 1
        item.bom_item_id = 1
        item.material_code = "MAT001"
        item.material_name = "物料1"
        item.specification = "规格A"

        result = calculate_order_item(item, 1, item.quantity)

        expected_amount = Decimal("999990.00")
        expected_tax = Decimal("129998.70")

        assert result["amount"] == expected_amount
        assert result["tax_amount"] == expected_tax
        assert result["amount_with_tax"] == expected_amount + expected_tax


@pytest.mark.unit
class TestBuildOrderItems:
    """测试构建订单明细列表"""

    def test_build_order_items_success(self):
        """测试成功构建订单明细"""
        item1 = Mock()
        item1.quantity = Decimal("10")
        item1.purchased_qty = Decimal("2")
        item1.unit_price = Decimal("100")
        item1.unit = "个"
        item1.material_id = 1
        item1.bom_item_id = 1
        item1.material_code = "MAT001"
        item1.material_name = "物料1"
        item1.specification = "规格A"

        item3 = Mock()
        item3.quantity = Decimal("20")
        item3.purchased_qty = Decimal("0")
        item3.unit_price = Decimal("25")
        item3.unit = "个"
        item3.material_id = 3
        item3.bom_item_id = 3
        item3.material_code = "MAT003"
        item3.material_name = "物料3"
        item3.specification = "规格C"

        order_items, total_amount, total_tax, total_with_tax = build_order_items(
            [item1, item3]
        )

        assert len(order_items) == 2
        assert order_items[0]["item_no"] == 1
        assert order_items[1]["item_no"] == 2

        assert total_amount == Decimal("800") + Decimal("500")
        assert total_tax == Decimal("104") + Decimal("65")
        assert total_with_tax == Decimal("904") + Decimal("565")

    def test_build_order_items_skip_fully_purchased(self):
        """测试跳过已完全采购的物料"""
        item1 = Mock()
        item1.quantity = Decimal("10")
        item1.purchased_qty = Decimal("10")
        item1.unit_price = Decimal("100")
        item1.unit = "个"
        item1.material_id = 1
        item1.bom_item_id = 1
        item1.material_code = "MAT001"
        item1.material_name = "物料1"
        item1.specification = "规格A"

        item2 = Mock()
        item2.quantity = Decimal("5")
        item2.purchased_qty = Decimal("2")
        item2.unit_price = Decimal("50")
        item2.unit = "个"
        item2.material_id = 2
        item2.bom_item_id = 2
        item2.material_code = "MAT002"
        item2.material_name = "物料2"
        item2.specification = "规格B"

        order_items, total_amount, total_tax, total_with_tax = build_order_items(
            [item1, item2]
        )

        assert len(order_items) == 1
        assert order_items[0]["item_no"] == 1
        assert total_amount == Decimal("150")

    def test_build_order_items_empty_list(self):
        """测试空列表"""
        order_items, total_amount, total_tax, total_with_tax = build_order_items([])

        assert order_items == []
        assert total_amount == Decimal("0")
        assert total_tax == Decimal("0")
        assert total_with_tax == Decimal("0")

    def test_build_order_items_all_purchased(self):
        """测试所有物料都已采购"""
        item1 = Mock()
        item1.quantity = Decimal("10")
        item1.purchased_qty = Decimal("10")
        item1.unit_price = Decimal("100")
        item1.unit = "个"
        item1.material_id = 1
        item1.bom_item_id = 1
        item1.material_code = "MAT001"
        item1.material_name = "物料1"
        item1.specification = "规格A"

        item2 = Mock()
        item2.quantity = Decimal("5")
        item2.purchased_qty = Decimal("5")
        item2.unit_price = Decimal("50")
        item2.unit = "个"
        item2.material_id = 2
        item2.bom_item_id = 2
        item2.material_code = "MAT002"
        item2.material_name = "物料2"
        item2.specification = "规格B"

        order_items, total_amount, total_tax, total_with_tax = build_order_items(
            [item1, item2]
        )

        assert order_items == []
        assert total_amount == Decimal("0")
        assert total_tax == Decimal("0")
        assert total_with_tax == Decimal("0")

    def test_build_order_items_item_no_sequential(self):
        """测试序号连续递增"""
        items = []
        for i in range(5):
            item = Mock()
            item.quantity = Decimal(str(i + 1))
            item.purchased_qty = Decimal("0")
            item.unit_price = Decimal("100")
            item.unit = "个"
            item.material_id = i + 1
            item.bom_item_id = i + 1
            item.material_code = f"MAT{i:03d}"
            item.material_name = f"物料{i}"
            item.specification = f"规格{i}"
            items.append(item)

        order_items, _, _, _ = build_order_items(items)

        for i, item in enumerate(order_items, start=1):
            assert item["item_no"] == i


@pytest.mark.unit
class TestCalculateSummary:
    """测试计算汇总统计"""

    def test_calculate_summary_single_order(self):
        """测试单个订单的汇总"""
        orders = [
            {
                "items": [{"item_no": 1}, {"item_no": 2}],
                "total_amount": 1000.0,
                "amount_with_tax": 1130.0,
            }
        ]

        summary = calculate_summary(orders)

        assert summary["total_orders"] == 1
        assert summary["total_items"] == 2
        assert summary["total_amount"] == 1000.0
        assert summary["total_amount_with_tax"] == 1130.0

    def test_calculate_summary_multiple_orders(self):
        """测试多个订单的汇总"""
        orders = [
            {
                "items": [{"item_no": 1}, {"item_no": 2}],
                "total_amount": 1000.0,
                "amount_with_tax": 1130.0,
            },
            {
                "items": [{"item_no": 1}],
                "total_amount": 500.0,
                "amount_with_tax": 565.0,
            },
            {
                "items": [],
                "total_amount": 0.0,
                "amount_with_tax": 0.0,
            },
        ]

        summary = calculate_summary(orders)

        assert summary["total_orders"] == 3
        assert summary["total_items"] == 3
        assert summary["total_amount"] == 1500.0
        assert summary["total_amount_with_tax"] == 1695.0

    def test_calculate_summary_empty_list(self):
        """测试空列表"""
        summary = calculate_summary([])

        assert summary["total_orders"] == 0
        assert summary["total_items"] == 0
        assert summary["total_amount"] == 0.0
        assert summary["total_amount_with_tax"] == 0.0


@pytest.mark.unit
class TestCreateOrderPreview:
    """测试创建订单预览"""

    def test_create_order_preview_success(self):
        """测试成功创建订单预览"""
        supplier = Mock()
        supplier.id = 1
        supplier.supplier_name = "测试供应商"

        bom = Mock()
        bom.bom_no = "BOM-TEST-001"
        bom.project = Mock()
        bom.project.project_name = "测试项目"

        order_items = [
            {
                "material_code": "MAT001",
                "material_name": "物料1",
                "quantity": Decimal("10"),
                "unit_price": Decimal("100"),
                "amount": Decimal("1000"),
                "tax_amount": Decimal("130"),
                "amount_with_tax": Decimal("1130"),
            }
        ]

        preview = create_order_preview(
            supplier,
            supplier.id,
            bom,
            1,
            order_items,
            Decimal("1000"),
            Decimal("130"),
            Decimal("1130"),
        )

        assert preview["supplier_id"] == 1
        assert preview["supplier_name"] == "测试供应商"
        assert preview["project_id"] == 1
        assert preview["project_name"] == "测试项目"
        assert preview["order_type"] == "NORMAL"
        assert preview["order_title"] == "BOM-TEST-001 - 测试供应商"
        assert preview["total_amount"] == 1000.0
        assert preview["tax_amount"] == 130.0
        assert preview["amount_with_tax"] == 1130.0
        assert preview["item_count"] == 1
        assert preview["items"] == order_items

    def test_create_order_preview_no_project(self):
        """测试BOM没有关联项目"""
        supplier = Mock()
        supplier.id = 1
        supplier.supplier_name = "测试供应商"

        bom = Mock()
        bom.bom_no = "BOM-TEST-001"
        bom.project = None

        order_items = []

        preview = create_order_preview(
            supplier,
            supplier.id,
            bom,
            0,
            order_items,
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        )

        assert preview["project_name"] is None
        assert preview["project_id"] == 0


@pytest.mark.unit
class TestDetermineSupplierForItem:
    """测试确定物料供应商"""

    def test_default_supplier_priority(self, db_session: Session):
        """测试默认供应商优先级最高"""
        item = Mock()
        item.supplier_id = 2

        supplier_id = determine_supplier_for_item(db_session, item, 1)

        assert supplier_id == 1

    def test_bom_item_supplier_when_no_default(self, db_session: Session):
        """测试没有默认供应商时使用BOM项供应商"""
        item = Mock()
        item.supplier_id = 1
        item.material_id = None

        supplier_id = determine_supplier_for_item(db_session, item, None)

        assert supplier_id == 1

    def test_material_default_supplier_fallback(self, db_session: Session):
        """测试回退到物料默认供应商"""

        material = Material(
            material_code="MAT-001",
            material_name="物料1",
            default_supplier_id=3,
            is_active=True,
        )
        db_session.add(material)
        db_session.flush()

        item = Mock()
        item.material_id = material.id
        item.supplier_id = None

        supplier_id = determine_supplier_for_item(db_session, item, None)

        assert supplier_id == 3

    def test_no_supplier_available(self, db_session: Session):
        """测试没有可用供应商时返回None"""
        item = Mock()
        item.material_id = None
        item.supplier_id = None

        supplier_id = determine_supplier_for_item(db_session, item, None)

        assert supplier_id is None

    def test_material_without_default_supplier(self, db_session: Session):
        """测试物料没有默认供应商时返回None"""

        material = Material(
            material_code="MAT-001",
            material_name="物料1",
            default_supplier_id=None,
            is_active=True,
        )
        db_session.add(material)
        db_session.flush()

        item = Mock()
        item.material_id = material.id
        item.supplier_id = None

        supplier_id = determine_supplier_for_item(db_session, item, None)

        assert supplier_id is None


@pytest.mark.unit
class TestGroupItemsBySupplier:
    """测试按供应商分组物料"""

    def test_group_items_by_supplier_success(self, db_session: Session):
        """测试成功按供应商分组"""
        supplier1_id = 1
        supplier2_id = 2
        default_supplier_id = 3

        item1 = Mock()
        item1.supplier_id = supplier1_id
        item1.material_id = None

        item2 = Mock()
        item2.supplier_id = supplier1_id
        item2.material_id = None

        item3 = Mock()
        item3.supplier_id = supplier2_id
        item3.material_id = None

        item4 = Mock()
        item4.supplier_id = None
        item4.material_id = None

        grouped = group_items_by_supplier(
            db_session, [item1, item2, item3, item4], default_supplier_id
        )

        assert supplier1_id in grouped
        assert supplier2_id in grouped
        assert default_supplier_id in grouped
        assert 0 in grouped

        assert len(grouped[supplier1_id]) == 2
        assert len(grouped[supplier2_id]) == 1
        assert len(grouped[default_supplier_id]) == 1
        assert len(grouped[0]) == 1

    def test_group_items_with_default_supplier(self, db_session: Session):
        """测试使用默认供应商分组"""
        default_supplier_id = 1

        item1 = Mock()
        item1.supplier_id = default_supplier_id
        item1.material_id = None

        item2 = Mock()
        item2.supplier_id = None
        item2.material_id = None

        item3 = Mock()
        item3.supplier_id = None
        item3.material_id = None

        grouped = group_items_by_supplier(
            db_session, [item1, item2, item3], default_supplier_id
        )

        assert default_supplier_id in grouped
        assert len(grouped[default_supplier_id]) == 3

    def test_group_items_empty_list(self, db_session: Session):
        """测试空列表返回空字典"""
        grouped = group_items_by_supplier(db_session, [], None)

        assert grouped == {}

    def test_group_items_all_no_supplier(self, db_session: Session):
        """测试所有物料都没有供应商"""
        item1 = Mock()
        item1.supplier_id = None
        item1.material_id = None

        item2 = Mock()
        item2.supplier_id = None
        item2.material_id = None

        grouped = group_items_by_supplier(db_session, [item1, item2], None)

        assert 0 in grouped
        assert len(grouped[0]) == 2


@pytest.mark.unit
class TestGetPurchaseItemsFromBom:
    """测试从BOM获取采购物料"""

    def test_get_purchase_items_filters_by_source_type(self, db_session: Session):
        """测试只返回采购类型的物料"""
        from app.models.material import BomItem, Project

        project = Project(
            project_code="PJ-TEST-001",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        bom = BomHeader(
            bom_no="BOM-TEST-001",
            bom_name="测试BOM",
            project_id=project.id,
            version="1.0",
            status="DRAFT",
            created_by=1,
        )
        db_session.add(bom)
        db_session.flush()

        item1 = BomItem(
            bom_id=bom.id,
            item_no=1,
            material_code="MAT001",
            material_name="物料1",
            source_type="PURCHASE",
            quantity=Decimal("10"),
            unit="个",
        )
        item2 = BomItem(
            bom_id=bom.id,
            item_no=2,
            material_code="MAT002",
            material_name="物料2",
            source_type="MANUFACTURE",
            quantity=Decimal("5"),
            unit="个",
        )
        item3 = BomItem(
            bom_id=bom.id,
            item_no=3,
            material_code="MAT003",
            material_name="物料3",
            source_type="PURCHASE",
            quantity=Decimal("20"),
            unit="个",
        )
        item4 = BomItem(
            bom_id=bom.id,
            item_no=4,
            material_code="MAT004",
            material_name="物料4",
            source_type="OUTSOURCE",
            quantity=Decimal("15"),
            unit="个",
        )

        db_session.add_all([item1, item2, item3, item4])
        db_session.commit()

        purchase_items = get_purchase_items_from_bom(db_session, bom)

        assert len(purchase_items) == 2
        assert all(item.source_type == "PURCHASE" for item in purchase_items)

    def test_get_purchase_items_empty_bom(self, db_session: Session):
        """测试空BOM返回空列表"""
        from app.models.material import Project

        project = Project(
            project_code="PJ-TEST-002",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        bom = BomHeader(
            bom_no="BOM-TEST-002",
            bom_name="测试BOM",
            project_id=project.id,
            version="1.0",
            status="DRAFT",
            created_by=1,
        )
        db_session.add(bom)
        db_session.commit()

        purchase_items = get_purchase_items_from_bom(db_session, bom)

        assert purchase_items == []

    def test_get_purchase_items_no_purchase_type(self, db_session: Session):
        """测试没有采购类型物料时返回空列表"""
        from app.models.material import Project

        project = Project(
            project_code="PJ-TEST-003",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        bom = BomHeader(
            bom_no="BOM-TEST-003",
            bom_name="测试BOM",
            project_id=project.id,
            version="1.0",
            status="DRAFT",
            created_by=1,
        )
        db_session.add(bom)
        db_session.flush()

        item1 = BomItem(
            bom_id=bom.id,
            item_no=1,
            material_code="MAT001",
            material_name="物料1",
            source_type="MANUFACTURE",
            quantity=Decimal("10"),
            unit="个",
        )
        item2 = BomItem(
            bom_id=bom.id,
            item_no=2,
            material_code="MAT002",
            material_name="物料2",
            source_type="OUTSOURCE",
            quantity=Decimal("5"),
            unit="个",
        )

        db_session.add_all([item1, item2])
        db_session.commit()

        purchase_items = get_purchase_items_from_bom(db_session, bom)

        assert purchase_items == []
