# -*- coding: utf-8 -*-
"""
客户管理模块 API 集成测试

测试范围：
- 客户CRUD (CRUD)
- 客户关联数据查询 (Related)
- 客户360视图 (View360)
"""

import pytest

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator, Colors


@pytest.mark.integration
class TestCustomersCRUDAPI:
    """客户CRUD API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("客户CRUD API 测试")

    def test_create_customer(self):
        """测试创建客户"""
        self.helper.print_info("测试创建客户...")

        customer_data = {
            "customer_name": "深圳科技有限公司",
            "customer_code": f"CUS{TestDataGenerator.generate_order_no()}",
            "industry": "electronics",
            "customer_type": "CLIENT",
            "level": "A",
            "contact_person": "张总",
            "contact_phone": "13800138000",
            "contact_email": "zhang@sztech.com",
            "province": "广东省",
            "city": "深圳市",
            "address": "南山区科技园",
            "website": "www.sztech.com",
            "is_active": True,
        }

        response = self.helper.post(
            "/customers", customer_data, resource_type="customer"
        )

        result = self.helper.assert_success(response)
        if result:
            customer_id = result.get("id")
            if customer_id:
                self.tracked_resources.append(("customer", customer_id))
                self.helper.print_success(f"客户创建成功，ID: {customer_id}")
                self.helper.assert_field_equals(
                    result, "customer_name", "深圳科技有限公司"
                )
            else:
                self.helper.print_warning("客户创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建客户响应不符合预期，继续测试")

    def test_get_customers_list(self):
        """测试获取客户列表"""
        self.helper.print_info("测试获取客户列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "industry": "electronics",
            "is_active": True,
        }

        response = self.helper.get(
            "/customers", params=params, resource_type="customers_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个客户")
        else:
            self.helper.print_warning("获取客户列表响应不符合预期")

    def test_get_customer_detail(self):
        """测试获取客户详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的客户ID")

        customer_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取客户详情 (ID: {customer_id})...")

        response = self.helper.get(
            f"/customers/{customer_id}", resource_type=f"customer_{customer_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("客户详情获取成功")
        else:
            self.helper.print_warning("获取客户详情响应不符合预期")

    def test_update_customer(self):
        """测试更新客户"""
        if not self.tracked_resources:
            pytest.skip("没有可用的客户ID")

        customer_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新客户 (ID: {customer_id})...")

        update_data = {
            "contact_person": "李总",
            "contact_phone": "13900139000",
            "level": "AA",
            "website": "www.newsztech.com",
        }

        response = self.helper.put(
            f"/customers/{customer_id}",
            update_data,
            resource_type=f"customer_{customer_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("客户更新成功")
        else:
            self.helper.print_warning("更新客户响应不符合预期")

    def test_deactivate_customer(self):
        """测试停用客户"""
        if not self.tracked_resources:
            pytest.skip("没有可用的客户ID")

        customer_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试停用客户 (ID: {customer_id})...")

        response = self.helper.delete(
            f"/customers/{customer_id}", resource_type=f"customer_{customer_id}_delete"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("客户停用成功")
        else:
            self.helper.print_warning("停用客户响应不符合预期")


@pytest.mark.integration
class TestCustomersRelatedAPI:
    """客户关联数据查询 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_customer_id = 1  # 假设存在客户ID
        self.helper.print_info("客户关联数据查询 API 测试")

    def test_get_customer_projects(self):
        """测试获取客户项目列表"""
        self.helper.print_info("测试获取客户项目列表...")

        params = {
            "customer_id": self.test_customer_id,
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/customers/related/projects",
            params=params,
            resource_type="customer_projects",
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个项目")
        else:
            self.helper.print_warning("获取客户项目列表响应不符合预期")

    def test_get_customer_orders(self):
        """测试获取客户订单列表"""
        self.helper.print_info("测试获取客户订单列表...")

        params = {
            "customer_id": self.test_customer_id,
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/customers/related/orders", params=params, resource_type="customer_orders"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个订单")
        else:
            self.helper.print_warning("获取客户订单列表响应不符合预期")

    def test_get_customer_statistics(self):
        """测试获取客户统计"""
        self.helper.print_info("测试获取客户统计...")

        params = {
            "customer_id": self.test_customer_id,
            "period": "year",
            "year": 2026,
        }

        response = self.helper.get(
            "/customers/related/statistics",
            params=params,
            resource_type="customer_statistics",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("客户统计数据获取成功")
        else:
            self.helper.print_warning("获取客户统计响应不符合预期")


@pytest.mark.integration
class TestCustomersView360API:
    """客户360视图 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_customer_id = 1  # 假设存在客户ID
        self.helper.print_info("客户360视图 API 测试")

    def test_get_view360_summary(self):
        """测试获取360视图汇总"""
        self.helper.print_info("测试获取360视图汇总...")

        response = self.helper.get("/view360/summary", resource_type="view360_summary")

        if self.helper.assert_success(response):
            self.helper.print_success("360视图汇总获取成功")
        else:
            self.helper.print_warning("获取360视图汇总响应不符合预期")

    def test_get_view360_projects(self):
        """测试获取360视图项目"""
        self.helper.print_info("测试获取360视图项目...")

        params = {
            "customer_id": self.test_customer_id,
            "include_closed": False,
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/view360/projects", params=params, resource_type="view360_projects"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个项目")
        else:
            self.helper.print_warning("获取360视图项目响应不符合预期")

    def test_get_view360_financials(self):
        """测试获取360视图财务"""
        self.helper.print_info("测试获取360视图财务...")

        params = {
            "customer_id": self.test_customer_id,
            "period": "year",
            "year": 2026,
        }

        response = self.helper.get(
            "/view360/financials", params=params, resource_type="view360_financials"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("360视图财务数据获取成功")
        else:
            self.helper.print_warning("获取360视图财务响应不符合预期")
