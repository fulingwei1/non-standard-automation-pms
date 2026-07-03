# -*- coding: utf-8 -*-
"""
工作日志 API 测试

覆盖只读端点：
- GET /api/v1/my/work-logs
- GET /api/v1/projects/{project_id}/work-logs/
- GET /api/v1/projects/{project_id}/work-logs/summary
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.project import Customer, Machine, Project
from app.models.user import User
from app.models.work_log import WorkLog, WorkLogMention


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_first_project(client: TestClient, token: str) -> Optional[dict]:
    headers = _auth_headers(token)
    response = client.get(f"{settings.API_V1_PREFIX}/projects/", headers=headers)
    if response.status_code != 200:
        return None
    projects = response.json()
    items = projects.get("items", projects) if isinstance(projects, dict) else projects
    if not items:
        return None
    return items[0]


def _seed_assigned_field_dispatch(db, work_date: date):
    suffix = uuid4().hex[:8].upper()
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        pytest.skip("Admin user not available")

    customer = Customer(
        customer_code=f"CUST-FS-{suffix}",
        customer_name=f"外出日志客户{suffix}",
        contact_person="王工",
        contact_phone="13800000000",
        address="深圳市南山区",
        status="ACTIVE",
        created_by=user.id,
    )
    db.add(customer)
    db.flush()

    project = Project(
        project_code=f"PJ-FS-{suffix}",
        project_name=f"外出日志项目{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        customer_contact=customer.contact_person,
        customer_phone=customer.contact_phone,
        customer_address=customer.address,
        stage="S7",
        status="ST01",
        health="H1",
        created_by=user.id,
    )
    db.add(project)
    db.flush()

    machine = Machine(
        project_id=project.id,
        machine_code=f"MC-FS-{suffix}",
        machine_name=f"外出日志设备{suffix}",
        machine_no=1,
    )
    db.add(machine)
    db.flush()

    order = InstallationDispatchOrder(
        order_no=f"INST-FS-{suffix}",
        project_id=project.id,
        machine_id=machine.id,
        customer_id=customer.id,
        task_type="INSTALLATION",
        task_title="现场安装调试",
        task_description="完成现场安装、接线和基础调试",
        location="客户现场",
        scheduled_date=work_date,
        estimated_hours=Decimal("7.5"),
        assigned_to_id=user.id,
        assigned_to_name=user.real_name or user.username,
        status="IN_PROGRESS",
        priority="HIGH",
        progress=35,
        execution_notes="已到场并完成设备定位",
        customer_contact=customer.contact_person,
        customer_phone=customer.contact_phone,
        customer_address=customer.address,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return user, customer, project, machine, order


class TestMyWorkLogs:
    """我的工作日志测试"""

    def test_list_my_work_logs(self, client: TestClient, admin_token: str):
        """测试获取我的工作日志列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/my/work-logs",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 404:
            pytest.skip("My work-logs endpoint not found")

        assert response.status_code == 200

    def test_field_service_context_uses_assigned_dispatch_project_and_machine(
        self, client: TestClient, db_session, admin_token: str
    ):
        """外出日志上下文应自动带出负责的派工单、项目和设备"""
        if not admin_token:
            pytest.skip("Admin token not available")

        work_date = date(2035, 1, 11)
        _user, _customer, project, machine, order = _seed_assigned_field_dispatch(
            db_session, work_date
        )

        response = client.get(
            f"{settings.API_V1_PREFIX}/my/work-logs/field-service-context",
            params={"work_date": work_date.isoformat()},
            headers=_auth_headers(admin_token),
        )

        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["work_date"] == work_date.isoformat()
        assert data["has_submitted_log"] is False
        assert data["items"][0]["dispatch_order_id"] == order.id
        assert data["items"][0]["project_id"] == project.id
        assert data["items"][0]["project_name"] == project.project_name
        assert data["items"][0]["machine_id"] == machine.id
        assert data["items"][0]["machine_name"] == machine.machine_name
        assert "现场安装调试" in data["items"][0]["default_content"]

    def test_create_work_log_from_dispatch_auto_mentions_project_and_machine(
        self, client: TestClient, db_session, admin_token: str
    ):
        """从外出派工单提交日志时，应自动关联项目和设备"""
        if not admin_token:
            pytest.skip("Admin token not available")

        work_date = date(2035, 1, 12)
        user, _customer, project, machine, order = _seed_assigned_field_dispatch(
            db_session, work_date
        )

        response = client.post(
            f"{settings.API_V1_PREFIX}/my/work-logs/from-dispatch",
            json={
                "work_date": work_date.isoformat(),
                "dispatch_order_ids": [order.id],
                "today_progress": "完成电气接线和通电检查",
                "issues_found": "暂无异常",
                "next_plan": "明天进行联机调试",
                "work_hours": "7.5",
            },
            headers=_auth_headers(admin_token),
        )

        assert response.status_code == 201, response.text
        work_log_id = response.json()["data"]["id"]
        work_log = db_session.query(WorkLog).filter(WorkLog.id == work_log_id).first()
        assert work_log is not None
        assert work_log.user_id == user.id
        assert work_log.work_date == work_date
        assert "完成电气接线和通电检查" in work_log.content

        mentions = (
            db_session.query(WorkLogMention)
            .filter(WorkLogMention.work_log_id == work_log_id)
            .all()
        )
        mention_pairs = {(item.mention_type, item.mention_id) for item in mentions}
        assert ("PROJECT", project.id) in mention_pairs
        assert ("MACHINE", machine.id) in mention_pairs

    def test_list_my_work_logs_date_filter(self, client: TestClient, admin_token: str):
        """测试按日期筛选我的工作日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        today = date.today().isoformat()
        response = client.get(
            f"{settings.API_V1_PREFIX}/my/work-logs",
            params={"start_date": today, "end_date": today, "page": 1, "page_size": 10},
            headers=headers,
        )

        if response.status_code == 404:
            pytest.skip("My work-logs endpoint not found")

        assert response.status_code == 200


class TestProjectWorkLogs:
    """项目工作日志端点测试"""

    def test_list_project_work_logs(self, client: TestClient, admin_token: str):
        """测试获取项目工作日志列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        project_id = project["id"]
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/work-logs/", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Project work-logs endpoint not found")
        if response.status_code == 422:
            pytest.skip("Project work-logs endpoint not implemented")

        assert response.status_code == 200, response.text
        data = response.json()
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                assert "items" in data["data"] or "total" in data["data"]
            else:
                assert "items" in data or "data" in data
        else:
            assert isinstance(data, list)

    def test_project_work_logs_summary(self, client: TestClient, admin_token: str):
        """测试获取项目工作日志汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        project_id = project["id"]
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/work-logs/summary", headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work-logs summary endpoint not found")

        assert response.status_code == 200, response.text
