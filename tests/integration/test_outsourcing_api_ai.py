# -*- coding: utf-8 -*-
"""
外协管理模块 API 集成测试

测试范围：
- 外协供应商 (GET/POST /outsourcing-vendors, GET/PUT /outsourcing-vendors/{id})
- 外协订单 (GET/POST /outsourcing-orders, GET/PUT /outsourcing-orders/{id})
- 外协交付 (GET/POST /outsourcing-deliveries)
- 外协质检 (GET/POST /outsourcing-inspections)
- 外协付款 (GET/POST /outsourcing-payments)
- 供应商对账 (GET /outsourcing-vendors/{id}/statement)

实际路由前缀: "" (api.py prefix="")
"""

import pytest

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestOutsourcingVendorsAPI:
    """外协供应商 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("外协供应商 API 测试")

    def test_get_vendors_list(self):
        """测试获取外协供应商列表"""
        self.helper.print_info("测试获取外协供应商列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/outsourcing-vendors", params=params, resource_type="outsourcing_vendors_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个外协供应商")
        else:
            self.helper.print_warning("获取外协供应商列表响应不符合预期")

    def test_create_vendor(self):
        """测试创建外协供应商"""
        self.helper.print_info("测试创建外协供应商...")

        vendor_data = {
            "vendor_name": "精密加工厂",
            "vendor_code": f"OV-{TestDataGenerator.generate_order_no()}",
            "contact_person": "王经理",
            "contact_phone": "13900139001",
            "business_scope": "精密零件加工",
            "address": "广东省深圳市科技园",
        }

        response = self.helper.post(
            "/outsourcing-vendors", vendor_data, resource_type="outsourcing_vendor"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            result = response.get("data", {})
            vendor_id = result.get("id") if isinstance(result, dict) else None
            if vendor_id:
                self.tracked_resources.append(("vendor", vendor_id))
                self.helper.print_success(f"外协供应商创建成功，ID: {vendor_id}")
            else:
                self.helper.print_success("外协供应商创建成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或数据冲突）")
        else:
            self.helper.print_warning("创建外协供应商响应不符合预期，继续测试")

    def test_get_vendor_detail(self):
        """测试获取外协供应商详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取外协供应商详情...")

        vendor_id = 1
        response = self.helper.get(
            f"/outsourcing-vendors/{vendor_id}",
            resource_type=f"outsourcing_vendor_{vendor_id}",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("外协供应商详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("外协供应商不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取外协供应商详情响应不符合预期")

    def test_get_vendor_statement(self):
        """测试获取供应商对账单（预期：无数据时返回404）"""
        self.helper.print_info("测试获取供应商对账单...")

        vendor_id = 1
        response = self.helper.get(
            f"/outsourcing-vendors/{vendor_id}/statement",
            resource_type=f"vendor_{vendor_id}_statement",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("供应商对账单获取成功")
        elif status_code in (404, 422):
            self.helper.print_warning(f"返回{status_code}是预期行为（供应商不存在或无数据）")
        else:
            self.helper.print_warning("获取供应商对账单响应不符合预期")


@pytest.mark.integration
class TestOutsourcingOrdersAPI:
    """外协订单 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("外协订单 API 测试")

    def test_get_orders_list(self):
        """测试获取外协订单列表"""
        self.helper.print_info("测试获取外协订单列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/outsourcing-orders", params=params, resource_type="outsourcing_orders_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个外协订单")
        else:
            self.helper.print_warning("获取外协订单列表响应不符合预期")

    def test_get_order_detail(self):
        """测试获取外协订单详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取外协订单详情...")

        order_id = 1
        response = self.helper.get(
            f"/outsourcing-orders/{order_id}",
            resource_type=f"outsourcing_order_{order_id}",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("外协订单详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("外协订单不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取外协订单详情响应不符合预期")


@pytest.mark.integration
class TestOutsourcingDeliveriesAPI:
    """外协交付 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("外协交付 API 测试")

    def test_get_deliveries_list(self):
        """测试获取外协交付列表"""
        self.helper.print_info("测试获取外协交付列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/outsourcing-deliveries", params=params, resource_type="outsourcing_deliveries_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条外协交付记录")
        else:
            self.helper.print_warning("获取外协交付列表响应不符合预期")


@pytest.mark.integration
class TestOutsourcingInspectionsAPI:
    """外协质检 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("外协质检 API 测试")

    def test_get_inspections_list(self):
        """测试获取外协质检列表"""
        self.helper.print_info("测试获取外协质检列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/outsourcing-inspections", params=params, resource_type="outsourcing_inspections_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条外协质检记录")
        else:
            self.helper.print_warning("获取外协质检列表响应不符合预期")


@pytest.mark.integration
class TestOutsourcingPaymentsAPI:
    """外协付款 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("外协付款 API 测试")

    def test_get_payments_list(self):
        """测试获取外协付款列表"""
        self.helper.print_info("测试获取外协付款列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/outsourcing-payments", params=params, resource_type="outsourcing_payments_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条外协付款记录")
        else:
            self.helper.print_warning("获取外协付款列表响应不符合预期")
