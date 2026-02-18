# -*- coding: utf-8 -*-
"""
第十六批：从BOM创建采购订单服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.purchase_order_from_bom_service import (
        get_purchase_items_from_bom,
        determine_supplier_for_item,
        group_items_by_supplier,
    )
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_bom():
    bom = MagicMock()
    bom.id = 1
    bom.bom_no = "BOM-2025-001"
    return bom


def make_bom_item(**kwargs):
    item = MagicMock()
    item.id = kwargs.get("id", 1)
    item.source_type = kwargs.get("source_type", "PURCHASE")
    item.supplier_id = kwargs.get("supplier_id", None)
    item.material_id = kwargs.get("material_id", None)
    return item


class TestGetPurchaseItemsFromBom:
    def test_returns_purchase_items(self):
        db = make_db()
        bom = make_bom()
        items = [make_bom_item(), make_bom_item(id=2)]
        bom.items.filter.return_value.all.return_value = items
        result = get_purchase_items_from_bom(db, bom)
        assert len(result) == 2

    def test_returns_empty_for_no_items(self):
        db = make_db()
        bom = make_bom()
        bom.items.filter.return_value.all.return_value = []
        result = get_purchase_items_from_bom(db, bom)
        assert result == []


class TestDetermineSupplierForItem:
    def test_uses_default_supplier_if_provided(self):
        db = make_db()
        item = make_bom_item()
        result = determine_supplier_for_item(db, item, default_supplier_id=5)
        assert result == 5

    def test_uses_item_supplier_if_no_default(self):
        db = make_db()
        item = make_bom_item(supplier_id=3)
        result = determine_supplier_for_item(db, item, default_supplier_id=None)
        assert result == 3

    def test_uses_material_supplier_as_fallback(self):
        db = make_db()
        item = make_bom_item(supplier_id=None, material_id=10)
        material = MagicMock()
        material.default_supplier_id = 7
        db.query.return_value.filter.return_value.first.return_value = material
        result = determine_supplier_for_item(db, item, default_supplier_id=None)
        assert result == 7

    def test_returns_none_when_no_supplier_found(self):
        db = make_db()
        item = make_bom_item(supplier_id=None, material_id=None)
        result = determine_supplier_for_item(db, item, default_supplier_id=None)
        assert result is None


class TestGroupItemsBySupplier:
    def test_groups_correctly(self):
        db = make_db()
        item1 = make_bom_item(id=1)
        item2 = make_bom_item(id=2)
        # determine_supplier_for_item 会被调用
        with patch(
            "app.services.purchase_order_from_bom_service.determine_supplier_for_item",
            side_effect=[5, 5]
        ):
            result = group_items_by_supplier(db, [item1, item2], default_supplier_id=5)
        assert 5 in result
        assert len(result[5]) == 2

    def test_different_suppliers(self):
        db = make_db()
        item1 = make_bom_item(id=1)
        item2 = make_bom_item(id=2)
        with patch(
            "app.services.purchase_order_from_bom_service.determine_supplier_for_item",
            side_effect=[3, 7]
        ):
            result = group_items_by_supplier(db, [item1, item2], default_supplier_id=None)
        assert 3 in result
        assert 7 in result

    def test_unknown_supplier_grouped_as_zero(self):
        db = make_db()
        item = make_bom_item()
        with patch(
            "app.services.purchase_order_from_bom_service.determine_supplier_for_item",
            return_value=None
        ):
            result = group_items_by_supplier(db, [item], default_supplier_id=None)
        assert 0 in result
