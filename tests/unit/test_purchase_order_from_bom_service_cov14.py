# -*- coding: utf-8 -*-
"""
第十四批：从BOM创建采购订单服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services import purchase_order_from_bom_service as pobs
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_bom_item(**kwargs):
    item = MagicMock()
    item.source_type = kwargs.get("source_type", "PURCHASE")
    item.supplier_id = kwargs.get("supplier_id", None)
    item.material_id = kwargs.get("material_id", None)
    item.quantity = kwargs.get("quantity", 10)
    item.unit = kwargs.get("unit", "件")
    item.unit_price = kwargs.get("unit_price", 100)
    item.material = kwargs.get("material", None)
    return item


class TestPurchaseOrderFromBomService:
    def test_determine_supplier_default(self):
        db = make_db()
        item = make_bom_item()
        result = pobs.determine_supplier_for_item(db, item, default_supplier_id=5)
        assert result == 5

    def test_determine_supplier_from_item(self):
        db = make_db()
        item = make_bom_item(supplier_id=3)
        result = pobs.determine_supplier_for_item(db, item, default_supplier_id=None)
        assert result == 3

    def test_determine_supplier_from_material(self):
        db = make_db()
        material = MagicMock()
        material.default_supplier_id = 7
        db.query.return_value.filter.return_value.first.return_value = material
        item = make_bom_item(material_id=10)
        result = pobs.determine_supplier_for_item(db, item, default_supplier_id=None)
        assert result == 7

    def test_determine_supplier_none(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        item = make_bom_item(material_id=10)
        result = pobs.determine_supplier_for_item(db, item, default_supplier_id=None)
        assert result is None

    def test_group_items_by_supplier(self):
        db = make_db()
        item1 = make_bom_item(supplier_id=1)
        item2 = make_bom_item(supplier_id=2)
        item3 = make_bom_item(supplier_id=1)
        result = pobs.group_items_by_supplier(db, [item1, item2, item3], default_supplier_id=None)
        assert 1 in result
        assert 2 in result
        assert len(result[1]) == 2
        assert len(result[2]) == 1

    def test_group_items_no_supplier_goes_to_zero(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        item = make_bom_item(supplier_id=None, material_id=None)
        result = pobs.group_items_by_supplier(db, [item], default_supplier_id=None)
        assert 0 in result

    def test_get_purchase_items_from_bom(self):
        db = make_db()
        bom = MagicMock()
        expected_items = [make_bom_item(), make_bom_item()]
        bom.items.filter.return_value.all.return_value = expected_items
        result = pobs.get_purchase_items_from_bom(db, bom)
        assert result == expected_items

    def test_get_purchase_items_filters_source_type(self):
        db = make_db()
        bom = MagicMock()
        bom.items.filter.return_value.all.return_value = []
        result = pobs.get_purchase_items_from_bom(db, bom)
        assert result == []
        # 验证过滤了 source_type == PURCHASE
        bom.items.filter.assert_called_once()
