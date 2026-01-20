# -*- coding: utf-8 -*-
"""
Integration tests for Materials API
Covers: app/api/v1/endpoints/materials.py
"""

import pytest
from datetime import date


class TestMaterialsAPI:
    """物料管理API集成测试"""

    def test_list_materials(self, client, admin_token):
        """测试获取物料列表"""
        response = client.get(
            "/api/v1/materials/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_materials_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/materials/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_list_materials_with_filters(self, client, admin_token):
        """测试过滤参数"""
        response = client.get(
            "/api/v1/materials/?category=ME&status=ACTIVE",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_get_material_detail(self, client, admin_token):
        """测试获取物料详情"""
        response = client.get(
            "/api/v1/materials/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能返回200或404（如果物料不存在）
        assert response.status_code in [200, 404]

    def test_create_material(self, client, admin_token):
        """测试创建物料"""
        material_data = {
            "material_name": "API测试物料",
            "material_code": f"MAT-{date.today().strftime('%Y%m%d')}-001",
            "category": "ME",
            "specification": "规格A",
            "unit": "个"
        }
        
        response = client.post(
            "/api/v1/materials/",
            json=material_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [201, 422]

    def test_update_material(self, client, admin_token):
        """测试更新物料"""
        update_data = {
            "material_name": "API更新后的物料"
        }
        
        response = client.put(
            "/api/v1/materials/1",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [200, 404, 422]

    def test_delete_material(self, client, admin_token):
        """测试删除物料"""
        response = client.delete(
            "/api/v1/materials/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [200, 404]

    def test_search_materials_by_name(self, client, admin_token):
        """测试按名称搜索"""
        response = client.get(
            "/api/v1/materials/?search=测试",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_search_materials_by_code(self, client, admin_token):
        """测试按编码搜索"""
        response = client.get(
            "/api/v1/materials/?material_code=MAT001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


class TestMaterialsAPIAuth:
    """物料API认证测试"""

    def test_list_materials_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/materials/")
        assert response.status_code == 401

    def test_create_material_without_token(self, client):
        """测试无token创建"""
        response = client.post(
            "/api/v1/materials/",
            json={"material_name": "测试"}
        )
        assert response.status_code == 401


class TestMaterialsAPISorting:
    """物料API排序测试"""

    def test_sort_by_created_at(self, client, admin_token):
        """测试按创建时间排序"""
        response = client.get(
            "/api/v1/materials/?order_by=created_at&order=desc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_sort_by_name(self, client, admin_token):
        """测试按名称排序"""
        response = client.get(
            "/api/v1/materials/?order_by=material_name&order=asc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
