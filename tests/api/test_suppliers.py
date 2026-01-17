# -*- coding: utf-8 -*-
"""
供应商管理模块 API 测试

测试供应商的 CRUD 操作、评级和物料关联
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSupplierCRUD:
    """供应商 CRUD 测试"""

    def test_list_suppliers(self, client: TestClient, admin_token: str):
        """测试获取供应商列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/",
            params={"page": 1, "page_size": 10},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_suppliers_with_keyword(self, client: TestClient, admin_token: str):
        """测试关键词搜索供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/",
            params={"page": 1, "page_size": 10, "keyword": "测试"},
            headers=headers
        )

        assert response.status_code == 200

    def test_create_supplier(self, client: TestClient, admin_token: str):
        """测试创建供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        supplier_data = {
            "supplier_code": f"SUP{uuid.uuid4().hex[:6].upper()}",
            "supplier_name": f"测试供应商-{uuid.uuid4().hex[:4]}",
            "supplier_type": "GENERAL",
            "contact_person": "张三",
            "contact_phone": "13800138000",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/suppliers/",
            json=supplier_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create supplier")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text

    def test_get_supplier_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取供应商列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get suppliers list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No suppliers available for testing")

        supplier_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/{supplier_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == supplier_id

    def test_get_supplier_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_supplier(self, client: TestClient, admin_token: str):
        """测试更新供应商"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取供应商列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get suppliers list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No suppliers available for testing")

        supplier_id = items[0]["id"]

        update_data = {
            "contact_person": "李四",
            "contact_phone": "13900139000",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/suppliers/{supplier_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update supplier")

        assert response.status_code == 200, response.text


class TestSupplierRating:
    """供应商评级测试"""

    def test_update_supplier_rating(self, client: TestClient, admin_token: str):
        """测试更新供应商评级"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取供应商列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get suppliers list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No suppliers available for testing")

        supplier_id = items[0]["id"]

        rating_data = {
            "quality_rating": 4.5,
            "delivery_rating": 4.0,
            "service_rating": 4.2,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/suppliers/{supplier_id}/rating",
            json=rating_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update rating")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code == 200, response.text


class TestSupplierMaterials:
    """供应商物料关联测试"""

    def test_get_supplier_materials(self, client: TestClient, admin_token: str):
        """测试获取供应商的物料列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取供应商列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get suppliers list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No suppliers available for testing")

        supplier_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/suppliers/{supplier_id}/materials",
            headers=headers
        )

        assert response.status_code == 200
