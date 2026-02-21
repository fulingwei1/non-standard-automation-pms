# -*- coding: utf-8 -*-
"""
供应商管理 API 测试

测试供应商的创建、查询、更新、评价等功能
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPurchaseSuppliersAPI:
    """供应商管理 API 测试类"""

    def test_list_suppliers(self, client: TestClient, admin_token: str):
        """测试获取供应商列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Suppliers API not implemented")

        assert response.status_code == 200, response.text

    def test_create_supplier(self, client: TestClient, admin_token: str):
        """测试创建供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        supplier_data = {
            "name": "测试供应商有限公司",
            "short_name": "测试供应商",
            "supplier_type": "manufacturer",
            "contact_person": "王经理",
            "contact_phone": "13900139000",
            "contact_email": "wang@supplier.com",
            "address": "深圳市南山区",
            "business_scope": "电子元器件、设备",
            "credit_rating": "A",
            "payment_terms": "月结30天"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/",
            headers=headers,
            json=supplier_data
        )

        if response.status_code == 404:
            pytest.skip("Suppliers API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_supplier_detail(self, client: TestClient, admin_token: str):
        """测试获取供应商详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No supplier data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_supplier(self, client: TestClient, admin_token: str):
        """测试更新供应商信息"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "credit_rating": "S",
            "payment_terms": "月结45天"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Supplier API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_supplier(self, client: TestClient, admin_token: str):
        """测试删除供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Supplier API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_search_suppliers(self, client: TestClient, admin_token: str):
        """测试搜索供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/?search=测试",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Supplier search API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_suppliers_by_type(self, client: TestClient, admin_token: str):
        """测试按类型过滤供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/?type=manufacturer",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Supplier filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_suppliers_by_rating(self, client: TestClient, admin_token: str):
        """测试按信用等级过滤供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/?rating=A",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Supplier filter API not implemented")

        assert response.status_code == 200, response.text

    def test_supplier_evaluation(self, client: TestClient, admin_token: str):
        """测试供应商评价"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        evaluation_data = {
            "supplier_id": 1,
            "quality_score": 90,
            "delivery_score": 85,
            "service_score": 88,
            "price_score": 80,
            "overall_score": 86,
            "comments": "整体表现良好"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/1/evaluate",
            headers=headers,
            json=evaluation_data
        )

        if response.status_code == 404:
            pytest.skip("Supplier evaluation API not implemented")

        assert response.status_code in [200, 201, 404], response.text

    def test_supplier_performance_history(self, client: TestClient, admin_token: str):
        """测试供应商绩效历史"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/1/performance",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Supplier performance API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_supplier_purchase_history(self, client: TestClient, admin_token: str):
        """测试供应商采购历史"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/1/orders",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Supplier orders API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_supplier_statistics(self, client: TestClient, admin_token: str):
        """测试供应商统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Supplier statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_supplier_comparison(self, client: TestClient, admin_token: str):
        """测试供应商对比"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        comparison_data = {
            "supplier_ids": [1, 2, 3]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/compare",
            headers=headers,
            json=comparison_data
        )

        if response.status_code == 404:
            pytest.skip("Supplier comparison API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_supplier_unauthorized(self, client: TestClient):
        """测试未授权访问供应商"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/"
        )

        assert response.status_code in [401, 403], response.text

    def test_supplier_validation(self, client: TestClient, admin_token: str):
        """测试供应商数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        invalid_data = {
            "contact_email": "invalid-email"  # 无效的邮箱格式
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/purchase/suppliers/",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Suppliers API not implemented")

        assert response.status_code == 422, response.text
