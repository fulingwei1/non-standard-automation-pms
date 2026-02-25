# -*- coding: utf-8 -*-
"""Tests for app/schemas/material.py"""
import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.material import (
    MaterialCategoryCreate,
    MaterialCategoryResponse,
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    WarehouseStatistics,
    MaterialSearchResponse,
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    BomItemCreate,
    BomCreate,
    BomUpdate,
    BomResponse,
)


class TestMaterialCategoryCreate:
    def test_valid(self):
        c = MaterialCategoryCreate(category_code="C001", category_name="电气件")
        assert c.sort_order == 0
        assert c.parent_id is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            MaterialCategoryCreate()

    def test_long_code(self):
        with pytest.raises(ValidationError):
            MaterialCategoryCreate(category_code="x" * 51, category_name="T")


class TestMaterialCreate:
    def test_minimal(self):
        m = MaterialCreate(material_name="螺丝M8")
        assert m.material_code is None
        assert m.unit == "件"
        assert m.source_type == "PURCHASE"
        assert m.lead_time_days == 0
        assert m.is_key_material is False

    def test_full(self):
        m = MaterialCreate(
            material_code="M001", material_name="螺丝",
            category_id=1, specification="M8x20",
            brand="国标", unit="个", drawing_no="DWG001",
            material_type="标准件", source_type="PURCHASE",
            standard_price=Decimal("0.5"), safety_stock=Decimal("1000"),
            lead_time_days=7, min_order_qty=Decimal("100"),
            is_key_material=True, remark="常用",
        )
        assert m.standard_price == Decimal("0.5")

    def test_negative_lead_time(self):
        with pytest.raises(ValidationError):
            MaterialCreate(material_name="T", lead_time_days=-1)

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            MaterialCreate()


class TestMaterialUpdate:
    def test_all_none(self):
        m = MaterialUpdate()
        assert m.material_name is None

    def test_partial(self):
        m = MaterialUpdate(material_name="新名称", is_active=False)
        assert m.is_active is False


class TestMaterialResponse:
    def test_valid(self):
        m = MaterialResponse(id=1, material_code="M001", material_name="T")
        assert m.unit == "件"
        assert m.is_active is True
        assert m.standard_price == 0
        assert m.current_stock == 0


class TestWarehouseStatistics:
    def test_defaults(self):
        w = WarehouseStatistics()
        assert w.total_items == 0
        assert w.warehouse_utilization == 0.0

    def test_with_data(self):
        w = WarehouseStatistics(total_items=100, low_stock_items=5)
        assert w.low_stock_items == 5


class TestSupplierCreate:
    def test_valid(self):
        s = SupplierCreate(supplier_code="S001", supplier_name="供应商A")
        assert s.contact_person is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            SupplierCreate()

    def test_full(self):
        s = SupplierCreate(
            supplier_code="S001", supplier_name="供应商A",
            contact_person="张三", contact_phone="123",
            tax_number="91310000",
        )
        assert s.tax_number == "91310000"


class TestBomItemCreate:
    def test_valid(self):
        b = BomItemCreate(
            material_code="M001", material_name="螺丝",
            quantity=Decimal("10"),
        )
        assert b.unit == "件"
        assert b.source_type == "PURCHASE"

    def test_zero_qty(self):
        with pytest.raises(ValidationError):
            BomItemCreate(material_code="M001", material_name="T", quantity=Decimal("0"))

    def test_negative_qty(self):
        with pytest.raises(ValidationError):
            BomItemCreate(material_code="M001", material_name="T", quantity=Decimal("-1"))


class TestBomCreate:
    def test_valid(self):
        b = BomCreate(bom_no="BOM001", bom_name="Test BOM", project_id=1)
        assert b.version == "1.0"
        assert b.items == []

    def test_with_items(self):
        item = BomItemCreate(material_code="M001", material_name="T", quantity=Decimal("5"))
        b = BomCreate(bom_no="B001", bom_name="BOM", project_id=1, items=[item])
        assert len(b.items) == 1

    def test_missing(self):
        with pytest.raises(ValidationError):
            BomCreate()


class TestBomResponse:
    def test_valid(self):
        b = BomResponse(id=1, bom_no="B001", bom_name="BOM", project_id=1)
        assert b.status == "DRAFT"
        assert b.is_latest is True
        assert b.items == []
