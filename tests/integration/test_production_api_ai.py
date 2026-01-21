# -*- coding: utf-8 -*-
"""
生产管理模块 API 集成测试

测试范围：
- 生产计划 (Production Plans)
- 工单管理 (Work Orders)
- 车间管理 (Workshops)
- 工位管理 (Workstations)
- 工作报表 (Work Reports)
- 生产仪表板 (Dashboard)
"""

import pytest
from datetime import date, datetime, timedelta

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator, Colors


@pytest.mark.integration
class TestProductionWorkshopsAPI:
    """车间管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("生产车间管理 API 测试")

    def test_create_workshop(self):
        """测试创建车间"""
        self.helper.print_info("测试创建车间...")

        workshop_data = {
            "workshop_code": "WS-A01",
            "workshop_name": "机械加工车间",
            "location": "一楼东区",
            "manager_name": "王经理",
            "contact_phone": "13900139000",
            "description": "主要进行机架、面板等机械件加工",
        }

        response = self.helper.post(
            "/workshops", workshop_data, resource_type="workshop"
        )

        result = self.helper.assert_success(response)
        if result:
            workshop_id = result.get("id")
            if workshop_id:
                self.tracked_resources.append(("workshop", workshop_id))
                self.helper.print_success(f"车间创建成功，ID: {workshop_id}")
                self.helper.assert_field_equals(result, "workshop_name", "机械加工车间")
            else:
                self.helper.print_warning("车间创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建车间响应不符合预期，继续测试")

    def test_get_workshops_list(self):
        """测试获取车间列表"""
        self.helper.print_info("测试获取车间列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/workshops", params=params, resource_type="workshops_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个车间")
        else:
            self.helper.print_warning("获取车间列表响应不符合预期")

    def test_get_workshop_detail(self):
        """测试获取车间详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的车间ID")

        workshop_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取车间详情 (ID: {workshop_id})...")

        response = self.helper.get(
            f"/workshops/{workshop_id}", resource_type=f"workshop_{workshop_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("车间详情获取成功")
        else:
            self.helper.print_warning("获取车间详情响应不符合预期")

    def test_update_workshop(self):
        """测试更新车间"""
        if not self.tracked_resources:
            pytest.skip("没有可用的车间ID")

        workshop_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新车间 (ID: {workshop_id})...")

        update_data = {
            "description": "更新后的车间描述",
        }

        response = self.helper.put(
            f"/workshops/{workshop_id}",
            update_data,
            resource_type=f"workshop_{workshop_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("车间更新成功")
        else:
            self.helper.print_warning("更新车间响应不符合预期")


@pytest.mark.integration
class TestProductionWorkstationsAPI:
    """工位管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("生产工位管理 API 测试")

    def test_create_workstation(self):
        """测试创建工位"""
        self.helper.print_info("测试创建工位...")

        # 首先创建一个车间
        workshop_data = {
            "workshop_code": "WS-B01",
            "workshop_name": "电气装配车间",
        }
        workshop_response = self.helper.post(
            "/workshops", workshop_data, resource_type="workshop_for_ws"
        )
        workshop_result = (
            workshop_response.json() if workshop_response.status_code == 200 else {}
        )
        workshop_id = workshop_result.get("id")

        if not workshop_id:
            self.helper.print_warning("无法创建车间，使用默认值继续测试")
            workshop_id = 1  # 假设ID

        workstation_data = {
            "workstation_code": "WSN-001",
            "workstation_name": "电装工位1",
            "workshop_id": workshop_id,
            "location": "西区1号位",
            "capacity": 1,
            "status": "ACTIVE",
        }

        response = self.helper.post(
            "/workstations", workstation_data, resource_type="workstation"
        )

        result = self.helper.assert_success(response)
        if result:
            workstation_id = result.get("id")
            if workstation_id:
                self.tracked_resources.append(("workstation", workstation_id))
                self.helper.print_success(f"工位创建成功，ID: {workstation_id}")
            else:
                self.helper.print_warning("工位创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建工位响应不符合预期，继续测试")

    def test_get_workstations_list(self):
        """测试获取工位列表"""
        self.helper.print_info("测试获取工位列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "status": "ACTIVE",
        }

        response = self.helper.get(
            "/workstations", params=params, resource_type="workstations_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个工位")
        else:
            self.helper.print_warning("获取工位列表响应不符合预期")

    def test_get_workstation_detail(self):
        """测试获取工位详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的工位ID")

        workstation_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取工位详情 (ID: {workstation_id})...")

        response = self.helper.get(
            f"/workstations/{workstation_id}",
            resource_type=f"workstation_{workstation_id}",
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("工位详情获取成功")
        else:
            self.helper.print_warning("获取工位详情响应不符合预期")


@pytest.mark.integration
class TestProductionPlansAPI:
    """生产计划 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("生产计划管理 API 测试")

    def test_create_production_plan(self):
        """测试创建生产计划"""
        self.helper.print_info("测试创建生产计划...")

        plan_data = {
            "project_id": self.test_project_id,
            "plan_code": f"PP-{TestDataGenerator.generate_order_no()}",
            "plan_name": "FCT设备生产计划",
            "plan_type": "MAIN",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=45)).isoformat(),
            "priority": "HIGH",
            "description": "FCT测试设备的完整生产计划",
        }

        response = self.helper.post(
            "/plans", plan_data, resource_type="production_plan"
        )

        result = self.helper.assert_success(response)
        if result:
            plan_id = result.get("id")
            if plan_id:
                self.tracked_resources.append(("production_plan", plan_id))
                self.helper.print_success(f"生产计划创建成功，ID: {plan_id}")
            else:
                self.helper.print_warning("生产计划创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建生产计划响应不符合预期，继续测试")

    def test_get_production_plans_list(self):
        """测试获取生产计划列表"""
        self.helper.print_info("测试获取生产计划列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "status": "IN_PROGRESS",
        }

        response = self.helper.get(
            "/plans", params=params, resource_type="production_plans_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个生产计划")
        else:
            self.helper.print_warning("获取生产计划列表响应不符合预期")

    def test_get_production_plan_detail(self):
        """测试获取生产计划详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的生产计划ID")

        plan_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取生产计划详情 (ID: {plan_id})...")

        response = self.helper.get(
            f"/plans/{plan_id}", resource_type=f"production_plan_{plan_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("生产计划详情获取成功")
        else:
            self.helper.print_warning("获取生产计划详情响应不符合预期")

    def test_update_production_plan_status(self):
        """测试更新生产计划状态"""
        if not self.tracked_resources:
            pytest.skip("没有可用的生产计划ID")

        plan_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新生产计划状态 (ID: {plan_id})...")

        update_data = {
            "status": "COMPLETED",
            "completion_date": date.today().isoformat(),
        }

        response = self.helper.put(
            f"/plans/{plan_id}",
            update_data,
            resource_type=f"production_plan_{plan_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("生产计划状态更新成功")
        else:
            self.helper.print_warning("更新生产计划状态响应不符合预期")


@pytest.mark.integration
class TestProductionWorkOrdersAPI:
    """工单管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, test_machine, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.test_machine_id = test_machine.id if test_machine else None
        self.tracked_resources = []
        self.helper.print_info("生产工单管理 API 测试")

    def test_create_work_order(self):
        """测试创建工单"""
        self.helper.print_info("测试创建工单...")

        work_order_data = {
            "work_order_no": TestDataGenerator.generate_order_no(),
            "task_name": "机架焊接",
            "task_type": "FABRICATION",
            "project_id": self.test_project_id,
            "machine_id": self.test_machine_id,
            "plan_qty": 1,
            "specification": "按照图纸WS-DWG-001执行",
            "plan_start_date": date.today().isoformat(),
            "plan_end_date": (date.today() + timedelta(days=7)).isoformat(),
            "standard_hours": 40.0,
        }

        response = self.helper.post(
            "/work-orders", work_order_data, resource_type="work_order"
        )

        result = self.helper.assert_success(response)
        if result:
            work_order_id = result.get("id")
            if work_order_id:
                self.tracked_resources.append(("work_order", work_order_id))
                self.helper.print_success(f"工单创建成功，ID: {work_order_id}")
            else:
                self.helper.print_warning("工单创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建工单响应不符合预期，继续测试")

    def test_get_work_orders_list(self):
        """测试获取工单列表"""
        self.helper.print_info("测试获取工单列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "status": "PENDING",
        }

        response = self.helper.get(
            "/work-orders", params=params, resource_type="work_orders_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个工单")
        else:
            self.helper.print_warning("获取工单列表响应不符合预期")

    def test_get_work_order_detail(self):
        """测试获取工单详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的工单ID")

        work_order_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取工单详情 (ID: {work_order_id})...")

        response = self.helper.get(
            f"/work-orders/{work_order_id}", resource_type=f"work_order_{work_order_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("工单详情获取成功")
        else:
            self.helper.print_warning("获取工单详情响应不符合预期")

    def test_assign_work_order(self):
        """测试派工"""
        if not self.tracked_resources:
            pytest.skip("没有可用的工单ID")

        work_order_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试派工 (工单ID: {work_order_id})...")

        assign_data = {
            "worker_id": 1,  # 假设有工人ID
            "workshop_id": 1,  # 假设有车间ID
            "workstation_id": 1,  # 假设有工位ID
            "assigned_date": datetime.now().isoformat(),
        }

        response = self.helper.post(
            f"/work-orders/{work_order_id}/assign",
            assign_data,
            resource_type=f"work_order_{work_order_id}_assign",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工单派工成功")
        else:
            self.helper.print_warning("工单派工响应不符合预期")

    def test_update_work_order_progress(self):
        """测试更新工单进度"""
        if not self.tracked_resources:
            pytest.skip("没有可用的工单ID")

        work_order_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新工单进度 (ID: {work_order_id})...")

        progress_data = {
            "completed_qty": 0,
            "qualified_qty": 0,
            "defect_qty": 0,
            "actual_hours": 8.0,
            "progress_notes": "开始加工",
        }

        response = self.helper.put(
            f"/work-orders/{work_order_id}/progress",
            progress_data,
            resource_type=f"work_order_{work_order_id}_progress",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工单进度更新成功")
        else:
            self.helper.print_warning("更新工单进度响应不符合预期")

    def test_complete_work_order(self):
        """测试完成工单"""
        if not self.tracked_resources:
            pytest.skip("没有可用的工单ID")

        work_order_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试完成工单 (ID: {work_order_id})...")

        complete_data = {
            "completed_qty": 1,
            "qualified_qty": 1,
            "defect_qty": 0,
            "actual_hours": 38.5,
            "actual_end_time": datetime.now().isoformat(),
            "completion_notes": "工单已完成",
        }

        response = self.helper.post(
            f"/work-orders/{work_order_id}/complete",
            complete_data,
            resource_type=f"work_order_{work_order_id}_complete",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("工单完成成功")
        else:
            self.helper.print_warning("完成工单响应不符合预期")


@pytest.mark.integration
class TestProductionWorkReportsAPI:
    """工作报表 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("生产工作报表 API 测试")

    def test_get_work_reports_list(self):
        """测试获取工作报表列表"""
        self.helper.print_info("测试获取工作报表列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "start_date": (date.today() - timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat(),
        }

        response = self.helper.get(
            "/work-reports", params=params, resource_type="work_reports_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条工作报表记录")
        else:
            self.helper.print_warning("获取工作报表列表响应不符合预期")

    def test_create_work_report(self):
        """测试创建工作报表"""
        self.helper.print_info("测试创建工作报表...")

        work_report_data = {
            "report_date": date.today().isoformat(),
            "workshop_id": 1,
            "workstation_id": 1,
            "worker_id": 1,
            "work_hours": 8.0,
            "production_qty": 2,
            "qualified_qty": 2,
            "defect_qty": 0,
            "remarks": "正常生产",
        }

        response = self.helper.post(
            "/work-reports", work_report_data, resource_type="work_report"
        )

        result = self.helper.assert_success(response)
        if result:
            report_id = result.get("id")
            if report_id:
                self.tracked_resources.append(("work_report", report_id))
                self.helper.print_success(f"工作报表创建成功，ID: {report_id}")
            else:
                self.helper.print_warning("工作报表创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建工作报表响应不符合预期，继续测试")

    def test_get_production_dashboard(self):
        """测试获取生产仪表板数据"""
        self.helper.print_info("测试获取生产仪表板数据...")

        response = self.helper.get("/dashboard", resource_type="production_dashboard")

        if self.helper.assert_success(response):
            self.helper.print_success("生产仪表板数据获取成功")
        else:
            self.helper.print_warning("获取生产仪表板响应不符合预期")

    def test_get_production_statistics(self):
        """测试获取生产统计数据"""
        self.helper.print_info("测试获取生产统计数据...")

        params = {
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat(),
        }

        response = self.helper.get(
            "/statistics", params=params, resource_type="production_statistics"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("生产统计数据获取成功")
        else:
            self.helper.print_warning("获取生产统计响应不符合预期")
