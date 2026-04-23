from decimal import Decimal

from app.schemas.material import MaterialCategoryResponse, MaterialResponse


def test_material_category_response_normalizes_none_fields():
    category = MaterialCategoryResponse(
        id=1,
        category_code="CAT-1",
        category_name="电气",
        level=None,
        is_active=None,
    )

    assert category.level == 1
    assert category.is_active is True


def test_material_category_response_keeps_explicit_fields():
    category = MaterialCategoryResponse(
        id=2,
        category_code="CAT-2",
        category_name="机械",
        level=3,
        is_active=False,
    )

    assert category.level == 3
    assert category.is_active is False


def test_material_response_normalizes_none_fields():
    material = MaterialResponse(
        id=1,
        material_name="传感器",
        material_code=None,
        unit=None,
        source_type=None,
        standard_price=None,
        last_price=None,
        safety_stock=None,
        current_stock=None,
        lead_time_days=None,
        is_key_material=None,
        is_active=None,
    )

    assert material.material_code == ""
    assert material.unit == "件"
    assert material.source_type == "PURCHASE"
    assert material.standard_price == Decimal("0")
    assert material.last_price == Decimal("0")
    assert material.safety_stock == Decimal("0")
    assert material.current_stock == Decimal("0")
    assert material.lead_time_days == 0
    assert material.is_key_material is False
    assert material.is_active is True


def test_material_response_keeps_explicit_values():
    material = MaterialResponse(
        id=2,
        material_name="电机",
        material_code="M-001",
        unit="台",
        source_type="MAKE",
        standard_price=Decimal("12.5"),
        last_price=Decimal("10.5"),
        safety_stock=Decimal("3"),
        current_stock=Decimal("9"),
        lead_time_days=7,
        is_key_material=True,
        is_active=False,
    )

    assert material.material_code == "M-001"
    assert material.unit == "台"
    assert material.source_type == "MAKE"
    assert material.standard_price == Decimal("12.5")
    assert material.last_price == Decimal("10.5")
    assert material.safety_stock == Decimal("3")
    assert material.current_stock == Decimal("9")
    assert material.lead_time_days == 7
    assert material.is_key_material is True
    assert material.is_active is False
