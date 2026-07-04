# -*- coding: utf-8 -*-
"""AS-23: service ticket endpoints must create real notifications."""
from datetime import date, datetime

from app.api.v1.endpoints import after_sales
from app.api.v1.endpoints.service.tickets.assignment import assign_service_ticket
from app.api.v1.endpoints.service.tickets.crud import create_service_ticket
from app.api.v1.endpoints.service.tickets.status import (
    close_service_ticket,
    update_service_ticket_status,
)
from app.models.notification import Notification
from app.models.project import Customer, Project
from app.models.service import ServiceTicket, ServiceTicketCcUser
from app.models.user import User
from app.schemas.service import ServiceTicketAssign, ServiceTicketClose, ServiceTicketCreate


def _user(username: str, *, superuser: bool = False) -> User:
    return User(
        username=username,
        password_hash="x",
        real_name=username.title(),
        is_active=True,
        is_superuser=superuser,
    )


def _seed_project(db_session, *, pm_id: int | None = None):
    customer = Customer(customer_code="AS23-CUST", customer_name="AS23 客户")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="AS23-PROJ",
        project_name="AS23 项目",
        customer_id=customer.id,
        pm_id=pm_id,
    )
    db_session.add(project)
    db_session.flush()
    return customer, project


def test_create_ticket_sends_notifications_to_assignee_and_cc(db_session):
    current_user = _user("as23-admin", superuser=True)
    assignee = _user("as23-assignee")
    cc_user = _user("as23-cc")
    db_session.add_all([current_user, assignee, cc_user])
    db_session.flush()
    customer, project = _seed_project(db_session)
    db_session.commit()

    ticket_in = ServiceTicketCreate(
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="AS23 create endpoint notification",
        urgency="HIGH",
        reported_by=str(current_user.id),
        reported_time=datetime(2026, 1, 1, 9, 0),
        assignee_id=assignee.id,
        cc_user_ids=[cc_user.id],
    )

    ticket = create_service_ticket(
        db=db_session,
        ticket_in=ticket_in,
        current_user=current_user,
    )

    notifications = (
        db_session.query(Notification)
        .filter(Notification.source_type == "service_ticket", Notification.source_id == ticket.id)
        .all()
    )
    notified_user_ids = {notification.user_id for notification in notifications}
    cc_record = (
        db_session.query(ServiceTicketCcUser)
        .filter(ServiceTicketCcUser.ticket_id == ticket.id, ServiceTicketCcUser.user_id == cc_user.id)
        .one()
    )

    assert {assignee.id, cc_user.id}.issubset(notified_user_ids)
    assert cc_record.notified_at is not None


def test_assign_ticket_sends_notifications_to_assignee_and_cc(db_session):
    current_user = _user("as23-assign-admin", superuser=True)
    assignee = _user("as23-new-assignee")
    cc_user = _user("as23-new-cc")
    db_session.add_all([current_user, assignee, cc_user])
    db_session.flush()
    customer, project = _seed_project(db_session)
    ticket = ServiceTicket(
        ticket_no="AS23-TICKET",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="AS23 assign endpoint notification",
        urgency="HIGH",
        reported_by=str(current_user.id),
        reported_time=datetime(2026, 1, 1, 9, 0),
        status="PENDING",
    )
    db_session.add(ticket)
    db_session.commit()

    assign_service_ticket(
        db=db_session,
        ticket_id=ticket.id,
        assign_in=ServiceTicketAssign(assignee_id=assignee.id, cc_user_ids=[cc_user.id]),
        current_user=current_user,
    )

    notifications = (
        db_session.query(Notification)
        .filter(Notification.source_type == "service_ticket", Notification.source_id == ticket.id)
        .all()
    )
    notified_user_ids = {notification.user_id for notification in notifications}
    cc_record = (
        db_session.query(ServiceTicketCcUser)
        .filter(ServiceTicketCcUser.ticket_id == ticket.id, ServiceTicketCcUser.user_id == cc_user.id)
        .one()
    )

    assert {assignee.id, cc_user.id}.issubset(notified_user_ids)
    assert cc_record.notified_at is not None


def test_status_update_sends_notifications_to_assignee_reporter_and_cc(db_session):
    current_user = _user("as23-status-admin", superuser=True)
    assignee = _user("as23-status-assignee")
    cc_user = _user("as23-status-cc")
    db_session.add_all([current_user, assignee, cc_user])
    db_session.flush()
    customer, project = _seed_project(db_session)
    ticket = ServiceTicket(
        ticket_no="AS23-STATUS",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="AS23 status notification",
        urgency="MEDIUM",
        reported_by=str(current_user.id),
        reported_time=datetime(2026, 1, 1, 9, 0),
        assigned_to_id=assignee.id,
        status="IN_PROGRESS",
    )
    db_session.add(ticket)
    db_session.flush()
    db_session.add(ServiceTicketCcUser(ticket_id=ticket.id, user_id=cc_user.id))
    db_session.commit()

    update_service_ticket_status(
        db=db_session,
        ticket_id=ticket.id,
        status="RESOLVED",
        current_user=current_user,
    )

    notifications = (
        db_session.query(Notification)
        .filter(
            Notification.source_type == "service_ticket",
            Notification.source_id == ticket.id,
            Notification.notification_type == "SERVICE_TICKET_STATUS_CHANGED_TO_RESOLVED",
        )
        .all()
    )
    notified_user_ids = {notification.user_id for notification in notifications}

    assert {current_user.id, assignee.id, cc_user.id}.issubset(notified_user_ids)


def test_close_ticket_sends_notifications_to_assignee_reporter_and_cc(db_session):
    current_user = _user("as23-close-admin", superuser=True)
    assignee = _user("as23-close-assignee")
    cc_user = _user("as23-close-cc")
    db_session.add_all([current_user, assignee, cc_user])
    db_session.flush()
    customer, project = _seed_project(db_session)
    ticket = ServiceTicket(
        ticket_no="AS23-CLOSE",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="AS23 close notification",
        urgency="MEDIUM",
        reported_by=str(current_user.id),
        reported_time=datetime(2026, 1, 1, 9, 0),
        assigned_to_id=assignee.id,
        status="RESOLVED",
    )
    db_session.add(ticket)
    db_session.flush()
    db_session.add(ServiceTicketCcUser(ticket_id=ticket.id, user_id=cc_user.id))
    db_session.commit()

    close_service_ticket(
        db=db_session,
        ticket_id=ticket.id,
        close_in=ServiceTicketClose(solution="已修复"),
        current_user=current_user,
    )

    notifications = (
        db_session.query(Notification)
        .filter(
            Notification.source_type == "service_ticket",
            Notification.source_id == ticket.id,
            Notification.notification_type == "SERVICE_TICKET_CLOSED",
        )
        .all()
    )
    notified_user_ids = {notification.user_id for notification in notifications}

    assert {current_user.id, assignee.id, cc_user.id}.issubset(notified_user_ids)


def _assert_notification(db_session, *, source_type: str, source_id: int, user_id: int):
    notification = (
        db_session.query(Notification)
        .filter(
            Notification.source_type == source_type,
            Notification.source_id == source_id,
            Notification.user_id == user_id,
        )
        .first()
    )
    assert notification is not None


def test_after_sales_project_write_endpoints_notify_project_pm(db_session):
    current_user = _user("as23-after-admin", superuser=True)
    pm = _user("as23-after-pm")
    db_session.add_all([current_user, pm])
    db_session.flush()
    _customer, project = _seed_project(db_session, pm_id=pm.id)
    db_session.commit()

    feedback = after_sales.create_feedback(
        project_id=project.id,
        feedback_type="COMPLAINT",
        feedback_content="客户反馈",
        priority="HIGH",
        db=db_session,
        current_user=current_user,
    )
    maintenance = after_sales.create_maintenance(
        project_id=project.id,
        maintenance_type="REGULAR",
        maintenance_content="定期保养",
        scheduled_date=date(2026, 1, 2),
        db=db_session,
        current_user=current_user,
    )
    ticket = after_sales.create_support_ticket(
        project_id=project.id,
        subject="技术支持",
        description="需要远程协助",
        category="TECHNICAL",
        priority="HIGH",
        db=db_session,
        current_user=current_user,
    )
    warranty = after_sales.create_warranty(
        project_id=project.id,
        warranty_type="STANDARD",
        warranty_months=12,
        scope="整机",
        db=db_session,
        current_user=current_user,
    )
    spare_part = after_sales.create_spare_part(
        project_id=project.id,
        part_name="测试备件",
        part_spec="SP-1",
        quantity=1,
        supplier="供应商",
        db=db_session,
        current_user=current_user,
    )
    field_service = after_sales.create_field_service(
        project_id=project.id,
        service_type="REPAIR",
        service_content="现场维修",
        planned_date=date(2026, 1, 3),
        engineer_name="工程师",
        db=db_session,
        current_user=current_user,
    )
    satisfaction = after_sales.create_satisfaction(
        project_id=project.id,
        overall_score=9,
        response_score=9,
        quality_score=9,
        attitude_score=9,
        nps_score=9,
        comments="满意",
        db=db_session,
        current_user=current_user,
    )

    expected = [
        ("after_sales_feedback", feedback["id"]),
        ("after_sales_maintenance", maintenance["id"]),
        ("after_sales_support_ticket", ticket["id"]),
        ("after_sales_warranty", warranty["id"]),
        ("after_sales_spare_part", spare_part["id"]),
        ("after_sales_field_service", field_service["id"]),
        ("after_sales_satisfaction", satisfaction["id"]),
    ]
    for source_type, source_id in expected:
        _assert_notification(
            db_session,
            source_type=source_type,
            source_id=source_id,
            user_id=pm.id,
        )


def test_after_sales_support_ticket_escalation_notifies_project_pm(db_session):
    current_user = _user("as23-escalate-admin", superuser=True)
    pm = _user("as23-escalate-pm")
    db_session.add_all([current_user, pm])
    db_session.flush()
    _customer, project = _seed_project(db_session, pm_id=pm.id)
    db_session.commit()
    ticket = after_sales.create_support_ticket(
        project_id=project.id,
        subject="技术支持升级",
        description="需要升级",
        category="TECHNICAL",
        priority="MEDIUM",
        db=db_session,
        current_user=current_user,
    )

    after_sales.escalate_ticket(
        project_id=project.id,
        ticket_id=ticket["id"],
        reason="超时",
        db=db_session,
        current_user=current_user,
    )

    notification = (
        db_session.query(Notification)
        .filter(
            Notification.source_type == "after_sales_support_ticket",
            Notification.source_id == ticket["id"],
            Notification.user_id == pm.id,
            Notification.notification_type == "AFTER_SALES_TICKET_ESCALATED",
        )
        .first()
    )
    assert notification is not None


def test_after_sales_knowledge_creation_notifies_creator(db_session):
    current_user = _user("as23-knowledge-admin", superuser=True)
    db_session.add(current_user)
    db_session.commit()

    knowledge = after_sales.create_knowledge(
        title="售后知识",
        category="FAQ",
        content="处理步骤",
        keywords="售后",
        project_type="ICT",
        db=db_session,
        current_user=current_user,
    )

    _assert_notification(
        db_session,
        source_type="after_sales_knowledge",
        source_id=knowledge["id"],
        user_id=current_user.id,
    )
