# -*- coding: utf-8 -*-
"""
Integration tests for Purchase Orders API
Covers: app/api/v1/endpoints/purchases.py
"""

import pytest
from datetime import date

import uuid

_PO001 = f"PO001-{uuid.uuid4().hex[:8]}"



class TestPurchaseOrdersAPI:
    """采购订单API集成测试"""

    def test_list_purchase_orders(self, client, admin_token):
        """测试获取采购订单列表"""
        response = client.get(
            "/api/v1/purchase-orders/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_purchase_orders_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/purchase-orders/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_list_purchase_orders_with_filters(self, client, admin_token):
        """测试过滤参数"""
        response = client.get(
            "/api/v1/purchase-orders/?status=DRAFT&supplier_id=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_get_purchase_order_detail(self, client, admin_token):
        """测试获取采购订单详情"""
        response = client.get(
            "/api/v1/purchase-orders/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 404]

    def test_create_purchase_order(self, client, admin_token):
        """测试创建采购订单"""
        po_data = {
            "order_no": f"PO-{date.today().strftime('%Y%m%d')}-001",
            "supplier_id": 1,
            "project_id": 1,
            "status": "DRAFT"
        }
        
        response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [201, 422]

    def test_create_purchase_order_with_items(self, client, admin_token):
        """测试创建带明细的采购订单"""
        po_data = {
            "order_no": f"PO-{date.today().strftime('%Y%m%d')}-002",
            "supplier_id": 1,
            "project_id": 1,
            "status": "DRAFT",
            "items": [
                {
                    "material_id": 1,
                    "quantity": 10,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/purchase-orders/",
            json=po_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [201, 422]

    def test_update_purchase_order(self, client, admin_token):
        """测试更新采购订单"""
        update_data = {
            "status": "SUBMITTED",
            "remark": "API更新"
        }
        
        response = client.put(
            "/api/v1/purchase-orders/1",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [200, 404, 422]

    def test_submit_purchase_order(self, client, admin_token):
        """测试提交采购订单"""
        response = client.post(
            "/api/v1/purchase-orders/1/submit",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [200, 404, 422]

    def test_approve_purchase_order(self, client, admin_token):
        """测试审批采购订单"""
        response = client.post(
            "/api/v1/purchase-orders/1/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [200, 404, 422]

    def test_reject_purchase_order(self, client, admin_token):
        """测试拒绝采购订单"""
        response = client.post(
            "/api/v1/purchase-orders/1/reject",
            json={"reason": "价格过高"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [200, 404, 422]

    def test_delete_purchase_order(self, client, admin_token):
        """测试删除采购订单"""
        response = client.delete(
            "/api/v1/purchase-orders/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [200, 404]


class TestPurchaseOrdersAPIAuth:
    """采购订单API认证测试"""

    def test_list_purchase_orders_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/purchase-orders/")
        assert response.status_code == 401

    def test_create_purchase_order_without_token(self, client):
        """测试无token创建"""
        response = client.post(
            "/api/v1/purchase-orders/",
            json={"order_no": _PO001}
        )
        assert response.status_code == 401


class TestPurchaseOrdersAPISearch:
    """采购订单API搜索测试"""

    def test_search_by_order_no(self, client, admin_token):
        """测试按订单号搜索"""
        response = client.get(
            "/api/v1/purchase-orders/?order_no=PO001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_search_by_supplier(self, client, admin_token):
        """测试按供应商搜索"""
        response = client.get(
            "/api/v1/purchase-orders/?supplier_id=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_search_by_project(self, client, admin_token):
        """测试按项目搜索"""
        response = client.get(
            "/api/v1/purchase-orders/?project_id=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_search_by_status(self, client, admin_token):
        """测试按状态搜索"""
        response = client.get(
            "/api/v1/purchase-orders/?status=DRAFT",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


class TestPurchaseOrdersAPISorting:
    """采购订单API排序测试"""

    def test_sort_by_created_at(self, client, admin_token):
        """测试按创建时间排序"""
        response = client.get(
            "/api/v1/purchase-orders/?order_by=created_at&order=desc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_sort_by_order_no(self, client, admin_token):
        """测试按订单号排序"""
        response = client.get(
            "/api/v1/purchase-orders/?order_by=order_no&order=asc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
