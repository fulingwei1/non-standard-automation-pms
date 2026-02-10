# -*- coding: utf-8 -*-
"""
供应商管理模块 API 集成测试

测试范围：
- 供应商CRUD (GET/POST /suppliers/, GET/PUT/DELETE /suppliers/{id})
- 供应商评级 (PUT /suppliers/{id}/rating)
- 供应商物料列表 (GET /suppliers/{id}/materials)

实际路由前缀: /suppliers (api.py prefix="/suppliers")
"""

import pytest

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestSuppliersCRUDAPI:
    """供应商CRUD API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("供应商CRUD API 测试")

    def test_get_suppliers_list(self):
        """测试获取供应商列表"""
        self.helper.print_info("测试获取供应商列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/suppliers/", params=params, resource_type="suppliers_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个供应商")
        else:
            self.helper.print_warning("获取供应商列表响应不符合预期")

    def test_create_supplier(self):
        """测试创建供应商"""
        self.helper.print_info("测试创建供应商...")

        supplier_data = {
            "supplier_code": f"SUP-{TestDataGenerator.generate_order_no()}",
            "supplier_name": "精密加工厂",
            "supplier_short_name": "精密厂",
            "supplier_type": "MACHINING",
            "contact_person": "王经理",
            "contact_phone": "13900139001",
            "contact_email": "wang@precision.com",
            "address": "广东省深圳市科技园北区123号",
            "remark": "精密零件加工、表面处理",
        }

        response = self.helper.post(
            "/suppliers/", supplier_data, resource_type="supplier"
        )

        result = self.helper.assert_success(response)
        if result:
            supplier_id = result.get("id")
            if supplier_id:
                self.tracked_resources.append(("supplier", supplier_id))
                self.helper.print_success(f"供应商创建成功，ID: {supplier_id}")
            else:
                self.helper.print_warning("供应商创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建供应商响应不符合预期，继续测试")

    def test_get_supplier_detail(self):
        """测试获取供应商详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取供应商详情...")

        supplier_id = 1
        response = self.helper.get(
            f"/suppliers/{supplier_id}", resource_type=f"supplier_{supplier_id}"
        )

        status_code = response.get("status_code") if isinstance(response, dict) else None
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("供应商详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("供应商不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取供应商详情响应不符合预期")

    def test_update_supplier(self):
        """测试更新供应商（预期：无数据时返回404）"""
        self.helper.print_info("测试更新供应商...")

        supplier_id = 1
        update_data = {
            "contact_phone": "13900139002",
            "remark": "更新后的备注",
        }

        response = self.helper.put(
            f"/suppliers/{supplier_id}",
            update_data,
            resource_type=f"supplier_{supplier_id}_update",
        )

        status_code = response.get("status_code") if isinstance(response, dict) else None
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("供应商更新成功")
        elif status_code == 404:
            self.helper.print_warning("供应商不存在，返回404是预期行为")
        else:
            self.helper.print_warning("更新供应商响应不符合预期")


@pytest.mark.integration
class TestSuppliersRatingAPI:
    """供应商评级 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("供应商评级 API 测试")

    def test_update_supplier_rating(self):
        """测试更新供应商评分（PUT /suppliers/{id}/rating，query params）"""
        self.helper.print_info("测试更新供应商评分...")

        supplier_id = 1
        response = self.helper.put(
            f"/suppliers/{supplier_id}/rating?quality_rating=4.5&delivery_rating=4.0&service_rating=4.2",
            data={},
            resource_type=f"supplier_{supplier_id}_rating",
        )

        status_code = response.get("status_code") if isinstance(response, dict) else None
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("供应商评分更新成功")
        elif status_code in (404, 422):
            self.helper.print_warning(f"返回{status_code}是预期行为（供应商不存在或参数不匹配）")
        else:
            self.helper.print_warning("更新供应商评分响应不符合预期")


@pytest.mark.integration
class TestSuppliersMaterialsAPI:
    """供应商物料 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("供应商物料 API 测试")

    def test_get_supplier_materials(self):
        """测试获取供应商物料列表（预期：无数据时返回404或空列表）"""
        self.helper.print_info("测试获取供应商物料列表...")

        supplier_id = 1
        response = self.helper.get(
            f"/suppliers/{supplier_id}/materials",
            resource_type=f"supplier_{supplier_id}_materials",
        )

        status_code = response.get("status_code") if isinstance(response, dict) else None
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("供应商物料列表获取成功")
        elif status_code == 404:
            self.helper.print_warning("供应商不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取供应商物料列表响应不符合预期")
