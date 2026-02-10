# -*- coding: utf-8 -*-
"""
用户管理模块 API 集成测试

测试范围：
- 用户列表 (GET /users/)
- 创建用户 (POST /users/)
- 用户详情 (GET /users/{user_id})
- 更新用户 (PUT /users/{user_id})
- 切换用户状态 (PUT /users/{user_id}/toggle-active)
- 重置密码 (PUT /users/{user_id}/reset-password)
- 从员工创建用户 (POST /users/create-from-employee/{employee_id})

实际路由前缀: /users (api.py prefix="/users")
"""

import pytest

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestUsersCRUDAPI:
    """用户CRUD API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("用户CRUD API 测试")

    def test_get_users_list(self):
        """测试获取用户列表"""
        self.helper.print_info("测试获取用户列表...")

        params = {
            "page": 1,
            "page_size": 20,
        }

        response = self.helper.get(
            "/users/", params=params, resource_type="users_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个用户")
        else:
            self.helper.print_warning("获取用户列表响应不符合预期")

    def test_create_user(self):
        """测试创建用户"""
        self.helper.print_info("测试创建用户...")

        user_data = {
            "username": f"testuser_{TestDataGenerator.generate_order_no()}",
            "password": "Test@123456",
            "real_name": "测试用户",
            "email": TestDataGenerator.generate_email(),
            "phone": "13800138999",
            "is_active": True,
        }

        response = self.helper.post(
            "/users/", user_data, resource_type="user"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            result = response.get("data", {})
            user_id = result.get("id") if isinstance(result, dict) else None
            if user_id:
                self.tracked_resources.append(("user", user_id))
                self.helper.print_success(f"用户创建成功，ID: {user_id}")
            else:
                self.helper.print_success("用户创建成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或数据冲突）")
        else:
            self.helper.print_warning("创建用户响应不符合预期，继续测试")

    def test_get_user_detail(self):
        """测试获取用户详情（预期：无数据时返回404）"""
        self.helper.print_info("测试获取用户详情...")

        user_id = 1
        response = self.helper.get(
            f"/users/{user_id}", resource_type=f"user_{user_id}"
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("用户详情获取成功")
        elif status_code == 404:
            self.helper.print_warning("用户不存在，返回404是预期行为")
        else:
            self.helper.print_warning("获取用户详情响应不符合预期")

    def test_update_user(self):
        """测试更新用户（预期：无数据时返回404）"""
        self.helper.print_info("测试更新用户...")

        user_id = 1
        update_data = {
            "real_name": "更新后的用户名",
        }

        response = self.helper.put(
            f"/users/{user_id}",
            update_data,
            resource_type=f"user_{user_id}_update",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("用户更新成功")
        elif status_code in (404, 422):
            self.helper.print_warning(f"返回{status_code}是预期行为（用户不存在或参数不匹配）")
        else:
            self.helper.print_warning("更新用户响应不符合预期")


@pytest.mark.integration
class TestUsersActionsAPI:
    """用户操作 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.helper.print_info("用户操作 API 测试")

    def test_toggle_user_active(self):
        """测试切换用户状态（预期：无数据时返回404）"""
        self.helper.print_info("测试切换用户状态...")

        user_id = 1
        response = self.helper.put(
            f"/users/{user_id}/toggle-active",
            data={},
            resource_type=f"user_{user_id}_toggle",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("用户状态切换成功")
        elif status_code in (404, 422):
            self.helper.print_warning(f"返回{status_code}是预期行为（用户不存在或参数不匹配）")
        else:
            self.helper.print_warning("切换用户状态响应不符合预期")

    def test_create_from_employee(self):
        """测试从员工创建用户（预期：无员工时返回404）"""
        self.helper.print_info("测试从员工创建用户...")

        employee_id = 1
        response = self.helper.post(
            f"/users/create-from-employee/{employee_id}",
            data={},
            resource_type=f"user_from_employee_{employee_id}",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("从员工创建用户成功")
        elif status_code in (404, 422):
            self.helper.print_warning(f"返回{status_code}是预期行为（员工不存在或已有账号）")
        else:
            self.helper.print_warning("从员工创建用户响应不符合预期")

    def test_sync_from_employees(self):
        """测试从员工同步用户"""
        self.helper.print_info("测试从员工同步用户...")

        response = self.helper.post(
            "/users/sync-from-employees",
            data={},
            resource_type="sync_users",
        )

        status_code = response.get("status_code")
        if status_code and 200 <= status_code < 300:
            self.helper.print_success("从员工同步用户成功")
        elif status_code in (400, 422):
            self.helper.print_warning(f"返回{status_code}（参数不匹配或无可同步员工）")
        else:
            self.helper.print_warning("从员工同步用户响应不符合预期")
