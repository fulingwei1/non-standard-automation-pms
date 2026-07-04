# -*- coding: utf-8 -*-
"""Tax basis helpers for sales amount fields."""

from decimal import Decimal, InvalidOperation
from typing import Any

ZERO = Decimal("0")
CENT = Decimal("0.01")


def to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return ZERO
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return ZERO


def _pick(source: dict[str, Any], *keys: str) -> Decimal:
    for key in keys:
        if source.get(key) not in (None, ""):
            return to_decimal(source.get(key))
    return ZERO


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT)


def build_tax_breakdown(source: dict[str, Any], *, fallback_total: Any = None) -> dict[str, Decimal]:
    amount_without_tax = _pick(source, "amount_without_tax", "amountWithoutTax", "net_amount")
    tax_rate = _pick(source, "tax_rate", "taxRate")
    tax_amount = _pick(source, "tax_amount", "taxAmount")
    amount_with_tax = _pick(
        source,
        "amount_with_tax",
        "amountWithTax",
        "total_amount_with_tax",
        "totalAmountWithTax",
    )
    fallback = to_decimal(fallback_total)

    if amount_with_tax <= ZERO and fallback > ZERO:
        amount_with_tax = fallback

    if tax_amount <= ZERO and amount_without_tax > ZERO and tax_rate > ZERO:
        tax_amount = _money(amount_without_tax * tax_rate / Decimal("100"))

    if amount_without_tax <= ZERO and amount_with_tax > ZERO:
        if tax_amount > ZERO:
            amount_without_tax = amount_with_tax - tax_amount
        elif tax_rate > ZERO:
            divisor = Decimal("1") + tax_rate / Decimal("100")
            amount_without_tax = _money(amount_with_tax / divisor)
            tax_amount = amount_with_tax - amount_without_tax

    if amount_with_tax <= ZERO and amount_without_tax > ZERO:
        amount_with_tax = amount_without_tax + tax_amount

    return {
        "amount_without_tax": _money(amount_without_tax) if amount_without_tax else ZERO,
        "tax_rate": _money(tax_rate) if tax_rate else ZERO,
        "tax_amount": _money(tax_amount) if tax_amount else ZERO,
        "amount_with_tax": _money(amount_with_tax) if amount_with_tax else ZERO,
    }
