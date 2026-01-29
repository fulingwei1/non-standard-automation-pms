# -*- coding: utf-8 -*-
"""
状态更新端点集成测试

测试使用统一状态更新服务重构后的API端点
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.service import ServiceTicket
from app.models.production import WorkOrder, Workstation
from app.models.stage_instance import ProjectStageInstance
from app.models.user import User
from app.models.project import Project
from app.models.project.customer import Customer


@pytest.mark.integration
class TestServiceTicketStatusUpdate:
    """测试服务工单状态更新端点"""

    def test_update_ticket_status_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试成功更新工单状态"""
        # 创建测试数据
        project = db_session.query(Project).first()
        customer = db_session.query(Customer).first()
        user = db_session.query(User).first()

        if not project or not customer or not user:
            pytest.skip("缺少测试数据：项目、客户或用户")

        ticket = ServiceTicket(
            ticket_no="TST001",
            project_id=project.id,
            customer_id=customer.id,
            problem_type="技术问题",
            problem_desc="测试问题",
            urgency="HIGH",
            reported_by="测试用户",
            reported_time=datetime.now(),
            status="PENDING",
        )
        db_session.add(ticket)
        db_session.commit()
        db_session.refresh(ticket)

        # 更新状态
        response = client.put(
            f"/api/v1/service/tickets/{ticket.id}/status",
            params={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"
        assert data["response_time"] is not None

        # 验证数据库
        db_session.refresh(ticket)
        assert ticket.status == "IN_PROGRESS"
        assert ticket.response_time is not None

    def test_update_ticket_status_invalid(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试无效状态值"""
        project = db_session.query(Project).first()
        customer = db_session.query(Customer).first()

        if not project or not customer:
            pytest.skip("缺少测试数据")

        ticket = ServiceTicket(
            ticket_no="TST002",
            project_id=project.id,
            customer_id=customer.id,
            problem_type="技术问题",
            problem_desc="测试问题",
            urgency="HIGH",
            reported_by="测试用户",
            reported_time=datetime.now(),
            status="PENDING",
        )
        db_session.add(ticket)
        db_session.commit()
        db_session.refresh(ticket)

        # 尝试使用无效状态
        response = client.put(
            f"/api/v1/service/tickets/{ticket.id}/status",
            params={"status": "INVALID_STATUS"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "无效的状态值" in response.json()["detail"]

    def test_close_ticket_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试关闭工单"""
        project = db_session.query(Project).first()
        customer = db_session.query(Customer).first()

        if not project or not customer:
            pytest.skip("缺少测试数据")

        ticket = ServiceTicket(
            ticket_no="TST003",
            project_id=project.id,
            customer_id=customer.id,
            problem_type="技术问题",
            problem_desc="测试问题",
            urgency="HIGH",
            reported_by="测试用户",
            reported_time=datetime.now(),
            status="RESOLVED",
        )
        db_session.add(ticket)
        db_session.commit()
        db_session.refresh(ticket)

        # 关闭工单
        response = client.put(
            f"/api/v1/service/tickets/{ticket.id}/close",
            json={
                "solution": "问题已解决",
                "root_cause": "配置错误",
                "preventive_action": "更新配置文档",
                "satisfaction": 5,
                "feedback": "服务很好",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"
        assert data["solution"] == "问题已解决"
        assert data["resolved_time"] is not None

        # 验证数据库
        db_session.refresh(ticket)
        assert ticket.status == "CLOSED"
        assert ticket.resolved_time is not None


@pytest.mark.integration
class TestWorkOrderStatusUpdate:
    """测试工单状态更新端点"""

    def test_start_work_order_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试开始工单"""
        # 创建测试数据
        workstation = Workstation(
            station_code="WS001",
            station_name="测试工位",
            status="IDLE",
        )
        db_session.add(workstation)
        db_session.commit()
        db_session.refresh(workstation)

        order = WorkOrder(
            order_no="WO001",
            status="ASSIGNED",
            workstation_id=workstation.id,
            assigned_to=1,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 开始工单
        response = client.put(
            f"/api/v1/production/work-orders/{order.id}/start",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "STARTED"
        assert data["actual_start_time"] is not None

        # 验证数据库
        db_session.refresh(order)
        assert order.status == "STARTED"
        assert order.actual_start_time is not None

        # 验证工位状态
        db_session.refresh(workstation)
        assert workstation.status == "WORKING"
        assert workstation.current_work_order_id == order.id

    def test_start_work_order_invalid_transition(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试无效状态转换"""
        order = WorkOrder(
            order_no="WO002",
            status="STARTED",  # 已经是STARTED状态
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 尝试从STARTED再次开始（应该失败）
        response = client.put(
            f"/api/v1/production/work-orders/{order.id}/start",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "不允许的状态转换" in response.json()["detail"]

    def test_complete_work_order_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试完成工单"""
        workstation = Workstation(
            station_code="WS002",
            station_name="测试工位2",
            status="WORKING",
        )
        db_session.add(workstation)
        db_session.commit()
        db_session.refresh(workstation)

        order = WorkOrder(
            order_no="WO003",
            status="STARTED",
            workstation_id=workstation.id,
            progress=80,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 完成工单
        response = client.put(
            f"/api/v1/production/work-orders/{order.id}/complete",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["progress"] == 100
        assert data["actual_end_time"] is not None

        # 验证数据库
        db_session.refresh(order)
        assert order.status == "COMPLETED"
        assert order.progress == 100
        assert order.actual_end_time is not None

        # 验证工位状态
        db_session.refresh(workstation)
        assert workstation.status == "IDLE"
        assert workstation.current_work_order_id is None

    def test_pause_work_order_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试暂停工单"""
        workstation = Workstation(
            station_code="WS003",
            station_name="测试工位3",
            status="WORKING",
        )
        db_session.add(workstation)
        db_session.commit()
        db_session.refresh(workstation)

        order = WorkOrder(
            order_no="WO004",
            status="STARTED",
            workstation_id=workstation.id,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 暂停工单
        response = client.put(
            f"/api/v1/production/work-orders/{order.id}/pause",
            json={"pause_reason": "设备故障"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PAUSED"

        # 验证数据库
        db_session.refresh(order)
        assert order.status == "PAUSED"
        assert "暂停原因" in (order.remark or "")

        # 验证工位状态
        db_session.refresh(workstation)
        assert workstation.status == "IDLE"

    def test_resume_work_order_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试恢复工单"""
        workstation = Workstation(
            station_code="WS004",
            station_name="测试工位4",
            status="IDLE",
        )
        db_session.add(workstation)
        db_session.commit()
        db_session.refresh(workstation)

        order = WorkOrder(
            order_no="WO005",
            status="PAUSED",
            workstation_id=workstation.id,
            assigned_to=1,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 恢复工单
        response = client.put(
            f"/api/v1/production/work-orders/{order.id}/resume",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "STARTED"

        # 验证数据库
        db_session.refresh(order)
        assert order.status == "STARTED"

        # 验证工位状态
        db_session.refresh(workstation)
        assert workstation.status == "WORKING"
        assert workstation.current_work_order_id == order.id

    def test_cancel_work_order_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试取消工单"""
        workstation = Workstation(
            station_code="WS005",
            station_name="测试工位5",
            status="WORKING",
        )
        db_session.add(workstation)
        db_session.commit()
        db_session.refresh(workstation)

        order = WorkOrder(
            order_no="WO006",
            status="STARTED",
            workstation_id=workstation.id,
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 取消工单
        response = client.put(
            f"/api/v1/production/work-orders/{order.id}/cancel",
            json={"cancel_reason": "订单取消"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"

        # 验证数据库
        db_session.refresh(order)
        assert order.status == "CANCELLED"
        assert "取消原因" in (order.remark or "")

        # 验证工位状态
        db_session.refresh(workstation)
        assert workstation.status == "IDLE"
        assert workstation.current_work_order_id is None


@pytest.mark.integration
class TestProjectStageStatusUpdate:
    """测试项目阶段状态更新端点"""

    def test_update_stage_status_success(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试成功更新阶段状态"""
        # 创建测试项目
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("缺少测试数据：项目")

        # 创建阶段实例
        stage = ProjectStageInstance(
            project_id=project.id,
            stage_code="S2",
            stage_name="方案设计",
            status="PENDING",
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        # 更新状态
        response = client.put(
            f"/api/v1/projects/stages/{stage.id}/status",
            json={
                "status": "IN_PROGRESS",
                "remark": "开始设计工作",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"
        assert data["remark"] == "开始设计工作"

        # 验证数据库
        db_session.refresh(stage)
        assert stage.status == "IN_PROGRESS"
        assert stage.remark == "开始设计工作"

    def test_update_stage_status_invalid(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试无效状态值"""
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("缺少测试数据：项目")

        stage = ProjectStageInstance(
            project_id=project.id,
            stage_code="S2",
            stage_name="方案设计",
            status="PENDING",
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        # 尝试使用无效状态
        response = client.put(
            f"/api/v1/projects/stages/{stage.id}/status",
            json={
                "status": "INVALID_STATUS",
                "remark": None,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "无效的状态值" in response.json()["detail"]
