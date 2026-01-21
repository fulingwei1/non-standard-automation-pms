# -*- coding: utf-8 -*-
"""
项目管理API集成测试（AI辅助生成）

使用AI分析现有API结构和业务逻辑，生成全面的测试用例。

测试覆盖：
- 项目CRUD操作
- 项目查询和过滤
- 项目状态和阶段管理
- 项目成员管理
- 项目健康度
"""

import pytest
from datetime import datetime

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestProjectCRUD:
    """项目CRUD操作测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_create_project_success(self, admin_token, test_customer):
        """测试创建项目成功"""
        self.helper.print_info("测试: 创建项目")

        project_data = {
            "project_code": TestDataGenerator.generate_project_code(),
            "project_name": f"AI测试项目-{datetime.now().strftime('%H%M%S')}",
            "customer_id": test_customer.id,
            "customer_name": test_customer.customer_name,
            "project_type": "FCT",
            "product_type": "测试设备",
            "contract_amount": 100000.00,
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
            "priority": "NORMAL",
            "description": "这是一个AI生成的测试项目",
        }

        response = self.helper.post(
            "/projects/", project_data, username="admin", password="admin123"
        )

        self.helper.print_request("POST", "/projects/", project_data)
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "创建项目成功")
        APITestHelper.assert_data_not_empty(response, "项目数据不为空")

        data = response["data"]
        assert data["project_name"] == project_data["project_name"]
        assert data["project_code"] == project_data["project_code"]
        assert data["stage"] == "S1"
        assert data["status"] == "ST01"

        # 记录创建的资源ID
        project_id = data.get("id")
        if project_id:
            self.helper.track_resource("project", project_id)

        self.helper.print_success(f"✓ 项目创建成功: {data.get('project_code')}")

    def test_create_project_validation_error(self, admin_token):
        """测试创建项目验证失败"""
        self.helper.print_info("测试: 创建项目验证失败（缺少必填字段）")

        # 缺少必填字段
        invalid_data = {"project_name": "不完整的项目"}

        response = self.helper.post(
            "/projects/", invalid_data, username="admin", password="admin123"
        )

        self.helper.print_request("POST", "/projects/", invalid_data)
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_status(response, 422, "验证失败返回422")

        self.helper.print_success("✓ 验证失败返回422状态码")

    def test_get_project_list(self, admin_token):
        """测试获取项目列表"""
        self.helper.print_info("测试: 获取项目列表")

        response = self.helper.get(
            "/projects/",
            username="admin",
            password="admin123",
            params={"page": 1, "page_size": 20},
        )

        self.helper.print_request("GET", "/projects/")
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "获取项目列表成功")

        data = response["data"]
        assert "items" in data, "响应缺少items字段"
        assert "total" in data, "响应缺少total字段"
        assert "page" in data, "响应缺少page字段"
        assert "page_size" in data, "响应缺少page_size字段"

        self.helper.print_success(f"✓ 获取到 {data.get('total', 0)} 个项目")

    def test_get_project_list_with_filters(self, admin_token):
        """测试带过滤条件获取项目列表"""
        self.helper.print_info("测试: 带过滤条件获取项目列表")

        # 多种过滤条件
        filters = {
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
            "page": 1,
            "page_size": 10,
        }

        response = self.helper.get(
            "/projects/", username="admin", password="admin123", params=filters
        )

        self.helper.print_request("GET", "/projects/", params=filters)
        self.helper.print_response(response, show_data=False)

        # 断言
        APITestHelper.assert_success(response, "带过滤条件获取项目列表成功")

        self.helper.print_success("✓ 过滤查询成功")

    def test_get_project_detail(self, admin_token):
        """测试获取项目详情"""
        self.helper.print_info("测试: 获取项目详情")

        # 先获取项目列表
        list_response = self.helper.get(
            "/projects/", username="admin", password="admin123", params={"page_size": 1}
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有项目数据，跳过测试")

        project_id = items[0].get("id")
        project_code = items[0].get("project_code")

        self.helper.print_info(f"使用项目ID: {project_id}, 编码: {project_code}")

        # 获取项目详情
        response = self.helper.get(
            f"/projects/{project_id}", username="admin", password="admin123"
        )

        self.helper.print_request("GET", f"/projects/{project_id}")
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "获取项目详情成功")

        data = response["data"]
        assert data["id"] == project_id, "项目ID不匹配"

        self.helper.print_success(f"✓ 获取项目详情成功: {data.get('project_name')}")

    def test_update_project(self, admin_token):
        """测试更新项目"""
        self.helper.print_info("测试: 更新项目")

        # 先获取一个项目
        list_response = self.helper.get(
            "/projects/", username="admin", password="admin123", params={"page_size": 1}
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有项目数据，跳过测试")

        project_id = items[0].get("id")

        # 更新项目
        update_data = {
            "project_name": f"更新后的项目-{datetime.now().strftime('%H%M%S')}",
            "description": "更新后的项目描述",
            "priority": "HIGH",
        }

        response = self.helper.put(
            f"/projects/{project_id}",
            update_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request("PUT", f"/projects/{project_id}", update_data)
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "更新项目成功")

        data = response["data"]
        assert data["project_name"] == update_data["project_name"]

        self.helper.print_success(f"✓ 项目更新成功: {data.get('project_name')}")

    def test_delete_project(self, admin_token, test_project):
        """测试删除项目（软删除）"""
        self.helper.print_info("测试: 删除项目（软删除）")

        project_id = test_project.id

        # 删除项目
        response = self.helper.delete(
            f"/projects/{project_id}", username="admin", password="admin123"
        )

        self.helper.print_request("DELETE", f"/projects/{project_id}")
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "删除项目成功")

        # 验证项目已被标记为不活跃
        get_response = self.helper.get(
            f"/projects/{project_id}", username="admin", password="admin123"
        )

        # 软删除后，可能返回404或返回is_active=False的数据
        if get_response["status_code"] == 200:
            assert get_response["data"].get("is_active") == False

        self.helper.print_success("✓ 项目删除成功（软删除）")


@pytest.mark.integration
class TestProjectStagesAndStatus:
    """项目阶段和状态测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_update_project_stage(self, admin_token):
        """测试更新项目阶段"""
        self.helper.print_info("测试: 更新项目阶段")

        # 获取一个项目
        list_response = self.helper.get(
            "/projects/", username="admin", password="admin123", params={"page_size": 1}
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有项目数据，跳过测试")

        project_id = items[0].get("id")
        current_stage = items[0].get("stage", "S1")

        # 更新阶段到S2
        update_data = {"stage": "S2"}

        response = self.helper.put(
            f"/projects/{project_id}",
            update_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request("PUT", f"/projects/{project_id}", update_data)
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "更新项目阶段成功")

        data = response["data"]
        assert data["stage"] == "S2"

        self.helper.print_success(f"✓ 项目阶段从 {current_stage} 更新到 S2")

    def test_get_stage_transitions(self, admin_token):
        """测试获取阶段转换"""
        self.helper.print_info("测试: 获取阶段转换配置")

        response = self.helper.get(
            "/stage-transitions/", username="admin", password="admin123"
        )

        self.helper.print_request("GET", "/stage-transitions/")
        self.helper.print_response(response, show_data=False)

        # 断言
        APITestHelper.assert_success(response, "获取阶段转换成功")

        self.helper.print_success("✓ 获取阶段转换配置成功")


@pytest.mark.integration
class TestProjectMembers:
    """项目成员管理测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_get_project_members(self, admin_token):
        """测试获取项目成员列表"""
        self.helper.print_info("测试: 获取项目成员列表")

        # 获取一个项目
        list_response = self.helper.get(
            "/projects/", username="admin", password="admin123", params={"page_size": 1}
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有项目数据，跳过测试")

        project_id = items[0].get("id")

        # 获取项目成员
        response = self.helper.get(
            f"/projects/{project_id}/members", username="admin", password="admin123"
        )

        self.helper.print_request("GET", f"/projects/{project_id}/members")
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "获取项目成员列表成功")

        self.helper.print_success("✓ 获取项目成员列表成功")

    def test_add_project_member(self, admin_token, test_project, normal_user):
        """测试添加项目成员"""
        self.helper.print_info("测试: 添加项目成员")

        project_id = test_project.id
        user_id = normal_user.id

        member_data = {
            "user_id": user_id,
            "role_code": "ENGINEER",
            "allocation_pct": 100,
            "is_lead": False,
        }

        response = self.helper.post(
            f"/projects/{project_id}/members",
            member_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request(
            "POST", f"/projects/{project_id}/members", member_data
        )
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "添加项目成员成功")

        data = response["data"]
        assert data["user_id"] == user_id
        assert data["role_code"] == "ENGINEER"

        self.helper.track_resource("project_member", data.get("id"))

        self.helper.print_success("✓ 添加项目成员成功")

    def test_update_project_member_role(self, admin_token):
        """测试更新项目成员角色"""
        self.helper.print_info("测试: 更新项目成员角色")

        # 获取项目和成员
        list_response = self.helper.get(
            "/projects/", username="admin", password="admin123", params={"page_size": 1}
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有项目数据，跳过测试")

        project_id = items[0].get("id")

        members_response = self.helper.get(
            f"/projects/{project_id}/members", username="admin", password="admin123"
        )

        members = members_response["data"].get("items", [])
        if not members:
            pytest.skip("没有成员数据，跳过测试")

        member_id = members[0].get("id")

        # 更新成员角色
        update_data = {"role_code": "PM", "allocation_pct": 80}

        response = self.helper.put(
            f"/projects/{project_id}/members/{member_id}",
            update_data,
            username="admin",
            password="admin123",
        )

        self.helper.print_request(
            "PUT", f"/projects/{project_id}/members/{member_id}", update_data
        )
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "更新成员角色成功")

        self.helper.print_success("✓ 更新项目成员角色成功")

    def test_remove_project_member(self, admin_token):
        """测试移除项目成员"""
        self.helper.print_info("测试: 移除项目成员")

        # 获取项目和成员
        list_response = self.helper.get(
            "/projects/", username="admin", password="admin123", params={"page_size": 1}
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有项目数据，跳过测试")

        project_id = items[0].get("id")

        members_response = self.helper.get(
            f"/projects/{project_id}/members", username="admin", password="admin123"
        )

        members = members_response["data"].get("items", [])
        if len(members) <= 1:  # 至少保留PM
            pytest.skip("项目成员数量不足，跳过测试")

        member_id = members[1].get("id")  # 移除非PM成员

        # 移除成员
        response = self.helper.delete(
            f"/projects/{project_id}/members/{member_id}",
            username="admin",
            password="admin123",
        )

        self.helper.print_request(
            "DELETE", f"/projects/{project_id}/members/{member_id}"
        )
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "移除成员成功")

        self.helper.print_success("✓ 移除项目成员成功")


@pytest.mark.integration
class TestProjectHealthAndMetrics:
    """项目健康度和指标测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_get_project_health(self, admin_token):
        """测试获取项目健康度"""
        self.helper.print_info("测试: 获取项目健康度")

        # 获取一个项目
        list_response = self.helper.get(
            "/projects/", username="admin", password="admin123", params={"page_size": 1}
        )

        items = list_response["data"].get("items", [])
        if not items:
            pytest.skip("没有项目数据，跳过测试")

        project_id = items[0].get("id")

        # 获取项目健康度
        response = self.helper.get(
            f"/projects/{project_id}/health", username="admin", password="admin123"
        )

        self.helper.print_request("GET", f"/projects/{project_id}/health")
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "获取项目健康度成功")

        self.helper.print_success("✓ 获取项目健康度成功")

    def test_get_project_statistics(self, admin_token):
        """测试获取项目统计"""
        self.helper.print_info("测试: 获取项目统计")

        response = self.helper.get(
            "/projects/statistics", username="admin", password="admin123"
        )

        self.helper.print_request("GET", "/projects/statistics")
        self.helper.print_response(response, show_data=False)

        # 断言
        APITestHelper.assert_success(response, "获取项目统计成功")

        self.helper.print_success("✓ 获取项目统计成功")


if __name__ == "__main__":
    print("=" * 60)
    print("项目管理API集成测试（AI辅助生成）")
    print("=" * 60)
    print("\n测试内容：")
    print("  1. 项目CRUD操作")
    print("  2. 项目阶段和状态管理")
    print("  3. 项目成员管理")
    print("  4. 项目健康度和指标")
    print("\n运行测试：")
    print("  pytest tests/integration/test_projects_api_ai.py -v")
    print("=" * 60)
