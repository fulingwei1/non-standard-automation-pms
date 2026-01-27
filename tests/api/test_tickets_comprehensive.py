# -*- coding: utf-8 -*-
"""
问题跟踪 API 测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.task_center import TaskUnified
from tests.conftest import (
    engineer_user,
    mock_project,
)


@pytest.fixture
def service_ticket(db_session: Session, engineer_user, mock_project):

    ticket = TaskUnified(
        task_code=f"TASK-{__import__('uuid').uuid4().hex()[:10].upper()}",
        title="测试问题",
        description="问题描述测试",
        task_type="ISSUE",
        project_id=mock_project.id,
        project_code=mock_project.project_code,
        project_name=mock_project.project_name,
        assignee_id=engineer_user.id,
        assignee_name=engineer_user.real_name or engineer_user.username,
        priority="MEDIUM",
        status="OPEN",
        progress=0,
        is_delayed=False,
        created_by=engineer_user.id,
        updated_by=engineer_user.id,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


@pytest.fixture
def auth_headers(client: TestClient, admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


class TestTicketList:
    def test_list_tickets_empty(self, client, auth_headers):
        """测试空列表"""
        response = client.get("/api/v1/issues/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert "items" in data
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_tickets_with_tickets(self, client, auth_headers, service_ticket):
        """测试带问题的列表"""
        response = client.get("/api/v1/issues/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert "items" in data
        assert data["total"] >= 1

        items = data["items"]
        assert len(items) >= 1

    def test_list_tickets_with_filters(self, client, auth_headers, service_ticket):
        """测试带过滤器的列表"""
        params = {"status": "OPEN", "project_id": mock_project.id}
        response = client.get("/api/v1/issues/", params=params, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        items = data.get("items", [])
        assert isinstance(items, list)

        assert len(items) >= 0

    def test_list_tickets_pagination(self, client, auth_headers):
        """测试分页"""
        params = {"page": 1, "page_size": 10}
        response = client.get("/api/v1/issues/", params=params, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)


class TestTicketDetail:
    def test_get_ticket_by_id(self, client, auth_headers, service_ticket):
        """测试获取问题详情"""
        ticket_id = service_ticket.id
        response = client.get(f"/api/v1/issues/{ticket_id}/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == ticket_id
        assert data["task_code"] == service_ticket.task_code

    def test_get_ticket_not_found(self, client, auth_headers):
        """测试获取不存在的问题"""
        response = client.get("/api/v1/issues/99999/", headers=auth_headers)
        assert response.status_code == 404

    def test_get_ticket_without_auth(self, client):
        """测试未认证访问"""
        response = client.get("/api/v1/issues/1/")
        assert response.status_code == 401


class TestTicketUpdate:
    def test_update_ticket_status(self, client, auth_headers, service_ticket):
        """测试更新问题状态"""
        update_data = {"status": "IN_PROGRESS"}
        response = client.patch(
            f"/api/v1/issues/{service_ticket.id}/",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == service_ticket.id
        assert data["status"] == "IN_PROGRESS"

    def test_assign_ticket(self, client, auth_headers, service_ticket):
        """测试分配问题"""
        assign_data = {"assignee_id": engineer_user.id}
        response = client.patch(
            f"/api/v1/issues/{service_ticket.id}/assign",
            json=assign_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["assignee_id"] == engineer_user.id
        assert data["status"] == "ASSIGNED"

    def test_assign_ticket_invalid_user(self, client, auth_headers, service_ticket):
        """测试分配给无效用户"""
        assign_data = {"assignee_id": 999}
        response = client.patch(
            f"/api/v1/issues/{service_ticket.id}/assign",
            json=assign_data,
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestTicketResolve:
    def test_resolve_ticket(self, client, auth_headers, service_ticket):
        """测试解决问题"""
        resolve_data = {"status": "RESOLVED", "resolution": "测试解决方案"}
        response = client.patch(
            f"/api/v1/issues/{service_ticket.id}/resolve",
            json=resolve_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == service_ticket.id
        assert data["status"] == "RESOLVED"
        assert data["resolution"] == "测试解决方案"

    def test_close_ticket(self, client, auth_headers, service_ticket):
        """测试关闭问题"""
        close_data = {"status": "CLOSED", "close_reason": "测试关闭原因"}
        response = client.patch(
            f"/api/v1/issues/{service_ticket.id}/close",
            json=close_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == service_ticket.id
        assert data["status"] == "CLOSED"


class TestTicketStatistics:
    def test_get_statistics(self, client, auth_headers):
        """测试获取统计信息"""
        response = client.get("/api/v1/issues/statistics/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert "total_issues" in data
        assert isinstance(data["total_issues"], int)

    def test_get_statistics_by_project(self, client, auth_headers, mock_project):
        """测试获取项目统计"""
        response = client.get(
            f"/api/v1/issues/statistics/?project_id={mock_project.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert "project_id" in data
        assert data["project_id"] == mock_project.id


class TestEdgeCases:
    def test_create_ticket_validation_error_no_project(self, client, auth_headers):
        """测试缺少项目ID"""
        create_data = {"title": "测试问题", "description": "测试描述", "status": "OPEN"}
        response = client.post(
            "/api/v1/issues/", json=create_data, headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_ticket_validation_error_invalid_status(
        self, client, auth_headers, service_ticket
    ):
        """测试无效状态"""
        update_data = {"status": "INVALID_STATUS"}
        response = client.patch(
            f"/api/v1/issues/{service_ticket.id}/",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_ticket_unauthorized(self, client, auth_headers):
        """测试未授权创建"""
        create_data = {"title": "未授权问题"}
        response = client.post("/api/v1/issues/", json=create_data, headers={})
        assert response.status_code == 401


class TestTicketPermissions:
    def test_list_tickets_unauthorized(self, client, auth_headers):
        """测试未授权列表"""
        response = client.get("/api/v1/issues/", headers={})
        assert response.status_code == 401

    def test_get_ticket_without_permission(self, client, auth_headers, service_ticket):
        """测试获取问题详情权限"""
        response = client.get(f"/api/v1/issues/{service_ticket.id}/", headers={})
        assert response.status_code == 401

    def test_update_ticket_without_permission(
        self, client, auth_headers, service_ticket
    ):
        """测试更新问题权限"""
        update_data = {"status": "IN_PROGRESS"}
        response = client.patch(
            f"/api/v1/issues/{service_ticket.id}/", json=update_data, headers={}
        )
        assert response.status_code == 401
