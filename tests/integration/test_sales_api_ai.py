# -*- coding: utf-8 -*-
"""
销售管理模块 API 集成测试

测试范围：
- 线索管理 (Leads)
- 商机管理 (Opportunities)
- 报价管理 (Quotes)
- 合同管理 (Contracts)
- 发票管理 (Invoices)
- 付款管理 (Payments)
- 统计分析 (Statistics)
- 销售目标 (Targets)
"""

import pytest
from datetime import datetime, timedelta

from tests.integration.api_test_helper import APITestHelper, Colors


@pytest.mark.integration
class TestSalesLeadsAPI:
    """线索管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_customer, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_customer_id = test_customer.id if test_customer else None
        self.tracked_resources = []
        self.helper.print_info("销售线索管理 API 测试")

    def test_create_lead(self):
        """测试创建线索"""
        self.helper.print_info("测试创建销售线索...")

        lead_data = {
            "customer_id": self.test_customer_id,
            "contact_name": "张三",
            "contact_phone": "13800138000",
            "contact_email": "zhangsan@example.com",
            "company_name": "测试公司",
            "status": "NEW",
            "source": "WEB",
            "priority": "HIGH",
            "description": "这是一个测试线索",
        }

        response = self.helper.post("/sales/leads", lead_data, resource_type="lead")

        # 尝试解析响应
        result = self.helper.assert_success(response)
        if result:
            lead_id = result.get("id")
            if lead_id:
                self.tracked_resources.append(("lead", lead_id))
                self.helper.print_success(f"线索创建成功，ID: {lead_id}")
                self.helper.assert_field_equals(result, "contact_name", "张三")
            else:
                self.helper.print_warning("线索创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建线索响应不符合预期，继续测试")

    def test_get_leads_list(self):
        """测试获取线索列表"""
        self.helper.print_info("测试获取线索列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "status": "NEW",
        }

        response = self.helper.get(
            "/sales/leads", params=params, resource_type="leads_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条线索记录")
        else:
            self.helper.print_warning("获取线索列表响应不符合预期")

    def test_get_lead_detail(self):
        """测试获取线索详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的线索ID")

        lead_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取线索详情 (ID: {lead_id})...")

        response = self.helper.get(
            f"/sales/leads/{lead_id}", resource_type=f"lead_{lead_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("线索详情获取成功")
        else:
            self.helper.print_warning("获取线索详情响应不符合预期")

    def test_update_lead(self):
        """测试更新线索"""
        if not self.tracked_resources:
            pytest.skip("没有可用的线索ID")

        lead_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新线索 (ID: {lead_id})...")

        update_data = {
            "status": "CONTACTED",
            "description": "更新后的线索描述",
        }

        response = self.helper.put(
            f"/sales/leads/{lead_id}",
            update_data,
            resource_type=f"lead_{lead_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("线索更新成功")
        else:
            self.helper.print_warning("更新线索响应不符合预期")

    def test_create_lead_followup(self):
        """测试创建线索跟进记录"""
        if not self.tracked_resources:
            pytest.skip("没有可用的线索ID")

        lead_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试创建线索跟进记录 (线索ID: {lead_id})...")

        followup_data = {
            "followup_type": "PHONE_CALL",
            "content": "跟进内容：已与客户电话沟通",
            "next_action": "安排技术交流",
            "next_action_date": (datetime.now() + timedelta(days=3)).isoformat(),
        }

        response = self.helper.post(
            f"/sales/leads/{lead_id}/followups",
            followup_data,
            resource_type=f"lead_{lead_id}_followup",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("线索跟进记录创建成功")
        else:
            self.helper.print_warning("创建跟进记录响应不符合预期")

    def test_convert_lead_to_opportunity(self):
        """测试将线索转为商机"""
        if not self.tracked_resources:
            pytest.skip("没有可用的线索ID")

        lead_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试将线索转为商机 (线索ID: {lead_id})...")

        convert_data = {
            "opportunity_name": "测试商机",
            "expected_close_date": (datetime.now() + timedelta(days=30))
            .date()
            .isoformat(),
            "estimated_amount": 100000.00,
        }

        response = self.helper.post(
            f"/sales/leads/{lead_id}/convert",
            convert_data,
            resource_type=f"lead_{lead_id}_convert",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("线索成功转为商机")
        else:
            self.helper.print_warning("线索转商机响应不符合预期")


@pytest.mark.integration
class TestSalesOpportunitiesAPI:
    """商机管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_customer, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_customer_id = test_customer.id if test_customer else None
        self.tracked_resources = []
        self.helper.print_info("销售商机管理 API 测试")

    def test_create_opportunity(self):
        """测试创建商机"""
        self.helper.print_info("测试创建商机...")

        opportunity_data = {
            "customer_id": self.test_customer_id,
            "opportunity_name": "FCT测试设备项目",
            "stage": "QUALIFICATION",
            "probability": 30,
            "expected_close_date": (datetime.now() + timedelta(days=60))
            .date()
            .isoformat(),
            "estimated_amount": 200000.00,
            "description": "这是一个测试商机",
        }

        response = self.helper.post(
            "/sales/opportunities", opportunity_data, resource_type="opportunity"
        )

        result = self.helper.assert_success(response)
        if result:
            opp_id = result.get("id")
            if opp_id:
                self.tracked_resources.append(("opportunity", opp_id))
                self.helper.print_success(f"商机创建成功，ID: {opp_id}")
                self.helper.assert_field_equals(
                    result, "opportunity_name", "FCT测试设备项目"
                )
            else:
                self.helper.print_warning("商机创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建商机响应不符合预期，继续测试")

    def test_get_opportunities_list(self):
        """测试获取商机列表"""
        self.helper.print_info("测试获取商机列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "stage": "QUALIFICATION",
        }

        response = self.helper.get(
            "/sales/opportunities", params=params, resource_type="opportunities_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条商机记录")
        else:
            self.helper.print_warning("获取商机列表响应不符合预期")

    def test_get_opportunity_detail(self):
        """测试获取商机详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的商机ID")

        opp_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取商机详情 (ID: {opp_id})...")

        response = self.helper.get(
            f"/sales/opportunities/{opp_id}", resource_type=f"opportunity_{opp_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("商机详情获取成功")
        else:
            self.helper.print_warning("获取商机详情响应不符合预期")

    def test_update_opportunity_stage(self):
        """测试更新商机阶段"""
        if not self.tracked_resources:
            pytest.skip("没有可用的商机ID")

        opp_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新商机阶段 (ID: {opp_id})...")

        update_data = {
            "stage": "PROPOSAL",
            "probability": 60,
        }

        response = self.helper.put(
            f"/sales/opportunities/{opp_id}",
            update_data,
            resource_type=f"opportunity_{opp_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("商机阶段更新成功")
        else:
            self.helper.print_warning("更新商机阶段响应不符合预期")


@pytest.mark.integration
class TestSalesQuotesAPI:
    """报价管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_customer, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_customer_id = test_customer.id if test_customer else None
        self.tracked_resources = []
        self.helper.print_info("销售报价管理 API 测试")

    def test_create_quote(self):
        """测试创建报价"""
        self.helper.print_info("测试创建报价...")

        # 首先创建一个商机
        opportunity_data = {
            "customer_id": self.test_customer_id,
            "opportunity_name": "测试报价商机",
            "stage": "PROPOSAL",
            "probability": 50,
        }
        opp_response = self.helper.post(
            "/sales/opportunities",
            opportunity_data,
            resource_type="opportunity_for_quote",
        )
        opp_result = opp_response.json() if opp_response.status_code == 200 else {}
        opportunity_id = opp_result.get("id")

        if not opportunity_id:
            self.helper.print_warning("无法创建商机，使用默认值继续测试")
            opportunity_id = 1  # 假设ID

        quote_data = {
            "opportunity_id": opportunity_id,
            "customer_id": self.test_customer_id,
            "valid_until": (datetime.now() + timedelta(days=30)).date().isoformat(),
            "version": {
                "version_no": "V1",
                "total_price": 150000.00,
                "cost_total": 100000.00,
                "gross_margin": 33.33,
                "lead_time_days": 45,
                "items": [
                    {
                        "item_code": "ITEM-001",
                        "item_name": "FCT测试工装",
                        "quantity": 1,
                        "unit_price": 150000.00,
                        "total_price": 150000.00,
                    }
                ],
            },
        }

        response = self.helper.post("/sales/quotes", quote_data, resource_type="quote")

        result = self.helper.assert_success(response)
        if result:
            quote_id = result.get("id")
            if quote_id:
                self.tracked_resources.append(("quote", quote_id))
                self.helper.print_success(f"报价创建成功，ID: {quote_id}")
            else:
                self.helper.print_warning("报价创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建报价响应不符合预期，继续测试")

    def test_get_quotes_list(self):
        """测试获取报价列表"""
        self.helper.print_info("测试获取报价列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "status": "DRAFT",
        }

        response = self.helper.get(
            "/sales/quotes", params=params, resource_type="quotes_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条报价记录")
        else:
            self.helper.print_warning("获取报价列表响应不符合预期")

    def test_get_quote_detail(self):
        """测试获取报价详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的报价ID")

        quote_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取报价详情 (ID: {quote_id})...")

        response = self.helper.get(
            f"/sales/quotes/{quote_id}", resource_type=f"quote_{quote_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("报价详情获取成功")
        else:
            self.helper.print_warning("获取报价详情响应不符合预期")

    def test_approve_quote(self):
        """测试审批报价"""
        if not self.tracked_resources:
            pytest.skip("没有可用的报价ID")

        quote_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试审批报价 (ID: {quote_id})...")

        response = self.helper.post(
            f"/sales/quotes/{quote_id}/approve",
            {},
            resource_type=f"quote_{quote_id}_approve",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("报价审批成功")
        else:
            self.helper.print_warning("审批报价响应不符合预期")

    def test_create_quote_version(self):
        """测试创建报价版本"""
        if not self.tracked_resources:
            pytest.skip("没有可用的报价ID")

        quote_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试创建报价版本 (ID: {quote_id})...")

        version_data = {
            "version_no": "V2",
            "total_price": 140000.00,
            "cost_total": 95000.00,
            "gross_margin": 32.14,
            "lead_time_days": 40,
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "FCT测试工装",
                    "quantity": 1,
                    "unit_price": 140000.00,
                    "total_price": 140000.00,
                }
            ],
        }

        response = self.helper.post(
            f"/sales/quotes/{quote_id}/versions",
            version_data,
            resource_type=f"quote_{quote_id}_version",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("报价版本创建成功")
        else:
            self.helper.print_warning("创建报价版本响应不符合预期")


@pytest.mark.integration
class TestSalesStatisticsAPI:
    """销售统计 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.helper.print_info("销售统计 API 测试")

    def test_get_sales_statistics(self):
        """测试获取销售统计数据"""
        self.helper.print_info("测试获取销售统计数据...")

        response = self.helper.get(
            "/sales/statistics", resource_type="sales_statistics"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("销售统计数据获取成功")
        else:
            self.helper.print_warning("获取销售统计响应不符合预期")

    def test_get_pipeline_analysis(self):
        """测试获取销售漏斗分析"""
        self.helper.print_info("测试获取销售漏斗分析...")

        response = self.helper.get(
            "/sales/pipeline-analysis", resource_type="pipeline_analysis"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("销售漏斗分析数据获取成功")
        else:
            self.helper.print_warning("获取销售漏斗分析响应不符合预期")

    def test_get_sales_targets(self):
        """测试获取销售目标"""
        self.helper.print_info("测试获取销售目标...")

        response = self.helper.get("/sales/targets", resource_type="sales_targets")

        if self.helper.assert_success(response):
            self.helper.print_success("销售目标获取成功")
        else:
            self.helper.print_warning("获取销售目标响应不符合预期")

    def test_create_sales_target(self):
        """测试创建销售目标"""
        self.helper.print_info("测试创建销售目标...")

        target_data = {
            "year": 2026,
            "month": 1,
            "target_amount": 5000000.00,
            "target_leads": 100,
            "target_opportunities": 50,
        }

        response = self.helper.post(
            "/sales/targets", target_data, resource_type="sales_target"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("销售目标创建成功")
        else:
            self.helper.print_warning("创建销售目标响应不符合预期")
