# -*- coding: utf-8 -*-
"""第二十五批 - purchase_request_from_bom_service 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from datetime import date

pytest.importorskip("app.services.purchase_request_from_bom_service")

from app.services.purchase_request_from_bom_service import (
    get_purchase_items_from_bom,
    determine_supplier_for_item,
    group_items_by_supplier,
    build_request_items,
    format_request_items,
    create_purchase_request,
)


def _make_bom_item(
    source_type="PURCHASE",
    quantity=Decimal("10"),
    purchased_qty=Decimal("0"),
    unit_price=Decimal("5"),
    supplier_id=None,
    material_id=None,
    is_key_item=False,
    required_date=None,
):
    item = MagicMock()
    item.source_type = source_type
    item.quantity = quantity
    item.purchased_qty = purchased_qty
    item.unit_price = unit_price
    item.supplier_id = supplier_id
    item.material_id = material_id
    item.is_key_item = is_key_item
    item.required_date = required_date
    item.material_code = "MAT001"
    item.material_name = "测试物料"
    item.specification = "规格A"
    item.unit = "件"
    return item


# ── get_purchase_items_from_bom ───────────────────────────────────────────────

class TestGetPurchaseItemsFromBom:
    def test_filters_by_purchase_source_type(self):
        bom = MagicMock()
        item1 = _make_bom_item(source_type="PURCHASE")
        item2 = _make_bom_item(source_type="MAKE")
        bom.items.filter.return_value.all.return_value = [item1]
        result = get_purchase_items_from_bom(bom)
        bom.items.filter.assert_called_once()
        assert result == [item1]

    def test_returns_empty_when_no_purchase_items(self):
        bom = MagicMock()
        bom.items.filter.return_value.all.return_value = []
        result = get_purchase_items_from_bom(bom)
        assert result == []


# ── determine_supplier_for_item ───────────────────────────────────────────────

class TestDetermineSupplierForItem:
    def test_uses_default_supplier_id_if_provided(self):
        db = MagicMock()
        item = _make_bom_item()
        result = determine_supplier_for_item(db, item, 42)
        assert result == 42

    def test_falls_back_to_item_supplier_id(self):
        db = MagicMock()
        item = _make_bom_item(supplier_id=7)
        result = determine_supplier_for_item(db, item, None)
        assert result == 7

    def test_falls_back_to_material_default_supplier(self):
        db = MagicMock()
        item = _make_bom_item(supplier_id=None, material_id=10)
        material = MagicMock(default_supplier_id=99)
        db.query.return_value.filter.return_value.first.return_value = material
        result = determine_supplier_for_item(db, item, None)
        assert result == 99

    def test_returns_zero_when_no_supplier(self):
        db = MagicMock()
        item = _make_bom_item(supplier_id=None, material_id=None)
        result = determine_supplier_for_item(db, item, None)
        assert result == 0

    def test_material_without_default_supplier_returns_zero(self):
        db = MagicMock()
        item = _make_bom_item(supplier_id=None, material_id=5)
        material = MagicMock(default_supplier_id=None)
        db.query.return_value.filter.return_value.first.return_value = material
        result = determine_supplier_for_item(db, item, None)
        assert result == 0


# ── group_items_by_supplier ───────────────────────────────────────────────────

class TestGroupItemsBySupplier:
    def test_groups_items_by_their_supplier(self):
        db = MagicMock()
        item1 = _make_bom_item(supplier_id=1)
        item2 = _make_bom_item(supplier_id=2)
        item3 = _make_bom_item(supplier_id=1)
        groups = group_items_by_supplier(db, [item1, item2, item3], None)
        assert 1 in groups
        assert 2 in groups
        assert len(groups[1]) == 2
        assert len(groups[2]) == 1

    def test_all_items_under_default_supplier(self):
        db = MagicMock()
        items = [_make_bom_item(supplier_id=None) for _ in range(3)]
        groups = group_items_by_supplier(db, items, 5)
        assert 5 in groups
        assert len(groups[5]) == 3

    def test_empty_items_returns_empty_dict(self):
        db = MagicMock()
        groups = group_items_by_supplier(db, [], None)
        assert len(groups) == 0


# ── build_request_items ───────────────────────────────────────────────────────

class TestBuildRequestItems:
    def test_calculates_remaining_qty_and_amount(self):
        item = _make_bom_item(quantity=Decimal("10"), purchased_qty=Decimal("3"), unit_price=Decimal("5"))
        items, total = build_request_items([item])
        assert len(items) == 1
        assert items[0]["quantity"] == Decimal("7")
        assert items[0]["amount"] == Decimal("35")
        assert total == Decimal("35")

    def test_skips_item_when_remaining_qty_zero(self):
        item = _make_bom_item(quantity=Decimal("5"), purchased_qty=Decimal("5"))
        items, total = build_request_items([item])
        assert len(items) == 0
        assert total == Decimal("0")

    def test_skips_item_when_remaining_qty_negative(self):
        item = _make_bom_item(quantity=Decimal("3"), purchased_qty=Decimal("5"))
        items, total = build_request_items([item])
        assert len(items) == 0

    def test_multiple_items_total(self):
        item1 = _make_bom_item(quantity=Decimal("10"), purchased_qty=Decimal("0"), unit_price=Decimal("2"))
        item2 = _make_bom_item(quantity=Decimal("5"), purchased_qty=Decimal("0"), unit_price=Decimal("4"))
        items, total = build_request_items([item1, item2])
        assert len(items) == 2
        assert total == Decimal("40")

    def test_item_dict_keys(self):
        item = _make_bom_item()
        items, _ = build_request_items([item])
        expected_keys = {"bom_item_id", "material_id", "material_code", "material_name",
                         "specification", "unit", "quantity", "unit_price", "amount",
                         "required_date", "is_key_item"}
        assert expected_keys.issubset(set(items[0].keys()))

    def test_zero_unit_price_item(self):
        item = _make_bom_item(quantity=Decimal("10"), unit_price=Decimal("0"))
        items, total = build_request_items([item])
        assert len(items) == 1
        assert total == Decimal("0")


# ── format_request_items ──────────────────────────────────────────────────────

class TestFormatRequestItems:
    def test_converts_decimal_to_float(self):
        raw_items = [{
            "bom_item_id": 1,
            "material_id": 2,
            "material_code": "M001",
            "material_name": "物料",
            "specification": "规格",
            "unit": "件",
            "quantity": Decimal("7"),
            "unit_price": Decimal("5"),
            "amount": Decimal("35"),
            "required_date": None,
            "is_key_item": False,
        }]
        result = format_request_items(raw_items)
        assert isinstance(result[0]["quantity"], float)
        assert isinstance(result[0]["unit_price"], float)
        assert isinstance(result[0]["amount"], float)

    def test_required_date_formatted_as_isoformat(self):
        d = date(2025, 6, 1)
        raw_items = [{
            "bom_item_id": 1, "material_id": 2, "material_code": "M",
            "material_name": "物", "specification": "规", "unit": "件",
            "quantity": Decimal("1"), "unit_price": Decimal("1"), "amount": Decimal("1"),
            "required_date": d, "is_key_item": False,
        }]
        result = format_request_items(raw_items)
        assert result[0]["required_date"] == "2025-06-01"

    def test_none_required_date_stays_none(self):
        raw_items = [{
            "bom_item_id": 1, "material_id": None, "material_code": "M",
            "material_name": "物", "specification": "规", "unit": "件",
            "quantity": Decimal("1"), "unit_price": Decimal("1"), "amount": Decimal("1"),
            "required_date": None, "is_key_item": False,
        }]
        result = format_request_items(raw_items)
        assert result[0]["required_date"] is None

    def test_empty_list_returns_empty(self):
        assert format_request_items([]) == []


# ── create_purchase_request ───────────────────────────────────────────────────

class TestCreatePurchaseRequest:
    def test_creates_pr_with_correct_fields(self):
        db = MagicMock()
        bom = MagicMock()
        bom.project_id = 10
        bom.machine_id = 20
        bom.id = 5
        bom.bom_no = "BOM001"
        bom.required_date = date(2025, 8, 1)

        request_items = []
        total_amount = Decimal("500")
        generate_request_no = MagicMock(return_value="PR20250001")

        pr = create_purchase_request(
            db, bom, supplier_id=3, supplier_name="供应商A",
            request_items=request_items, total_amount=total_amount,
            current_user_id=1, generate_request_no=generate_request_no
        )

        db.add.assert_called()
        db.flush.assert_called()
        assert pr.request_no == "PR20250001"
        assert pr.source_type == "BOM"
        assert pr.status == "DRAFT"

    def test_creates_pr_items_for_each_item(self):
        db = MagicMock()
        bom = MagicMock()
        bom.project_id = 1
        bom.machine_id = None
        bom.id = 1
        bom.bom_no = "BOM002"
        bom.required_date = None

        request_items = [
            {"bom_item_id": 1, "material_id": 2, "material_code": "M", "material_name": "物",
             "specification": "规", "unit": "件", "quantity": Decimal("5"),
             "unit_price": Decimal("2"), "amount": Decimal("10"), "required_date": None},
        ]
        generate_request_no = MagicMock(return_value="PR001")

        create_purchase_request(
            db, bom, supplier_id=0, supplier_name="",
            request_items=request_items, total_amount=Decimal("10"),
            current_user_id=1, generate_request_no=generate_request_no
        )

        # Should add once for PurchaseRequest + once for each PurchaseRequestItem
        assert db.add.call_count >= 2

    def test_supplier_id_zero_sets_none(self):
        db = MagicMock()
        bom = MagicMock()
        bom.project_id = 1
        bom.machine_id = None
        bom.id = 1
        bom.bom_no = "BOM003"
        bom.required_date = None
        generate_request_no = MagicMock(return_value="PR002")

        pr = create_purchase_request(
            db, bom, supplier_id=0, supplier_name="",
            request_items=[], total_amount=Decimal("0"),
            current_user_id=1, generate_request_no=generate_request_no
        )
        assert pr.supplier_id is None
