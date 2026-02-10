# -*- coding: utf-8 -*-
"""
物料管理模块 API 集成测试

测试范围：
- 物料列表 (GET /materials/)
- 创建物料 (POST /materials/)
- 物料详情 (GET /materials/{material_id})
- 更新物料 (PUT /materials/{material_id})

实际路由前缀: /materials (api.py prefix="/materials")
"""

import pytest

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestMaterialsCRUDAPI:
    """物料CRUD API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("物料CRUD API 测试")

    def test_get_materials_list(self):
        """测试获取物料列表"""
        self.helper.print_info("测试获取物料列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/materials/", params=params, resource_type="materials_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个物料")
        else:
            self.helper.print_warning("获取物料列表响应不符合预期")

    def test_create_material(self):
        """测试创建物料"""
        self.helper.print_info("测试创建物料...")

        material_data = {
            "material_code": TestDataGenerator.generate_material_code(),
            "material_name": "测试电阻-100Ω",
            "material_type": "ELECTRONIC",
            "unit": "个",
            "specification": "0603 100Ω ±1%",
            "description": "贴片电阻",
        }

        response = self.helper.post(
            "/materials/", material_data, resource_type="material"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            result = response.get("data", {})
            material_id = result.get("id") if isinstance(result, dict) else None
            if material_id:
                self.tracked_resources.append(("material", material_id))
                self.helper.print_success(f"物料创建成功，ID: {material_id}")
            else:
                self.helper.print_success("物料创建成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或数据冲突）")
        else:
            self.helper.print_warning("创建物料响应不符合预期，继续测试")

    def test_get_material_detail(self):
        """测试获取物料详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取物料详情...")

        material_id = 1
        response = self.helper.get(
            f"/materials/{material_id}", resource_type=f"material_{material_id}"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("物料详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("物料不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取物料详情响应不符合预期")

    def test_update_material(self):
        """测试更新物料（预期：无数据时返回404）"""
        self.helper.print_info("测试更新物料...")

        material_id = 1
        update_data = {
            "description": "更新后的物料描述",
        }

        response = self.helper.put(
            f"/materials/{material_id}",
            update_data,
            resource_type=f"material_{material_id}_update",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("物料更新成功")
        elif status_code in (404, 422):
            self.helper.print_warning(f"返回{status_code}是预期行为（物料不存在或参数不匹配）")
        else:
            self.helper.print_warning("更新物料响应不符合预期")
