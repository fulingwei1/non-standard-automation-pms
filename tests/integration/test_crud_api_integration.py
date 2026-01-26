# -*- coding: utf-8 -*-
"""
CRUD基类API集成测试
测试使用CRUD基类实现的API端点
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.integration.api_test_helper import APITestHelper

client = TestClient(app)
helper = APITestHelper(client)


@pytest.mark.integration
@pytest.mark.api
class TestCRUDAPIIntegration:
    """CRUD基类API集成测试"""
    
    def test_suppliers_crud_workflow(self):
        """测试供应商CRUD完整流程（使用CRUD基类）"""
        # 创建供应商
        supplier_data = {
            "name": "测试供应商",
            "code": f"SUP-{helper.generate_code()}",
            "contact_person": "张三",
            "phone": "13800138000",
            "email": f"test-{helper.generate_code()}@example.com",
        }
        
        response = helper.post(
            "/api/v1/suppliers/",
            data=supplier_data,
            username="admin",
            password="admin123"
        )
        
        APITestHelper.assert_success(response, "创建供应商成功")
        supplier_id = response.json()["data"]["id"]
        helper.track_resource("supplier", supplier_id)
        
        # 获取供应商
        response = helper.get(
            f"/api/v1/suppliers/{supplier_id}",
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "获取供应商成功")
        assert response.json()["data"]["name"] == supplier_data["name"]
        
        # 更新供应商
        update_data = {
            "name": "更新后的供应商名称",
            "contact_person": "李四",
        }
        response = helper.put(
            f"/api/v1/suppliers/{supplier_id}",
            data=update_data,
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "更新供应商成功")
        assert response.json()["data"]["name"] == update_data["name"]
        
        # 列表查询
        response = helper.get(
            "/api/v1/suppliers/",
            params={"page": 1, "page_size": 20},
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "获取供应商列表成功")
        APITestHelper.assert_data_not_empty(response, "供应商列表不为空")
        
        # 关键词搜索
        response = helper.get(
            "/api/v1/suppliers/",
            params={"keyword": "测试", "page": 1, "page_size": 20},
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "关键词搜索成功")
        
        # 筛选查询
        response = helper.get(
            "/api/v1/suppliers/",
            params={"filters": {"status": "ACTIVE"}, "page": 1, "page_size": 20},
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "筛选查询成功")
        
        # 删除供应商
        response = helper.delete(
            f"/api/v1/suppliers/{supplier_id}",
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "删除供应商成功")
        
        # 验证已删除
        response = helper.get(
            f"/api/v1/suppliers/{supplier_id}",
            username="admin",
            password="admin123"
        )
        assert response.status_code == 404
    
    def test_materials_crud_workflow(self):
        """测试物料CRUD完整流程（使用CRUD基类）"""
        # 创建物料
        material_data = {
            "name": "测试物料",
            "code": f"MAT-{helper.generate_code()}",
            "category": "标准件",
            "unit": "个",
            "specification": "测试规格",
        }
        
        response = helper.post(
            "/api/v1/materials/",
            data=material_data,
            username="admin",
            password="admin123"
        )
        
        APITestHelper.assert_success(response, "创建物料成功")
        material_id = response.json()["data"]["id"]
        helper.track_resource("material", material_id)
        
        # 获取物料
        response = helper.get(
            f"/api/v1/materials/{material_id}",
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "获取物料成功")
        
        # 列表查询
        response = helper.get(
            "/api/v1/materials/",
            params={"page": 1, "page_size": 20},
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "获取物料列表成功")
        
        # 统计
        response = helper.get(
            "/api/v1/materials/statistics/",
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "获取物料统计成功")
        
        # 清理
        helper.delete(
            f"/api/v1/materials/{material_id}",
            username="admin",
            password="admin123"
        )
    
    def test_pagination_and_filtering(self):
        """测试分页和筛选功能"""
        # 创建多个测试数据
        supplier_ids = []
        for i in range(5):
            supplier_data = {
                "name": f"供应商{i}",
                "code": f"SUP-{helper.generate_code()}",
                "status": "ACTIVE" if i % 2 == 0 else "INACTIVE",
            }
            response = helper.post(
                "/api/v1/suppliers/",
                data=supplier_data,
                username="admin",
                password="admin123"
            )
            if response.status_code == 200:
                supplier_ids.append(response.json()["data"]["id"])
                helper.track_resource("supplier", supplier_ids[-1])
        
        # 测试分页
        response = helper.get(
            "/api/v1/suppliers/",
            params={"page": 1, "page_size": 2},
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "分页查询成功")
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 2
        
        # 测试筛选
        response = helper.get(
            "/api/v1/suppliers/",
            params={
                "filters": {"status": "ACTIVE"},
                "page": 1,
                "page_size": 20
            },
            username="admin",
            password="admin123"
        )
        APITestHelper.assert_success(response, "筛选查询成功")
        
        # 清理
        for supplier_id in supplier_ids:
            helper.delete(
                f"/api/v1/suppliers/{supplier_id}",
                username="admin",
                password="admin123"
            )
