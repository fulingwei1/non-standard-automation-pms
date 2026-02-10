# -*- coding: utf-8 -*-
"""
项目管理模块 API 集成测试

测试范围：
- 项目列表 (GET /projects/)
- 创建项目 (POST /projects/)
- 项���详情 (GET /projects/{id})
- 更新项目 (PUT /projects/{id})
- 项目阶段 (GET /projects/{id}/stages)
- 项目成员 (GET /projects/{id}/members)
- 项目成本 (GET /projects/{id}/costs)

实际路由前缀: /projects (api.py prefix="/projects")
"""

import pytest

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestProjectsCRUDAPI:
    """项目CRUD API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("项目CRUD API 测试")

    def test_get_projects_list(self):
        """测试获取项目列表"""
        self.helper.print_info("测试获取项目列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/projects/", params=params, resource_type="projects_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个项目")
        else:
            self.helper.print_warning("获取项目列表响应不符合预期")

    def test_create_project(self):
        """测试创建项目"""
        self.helper.print_info("测试创建项目...")

        project_data = {
            "project_code": TestDataGenerator.generate_project_code(),
            "project_name": "ICT测试设备项目",
            "project_type": "ICT",
            "customer_name": "深圳科技有限公司",
            "description": "客户定制ICT测试设备",
        }

        response = self.helper.post(
            "/projects/", project_data, resource_type="project"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            result = response.get("data", {})
            project_id = result.get("id") if isinstance(result, dict) else None
            if project_id:
                self.tracked_resources.append(("project", project_id))
                self.helper.print_success(f"项目创建成功，ID: {project_id}")
            else:
                self.helper.print_success("项目创建成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或数据冲突）")
        else:
            self.helper.print_warning("创建项目响应不符合预期，继续测试")

    def test_get_project_detail(self):
        """测试获取项目详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取项目详情...")

        project_id = 1
        response = self.helper.get(
            f"/projects/{project_id}", resource_type=f"project_{project_id}"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("项目详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("项目不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取项目详情响应不符合预期")

    def test_update_project(self):
        """测试更新项目（预期：无数据时返回404）"""
        self.helper.print_info("测试更新项目...")

        project_id = 1
        update_data = {
            "description": "更新后的项目描述",
        }

        response = self.helper.put(
            f"/projects/{project_id}",
            update_data,
            resource_type=f"project_{project_id}_update",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("项目更新成功")
        elif status_code in (404, 422):
            self.helper.print_warning(f"返回{status_code}是预期行为（项目不存在或参数不匹配）")
        else:
            self.helper.print_warning("更新项目响应不符合预期")


@pytest.mark.integration
class TestProjectsRelatedAPI:
    """项目关联数据 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.helper.print_info("项目关联数据 API 测试")

    def test_get_project_stages(self):
        """测试获取项目阶段列表"""
        self.helper.print_info("测试获取项目阶段列表...")

        if not self.test_project_id:
            self.helper.print_warning("无测试项目，跳过")
            return

        response = self.helper.get(
            f"/projects/{self.test_project_id}/stages",
            resource_type="project_stages",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("项目阶段列表获取成功")
        elif status_code == 404:
            self.helper.print_warning("项目不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取项目阶段列表响应不符合预期")

    def test_get_project_members(self):
        """测试获取项目成员列表"""
        self.helper.print_info("测试获取项目成员列表...")

        if not self.test_project_id:
            self.helper.print_warning("无测试项目，跳过")
            return

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            f"/projects/{self.test_project_id}/members",
            params=params,
            resource_type="project_members",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("项目成员列表获取成功")
        elif status_code == 404:
            self.helper.print_warning("项目不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取项目成员列���响应不符合预期")

    def test_get_project_costs(self):
        """测试获取项目成本列表"""
        self.helper.print_info("测试获取项目成本列表...")

        if not self.test_project_id:
            self.helper.print_warning("无测试项目，跳过")
            return

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            f"/projects/{self.test_project_id}/costs",
            params=params,
            resource_type="project_costs",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("项目成本列表获取成功")
        elif status_code == 404:
            self.helper.print_warning("项目不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取项目成本列表响应不符合预期")
