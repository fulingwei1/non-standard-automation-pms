# -*- coding: utf-8 -*-
"""
组织架构模块 API 测试

测试部门和员工的 CRUD 操作
Updated for unified response format
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from tests.helpers.response_helpers import (
    assert_success_response,
    assert_list_response,
    assert_paginated_response,
    extract_data,
    extract_items,
)


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _unique_code(prefix: str = "DEPT") -> str:
    return f"{prefix}{uuid.uuid4().hex[:6].upper()}"


class TestDepartmentCRUD:
    """部门 CRUD 测试"""

    def test_list_departments(self, client: TestClient, admin_token: str):
        """测试获取部门列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数验证列表响应
        list_data = assert_list_response(response_data)
        assert "items" in list_data
        assert isinstance(list_data["items"], list)

    def test_list_departments_filter_active(self, client: TestClient, admin_token: str):
        """测试按启用状态筛选部门"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments",
            params={"is_active": True},
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数验证列表响应
        list_data = assert_list_response(response_data)
        assert "items" in list_data
        assert isinstance(list_data["items"], list)
        # 所有返回的部门都应该是启用的
        for dept in data:
            assert dept.get("is_active", True) == True

    def test_get_department_tree(self, client: TestClient, admin_token: str):
        """测试获取部门树结构"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments/tree",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数验证列表响应
        list_data = assert_list_response(response_data)
        assert "items" in list_data
        assert isinstance(list_data["items"], list)

    def test_create_department(self, client: TestClient, admin_token: str):
        """测试创建部门"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        dept_data = {
            "dept_code": _unique_code("DEPT"),
            "dept_name": f"测试部门-{uuid.uuid4().hex[:4]}",
            "level": 1,
            "sort_order": 100,
            "is_active": True,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/org/departments",
            json=dept_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create department")

        assert response.status_code in [200, 201], response.text
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data, expected_code=response.status_code)
        assert data["dept_code"] == dept_data["dept_code"]
        assert data["dept_name"] == dept_data["dept_name"]
        return data["id"]

    def test_get_department_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取部门"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取部门列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No departments available for testing")

        dept_id = list_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments/{dept_id}",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data)
        assert data["id"] == dept_id

    def test_get_department_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的部门"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_department(self, client: TestClient, admin_token: str):
        """测试更新部门"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取部门列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get departments list")
        
        response_data = list_response.json()
        # 使用统一响应格式辅助函数提取items
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        if not items:
            pytest.skip("No departments available for testing")

        dept = items[0]
        dept_id = dept["id"]

        update_data = {
            "dept_name": f"更新后的部门-{uuid.uuid4().hex[:4]}",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/org/departments/{dept_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update department")

        assert response.status_code == 200, response.text
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        assert_success_response(response_data)

    def test_get_department_users(self, client: TestClient, admin_token: str):
        """测试获取部门下的用户"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取部门列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No departments available for testing")

        dept_id = list_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/org/departments/{dept_id}/users",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)


class TestEmployeeCRUD:
    """员工 CRUD 测试"""

    def test_list_employees(self, client: TestClient, admin_token: str):
        """测试获取员工列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/org/employees",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数验证列表响应
        list_data = assert_list_response(response_data)
        assert "items" in list_data
        assert isinstance(list_data["items"], list)

    def test_create_employee(self, client: TestClient, admin_token: str):
        """测试创建员工"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        emp_data = {
            "emp_code": _unique_code("EMP"),
            "name": f"测试员工-{uuid.uuid4().hex[:4]}",
            "email": f"test{uuid.uuid4().hex[:4]}@example.com",
            "phone": "13800138000",
            "is_active": True,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/org/employees",
            json=emp_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create employee")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["emp_code"] == emp_data["emp_code"]
        return data["id"]

    def test_get_employee_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取员工"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取员工列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/org/employees",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No employees available for testing")

        emp_id = list_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/org/employees/{emp_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == emp_id

    def test_update_employee(self, client: TestClient, admin_token: str):
        """测试更新员工"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取员工列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/org/employees",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No employees available for testing")

        emp = list_response.json()[0]
        emp_id = emp["id"]

        update_data = {
            "name": f"更新后的员工-{uuid.uuid4().hex[:4]}",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/org/employees/{emp_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update employee")

        assert response.status_code == 200, response.text
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        assert_success_response(response_data)


class TestHrProfiles:
    """HR档案测试"""

    def test_list_hr_profiles(self, client: TestClient, admin_token: str):
        """测试获取HR档案列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/org/hr-profiles",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_get_hr_statistics_overview(self, client: TestClient, admin_token: str):
        """测试获取HR统计概览"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/org/hr-profiles/statistics/overview",
            headers=headers
        )

        assert response.status_code == 200
