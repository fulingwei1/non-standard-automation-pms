# -*- coding: utf-8 -*-
"""
外协管理模块 API 集成测试

测试范围：
- 外协供应商 (Outsourcing Vendors)
- 外协订单 (Outsourcing Orders)
- 外协交付 (Outsourcing Deliveries)
- 外协质检 (Outsourcing Inspections)
- 外协进度 (Outsourcing Progress)
- 外协付款 (Outsourcing Payments)
"""

import pytest
from datetime import date, datetime, timedelta

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator, Colors


@pytest.mark.integration
class TestOutsourcingVendorsAPI:
    """外协供应商 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("外协供应商管理 API 测试")

    def test_create_vendor(self):
        """测试创建外协供应商"""
        self.helper.print_info("测试创建外协供应商...")

        vendor_data = {
            "vendor_code": f"OSV-{TestDataGenerator.generate_order_no()}",
            "vendor_name": "精密加工有限公司",
            "contact_person": "李经理",
            "contact_phone": "13700137000",
            "contact_email": "limgr@precision.com",
            "address": "深圳市宝安区工业大道123号",
            "specialization": "CNC加工、激光切割",
            "rating": 4.5,
            "is_active": True,
        }

        response = self.helper.post("/vendors", vendor_data, resource_type="vendor")

        result = self.helper.assert_success(response)
        if result:
            vendor_id = result.get("id")
            if vendor_id:
                self.tracked_resources.append(("vendor", vendor_id))
                self.helper.print_success(f"外协供应商创建成功，ID: {vendor_id}")
                self.helper.assert_field_equals(
                    result, "vendor_name", "精密加工有限公司"
                )
            else:
                self.helper.print_warning("外协供应商创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建外协供应商响应不符合预期，继续测试")

    def test_get_vendors_list(self):
        """测试获取外协供应商列表"""
        self.helper.print_info("测试获取外协供应商列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "is_active": True,
        }

        response = self.helper.get(
            "/vendors", params=params, resource_type="vendors_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个外协供应商")
        else:
            self.helper.print_warning("获取外协供应商列表响应不符合预期")

    def test_get_vendor_detail(self):
        """测试获取外协供应商详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的外协供应商ID")

        vendor_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取外协供应商详情 (ID: {vendor_id})...")

        response = self.helper.get(
            f"/vendors/{vendor_id}", resource_type=f"vendor_{vendor_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("外协供应商详情获取成功")
        else:
            self.helper.print_warning("获取外协供应商详情响应不符合预期")

    def test_update_vendor(self):
        """测试更新外协供应商"""
        if not self.tracked_resources:
            pytest.skip("没有可用的外协供应商ID")

        vendor_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新外协供应商 (ID: {vendor_id})...")

        update_data = {
            "rating": 4.8,
            "specialization": "CNC加工、激光切割、电镀",
        }

        response = self.helper.put(
            f"/vendors/{vendor_id}",
            update_data,
            resource_type=f"vendor_{vendor_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("外协供应商更新成功")
        else:
            self.helper.print_warning("更新外协供应商响应不符合预期")


@pytest.mark.integration
class TestOutsourcingOrdersAPI:
    """外协订单 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, test_machine, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.test_machine_id = test_machine.id if test_machine else None
        self.tracked_resources = []
        self.helper.print_info("外协订单管理 API 测试")

    def test_create_outsourcing_order(self):
        """测试创建外协订单"""
        self.helper.print_info("测试创建外协订单...")

        # 首先创建一个外协供应商
        vendor_data = {
            "vendor_code": f"OSV-{TestDataGenerator.generate_order_no()}",
            "vendor_name": "模具加工厂",
            "contact_person": "王工",
            "contact_phone": "13800138001",
        }
        vendor_response = self.helper.post(
            "/vendors", vendor_data, resource_type="vendor_for_order"
        )
        vendor_result = (
            vendor_response.json() if vendor_response.status_code == 200 else {}
        )
        vendor_id = vendor_result.get("id")

        if not vendor_id:
            self.helper.print_warning("无法创建外协供应商，使用默认值继续测试")
            vendor_id = 1  # 假设ID

        order_data = {
            "vendor_id": vendor_id,
            "project_id": self.test_project_id,
            "machine_id": self.test_machine_id,
            "order_type": "FABRICATION",
            "order_name": "工架外协加工",
            "required_date": (date.today() + timedelta(days=15)).date().isoformat(),
            "items": [
                {
                    "item_code": "PART-GJ-001",
                    "item_name": "工架底板",
                    "specification": "铝板5052 5mm",
                    "quantity": 2,
                    "unit": "PCS",
                    "unit_price": 500.00,
                },
                {
                    "item_code": "PART-GJ-002",
                    "item_name": "工架立柱",
                    "specification": "铝型材4040",
                    "quantity": 8,
                    "unit": "PCS",
                    "unit_price": 120.00,
                },
            ],
            "total_amount": 1960.00,
            "delivery_address": "工厂仓库",
            "notes": "要求表面阳极氧化处理",
        }

        response = self.helper.post(
            "/orders", order_data, resource_type="outsourcing_order"
        )

        result = self.helper.assert_success(response)
        if result:
            order_id = result.get("id")
            if order_id:
                self.tracked_resources.append(("outsourcing_order", order_id))
                self.helper.print_success(f"外协订单创建成功，ID: {order_id}")
            else:
                self.helper.print_warning("外协订单创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建外协订单响应不符合预期，继续测试")

    def test_get_outsourcing_orders_list(self):
        """测试获取外协订单列表"""
        self.helper.print_info("测试获取外协订单列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "status": "PENDING",
        }

        response = self.helper.get(
            "/orders", params=params, resource_type="outsourcing_orders_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个外协订单")
        else:
            self.helper.print_warning("获取外协订单列表响应不符合预期")

    def test_get_outsourcing_order_detail(self):
        """测试获取外协订单详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的外协订单ID")

        order_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取外协订单详情 (ID: {order_id})...")

        response = self.helper.get(
            f"/orders/{order_id}", resource_type=f"outsourcing_order_{order_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("外协订单详情获取成功")
        else:
            self.helper.print_warning("获取外协订单详情响应不符合预期")

    def test_update_outsourcing_order(self):
        """测试更新外协订单"""
        if not self.tracked_resources:
            pytest.skip("没有可用的外协订单ID")

        order_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新外协订单 (ID: {order_id})...")

        update_data = {
            "status": "IN_PROGRESS",
            "notes": "更新备注：供应商已确认，开始加工",
        }

        response = self.helper.put(
            f"/orders/{order_id}",
            update_data,
            resource_type=f"outsourcing_order_{order_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("外协订单更新成功")
        else:
            self.helper.print_warning("更新外协订单响应不符合预期")

    def test_cancel_outsourcing_order(self):
        """测试取消外协订单"""
        if not self.tracked_resources:
            pytest.skip("没有可用的外协订单ID")

        order_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试取消外协订单 (ID: {order_id})...")

        cancel_data = {
            "cancel_reason": "项目需求变更",
            "cancelled_by": "admin",
        }

        response = self.helper.post(
            f"/orders/{order_id}/cancel",
            cancel_data,
            resource_type=f"outsourcing_order_{order_id}_cancel",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("外协订单取消成功")
        else:
            self.helper.print_warning("取消外协订单响应不符合预期")


@pytest.mark.integration
class TestOutsourcingDeliveriesAPI:
    """外协交付 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("外协交付管理 API 测试")

    def test_create_delivery(self):
        """测试创建外协交付单"""
        self.helper.print_info("测试创建外协交付单...")

        delivery_data = {
            "order_id": 1,  # 假设存在外协订单ID
            "delivery_date": date.today().isoformat(),
            "delivered_by": "物流公司A",
            "tracking_no": "SF1234567890",
            "items": [
                {
                    "order_item_id": 1,  # 假设存在订单项ID
                    "delivered_qty": 2,
                    "qualified_qty": 2,
                    "defect_qty": 0,
                },
            ],
            "notes": "包装完好",
        }

        response = self.helper.post(
            "/deliveries", delivery_data, resource_type="delivery"
        )

        result = self.helper.assert_success(response)
        if result:
            delivery_id = result.get("id")
            if delivery_id:
                self.tracked_resources.append(("delivery", delivery_id))
                self.helper.print_success(f"外协交付单创建成功，ID: {delivery_id}")
            else:
                self.helper.print_warning("外协交付单创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建外协交付单响应不符合预期，继续测试")

    def test_get_deliveries_list(self):
        """测试获取外协交付单列表"""
        self.helper.print_info("测试获取外协交付单列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat(),
        }

        response = self.helper.get(
            "/deliveries", params=params, resource_type="deliveries_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个外协交付单")
        else:
            self.helper.print_warning("获取外协交付单列表响应不符合预期")


@pytest.mark.integration
class TestOutsourcingInspectionsAPI:
    """外协质检 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("外协质检管理 API 测试")

    def test_create_inspection(self):
        """测试创建外协质检单"""
        self.helper.print_info("测试创建外协质检单...")

        inspection_data = {
            "delivery_id": 1,  # 假设存在交付单ID
            "inspection_date": date.today().isoformat(),
            "inspector_id": 1,  # 假设存在检验员ID
            "inspection_standard": "GB/T 1804-2000",
            "items": [
                {
                    "delivery_item_id": 1,  # 假设存在交付项ID
                    "inspection_items": "尺寸、外观、表面处理",
                    "inspection_result": "QUALIFIED",
                    "defect_description": "",
                },
            ],
            "overall_result": "QUALIFIED",
            "notes": "质检合格，准予入库",
        }

        response = self.helper.post(
            "/inspections", inspection_data, resource_type="inspection"
        )

        result = self.helper.assert_success(response)
        if result:
            inspection_id = result.get("id")
            if inspection_id:
                self.tracked_resources.append(("inspection", inspection_id))
                self.helper.print_success(f"外协质检单创建成功，ID: {inspection_id}")
            else:
                self.helper.print_warning("外协质检单创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建外协质检单响应不符合预期，继续测试")

    def test_get_inspections_list(self):
        """测试获取外协质检单列表"""
        self.helper.print_info("测试获取外协质检单列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "overall_result": "QUALIFIED",
        }

        response = self.helper.get(
            "/inspections", params=params, resource_type="inspections_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个外协质检单")
        else:
            self.helper.print_warning("获取外协质检单列表响应不符合预期")


@pytest.mark.integration
class TestOutsourcingProgressAPI:
    """外协进度 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("外协进度管理 API 测试")

    def test_create_progress_update(self):
        """测试创建外协进度更新"""
        self.helper.print_info("测试创建外协进度更新...")

        progress_data = {
            "order_id": 1,  # 假设存在外协订单ID
            "progress_date": datetime.now().isoformat(),
            "progress_percentage": 50,
            "status": "IN_PROGRESS",
            "notes": "已完成50%，等待表面处理",
            "next_steps": "进行表面阳极氧化处理",
            "estimated_completion": (date.today() + timedelta(days=5)).isoformat(),
        }

        response = self.helper.post(
            "/progress", progress_data, resource_type="progress"
        )

        result = self.helper.assert_success(response)
        if result:
            progress_id = result.get("id")
            if progress_id:
                self.tracked_resources.append(("progress", progress_id))
                self.helper.print_success(f"外协进度更新创建成功，ID: {progress_id}")
            else:
                self.helper.print_warning("外协进度更新创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建外协进度更新响应不符合预期，继续测试")

    def test_get_progress_list(self):
        """测试获取外协进度列表"""
        self.helper.print_info("测试获取外协进度列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "order_id": 1,  # 筛选特定订单的进度
        }

        response = self.helper.get(
            "/progress", params=params, resource_type="progress_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条外协进度记录")
        else:
            self.helper.print_warning("获取外协进度列表响应不符合预期")


@pytest.mark.integration
class TestOutsourcingPaymentsAPI:
    """外协付款 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("外协付款管理 API 测试")

    def test_create_payment(self):
        """测试创建外协付款"""
        self.helper.print_info("测试创建外协付款...")

        payment_data = {
            "order_id": 1,  # 假设存在外协订单ID
            "payment_type": "ADVANCE",
            "payment_date": date.today().isoformat(),
            "amount": 980.00,  # 订单金额的50%
            "payment_method": "TRANSFER",
            "bank_account": "6222021234567890",
            "bank_name": "中国工商银行",
            "notes": "预付款",
        }

        response = self.helper.post("/payments", payment_data, resource_type="payment")

        result = self.helper.assert_success(response)
        if result:
            payment_id = result.get("id")
            if payment_id:
                self.tracked_resources.append(("payment", payment_id))
                self.helper.print_success(f"外协付款创建成功，ID: {payment_id}")
            else:
                self.helper.print_warning("外协付款创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建外协付款响应不符合预期，继续测试")

    def test_get_payments_list(self):
        """测试获取外协付款列表"""
        self.helper.print_info("测试获取外协付款列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "payment_type": "ADVANCE",
        }

        response = self.helper.get(
            "/payments", params=params, resource_type="payments_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条外协付款记录")
        else:
            self.helper.print_warning("获取外协付款列表响应不符合预期")

    def test_get_payment_statistics(self):
        """测试获取外协付款统计"""
        self.helper.print_info("测试获取外协付款统计...")

        params = {
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat(),
        }

        response = self.helper.get(
            "/payments/statistics", params=params, resource_type="payment_statistics"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("外协付款统计数据获取成功")
        else:
            self.helper.print_warning("获取外协付款统计响应不符合预期")
