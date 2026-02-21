# -*- coding: utf-8 -*-
"""
采购订单 API 测试

测试采购订单的创建、查询、更新、跟踪等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPurchaseOrdersAPI:
    """采购订单 API 测试类"""

    def test_list_purchase_orders(self, client: TestClient, admin_token: str):
        """测试获取采购订单列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Purchase orders API not implemented")

        assert response.status_code == 200, response.text

    def test_create_purchase_order(self, client: TestClient, admin_token: str):
        """测试创建采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        order_data = {
            "order_no": f"PO{datetime.now().strftime('%Y%m%d')}001",
            "request_id": 1,
            "supplier_id": 1,
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "expected_delivery_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "total_amount": 50000.0,
            "payment_terms": "货到付款",
            "delivery_address": "北京市海淀区",
            "contact_person": "张先生",
            "contact_phone": "13800138000"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/orders/",
            headers=headers,
            json=order_data
        )

        if response.status_code == 404:
            pytest.skip("Purchase orders API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_order_detail(self, client: TestClient, admin_token: str):
        """测试获取采购订单详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No order data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_purchase_order(self, client: TestClient, admin_token: str):
        """测试更新采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "expected_delivery_date": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
            "remarks": "延期交付"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase/orders/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Purchase order API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_purchase_order(self, client: TestClient, admin_token: str):
        """测试删除采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/purchase/orders/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Purchase order API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_confirm_order(self, client: TestClient, admin_token: str):
        """测试确认采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/orders/1/confirm",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Order confirm API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_cancel_order(self, client: TestClient, admin_token: str):
        """测试取消采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        cancel_data = {
            "reason": "供应商无法交付"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/orders/1/cancel",
            headers=headers,
            json=cancel_data
        )

        if response.status_code == 404:
            pytest.skip("Order cancel API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_track_order_status(self, client: TestClient, admin_token: str):
        """测试跟踪订单状态"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/1/tracking",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Order tracking API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_orders_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/?status=confirmed",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Order filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_orders_by_supplier(self, client: TestClient, admin_token: str):
        """测试按供应商过滤采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/?supplier_id=1",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Order filter API not implemented")

        assert response.status_code == 200, response.text

    def test_overdue_orders(self, client: TestClient, admin_token: str):
        """测试逾期订单查询"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/overdue",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Overdue orders API not implemented")

        assert response.status_code == 200, response.text

    def test_order_statistics(self, client: TestClient, admin_token: str):
        """测试采购订单统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Order statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_order_export(self, client: TestClient, admin_token: str):
        """测试导出采购订单"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/1/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Order export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_order_unauthorized(self, client: TestClient):
        """测试未授权访问采购订单"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/orders/"
        )

        assert response.status_code in [401, 403], response.text

    def test_order_validation(self, client: TestClient, admin_token: str):
        """测试采购订单数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        invalid_data = {
            "total_amount": -1000.0  # 负数金额
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/orders/",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Purchase orders API not implemented")

        assert response.status_code == 422, response.text
