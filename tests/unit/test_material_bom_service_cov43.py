# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/material/bom_service.py
"""
import pytest

pytest.importorskip("app.services.material.bom_service")

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.material.bom_service import BOMService


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def make_async_db():
    db = AsyncMock()
    return db


# 所有测试都 patch selectinload 以避免 SQLAlchemy ORM 属性检查
SELECTINLOAD_PATCH = "app.services.material.bom_service.selectinload"


# ── 1. BOM 不存在时抛出 ValueError ──────────────────────────────────────────
def test_approve_bom_not_found():
    db = make_async_db()
    result_mock = MagicMock()
    result_mock.first.return_value = None
    db.execute.return_value = result_mock

    with patch(SELECTINLOAD_PATCH, return_value=MagicMock()):
        with pytest.raises(ValueError, match="BOM不存在"):
            run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=999, approved_by=1))


# ── 2. BOM 状态不是 APPROVED 时抛出 ValueError ──────────────────────────────
def test_approve_bom_wrong_status():
    db = make_async_db()

    bom = MagicMock()
    bom.status = "DRAFT"
    project = MagicMock()

    result_mock = MagicMock()
    result_mock.first.return_value = (bom, project)
    db.execute.return_value = result_mock

    with patch(SELECTINLOAD_PATCH, return_value=MagicMock()):
        with pytest.raises(ValueError, match="状态不是已审核"):
            run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=1, approved_by=1))


# ── 3. BOM 明细为空时返回 success=False ─────────────────────────────────────
def test_approve_bom_no_items():
    db = make_async_db()

    bom = MagicMock()
    bom.status = "APPROVED"
    bom.id = 1
    bom.bom_name = "BOM-001"
    project = MagicMock()

    bom_result = MagicMock()
    bom_result.first.return_value = (bom, project)

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []

    db.execute.side_effect = [bom_result, items_result]

    with patch(SELECTINLOAD_PATCH, return_value=MagicMock()):
        result = run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=1, approved_by=1))
    assert result["success"] is False
    assert "没有明细" in result["message"]


# ── 4. 有明细但物料没有供应商时跳过 ─────────────────────────────────────────
def test_approve_bom_items_no_supplier():
    db = make_async_db()

    bom = MagicMock()
    bom.status = "APPROVED"
    bom.id = 2
    bom.bom_name = "BOM-002"
    project = MagicMock()
    project.id = 1

    bom_result = MagicMock()
    bom_result.first.return_value = (bom, project)

    material = MagicMock()
    material.primary_supplier_id = None
    material.default_supplier_id = None

    item = MagicMock()
    item.material = material

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [item]

    db.execute.side_effect = [bom_result, items_result]

    with patch(SELECTINLOAD_PATCH, return_value=MagicMock()):
        result = run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=2, approved_by=1))
    assert result["success"] is True
    assert result["purchase_orders_count"] == 0


# ── 5. 有供应商但 vendor 不存在时跳过 ────────────────────────────────────────
def test_approve_bom_vendor_not_found():
    db = make_async_db()

    bom = MagicMock()
    bom.status = "APPROVED"
    bom.id = 3
    bom.bom_name = "BOM-003"
    project = MagicMock()
    project.id = 1

    bom_result = MagicMock()
    bom_result.first.return_value = (bom, project)

    material = MagicMock()
    material.primary_supplier_id = 99
    material.default_supplier_id = None

    item = MagicMock()
    item.material = material

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [item]

    vendor_result = MagicMock()
    vendor_result.scalar_one_or_none.return_value = None

    db.execute.side_effect = [bom_result, items_result, vendor_result]

    with patch(SELECTINLOAD_PATCH, return_value=MagicMock()):
        result = run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=3, approved_by=1))
    assert result["success"] is True
    assert result["purchase_orders_count"] == 0


# ── 6. 正常创建采购订单 ───────────────────────────────────────────────────────
def test_approve_bom_creates_purchase_order():
    db = make_async_db()

    bom = MagicMock()
    bom.status = "APPROVED"
    bom.id = 4
    bom.bom_name = "BOM-004"
    project = MagicMock()
    project.id = 2

    bom_result = MagicMock()
    bom_result.first.return_value = (bom, project)

    material = MagicMock()
    material.primary_supplier_id = 10
    material.default_supplier_id = None
    material.standard_price = 100
    material.id = 1

    item = MagicMock()
    item.material = material
    item.material_id = 1
    item.quantity = 5
    item.id = 1

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [item]

    vendor = MagicMock()
    vendor.id = 10
    vendor_result = MagicMock()
    vendor_result.scalar_one_or_none.return_value = vendor

    db.execute.side_effect = [bom_result, items_result, vendor_result]

    po = MagicMock()
    po.id = 100

    with patch(SELECTINLOAD_PATCH, return_value=MagicMock()), \
         patch("app.services.material.bom_service.PurchaseOrder", return_value=po), \
         patch("app.services.material.bom_service.PurchaseOrderItem"):
        result = run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=4, approved_by=1))

    assert result["success"] is True
    assert result["purchase_orders_count"] == 1
