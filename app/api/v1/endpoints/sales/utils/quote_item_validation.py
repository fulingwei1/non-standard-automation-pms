# -*- coding: utf-8 -*-
"""报价明细数量与价格校验。"""

from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import HTTPException


def _is_missing(value) -> bool:
    return value is None or value == ""


def _parse_decimal(value, field_name: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"{field_name}必须为数字")

    if not parsed.is_finite():
        raise HTTPException(status_code=400, detail=f"{field_name}必须为数字")

    return parsed


def validate_positive_quantity(value, *, required: bool = True) -> Optional[Decimal]:
    if _is_missing(value):
        if required:
            raise HTTPException(status_code=400, detail="数量必须大于 0")
        return None

    quantity = _parse_decimal(value, "数量")
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="数量必须大于 0")
    return quantity


def validate_positive_unit_price(value, *, required: bool = True) -> Optional[Decimal]:
    if _is_missing(value):
        if required:
            raise HTTPException(status_code=400, detail="单价必须大于 0")
        return None

    unit_price = _parse_decimal(value, "单价")
    if unit_price <= 0:
        raise HTTPException(status_code=400, detail="单价必须大于 0")
    return unit_price


def validate_quote_item_quantity_price(
    qty,
    unit_price,
    *,
    require_qty: bool = True,
    require_unit_price: bool = True,
) -> tuple[Optional[Decimal], Optional[Decimal]]:
    return (
        validate_positive_quantity(qty, required=require_qty),
        validate_positive_unit_price(unit_price, required=require_unit_price),
    )
