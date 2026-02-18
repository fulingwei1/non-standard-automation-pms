# -*- coding: utf-8 -*-
"""第十七批 - 物料BOM服务单元测试（material/bom_service.py）"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

pytest.importorskip("app.services.material.bom_service")


def _run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


class TestBOMService:

    def _make_db_with_bom(self, bom_status="APPROVED", bom_name="TestBOM",
                          has_items=True, vendor_found=True):
        """构建返回指定状态 BOM 的异步 db mock"""
        db = AsyncMock()

        bom = MagicMock()
        bom.status = bom_status
        bom.id = 1
        bom.bom_name = bom_name

        project = MagicMock()
        project.id = 10

        mock_bom_result = MagicMock()
        mock_bom_result.first.return_value = (bom, project)

        # BOM items
        item = MagicMock()
        item.id = 100
        item.material_id = 200
        item.quantity = 5
        item.material.primary_supplier_id = 50
        item.material.default_supplier_id = None
        item.material.standard_price = 100.0

        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = [item] if has_items else []

        vendor = MagicMock()
        vendor.id = 50
        mock_vendor_result = MagicMock()
        mock_vendor_result.scalar_one_or_none.return_value = vendor if vendor_found else None

        return db, bom, project, item, mock_bom_result, mock_items_result, mock_vendor_result

    def test_approve_bom_raises_when_not_found(self):
        """BOM不存在时抛出 ValueError"""
        from app.services.material.bom_service import BOMService

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None

        # Patch select/selectinload to avoid SQLAlchemy ORM issues
        with patch("app.services.material.bom_service.select", return_value=MagicMock()), \
             patch("app.services.material.bom_service.selectinload", return_value=MagicMock()):
            db.execute = AsyncMock(return_value=mock_result)
            with pytest.raises(ValueError, match="BOM不存在"):
                _run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=999, approved_by=1))

    def test_approve_bom_raises_when_wrong_status(self):
        """BOM状态不是 APPROVED 时抛出 ValueError"""
        from app.services.material.bom_service import BOMService

        db = AsyncMock()
        bom = MagicMock()
        bom.status = "DRAFT"
        bom.bom_name = "TestBOM"
        project = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = (bom, project)

        with patch("app.services.material.bom_service.select", return_value=MagicMock()), \
             patch("app.services.material.bom_service.selectinload", return_value=MagicMock()):
            db.execute = AsyncMock(return_value=mock_result)
            with pytest.raises(ValueError, match="BOM状态不是已审核"):
                _run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=1, approved_by=1))

    def test_approve_bom_returns_no_items_message(self):
        """BOM无明细时返回失败消息"""
        from app.services.material.bom_service import BOMService

        db = AsyncMock()
        bom = MagicMock()
        bom.status = "APPROVED"
        bom.id = 1
        bom.bom_name = "EmptyBOM"
        project = MagicMock()
        project.id = 10

        mock_bom_result = MagicMock()
        mock_bom_result.first.return_value = (bom, project)

        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = []

        with patch("app.services.material.bom_service.select", return_value=MagicMock()), \
             patch("app.services.material.bom_service.selectinload", return_value=MagicMock()):
            db.execute = AsyncMock(side_effect=[mock_bom_result, mock_items_result])
            result = _run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=1, approved_by=1))

        assert result["success"] is False
        assert "没有明细" in result["message"]

    def test_approve_bom_success_creates_purchase_orders(self):
        """BOM有明细时成功创建采购订单"""
        from app.services.material.bom_service import BOMService

        db = AsyncMock()
        bom = MagicMock()
        bom.status = "APPROVED"
        bom.id = 1
        bom.bom_name = "TestBOM"
        project = MagicMock()
        project.id = 10

        mock_bom_result = MagicMock()
        mock_bom_result.first.return_value = (bom, project)

        item = MagicMock()
        item.id = 100
        item.material_id = 200
        item.quantity = 5
        item.material.primary_supplier_id = 50
        item.material.default_supplier_id = None
        item.material.standard_price = 100.0

        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = [item]

        vendor = MagicMock()
        vendor.id = 50
        mock_vendor_result = MagicMock()
        mock_vendor_result.scalar_one_or_none.return_value = vendor

        po = MagicMock()
        po.id = 1001

        with patch("app.services.material.bom_service.select", return_value=MagicMock()), \
             patch("app.services.material.bom_service.selectinload", return_value=MagicMock()), \
             patch("app.services.material.bom_service.PurchaseOrder", return_value=po), \
             patch("app.services.material.bom_service.PurchaseOrderItem", return_value=MagicMock()):
            db.execute = AsyncMock(side_effect=[mock_bom_result, mock_items_result, mock_vendor_result])
            result = _run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=1, approved_by=1))

        assert result["success"] is True
        assert "已创建" in result["message"]
        db.commit.assert_called()

    def test_approve_bom_skips_no_supplier(self):
        """物料无供应商时跳过该物料"""
        from app.services.material.bom_service import BOMService

        db = AsyncMock()
        bom = MagicMock()
        bom.status = "APPROVED"
        bom.id = 1
        bom.bom_name = "TestBOM"
        project = MagicMock()
        project.id = 10

        mock_bom_result = MagicMock()
        mock_bom_result.first.return_value = (bom, project)

        item = MagicMock()
        item.material.primary_supplier_id = None
        item.material.default_supplier_id = None

        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = [item]

        with patch("app.services.material.bom_service.select", return_value=MagicMock()), \
             patch("app.services.material.bom_service.selectinload", return_value=MagicMock()):
            db.execute = AsyncMock(side_effect=[mock_bom_result, mock_items_result])
            result = _run(BOMService.approve_bom_and_create_purchase_orders(db, bom_id=1, approved_by=1))

        # 无供应商时创建0个订单，success=True
        assert result["purchase_orders_count"] == 0
