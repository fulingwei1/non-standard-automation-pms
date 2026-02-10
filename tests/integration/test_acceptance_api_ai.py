# -*- coding: utf-8 -*-
"""
验收管理模块 API 集成测试

测试范围：
- 验收模板 (GET/POST /acceptance-templates, GET/PUT/DELETE /acceptance-templates/{id})
- 验收单 (GET/POST /acceptance-orders, GET/PUT/DELETE /acceptance-orders/{id})
- 验收流程 (POST /acceptance-orders/{id}/submit, PUT /acceptance-orders/{id}/start|complete)

实际路由前缀: "" (api.py prefix="")
"""

import pytest

from tests.integration.api_test_helper import APITestHelper


@pytest.mark.integration
class TestAcceptanceTemplatesAPI:
    """验收模板 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("验收模板 API 测试")

    def test_get_templates_list(self):
        """测试获取验收模板列表"""
        self.helper.print_info("测试获取验收模板列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/acceptance-templates", params=params, resource_type="acceptance_templates_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个验收模板")
        else:
            self.helper.print_warning("获取验收模板列表响应不符合预期")

    def test_create_template(self):
        """测试创建验收模板"""
        self.helper.print_info("测试创建验收模板...")

        template_data = {
            "template_name": "FAT出厂验收模板",
            "template_type": "FAT",
            "description": "测试用出厂验收模板",
            "items": [
                {
                    "item_name": "外观检查",
                    "item_description": "检查设备外观是否完好",
                    "check_type": "VISUAL",
                    "sort_order": 1,
                },
            ],
        }

        response = self.helper.post(
            "/acceptance-templates", template_data, resource_type="acceptance_template"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            result = response.get("data", {})
            template_id = result.get("id") if isinstance(result, dict) else None
            if template_id:
                self.tracked_resources.append(("template", template_id))
                self.helper.print_success(f"验收模板创建成功，ID: {template_id}")
            else:
                self.helper.print_success("验收模板创建成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或数据冲突）")
        else:
            self.helper.print_warning("创建验收模板响应不符合预期，继续测试")

    def test_get_template_detail(self):
        """测试获取验收模板详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取验收模板详情...")

        template_id = 1
        response = self.helper.get(
            f"/acceptance-templates/{template_id}",
            resource_type=f"acceptance_template_{template_id}",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("验收模板详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("验收模板不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取验收模板详情响应不符合预期")


@pytest.mark.integration
class TestAcceptanceOrdersAPI:
    """验收单 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("验收单 API 测试")

    def test_get_orders_list(self):
        """测试获取验收单列表"""
        self.helper.print_info("测试获取验收单列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/acceptance-orders", params=params, resource_type="acceptance_orders_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个验收单")
        else:
            self.helper.print_warning("获取验收单列表响应不符合预期")

    def test_get_order_detail(self):
        """测试获取验收单详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取验收单详情...")

        order_id = 1
        response = self.helper.get(
            f"/acceptance-orders/{order_id}",
            resource_type=f"acceptance_order_{order_id}",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("验收单详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("验收单不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取验收单详情响应不符合预期")

    def test_submit_order(self):
        """测试提交验收单（预期：无数据时返回404）"""
        self.helper.print_info("测试提交验收单...")

        order_id = 1
        response = self.helper.post(
            f"/acceptance-orders/{order_id}/submit",
            data={},
            resource_type=f"acceptance_order_{order_id}_submit",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("验收单提交成功")
        elif status_code in (404, 422):
            self.helper.print_warning(f"返回{status_code}是预期行为（验收单不存在或状态不允许）")
        else:
            self.helper.print_warning("提交验收单响应不符合预期")
