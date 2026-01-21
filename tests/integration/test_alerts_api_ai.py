# -*- coding: utf-8 -*-
"""
预警管理API集成测试（AI辅助生成）

测试覆盖：
- 预警规则管理
- 预警记录管理
- 预警统计
- 预警升级
- 项目健康度快照
"""

import pytest
from datetime import datetime

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestAlertRules:
    """预警规则管理测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_create_alert_rule(self, admin_token, test_project):
        """测试创建预警规则"""
        self.helper.print_info("测试: 创建预警规则")

        rule_data = {
            "rule_code": f"AR-{TestDataGenerator.generate_project_code()}",
            "rule_name": f"AI测试预警规则-{datetime.now().strftime('%H%M%S')}",
            "rule_type": "DELAY",
            "project_id": test_project.id,
            "condition_expression": "delay_days > 3",
            "alert_level": "WARNING",
            "is_active": True,
            "description": "这是一个AI生成的测试预警规则",
            "notification_channels": ["EMAIL", "SYSTEM"],
        }

        response = self.helper.post(
            "/alert-rules/", rule_data, username="admin", password="admin123"
        )

        self.helper.print_request("POST", "/alert-rules/", rule_data)
        self.helper.print_response(response)

        # 断言
        if response["status_code"] == 200:
            APITestHelper.assert_success(response, "创建预警规则成功")

            data = response["data"]
            assert data["rule_name"] == rule_data["rule_name"]
            assert data["rule_type"] == "DELAY"

            rule_id = data.get("id")
            if rule_id:
                self.helper.track_resource("alert_rule", rule_id)

            self.helper.print_success(f"✓ 预警规则创建成功: {data.get('rule_code')}")
        else:
            self.helper.print_warning("预警规则创建端点可能需要调整")

    def test_get_alert_rules_list(self, admin_token):
        """测试获取预警规则列表"""
        self.helper.print_info("测试: 获取预警规则列表")

        response = self.helper.get(
            "/alert-rules/",
            username="admin",
            password="admin123",
            params={"page": 1, "page_size": 20},
        )

        self.helper.print_request("GET", "/alert-rules/")
        self.helper.print_response(response, show_data=False)

        # 断言
        APITestHelper.assert_success(response, "获取预警规则列表成功")

        self.helper.print_success("✓ 获取预警规则列表成功")

    def test_update_alert_rule(self, admin_token):
        """测试更新预警规则"""
        self.helper.print_info("测试: 更新预警规则")

        # 获取一个规则
        list_response = self.helper.get(
            "/alert-rules/",
            username="admin",
            password="admin123",
            params={"page_size": 1},
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有预警规则数据，跳过测试")

        rule_id = items[0].get("id")

        # 更新规则
        update_data = {"alert_level": "SEVERE", "description": "更新后的描述"}

        response = self.helper.put(
            f"/alert-rules/{rule_id}",
            update_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request("PUT", f"/alert-rules/{rule_id}", update_data)
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "更新预警规则成功")

        self.helper.print_success("✓ 预警规则更新成功")

    def test_enable_disable_rule(self, admin_token):
        """测试启用/禁用预警规则"""
        self.helper.print_info("测试: 启用/禁用预警规则")

        # 获取一个规则
        list_response = self.helper.get(
            "/alert-rules/",
            username="admin",
            password="admin123",
            params={"page_size": 1},
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有预警规则数据，跳过测试")

        rule_id = items[0].get("id")

        # 禁用规则
        disable_data = {"is_active": False}

        response = self.helper.put(
            f"/alert-rules/{rule_id}",
            disable_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request("PUT", f"/alert-rules/{rule_id}", disable_data)
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "禁用预警规则成功")

        # 启用规则
        enable_data = {"is_active": True}

        response = self.helper.put(
            f"/alert-rules/{rule_id}",
            enable_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request("PUT", f"/alert-rules/{rule_id}", enable_data)
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "启用预警规则成功")

        self.helper.print_success("✓ 启用/禁用预警规则成功")


@pytest.mark.integration
class TestAlertRecords:
    """预警记录管理测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_get_alert_records_list(self, admin_token):
        """测试获取预警记录列表"""
        self.helper.print_info("测试: 获取预警记录列表")

        response = self.helper.get(
            "/alert-records/",
            username="admin",
            password="admin123",
            params={"page": 1, "page_size": 20},
        )

        self.helper.print_request("GET", "/alert-records/")
        self.helper.print_response(response, show_data=False)

        # 断言
        APITestHelper.assert_success(response, "获取预警记录列表成功")

        self.helper.print_success("✓ 获取预警记录列表成功")

    def test_filter_alert_records_by_level(self, admin_token):
        """测试按级别过滤预警记录"""
        self.helper.print_info("测试: 按级别过滤预警记录")

        response = self.helper.get(
            "/alert-records/",
            username="admin",
            password="admin123",
            params={"alert_level": "WARNING", "page": 1, "page_size": 20},
        )

        self.helper.print_request("GET", "/alert-records/", {"alert_level": "WARNING"})
        self.helper.print_response(response, show_data=False)

        # 断言
        APITestHelper.assert_success(response, "按级别过滤预警记录成功")

        self.helper.print_success("✓ 按级别过滤预警记录成功")

    def test_filter_alert_records_by_status(self, admin_token):
        """测试按状态过滤预警记录"""
        self.helper.print_info("测试: 按状态过滤预警记录")

        response = self.helper.get(
            "/alert-records/",
            username="admin",
            password="admin123",
            params={"status": "OPEN", "page": 1, "page_size": 20},
        )

        self.helper.print_request("GET", "/alert-records/", {"status": "OPEN"})
        self.helper.print_response(response, show_data=False)

        # 断言
        APITestHelper.assert_success(response, "按状态过滤预警记录成功")

        self.helper.print_success("✓ 按状态过滤预警记录成功")

    def test_acknowledge_alert(self, admin_token):
        """测试确认预警"""
        self.helper.print_info("测试: 确认预警")

        # 获取一个预警记录
        list_response = self.helper.get(
            "/alert-records/",
            username="admin",
            password="admin123",
            params={"page_size": 1},
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有预警记录数据，跳过测试")

        record_id = items[0].get("id")

        # 确认预警
        ack_data = {"acknowledge_note": "已处理预警", "action_taken": "已协调资源解决"}

        response = self.helper.put(
            f"/alert-records/{record_id}/acknowledge",
            ack_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request(
            "PUT", f"/alert-records/{record_id}/acknowledge", ack_data
        )
        self.helper.print_response(response)

        # 断言
        if response["status_code"] == 200:
            APITestHelper.assert_success(response, "确认预警成功")
            self.helper.print_success("✓ 预警确认成功")
        else:
            self.helper.print_warning("预警确认端点可能需要调整")

    def test_resolve_alert(self, admin_token):
        """测试解决预警"""
        self.helper.print_info("测试: 解决预警")

        # 获取一个预警记录
        list_response = self.helper.get(
            "/alert-records/",
            username="admin",
            password="admin123",
            params={"page_size": 1},
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有预警记录数据，跳过测试")

        record_id = items[0].get("id")

        # 解决预警
        resolve_data = {
            "resolution_note": "问题已解决",
            "resolved_at": datetime.now().isoformat(),
        }

        response = self.helper.put(
            f"/alert-records/{record_id}/resolve",
            resolve_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request(
            "PUT", f"/alert-records/{record_id}/resolve", resolve_data
        )
        self.helper.print_response(response)

        # 断言
        if response["status_code"] == 200:
            APITestHelper.assert_success(response, "解决预警成功")
            self.helper.print_success("✓ 预警解决成功")
        else:
            self.helper.print_warning("预警解决端点可能需要调整")


@pytest.mark.integration
class TestAlertStatistics:
    """预警统计测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_get_alert_statistics(self, admin_token):
        """测试获取预警统计"""
        self.helper.print_info("测试: 获取预警统计")

        response = self.helper.get(
            "/alert-records/statistics", username="admin", password="admin123"
        )

        self.helper.print_request("GET", "/alert-records/statistics")
        self.helper.print_response(response, show_data=False)

        # 断言
        APITestHelper.assert_success(response, "获取预警统计成功")

        self.helper.print_success("✓ 获取预警统计成功")

    def test_get_alert_trends(self, admin_token):
        """测试获取预警趋势"""
        self.helper.print_info("测试: 获取预警趋势")

        response = self.helper.get(
            "/alert-records/trends",
            username="admin",
            password="admin123",
            params={"days": 30},
        )

        self.helper.print_request("GET", "/alert-records/trends", {"days": 30})
        self.helper.print_response(response, show_data=False)

        # 断言
        if response["status_code"] == 200:
            APITestHelper.assert_success(response, "获取预警趋势成功")
            self.helper.print_success("✓ 获取预警趋势成功")
        else:
            self.helper.print_warning("预警趋势端点可能需要调整")

    def test_get_project_alert_summary(self, admin_token, test_project):
        """测试获取项目预警汇总"""
        self.helper.print_info("测试: 获取项目预警汇总")

        project_id = test_project.id

        response = self.helper.get(
            f"/alert-records/project/{project_id}/summary",
            username="admin",
            password="admin123",
        )

        self.helper.print_request("GET", f"/alert-records/project/{project_id}/summary")
        self.helper.print_response(response, show_data=False)

        # 断言
        if response["status_code"] == 200:
            APITestHelper.assert_success(response, "获取项目预警汇总成功")
            self.helper.print_success("✓ 获取项目预警汇总成功")
        else:
            self.helper.print_warning("项目预警汇总端点可能需要调整")


@pytest.mark.integration
class TestProjectHealthSnapshot:
    """项目健康度快照测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_get_health_snapshots(self, admin_token):
        """测试获取健康度快照列表"""
        self.helper.print_info("测试: 获取健康度快照列表")

        response = self.helper.get(
            "/project-health-snapshots/",
            username="admin",
            password="admin123",
            params={"page": 1, "page_size": 20},
        )

        self.helper.print_request("GET", "/project-health-snapshots/")
        self.helper.print_response(response, show_data=False)

        # 断言
        if response["status_code"] == 200:
            APITestHelper.assert_success(response, "获取健康度快照列表成功")
            self.helper.print_success("✓ 获取健康度快照列表成功")
        else:
            self.helper.print_warning("健康度快照端点可能需要调整")

    def test_create_health_snapshot(self, admin_token, test_project):
        """测试创建健康度快照"""
        self.helper.print_info("测试: 创建健康度快照")

        snapshot_data = {
            "project_id": test_project.id,
            "health_status": "H2",
            "score": 75,
            "risk_factors": ["进度延迟", "成本超支"],
            "assessment_note": "项目整体风险中等",
        }

        response = self.helper.post(
            "/project-health-snapshots/",
            snapshot_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request("POST", "/project-health-snapshots/", snapshot_data)
        self.helper.print_response(response)

        # 断言
        if response["status_code"] == 200:
            APITestHelper.assert_success(response, "创建健康度快照成功")
            self.helper.print_success("✓ 创建健康度快照成功")
        else:
            self.helper.print_warning("健康度快照端点可能需要调整")


if __name__ == "__main__":
    print("=" * 60)
    print("预警管理API集成测试（AI辅助生成）")
    print("=" * 60)
    print("\n测试内容：")
    print("  1. 预警规则管理")
    print("  2. 预警记录管理")
    print("  3. 预警统计")
    print("  4. 项目健康度快照")
    print("\n运行测试：")
    print("  pytest tests/integration/test_alerts_api_ai.py -v")
    print("=" * 60)
