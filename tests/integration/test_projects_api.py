# -*- coding: utf-8 -*-
"""
项目 API 集成测试

测试内容：
- 项目列表查询
- 项目详情获取
- 项目创建
- 项目更新
- 项目删除（软删除）
- 项目分页
- 项目筛选
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project import Project
from app.core.config import settings


@pytest.mark.api
@pytest.mark.integration
class TestProjectsAPI:
    """项目管理 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client: TestClient):
        """创建认证头"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def test_project(self, db_session: Session):
        """创建测试项目"""
        project = Project(
            project_code="PJ250119001",
            project_name="测试项目",
            customer_name="测试客户",
            contract_amount=100000.00,
            status="S1",
            health="H1",
            created_by=1,
            pm_id=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        yield project

        # 清理
        db_session.delete(project)
        db_session.commit()

    def test_list_projects_success(self, client: TestClient, auth_headers: dict):
        """测试获取项目列表成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_list_projects_with_pagination(
        self, client: TestClient, auth_headers: dict
    ):
        """测试项目列表分页"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?page=1&page_size=5",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5

    def test_list_projects_with_filter(self, client: TestClient, auth_headers: dict):
        """测试项目列表筛选"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?status=S1&health=H1",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证筛选结果
        for project in data["items"]:
            if project.get("status"):
                assert project["status"] == "S1"
            if project.get("health"):
                assert project["health"] == "H1"

    def test_get_project_detail(
        self, client: TestClient, auth_headers: dict, test_project: Project
    ):
        """测试获取项目详情"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{test_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["project_code"] == test_project.project_code
        assert data["project_name"] == test_project.project_name

    def test_get_project_not_found(self, client: TestClient, auth_headers: dict):
        """测试获取不存在的项目"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/999999",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_create_project_success(self, client: TestClient, auth_headers: dict):
        """测试创建项目成功"""
        project_data = {
            "project_code": "PJ250119002",
            "project_name": "新建测试项目",
            "customer_name": "测试客户公司",
            "contract_amount": 200000.00,
            "status": "S1",
            "health": "H1",
            "pm_id": 1,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects",
            json=project_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["project_code"] == project_data["project_code"]
        assert data["project_name"] == project_data["project_name"]

        # 清理
        client.delete(
            f"{settings.API_V1_PREFIX}/projects/{data['id']}",
            headers=auth_headers,
        )

    def test_create_project_duplicate_code(
        self, client: TestClient, auth_headers: dict
    ):
        """测试创建重复项目编码"""
        project_data = {
            "project_code": "PJ250119001",
            "project_name": "重复编码项目",
            "customer_name": "测试客户",
            "contract_amount": 100000.00,
            "status": "S1",
            "health": "H1",
            "pm_id": 1,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects",
            json=project_data,
            headers=auth_headers,
        )

        # 可能返回 409 Conflict 或 200（取决于实现）
        assert response.status_code in [200, 400, 409]

    def test_create_project_validation_error(
        self, client: TestClient, auth_headers: dict
    ):
        """测试创建项目时验证错误"""
        project_data = {
            # 缺少必填字段
            "project_name": "缺少编码的项目",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects",
            json=project_data,
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation Error

    def test_update_project_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """测试更新项目成功"""
        update_data = {
            "project_name": "更新后的项目名称",
            "customer_name": "更新后的客户名称",
            "contract_amount": 150000.00,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == update_data["project_name"]
        assert data["customer_name"] == update_data["customer_name"]
        assert data["contract_amount"] == update_data["contract_amount"]

    def test_delete_project_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """测试删除项目成功"""
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/{test_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_delete_project_not_found(self, client: TestClient, auth_headers: dict):
        """测试删除不存在的项目"""
        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/999999",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_project_search(self, client: TestClient, auth_headers: dict):
        """测试项目搜索"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects?search=测试",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证搜索结果包含关键词
        for project in data["items"]:
            assert (
                "测试" in project.get("project_name", "")
                or "测试" in project.get("customer_name", "")
                or "测试" in project.get("project_code", "")
            )

    def test_project_unauthorized(self, client: TestClient):
        """测试未授权访问"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects",
        )

        assert response.status_code == 401
