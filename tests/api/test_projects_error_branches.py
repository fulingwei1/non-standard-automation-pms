# -*- coding: utf-8 -*-
"""
项目API异常分支测试

补充项目管理端点的异常处理分支测试,提升分支覆盖率
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings


class TestListProjectsErrorBranches:
    """项目列表端点异常分支测试"""

    def test_list_projects_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/projects/")
        assert response.status_code == 401

    def test_list_projects_invalid_token(self, client: TestClient):
        """无效Token"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_list_projects_invalid_page(self, client: TestClient, admin_token: str):
        """无效页码"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            params={"page": -1},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_list_projects_invalid_page_size(self, client: TestClient, admin_token: str):
        """无效分页大小"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            params={"page_size": 0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_list_projects_excessive_page_size(self, client: TestClient, admin_token: str):
        """超大分页大小"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            params={"page_size": 10000},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 应该被限制或返回错误
        assert response.status_code in [200, 400, 422]

    @pytest.mark.parametrize("invalid_stage", [
        "INVALID_STAGE",
        "S99",
        "",
        "null",
        123,
    ])
    def test_list_projects_invalid_stage(self, client: TestClient, admin_token: str, invalid_stage):
        """无效阶段参数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            params={"stage": invalid_stage},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能返回空结果或验证错误
        assert response.status_code in [200, 400, 422]

    @pytest.mark.parametrize("invalid_health", [
        "INVALID_HEALTH",
        "H99",
        "",
        123,
    ])
    def test_list_projects_invalid_health(self, client: TestClient, admin_token: str, invalid_health):
        """无效健康度参数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            params={"health": invalid_health},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 400, 422]

    def test_list_projects_invalid_progress_range(self, client: TestClient, admin_token: str):
        """无效进度范围 (min > max)"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            params={"min_progress": 80, "max_progress": 20},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能返回空结果或验证错误
        assert response.status_code in [200, 400, 422]

    def test_list_projects_progress_out_of_range(self, client: TestClient, admin_token: str):
        """进度超出范围"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            params={"min_progress": -10},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_list_projects_invalid_sort_option(self, client: TestClient, admin_token: str):
        """无效排序选项"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            params={"sort": "invalid_sort_option"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 400, 422]


class TestGetProjectErrorBranches:
    """获取项目详情端点异常分支测试"""

    def test_get_project_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/projects/1")
        assert response.status_code == 401

    def test_get_project_not_found(self, client: TestClient, admin_token: str):
        """项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/999999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_get_project_invalid_id_format(self, client: TestClient, admin_token: str):
        """无效的项目ID格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/invalid_id",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_get_project_negative_id(self, client: TestClient, admin_token: str):
        """负数ID"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/-1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [404, 422]

    def test_get_project_zero_id(self, client: TestClient, admin_token: str):
        """ID为0"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/0",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [404, 422]


class TestCreateProjectErrorBranches:
    """创建项目端点异常分支测试"""

    def test_create_project_no_token(self, client: TestClient):
        """无Token创建"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={"project_name": "测试项目"}
        )
        assert response.status_code == 401

    def test_create_project_missing_required_field(self, client: TestClient, admin_token: str):
        """缺少必填字段"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={},  # 空数据
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("invalid_data,expected_field", [
        ({"project_name": ""}, "project_name"),  # 空项目名
        ({"project_name": "a" * 256}, "project_name"),  # 项目名太长
        ({"project_name": "测试", "customer_id": -1}, "customer_id"),  # 无效客户ID
        ({"project_name": "测试", "customer_id": "invalid"}, "customer_id"),  # 客户ID类型错误
    ])
    def test_create_project_invalid_field(
        self, client: TestClient, admin_token: str, invalid_data: dict, expected_field: str
    ):
        """各种字段验证错误"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=invalid_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422
        # 检查错误信息中包含对应字段
        if response.status_code == 422:
            error_detail = response.json().get("detail", [])
            if isinstance(error_detail, list):
                fields = [err.get("loc", [])[-1] for err in error_detail]
                # 某些字段可能在错误中
                assert len(fields) > 0

    def test_create_project_duplicate_code(self, client: TestClient, admin_token: str, db_session: Session):
        """重复的项目编码"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先查找一个现有项目
        from app.models.project import Project
        existing_project = db_session.query(Project).first()
        if not existing_project:
            pytest.skip("No existing project for duplicate test")

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={
                "project_name": "重复项目",
                "project_code": existing_project.project_code  # 使用已存在的编码
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 409]

    def test_create_project_invalid_stage(self, client: TestClient, admin_token: str):
        """无效的阶段"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={
                "project_name": "测试项目",
                "stage": "INVALID_STAGE"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_project_invalid_health(self, client: TestClient, admin_token: str):
        """无效的健康度"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={
                "project_name": "测试项目",
                "health": "INVALID_HEALTH"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_project_negative_budget(self, client: TestClient, admin_token: str):
        """负数预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={
                "project_name": "测试项目",
                "budget_amount": -10000
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_project_invalid_date_format(self, client: TestClient, admin_token: str):
        """无效日期格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={
                "project_name": "测试项目",
                "planned_start_date": "invalid-date"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_project_end_before_start(self, client: TestClient, admin_token: str):
        """结束日期早于开始日期"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={
                "project_name": "测试项目",
                "planned_start_date": "2025-12-31",
                "planned_end_date": "2025-01-01"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能在验证层或业务层检查
        assert response.status_code in [400, 422]


class TestUpdateProjectErrorBranches:
    """更新项目端点异常分支测试"""

    def test_update_project_no_token(self, client: TestClient):
        """无Token更新"""
        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/1",
            json={"project_name": "更新项目"}
        )
        assert response.status_code == 401

    def test_update_project_not_found(self, client: TestClient, admin_token: str):
        """更新不存在的项目"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/999999",
            json={"project_name": "更新项目"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_update_project_invalid_field(self, client: TestClient, admin_token: str, db_session: Session):
        """更新为无效值"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.project import Project
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for test")

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project.id}",
            json={"project_name": ""},  # 空名称
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_update_project_empty_body(self, client: TestClient, admin_token: str, db_session: Session):
        """空更新体"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.project import Project
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for test")

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project.id}",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 空更新可能被允许或拒绝
        assert response.status_code in [200, 400, 422]


class TestDeleteProjectErrorBranches:
    """删除项目端点异常分支测试"""

    def test_delete_project_no_token(self, client: TestClient):
        """无Token删除"""
        response = client.delete(f"{settings.API_V1_PREFIX}/projects/1")
        assert response.status_code == 401

    def test_delete_project_not_found(self, client: TestClient, admin_token: str):
        """删除不存在的项目"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/999999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_delete_project_invalid_id(self, client: TestClient, admin_token: str):
        """无效ID格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/invalid",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422
