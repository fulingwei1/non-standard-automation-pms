# -*- coding: utf-8 -*-
"""PROJ-21: project change requests must create real system notifications."""

from app.models.enums import ApprovalDecisionEnum, ChangeSourceEnum, ChangeStatusEnum, ChangeTypeEnum
from app.models.notification import Notification
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.change_request import ChangeApprovalRequest, ChangeRequestCreate
from app.services.project_change_requests.service import ProjectChangeRequestsService


def _user(username: str) -> User:
    return User(
        username=username,
        password_hash="x",
        real_name=username.title(),
        is_active=True,
    )


def _seed_project(db_session, *, pm_id: int) -> Project:
    customer = Customer(customer_code="PROJ21-CUST", customer_name="PROJ21 客户")
    db_session.add(customer)
    db_session.flush()
    project = Project(
        project_code="PROJ21-PROJ",
        project_name="PROJ21 项目",
        customer_id=customer.id,
        pm_id=pm_id,
    )
    db_session.add(project)
    db_session.flush()
    return project


def _change_in(project_id: int) -> ChangeRequestCreate:
    return ChangeRequestCreate(
        project_id=project_id,
        title="客户需求变更",
        description="客户要求追加范围",
        change_type=ChangeTypeEnum.SCOPE,
        change_source=ChangeSourceEnum.CUSTOMER,
        notify_team=True,
    )


def test_create_change_request_notifies_project_pm(db_session):
    submitter = _user("proj21-submitter")
    pm = _user("proj21-pm")
    db_session.add_all([submitter, pm])
    db_session.flush()
    project = _seed_project(db_session, pm_id=pm.id)
    db_session.commit()

    change = ProjectChangeRequestsService(db_session).create_change_request(
        _change_in(project.id),
        submitter,
    )

    notification = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == pm.id,
            Notification.source_type == "project_change_request",
            Notification.source_id == change.id,
            Notification.notification_type == "PROJECT_CHANGE_SUBMITTED",
        )
        .first()
    )
    assert notification is not None


def test_approve_change_request_notifies_submitter(db_session):
    submitter = _user("proj21-approval-submitter")
    pm = _user("proj21-approval-pm")
    approver = _user("proj21-approver")
    db_session.add_all([submitter, pm, approver])
    db_session.flush()
    project = _seed_project(db_session, pm_id=pm.id)
    db_session.commit()
    service = ProjectChangeRequestsService(db_session)
    change = service.create_change_request(_change_in(project.id), submitter)
    change.status = ChangeStatusEnum.PENDING_APPROVAL
    db_session.add(change)
    db_session.commit()

    service.approve_change_request(
        change.id,
        ChangeApprovalRequest(decision=ApprovalDecisionEnum.APPROVED, comments="同意"),
        approver,
    )

    notification = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == submitter.id,
            Notification.source_type == "project_change_request",
            Notification.source_id == change.id,
            Notification.notification_type == "PROJECT_CHANGE_APPROVED",
        )
        .first()
    )
    assert notification is not None
