# -*- coding: utf-8 -*-
"""
从 BOM 创建采购订单 API 端点单元测试
直接测试端点函数，不使用 TestClient
"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.api.v1.endpoints.purchase.orders_refactored import (
        create_purchase_orders_from_bom,
        preview_purchase_orders_from_bom,
    )
    SKIP = False
except Exception as e:
    SKIP = True
    print(f"导入失败：{e}")

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_mock_db():
    """创建模拟数据库"""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()
    return db


def make_mock_user():
    """创建模拟用户"""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    return user


def make_bom_header(bom_id=1, bom_no="BOM-20260315-001", project_id=1):
    """创建模拟 BOM"""
    bom = MagicMock()
    bom.id = bom_id
    bom.bom_no = bom_no
    bom.project_id = project_id
    bom.project = MagicMock()
    bom.project.project_name = "测试项目"
    bom.required_date = date.today()
    return bom


def make_bom_item(item_id=1, source_type="PURCHASE", supplier_id=1, quantity=10, unit_price=100):
    """创建模拟 BOM 明细项"""
    item = MagicMock()
    item.id = item_id
    item.source_type = source_type
    item.supplier_id = supplier_id
    item.material_id = 1
    item.material_code = "MAT-001"
    item.material_name = "测试物料"
    item.specification = "规格 A"
    item.unit = "件"
    item.quantity = Decimal(str(quantity))
    item.unit_price = Decimal(str(unit_price))
    item.purchased_qty = 0
    item.required_date = date.today()
    return item


def make_vendor(vendor_id=1, supplier_name="测试供应商"):
    """创建模拟供应商"""
    vendor = MagicMock()
    vendor.id = vendor_id
    vendor.supplier_name = supplier_name
    vendor.vendor_type = "MATERIAL"
    return vendor


class TestPurchaseOrderFromBomEndpoint:
    """测试从 BOM 创建采购订单端点"""
    
    def test_preview_from_bom_success(self):
        """测试预览从 BOM 创建采购订单成功"""
        # 准备数据
        db = make_mock_db()
        user = make_mock_user()
        bom = make_bom_header()
        bom_item = make_bom_item()
        vendor = make_vendor()
        
        # Mock 数据库查询
        db.query.return_value.filter.return_value.first.side_effect = [
            bom,  # get_or_404 for BomHeader
            vendor,  # Vendor query
        ]
        bom.items.filter.return_value.all.return_value = [bom_item]
        
        # 调用端点函数
        with patch('app.api.v1.endpoints.purchase.orders_refactored.get_or_404', return_value=bom):
            response = preview_purchase_orders_from_bom(
                payload={"bom_id": 1},
                db=db,
                current_user=user
            )
            
            assert response.success is True
            assert "orders" in response.data
            assert "summary" in response.data
    
    def test_preview_from_bom_no_purchase_items(self):
        """测试 BOM 中没有需要采购的物料"""
        db = make_mock_db()
        user = make_mock_user()
        bom = make_bom_header()
        
        db.query.return_value.filter.return_value.first.return_value = bom
        bom.items.filter.return_value.all.return_value = []
        
        with patch('app.api.v1.endpoints.purchase.orders_refactored.get_or_404', return_value=bom):
            response = preview_purchase_orders_from_bom(
                payload={"bom_id": 1},
                db=db,
                current_user=user
            )
            
            assert response.success is True
            assert response.data["summary"]["total_orders"] == 0
    
    def test_preview_from_bom_missing_bom_id(self):
        """测试缺少 bom_id 参数"""
        db = make_mock_db()
        user = make_mock_user()
        
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            preview_purchase_orders_from_bom(
                payload={},
                db=db,
                current_user=user
            )
        
        assert exc_info.value.status_code == 422
    
    def test_preview_from_bom_not_found(self):
        """测试 BOM 不存在"""
        db = make_mock_db()
        user = make_mock_user()
        
        from fastapi import HTTPException
        
        with patch('app.api.v1.endpoints.purchase.orders_refactored.get_or_404', side_effect=HTTPException(status_code=404)):
            with pytest.raises(HTTPException) as exc_info:
                preview_purchase_orders_from_bom(
                    payload={"bom_id": 999},
                    db=db,
                    current_user=user
                )
            
            assert exc_info.value.status_code == 404
    
    def test_create_from_bom_success(self):
        """测试从 BOM 创建采购订单成功"""
        # 准备数据
        db = make_mock_db()
        user = make_mock_user()
        bom = make_bom_header()
        bom_item = make_bom_item()
        vendor = make_vendor()
        
        # Mock 数据库查询
        db.query.return_value.filter.return_value.first.side_effect = [
            bom,  # get_or_404 for BomHeader
            vendor,  # Vendor query
        ]
        bom.items.filter.return_value.all.return_value = [bom_item]
        
        # Mock 订单创建
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO-20260315-001"
        mock_order.total_amount = Decimal("1000.00")
        
        mock_order_item = MagicMock()
        mock_order_item.id = 1
        
        with patch('app.api.v1.endpoints.purchase.orders_refactored.get_or_404', return_value=bom), \
             patch('app.api.v1.endpoints.purchase.orders_refactored.PurchaseOrder', return_value=mock_order), \
             patch('app.api.v1.endpoints.purchase.orders_refactored.PurchaseOrderItem', return_value=mock_order_item), \
             patch('app.api.v1.endpoints.purchase.orders_refactored.generate_order_no', return_value="PO-20260315-001"):
            
            response = create_purchase_orders_from_bom(
                payload={"bom_id": 1},
                db=db,
                current_user=user
            )
            
            assert response.success is True
            assert "orders" in response.data
    
    def test_create_from_bom_missing_bom_id(self):
        """测试缺少 bom_id 参数"""
        db = make_mock_db()
        user = make_mock_user()
        
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            create_purchase_orders_from_bom(
                payload={},
                db=db,
                current_user=user
            )
        
        assert exc_info.value.status_code == 422
    
    def test_create_from_bom_no_purchase_items(self):
        """测试 BOM 中没有需要采购的物料"""
        db = make_mock_db()
        user = make_mock_user()
        bom = make_bom_header()
        
        db.query.return_value.filter.return_value.first.return_value = bom
        bom.items.filter.return_value.all.return_value = []
        
        from fastapi import HTTPException
        
        with patch('app.api.v1.endpoints.purchase.orders_refactored.get_or_404', return_value=bom):
            with pytest.raises(HTTPException) as exc_info:
                create_purchase_orders_from_bom(
                    payload={"bom_id": 1},
                    db=db,
                    current_user=user
                )
            
            assert exc_info.value.status_code == 400
    
    def test_create_from_bom_multiple_suppliers(self):
        """测试从 BOM 创建多个供应商的采购订单"""
        db = make_mock_db()
        user = make_mock_user()
        bom = make_bom_header()
        bom_item1 = make_bom_item(item_id=1, supplier_id=1)
        bom_item2 = make_bom_item(item_id=2, supplier_id=2)
        vendor1 = make_vendor(vendor_id=1, supplier_name="供应商 A")
        vendor2 = make_vendor(vendor_id=2, supplier_name="供应商 B")
        
        db.query.return_value.filter.return_value.first.side_effect = [
            bom,
            vendor1,
            vendor2,
        ]
        bom.items.filter.return_value.all.return_value = [bom_item1, bom_item2]
        
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO-20260315-001"
        mock_order.total_amount = Decimal("1000.00")
        
        mock_order_item = MagicMock()
        mock_order_item.id = 1
        
        with patch('app.api.v1.endpoints.purchase.orders_refactored.get_or_404', return_value=bom), \
             patch('app.api.v1.endpoints.purchase.orders_refactored.PurchaseOrder', return_value=mock_order), \
             patch('app.api.v1.endpoints.purchase.orders_refactored.PurchaseOrderItem', return_value=mock_order_item), \
             patch('app.api.v1.endpoints.purchase.orders_refactored.generate_order_no', return_value="PO-20260315-001"):
            
            response = create_purchase_orders_from_bom(
                payload={"bom_id": 1},
                db=db,
                current_user=user
            )
            
            assert response.success is True
            # 应该创建 2 个订单（每个供应商一个）
            assert len(response.data["orders"]) == 2
