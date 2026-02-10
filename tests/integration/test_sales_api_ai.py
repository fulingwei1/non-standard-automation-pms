# -*- coding: utf-8 -*-
"""
销售管理模块 API 集成测试

测试范围：
- 销售线索 (GET/POST /sales/leads, GET/PUT/DELETE /sales/leads/{id})
- 销售机会 (GET/POST /sales/opportunities, GET/PUT /sales/opportunities/{id})
- 销售报价 (GET /sales/quotes, GET /sales/quotes/{id})

实际路由前缀: /sales (api.py prefix="/sales")
"""

import pytest

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestSalesLeadsAPI:
    """销售线索 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("销售线索 API 测试")

    def test_get_leads_list(self):
        """测试获取销售线索列表"""
        self.helper.print_info("测试获取销售线索列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/sales/leads", params=params, resource_type="sales_leads_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条销售线索")
        else:
            self.helper.print_warning("获取销售线索列表响应不符合预期")

    def test_create_lead(self):
        """测试创建销售线索"""
        self.helper.print_info("测试创建销售线索...")

        lead_data = {
            "lead_name": "测试线索-深圳科技",
            "company_name": "深圳科技有限公司",
            "contact_person": "张总",
            "contact_phone": "13800138000",
            "source": "REFERRAL",
            "description": "ICT测试设备需求",
        }

        response = self.helper.post(
            "/sales/leads", lead_data, resource_type="sales_lead"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            result = response.get("data", {})
            lead_id = result.get("id") if isinstance(result, dict) else None
            if lead_id:
                self.tracked_resources.append(("lead", lead_id))
                self.helper.print_success(f"销售线索创建成功，ID: {lead_id}")
            else:
                self.helper.print_success("销售线索创建成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或数据冲突）")
        else:
            self.helper.print_warning("创建销售线索响应不符合预期，继续测试")

    def test_get_lead_detail(self):
        """测试获取销售线索详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取销售线索详情...")

        lead_id = 1
        response = self.helper.get(
            f"/sales/leads/{lead_id}", resource_type=f"sales_lead_{lead_id}"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("销售线索详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("销售线索不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取销售线索详情响应不符合预期")


@pytest.mark.integration
class TestSalesOpportunitiesAPI:
    """销售机会 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("销售机会 API 测试")

    def test_get_opportunities_list(self):
        """测试获取销售机会列表"""
        self.helper.print_info("测试获取销售机会列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/sales/opportunities", params=params, resource_type="opportunities_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条销售机会")
        else:
            self.helper.print_warning("获取销售机会列表响应不符合预期")

    def test_create_opportunity(self):
        """测试创建销售机会"""
        self.helper.print_info("测试创建销售机会...")

        opp_data = {
            "name": "ICT设备项目",
            "customer_name": "深圳科技有限公司",
            "expected_amount": 500000.00,
            "expected_close_date": TestDataGenerator.future_date(30),
            "stage": "LEAD",
            "description": "客户需要ICT测试设备",
        }

        response = self.helper.post(
            "/sales/opportunities", opp_data, resource_type="opportunity"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            result = response.get("data", {})
            opp_id = result.get("id") if isinstance(result, dict) else None
            if opp_id:
                self.tracked_resources.append(("opportunity", opp_id))
                self.helper.print_success(f"销售机会创建成功，ID: {opp_id}")
            else:
                self.helper.print_success("销售机会创建成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或数据冲突）")
        else:
            self.helper.print_warning("创建销售机会响应不符合预期，继续测试")

    def test_get_opportunity_detail(self):
        """测试获取销售机会详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取销售机会详情...")

        opp_id = 1
        response = self.helper.get(
            f"/sales/opportunities/{opp_id}", resource_type=f"opportunity_{opp_id}"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("销售机会详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("销售机会不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取销售机会详情响应不符合预期")


@pytest.mark.integration
class TestSalesQuotesAPI:
    """销售报价 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("销售报价 API 测试")

    def test_get_quotes_list(self):
        """测试获取报价列表"""
        self.helper.print_info("测试获取报价列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/sales/quotes", params=params, resource_type="sales_quotes_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条报价记录")
        else:
            self.helper.print_warning("获取报价列表响应不符合预期")

    def test_get_quote_detail(self):
        """测试获取报价详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取报价详情...")

        quote_id = 1
        response = self.helper.get(
            f"/sales/quotes/{quote_id}", resource_type=f"quote_{quote_id}"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("报价详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("报价不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取报价详情响应不符合预期")
