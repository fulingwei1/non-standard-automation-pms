# -*- coding: utf-8 -*-
"""BOM服务测试"""
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest


class TestBOMService:
    """BOMService 测试类 - 使用 patch 方式测试"""

    @pytest.mark.asyncio
    @patch('app.services.material.bom_service.select')
    @patch('app.services.material.bom_service.selectinload')
    async def test_approve_bom_not_found(self, mock_selectinload, mock_select):
        """测试BOM不存在时抛出异常"""
        from app.services.material.bom_service import BOMService

        # Mock 查询结果为空
        mock_result = Mock()
        mock_result.first = Mock(return_value=None)

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        bom_service = BOMService()

        with pytest.raises(ValueError, match="BOM不存在"):
            await bom_service.approve_bom_and_create_purchase_orders(
                db=mock_db, bom_id=999, approved_by=1
            )

    @pytest.mark.asyncio
    @patch('app.services.material.bom_service.select')
    @patch('app.services.material.bom_service.selectinload')
    async def test_approve_bom_wrong_status(self, mock_selectinload, mock_select):
        """测试BOM状态不正确时抛出异常"""
        from app.services.material.bom_service import BOMService

        # 模拟BOM存在但状态不是APPROVED
        mock_bom = Mock()
        mock_bom.id = 1
        mock_bom.status = "DRAFT"
        mock_bom.bom_name = "Test BOM"

        mock_project = Mock()
        mock_project.id = 1

        mock_result = Mock()
        mock_result.first = Mock(return_value=(mock_bom, mock_project))

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        bom_service = BOMService()

        with pytest.raises(ValueError, match="BOM状态不是已审核"):
            await bom_service.approve_bom_and_create_purchase_orders(
                db=mock_db, bom_id=1, approved_by=1
            )

    @pytest.mark.asyncio
    @patch('app.services.material.bom_service.select')
    @patch('app.services.material.bom_service.selectinload')
    async def test_approve_bom_no_items(self, mock_selectinload, mock_select):
        """测试BOM没有明细时返回失败"""
        from app.services.material.bom_service import BOMService

        mock_bom = Mock()
        mock_bom.id = 1
        mock_bom.status = "APPROVED"
        mock_bom.bom_name = "Test BOM"

        mock_project = Mock()
        mock_project.id = 1

        # BOM查询结果
        mock_bom_result = Mock()
        mock_bom_result.first = Mock(return_value=(mock_bom, mock_project))

        # 明细为空
        mock_items_result = Mock()
        mock_items_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=[mock_bom_result, mock_items_result])

        bom_service = BOMService()

        result = await bom_service.approve_bom_and_create_purchase_orders(
            db=mock_db, bom_id=1, approved_by=1
        )

        assert result["success"] is False
        assert "没有明细" in result["message"]

    @pytest.mark.asyncio
    @patch('app.services.material.bom_service.select')
    @patch('app.services.material.bom_service.selectinload')
    async def test_approve_bom_with_items_no_supplier(self, mock_selectinload, mock_select):
        """测试BOM有明细但没有供应商"""
        from app.services.material.bom_service import BOMService

        mock_bom = Mock()
        mock_bom.id = 1
        mock_bom.status = "APPROVED"
        mock_bom.bom_name = "Test BOM"

        mock_project = Mock()
        mock_project.id = 1

        # 模拟BOM
        mock_bom_result = Mock()
        mock_bom_result.first = Mock(return_value=(mock_bom, mock_project))

        # 模拟物料 - 没有供应商
        mock_material = Mock()
        mock_material.id = 100
        mock_material.primary_supplier_id = None
        mock_material.default_supplier_id = None
        mock_material.standard_price = Decimal("100")

        mock_bom_item = Mock()
        mock_bom_item.id = 1
        mock_bom_item.material_id = 100
        mock_bom_item.quantity = Decimal("10")
        mock_bom_item.material = mock_material

        mock_items_result = Mock()
        mock_items_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_bom_item])))

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=[mock_bom_result, mock_items_result])
        mock_db.commit = AsyncMock()

        bom_service = BOMService()

        result = await bom_service.approve_bom_and_create_purchase_orders(
            db=mock_db, bom_id=1, approved_by=1
        )

        # 因为没有供应商，不创建订单
        assert result["purchase_orders_count"] == 0