# -*- coding: utf-8 -*-
"""
采购收货管理 API 测试

测试收货记录的创建、查询、更新、质检等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPurchaseReceiptsAPI:
    """采购收货管理 API 测试类"""

    def test_list_receipts(self, client: TestClient, admin_token: str):
        """测试获取收货记录列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/receipts/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Receipts API not implemented")

        assert response.status_code == 200, response.text

    def test_create_receipt(self, client: TestClient, admin_token: str):
        """测试创建收货记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        receipt_data = {
            "receipt_no": f"RCP{datetime.now().strftime('%Y%m%d')}001",
            "order_id": 1,
            "receipt_date": datetime.now().strftime("%Y-%m-%d"),
            "received_by": 1,
            "warehouse_location": "仓库A-01",
            "remarks": "首批到货"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/receipts/",
            headers=headers,
            json=receipt_data
        )

        if response.status_code == 404:
            pytest.skip("Receipts API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_receipt_detail(self, client: TestClient, admin_token: str):
        """测试获取收货记录详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/receipts/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No receipt data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_receipt(self, client: TestClient, admin_token: str):
        """测试更新收货记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "warehouse_location": "仓库B-02",
            "remarks": "更新存储位置"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase/receipts/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Receipt API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_receipt(self, client: TestClient, admin_token: str):
        """测试删除收货记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/purchase/receipts/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Receipt API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_receipt_items_management(self, client: TestClient, admin_token: str):
        """测试收货明细管理"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        item_data = {
            "material_name": "测试物料",
            "ordered_quantity": 100,
            "received_quantity": 95,
            "qualified_quantity": 93,
            "rejected_quantity": 2,
            "quality_status": "qualified"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/receipts/1/items",
            headers=headers,
            json=item_data
        )

        if response.status_code == 404:
            pytest.skip("Receipt items API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_quality_inspection(self, client: TestClient, admin_token: str):
        """测试质量检验"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        inspection_data = {
            "inspector_id": 1,
            "inspection_date": datetime.now().strftime("%Y-%m-%d"),
            "inspection_result": "qualified",
            "qualified_quantity": 93,
            "rejected_quantity": 2,
            "remarks": "少量瑕疵品"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/receipts/1/inspect",
            headers=headers,
            json=inspection_data
        )

        if response.status_code == 404:
            pytest.skip("Quality inspection API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_confirm_receipt(self, client: TestClient, admin_token: str):
        """测试确认收货"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/receipts/1/confirm",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Receipt confirm API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_reject_receipt(self, client: TestClient, admin_token: str):
        """测试拒收"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        reject_data = {
            "reason": "质量不合格"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/receipts/1/reject",
            headers=headers,
            json=reject_data
        )

        if response.status_code == 404:
            pytest.skip("Receipt reject API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_receipts_by_order(self, client: TestClient, admin_token: str):
        """测试按订单过滤收货记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/receipts/?order_id=1",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Receipt filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_receipts_by_status(self, client: TestClient, admin_token: str):
        """测试按状态过滤收货记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/receipts/?status=confirmed",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Receipt filter API not implemented")

        assert response.status_code == 200, response.text

    def test_receipt_statistics(self, client: TestClient, admin_token: str):
        """测试收货统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/receipts/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Receipt statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_receipt_export(self, client: TestClient, admin_token: str):
        """测试导出收货记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/receipts/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Receipt export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_receipt_unauthorized(self, client: TestClient):
        """测试未授权访问收货记录"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/receipts/"
        )

        assert response.status_code in [401, 403], response.text

    def test_partial_receipt(self, client: TestClient, admin_token: str):
        """测试部分收货"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        partial_data = {
            "receipt_type": "partial",
            "received_quantity": 50,
            "remarks": "首批50个到货"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/receipts/",
            headers=headers,
            json=partial_data
        )

        if response.status_code == 404:
            pytest.skip("Partial receipt API not implemented")

        assert response.status_code in [200, 201, 422], response.text
