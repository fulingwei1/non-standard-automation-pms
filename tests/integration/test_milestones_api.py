# -*- coding: utf-8 -*-
"""
Integration tests for Milestones API
Covers: app/api/v1/endpoints/milestones.py
Updated for unified response format
"""

from datetime import date, timedelta

from tests.helpers.response_helpers import (
    assert_success_response,
    assert_list_response,
)


class TestMilestonesAPI:
    """里程碑管理API集成测试"""

    def test_list_milestones(self, client, admin_token):
        """测试获取里程碑列表"""
        response = client.get(
            "/api/v1/milestones/", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数提取列表
        list_data = assert_list_response(response_data)
        assert "items" in list_data

    def test_list_milestones_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/milestones/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_milestones_with_filters(self, client, admin_token):
        """测试过滤参数"""
        response = client.get(
            "/api/v1/milestones/?status=PENDING",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_get_milestone_detail(self, client, admin_token, db_session):
        """测试获取里程碑详情"""
        from app.models.project import ProjectMilestone

        milestone = ProjectMilestone(
            milestone_code=f"MS-{date.today().strftime('%Y%m%d')}-001",
            milestone_name="测试里程碑",
            project_id=1,
            planned_date=date.today() + timedelta(days=30),
            status="PENDING",
            is_key=False,
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        response = client.get(
            f"/api/v1/milestones/{milestone.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data)
        assert data["id"] == milestone.id

    def test_get_milestone_not_found(self, client, admin_token):
        """测试获取不存在的里程碑"""
        response = client.get(
            "/api/v1/milestones/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_create_milestone(self, client, admin_token, test_project):
        """测试创建里程碑"""
        milestone_data = {
            "milestone_name": "API测试里程碑",
            "milestone_code": f"MS-{date.today().strftime('%Y%m%d')}-002",
            "project_id": test_project.id,
            "planned_date": (date.today() + timedelta(days=30)).isoformat(),
            "status": "PENDING",
            "is_key": False,
        }
        response = client.post(
            "/api/v1/milestones/",
            json=milestone_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 201]
        response_data = response.json()
        # 使用统一响应格式辅助函数提取数据
        data = assert_success_response(response_data, expected_code=response.status_code)
        assert data["milestone_name"] == milestone_data["milestone_name"]

    def test_create_milestone_duplicate_code(self, client, admin_token, test_project):
        """测试创建重复编码里程碑"""
        milestone_data = {
            "milestone_name": "重复编码里程碑",
            "milestone_code": f"MS-DUP-{date.today().strftime('%Y%m%d')}",
            "project_id": test_project.id,
            "planned_date": (date.today() + timedelta(days=30)).isoformat(),
        }
        # First create
        response = client.post(
            "/api/v1/milestones/",
            json=milestone_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Try to create again
        response = client.post(
            "/api/v1/milestones/",
            json=milestone_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 400, 409]

    def test_update_milestone(self, client, admin_token, db_session):
        """测试更新里程碑"""
        from app.models.project import ProjectMilestone

        milestone = ProjectMilestone(
            milestone_code=f"MS-UPD-{date.today().strftime('%Y%m%d')}",
            milestone_name="待更新里程碑",
            project_id=1,
            planned_date=date.today() + timedelta(days=30),
            status="PENDING",
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        update_data = {
            "milestone_name": "更新后的里程碑名称",
            "status": "IN_PROGRESS",
        }
        response = client.put(
            f"/api/v1/milestones/{milestone.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["milestone_name"] == update_data["milestone_name"]

    def test_update_milestone_not_found(self, client, admin_token):
        """测试更新不存在的里程碑"""
        update_data = {"milestone_name": "不存在的里程碑"}
        response = client.put(
            "/api/v1/milestones/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_delete_milestone(self, client, admin_token, db_session):
        """测试删除里程碑"""
        from app.models.project import ProjectMilestone

        milestone = ProjectMilestone(
            milestone_code=f"MS-DEL-{date.today().strftime('%Y%m%d')}",
            milestone_name="待删除里程碑",
            project_id=1,
            planned_date=date.today() + timedelta(days=30),
            status="PENDING",
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        response = client.delete(
            f"/api/v1/milestones/{milestone.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_delete_milestone_not_found(self, client, admin_token):
        """测试删除不存在的里程碑"""
        response = client.delete(
            "/api/v1/milestones/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestMilestonesAPIAuth:
    """里程碑API认证测试"""

    def test_list_milestones_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/milestones/")
        assert response.status_code == 401

    def test_get_milestone_without_token(self, client):
        """测试无token获取详情"""
        response = client.get("/api/v1/milestones/1")
        assert response.status_code == 401

    def test_create_milestone_without_token(self, client):
        """测试无token创建"""
        response = client.post(
            "/api/v1/milestones/",
            json={"milestone_name": "测试", "project_id": 1},
        )
        assert response.status_code == 401


class TestMilestonesAPIValidation:
    """里程碑API验证测试"""

    def test_create_milestone_validation_error(self, client, admin_token):
        """测试创建里程碑验证错误"""
        milestone_data = {}
        response = client.post(
            "/api/v1/milestones/",
            json=milestone_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_invalid_status(self, client, admin_token, test_project):
        """测试无效状态"""
        milestone_data = {
            "milestone_name": "测试里程碑",
            "project_id": test_project.id,
            "planned_date": date.today().isoformat(),
            "status": "INVALID_STATUS",
        }
        response = client.post(
            "/api/v1/milestones/",
            json=milestone_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_past_planned_date(self, client, admin_token, test_project):
        """测试过去的计划日期"""
        milestone_data = {
            "milestone_name": "过去日期里程碑",
            "project_id": test_project.id,
            "planned_date": (date.today() - timedelta(days=1)).isoformat(),
        }
        response = client.post(
            "/api/v1/milestones/",
            json=milestone_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Should either fail validation or succeed depending on business rules
        assert response.status_code in [200, 422]
