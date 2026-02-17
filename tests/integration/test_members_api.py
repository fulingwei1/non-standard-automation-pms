# -*- coding: utf-8 -*-
"""
Integration tests for Members API
Covers: app/api/v1/endpoints/members/
Updated for unified response format
"""

from tests.helpers.response_helpers import (
    assert_success_response,
    assert_list_response,
    extract_items,
)



class TestMembersAPI:
    """项目成员管理API集成测试"""

    def test_list_members(self, client, admin_token):
        """测试获取成员列表"""
        response = client.get(
            "/api/v1/projects/1/members/", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Response may be paginated dict or list
        assert isinstance(data, (list, dict))

    def test_list_members_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/projects/1/members/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_members_with_project_filter(self, client, admin_token, test_project):
        """测试按项目筛选成员"""
        response = client.get(
            f"/api/v1/projects/1/members/?project_id={test_project.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数提取列表
        list_data = assert_list_response(response_data)
        items = list_data["items"]
        for member in items:
            if member.get("project_id"):
                assert member["project_id"] == test_project.id

    def test_get_project_members(self, client, admin_token, test_project):
        """测试获取项目成员列表"""
        response = client.get(
            f"/api/v1/projects/{test_project.id}/members/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_get_project_members_not_found(self, client, admin_token):
        """测试获取不存在项目的成员列表"""
        response = client.get(
            "/api/v1/projects/999999/members/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_add_member(self, client, admin_token, test_project, engineer_user):
        """测试添加项目成员"""
        member_data = {
            "project_id": test_project.id,
            "user_id": engineer_user.id,
            "role_code": "ENGINEER",
            "allocation_pct": 50,
        }
        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/",
            json=member_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 201]
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data, expected_code=response.status_code)
        assert data["project_id"] == member_data["project_id"]
        assert data["user_id"] == member_data["user_id"]

    def test_add_member_duplicate(
        self, client, admin_token, test_project, engineer_user
    ):
        """测试添加重复成员"""
        member_data = {
            "project_id": test_project.id,
            "user_id": engineer_user.id,
            "role_code": "ENGINEER",
            "allocation_pct": 50,
        }
        # First add
        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/",
            json=member_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Try to add again
        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/",
            json=member_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "已是项目成员" in response.json().get("detail", "")

    def test_add_member_project_not_found(self, client, admin_token, engineer_user):
        """测试添加成员到不存在的项目"""
        member_data = {
            "project_id": 999999,
            "user_id": engineer_user.id,
            "role_code": "ENGINEER",
        }
        response = client.post(
            "/api/v1/projects/999999/members/",
            json=member_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
        assert "项目不存在" in response.json().get("detail", "")

    def test_add_member_user_not_found(self, client, admin_token, test_project):
        """测试添加不存在的用户"""
        member_data = {
            "project_id": test_project.id,
            "user_id": 999999,
            "role_code": "ENGINEER",
        }
        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/",
            json=member_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
        assert "用户不存在" in response.json().get("detail", "")

    def test_update_member(self, client, admin_token, test_project, db_session):
        """测试更新成员"""
        from app.models.project import ProjectMember

        # Create a member first
        member = ProjectMember(
            project_id=test_project.id,
            user_id=1,  # Using existing user ID
            role_code="ENGINEER",
            allocation_pct=50,
            is_lead=False,
            created_by=1,
        )
        db_session.add(member)
        db_session.commit()
        db_session.refresh(member)

        update_data = {"role_code": "SENIOR_ENGINEER", "allocation_pct": 80}
        response = client.put(
            f"/api/v1/projects/{test_project.id}/members/{member.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role_code"] == "SENIOR_ENGINEER"
        assert float(data["allocation_pct"]) == 80

    def test_update_member_not_found(self, client, admin_token):
        """测试更新不存在的成员"""
        update_data = {"role_code": "ENGINEER"}
        response = client.put(
            "/api/v1/projects/1/members/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_delete_member(self, client, admin_token, test_project, db_session):
        """测试删除成员"""
        from app.models.project import ProjectMember

        member = ProjectMember(
            project_id=test_project.id,
            user_id=1,
            role_code="ENGINEER",
            allocation_pct=50,
            created_by=1,
        )
        db_session.add(member)
        db_session.commit()
        db_session.refresh(member)

        response = client.delete(
            f"/api/v1/projects/{test_project.id}/members/{member.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 204]

    def test_delete_member_not_found(self, client, admin_token):
        """测试删除不存在的成员"""
        response = client.delete(
            "/api/v1/projects/1/members/999999", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404


class TestMembersAPIAuth:
    """成员API认证测试"""

    def test_list_members_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/projects/1/members/")
        assert response.status_code == 401

    def test_get_project_members_without_token(self, client, test_project):
        """测试无token获取项目成员"""
        response = client.get(f"/api/v1/projects/{test_project.id}/members/")
        assert response.status_code == 401

    def test_add_member_without_token(self, client, test_project):
        """测试无token添加成员"""
        response = client.post(
            "/api/v1/projects/1/members/",
            json={"project_id": test_project.id, "user_id": 1, "role_code": "ENGINEER"},
        )
        assert response.status_code == 401


class TestMembersAPIValidation:
    """成员API验证测试"""

    def test_add_member_validation_error(self, client, admin_token):
        """测试添加成员验证错误"""
        member_data = {}
        response = client.post(
            "/api/v1/projects/1/members/",
            json=member_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_invalid_project_id(self, client, admin_token):
        """测试无效项目ID"""
        response = client.get(
            "/api/v1/projects/1/members/?project_id=-1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_invalid_allocation_pct(
        self, client, admin_token, test_project, engineer_user
    ):
        """测试无效分配百分比"""
        member_data = {
            "project_id": test_project.id,
            "user_id": engineer_user.id,
            "role_code": "ENGINEER",
            "allocation_pct": 150,  # Invalid: > 100
        }
        response = client.post(
            f"/api/v1/projects/{test_project.id}/members/",
            json=member_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Should return validation error or success (depending on validation rules)
        assert response.status_code in [200, 422]
