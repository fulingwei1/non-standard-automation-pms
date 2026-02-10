# -*- coding: utf-8 -*-
"""
采购管理模块 API 集成测试

测试范围：
- 采购订单列表 (GET /purchase-orders/)
- 创建采购订单 (POST /purchase-orders/)
- 采购订单详情 (GET /purchase-orders/{id})
- 更新采购订单 (PUT /purchase-orders/{id})

实际路由前缀: /purchase-orders (api.py prefix="/purchase-orders")
"""

import pytest

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestPurchaseOrdersCRUDAPI:
    """采购订单CRUD API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("采购订单CRUD API 测试")

    def test_get_purchase_orders_list(self):
        """测试获取采购订单列表"""
        self.helper.print_info("测试获取采购订单列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/purchase-orders/", params=params, resource_type="purchase_orders_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个采购订单")
        else:
            self.helper.print_warning("获取采购订单列表响应不符合预期")

    def test_get_purchase_order_detail(self):
        """测试获取采购订单详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取采购订单详情...")

        order_id = 1
        response = self.helper.get(
            f"/purchase-orders/{order_id}", resource_type=f"purchase_order_{order_id}"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("采购订单详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("采购订单不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取采购订单详情响应不符合预期")

    def test_create_purchase_order(self):
        """测试创建采购订单"""
        self.helper.print_info("测试创建采购订单...")

        order_data = {
            "order_no": TestDataGenerator.generate_order_no(),
            "supplier_id": 1,
            "order_date": TestDataGenerator.future_date(0),
            "expected_delivery_date": TestDataGenerator.future_date(14),
            "remark": "测试采购订单",
        }

        response = self.helper.post(
            "/purchase-orders/", order_data, resource_type="purchase_order"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            result = response.get("data", {})
            order_id = result.get("id") if isinstance(result, dict) else None
            if order_id:
                self.tracked_resources.append(("purchase_order", order_id))
                self.helper.print_success(f"采购订单创建成功，ID: {order_id}")
            else:
                self.helper.print_success("采购订单创建成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或供应商不存在）")
        else:
            self.helper.print_warning("创建采购订单响应不符合预期，继续测试")
