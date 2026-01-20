# -*- coding: utf-8 -*-
"""
Integration tests for Organization API
Covers: app/api/v1/endpoints/organization.py
"""



class TestOrganizationAPI:
    """组织架构API集成测试"""

    def test_list_departments(self, client, admin_token):
        """测试获取部门列表"""
        response = client.get(
            "/api/v1/organization/departments/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_departments_with_tree(self, client, admin_token):
        """测试获取部门树形结构"""
        response = client.get(
            "/api/v1/organization/departments/tree",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_get_department_detail(self, client, admin_token):
        """测试获取部门详情"""
        response = client.get(
            "/api/v1/organization/departments/1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # 200 if exists, 404 if not
        assert response.status_code in [200, 404]

    def test_list_employees(self, client, admin_token):
        """测试获取员工列表"""
        response = client.get(
            "/api/v1/organization/employees/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_employees_with_pagination(self, client, admin_token):
        """测试员工分页"""
        response = client.get(
            "/api/v1/organization/employees/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_employees_with_department_filter(self, client, admin_token):
        """测试按部门筛选员工"""
        response = client.get(
            "/api/v1/organization/employees/?department=工程部",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_get_employee_detail(self, client, admin_token):
        """测试获取员工详情"""
        response = client.get(
            "/api/v1/organization/employees/1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # 200 if exists, 404 if not
        assert response.status_code in [200, 404]

    def test_list_positions(self, client, admin_token):
        """测试获取职位列表"""
        response = client.get(
            "/api/v1/organization/positions/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_position_detail(self, client, admin_token):
        """测试获取职位详情"""
        response = client.get(
            "/api/v1/organization/positions/1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 404]


class TestOrganizationAPIAuth:
    """组织架构API认证测试"""

    def test_list_departments_without_token(self, client):
        """测试无token访问部门"""
        response = client.get("/api/v1/organization/departments/")
        assert response.status_code == 401

    def test_list_employees_without_token(self, client):
        """测试无token访问员工"""
        response = client.get("/api/v1/organization/employees/")
        assert response.status_code == 401

    def test_list_positions_without_token(self, client):
        """测试无token访问职位"""
        response = client.get("/api/v1/organization/positions/")
        assert response.status_code == 401


class TestOrganizationAPIValidation:
    """组织架构API验证测试"""

    def test_invalid_page_number(self, client, admin_token):
        """测试无效页码"""
        response = client.get(
            "/api/v1/organization/employees/?page=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_invalid_department_id(self, client, admin_token):
        """测试无效部门ID"""
        response = client.get(
            "/api/v1/organization/departments/-1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_invalid_employee_id(self, client, admin_token):
        """测试无效员工ID"""
        response = client.get(
            "/api/v1/organization/employees/-1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_search_with_special_chars(self, client, admin_token):
        """测试特殊字符搜索"""
        response = client.get(
            "/api/v1/organization/employees/?search=测试'\"<>",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200


class TestOrganizationAPITree:
    """组织架构树形结构测试"""

    def test_department_tree_structure(self, client, admin_token):
        """测试部门树形结构"""
        response = client.get(
            "/api/v1/organization/departments/tree",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Tree should have children or be flat list
        assert isinstance(data, list)

    def test_employees_by_department(self, client, admin_token):
        """测试按部门获取员工"""
        response = client.get(
            "/api/v1/organization/departments/1/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 404]
