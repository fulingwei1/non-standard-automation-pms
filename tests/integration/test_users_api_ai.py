# -*- coding: utf-8 -*-
"""
用户管理 API 集成测试

测试模块：
- User CRUD operations
- User sync (employee sync, account creation, status management)
- Time allocation
"""

import pytest
from datetime import datetime, date

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator, Colors


@pytest.mark.integration
class TestUsersCRUDAPI:
    """测试用户基本CRUD操作"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token):
        """测试初始化"""
        self.helper = APITestHelper(client, admin_token)
        self.generator = TestDataGenerator()
        self.tracked_resources = []

        self.helper.print_info("用户管理 - 基本CRUD操作")

    def test_get_users_list(self):
        """测试获取用户列表"""
        self.helper.print_info("测试获取用户列表...")

        response = self.helper.get(
            "/users/",
            params={
                "page": 1,
                "page_size": 20,
                "is_active": True,
            },
        )

        if self.helper.assert_success(response):
            # 统一响应格式：分页响应直接包含items和total
            result = response.get("data", response)
            items = result.get("items", [])
            total = result.get("total", 0)
            self.helper.print_success(f"获取到 {len(items)} 个用户，总计 {total} 个")
        else:
            self.helper.print_warning("获取用户列表响应不符合预期")

    def test_create_user(self):
        """测试创建用户"""
        self.helper.print_info("测试创建用户...")

        user_data = {
            "username": f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "email": f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
            "full_name": "测试用户",
            "department_id": 1,
            "role_ids": [1],
            "phone": "13800138000",
            "is_active": True,
        }

        response = self.helper.post("/users/", user_data, resource_type="user")

        if self.helper.assert_success(response):
            # 统一响应格式：data字段包含用户对象
            result = response.get("data", {})
            user_id = result.get("id")
            if user_id:
                self.tracked_resources.append(("user", user_id))
                self.helper.print_success(f"用户创建成功，ID: {user_id}")
            else:
                self.helper.print_warning("用户创建成功，但未返回ID")
        else:
            self.helper.print_warning("用户创建响应不符合预期")

    def test_get_user_detail(self):
        """测试获取用户详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的用户ID")

        user_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取用户详情 (ID: {user_id})...")

        response = self.helper.get(f"/users/{user_id}", resource_type=f"user_{user_id}")

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("用户详情获取成功")
        else:
            self.helper.print_warning("获取用户详情响应不符合预期")

    def test_update_user(self):
        """测试更新用户"""
        if not self.tracked_resources:
            pytest.skip("没有可用的用户ID")

        user_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新用户 (ID: {user_id})...")

        update_data = {
            "full_name": "测试用户（已更新）",
            "phone": "13900139000",
            "is_active": True,
        }

        response = self.helper.put(
            f"/users/{user_id}", update_data, resource_type=f"user_{user_id}_update"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("用户更新成功")
        else:
            self.helper.print_warning("更新用户响应不符合预期")

    def test_update_user_roles(self):
        """测试更新用户角色"""
        if not self.tracked_resources:
            pytest.skip("没有可用的用户ID")

        user_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新用户角色 (ID: {user_id})...")

        role_data = {
            "role_ids": [1, 2],
        }

        response = self.helper.put(
            f"/users/{user_id}/roles", role_data, resource_type=f"user_{user_id}_roles"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("用户角色更新成功")
        else:
            self.helper.print_warning("更新用户角色响应不符合预期")

    def test_delete_user(self):
        """测试删除用户"""
        # 为删除测试创建一个单独的用户
        self.helper.print_info("测试删除用户...")

        user_data = {
            "username": f"delete_test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "email": f"delete_test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
            "full_name": "待删除用户",
            "department_id": 1,
            "role_ids": [1],
            "is_active": True,
        }

        response = self.helper.post(
            "/users/", user_data, resource_type="user_to_delete"
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            user_id = result.get("id")
            if user_id:
                delete_response = self.helper.delete(
                    f"/users/{user_id}", resource_type=f"user_{user_id}_delete"
                )

                if self.helper.assert_success(delete_response):
                    self.helper.print_success("用户删除成功")
                else:
                    self.helper.print_warning("删除用户响应不符合预期")
            else:
                self.helper.print_warning("删除测试用户创建失败")
        else:
            self.helper.print_warning("删除测试用户创建失败，跳过删除测试")


@pytest.mark.integration
class TestUsersSyncAPI:
    """测试用户同步"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token):
        """测试初始化"""
        self.helper = APITestHelper(client, admin_token)
        self.generator = TestDataGenerator()
        self.tracked_resources = []

        self.helper.print_info("用户管理 - 用户同步")

    def test_sync_from_employees(self):
        """测试从员工同步用户"""
        self.helper.print_info("测试从员工同步用户...")

        sync_data = {
            "employee_ids": [1, 2, 3],
            "auto_create_accounts": True,
        }

        response = self.helper.post(
            "/users/sync-from-employees", sync_data, resource_type="user_sync"
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            synced_count = result.get("synced_count", 0)
            self.helper.print_success(f"用户同步成功，同步了 {synced_count} 个用户")
        else:
            self.helper.print_warning("用户同步响应不符合预期")

    def test_create_user_from_employee(self):
        """测试从员工创建用户"""
        self.helper.print_info("测试从员工创建用户...")

        response = self.helper.post(
            "/users/create-from-employee/1", resource_type="user_from_employee"
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            user_id = result.get("id")
            if user_id:
                self.tracked_resources.append(("user", user_id))
                self.helper.print_success(f"从员工创建用户成功，ID: {user_id}")
            else:
                self.helper.print_warning("从员工创建用户成功，但未返回ID")
        else:
            self.helper.print_warning("从员工创建用户响应不符合预期")

    def test_toggle_user_active(self):
        """测试切换用户激活状态"""
        if not self.tracked_resources:
            pytest.skip("没有可用的用户ID")

        user_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试切换用户激活状态 (ID: {user_id})...")

        toggle_data = {
            "is_active": False,
            "reason": "测试停用",
        }

        response = self.helper.put(
            f"/users/{user_id}/toggle-active",
            toggle_data,
            resource_type=f"user_{user_id}_toggle",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("用户激活状态切换成功")
        else:
            self.helper.print_warning("切换用户激活状态响应不符合预期")

    def test_reset_user_password(self):
        """测试重置用户密码"""
        if not self.tracked_resources:
            pytest.skip("没有可用的用户ID")

        user_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试重置用户密码 (ID: {user_id})...")

        password_data = {
            "new_password": "Test@123456",
            "confirm_password": "Test@123456",
            "force_reset_on_next_login": True,
        }

        response = self.helper.put(
            f"/users/{user_id}/reset-password",
            password_data,
            resource_type=f"user_{user_id}_password",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("用户密码重置成功")
        else:
            self.helper.print_warning("重置用户密码响应不符合预期")

    def test_batch_toggle_user_active(self):
        """测试批量切换用户激活状态"""
        self.helper.print_info("测试批量切换用户激活状态...")

        batch_data = {
            "user_ids": [1, 2, 3],
            "is_active": False,
            "reason": "批量停用测试",
        }

        response = self.helper.post(
            "/users/batch-toggle-active", batch_data, resource_type="user_batch_toggle"
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            updated_count = result.get("updated_count", 0)
            self.helper.print_success(f"批量切换激活状态成功，更新了 {updated_count} 个用户")
        else:
            self.helper.print_warning("批量切换激活状态响应不符合预期")


@pytest.mark.integration
class TestUsersTimeAllocationAPI:
    """测试用户工时分配"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token):
        """测试初始化"""
        self.helper = APITestHelper(client, admin_token)
        self.generator = TestDataGenerator()
        self.tracked_resources = []

        self.helper.print_info("用户管理 - 工时分配")

    def test_get_user_time_allocation(self):
        """测试获取用户工时分配"""
        self.helper.print_info("测试获取用户工时分配...")

        user_id = 1
        response = self.helper.get(
            f"/users/{user_id}/time-allocation",
            params={
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat(),
            },
            resource_type=f"user_{user_id}_time_allocation",
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            allocations = result.get("allocations", [])
            total_hours = result.get("total_hours", 0)
            self.helper.print_success(
                f"获取到 {len(allocations)} 个工时分配，总计 {total_hours} 小时"
            )
        else:
            self.helper.print_warning("获取用户工时分配响应不符合预期")
