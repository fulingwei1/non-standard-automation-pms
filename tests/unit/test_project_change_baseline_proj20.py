# -*- coding: utf-8 -*-
"""PROJ-20: approved project change requests must update project baselines."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.enums import (
    ApprovalDecisionEnum,
    ChangeSourceEnum,
    ChangeStatusEnum,
    ChangeTypeEnum,
    ImpactLevelEnum,
)
from app.models.project import Customer, Project, ProjectCost, ProjectMilestone
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


def _seed_project(db_session, suffix: str, *, planned_end_date: date) -> Project:
    customer = Customer(
        customer_code=f"PROJ20-CUST-{suffix}",
        customer_name=f"PROJ20 客户 {suffix}",
    )
    db_session.add(customer)
    db_session.flush()

    project = Project(
        project_code=f"PROJ20-PROJ-{suffix}",
        project_name=f"PROJ20 项目 {suffix}",
        customer_id=customer.id,
        planned_end_date=planned_end_date,
        actual_cost=Decimal("100.00"),
    )
    db_session.add(project)
    db_session.flush()
    return project


def _change_in(project_id: int, milestone_id: int | None = None) -> ChangeRequestCreate:
    affected_milestones = []
    if milestone_id:
        affected_milestones.append({"milestone_id": milestone_id})

    return ChangeRequestCreate(
        project_id=project_id,
        title="客户追加检测范围",
        description="客户要求追加检测工位和报表字段",
        change_type=ChangeTypeEnum.SCOPE,
        change_source=ChangeSourceEnum.CUSTOMER,
        cost_impact=Decimal("1250.00"),
        cost_impact_level=ImpactLevelEnum.MEDIUM,
        time_impact=7,
        time_impact_level=ImpactLevelEnum.MEDIUM,
        impact_details={"schedule": {"affected_milestones": affected_milestones}},
        notify_team=False,
    )


def test_approved_change_request_updates_project_baseline(db_session):
    suffix = uuid4().hex[:8]
    submitter = _user(f"proj20-submitter-{suffix}")
    approver = _user(f"proj20-approver-{suffix}")
    db_session.add_all([submitter, approver])
    db_session.flush()
    project = _seed_project(db_session, suffix, planned_end_date=date(2026, 1, 31))
    milestone = ProjectMilestone(
        project_id=project.id,
        milestone_name="FAT",
        planned_date=date(2026, 1, 20),
        status="PENDING",
        is_key=True,
    )
    db_session.add(milestone)
    db_session.commit()

    service = ProjectChangeRequestsService(db_session)
    change = service.create_change_request(_change_in(project.id, milestone.id), submitter)
    change.status = ChangeStatusEnum.PENDING_APPROVAL
    db_session.add(change)
    db_session.commit()

    service.approve_change_request(
        change.id,
        ChangeApprovalRequest(decision=ApprovalDecisionEnum.APPROVED, comments="同意"),
        approver,
    )

    db_session.expire_all()
    project = db_session.get(Project, project.id)
    milestone = db_session.get(ProjectMilestone, milestone.id)
    change = db_session.get(type(change), change.id)
    cost = (
        db_session.query(ProjectCost)
        .filter(
            ProjectCost.project_id == project.id,
            ProjectCost.source_type == "CHANGE_REQUEST",
            ProjectCost.source_id == change.id,
        )
        .one()
    )

    assert project.planned_end_date == date(2026, 2, 7)
    assert project.actual_cost == Decimal("1350.00")
    assert milestone.planned_date == date(2026, 1, 27)
    assert cost.amount == Decimal("1250.00")
    assert cost.cost_basis == "ACTUAL"
    assert change.impact_details["baseline_application"]["applied"] is True


def test_rejected_change_request_does_not_update_project_baseline(db_session):
    suffix = uuid4().hex[:8]
    submitter = _user(f"proj20-reject-submitter-{suffix}")
    approver = _user(f"proj20-reject-approver-{suffix}")
    db_session.add_all([submitter, approver])
    db_session.flush()
    project = _seed_project(db_session, suffix, planned_end_date=date(2026, 3, 31))
    db_session.commit()

    service = ProjectChangeRequestsService(db_session)
    change = service.create_change_request(_change_in(project.id), submitter)
    change.status = ChangeStatusEnum.PENDING_APPROVAL
    db_session.add(change)
    db_session.commit()

    service.approve_change_request(
        change.id,
        ChangeApprovalRequest(decision=ApprovalDecisionEnum.REJECTED, comments="不同意"),
        approver,
    )

    db_session.expire_all()
    project = db_session.get(Project, project.id)
    cost_count = (
        db_session.query(ProjectCost)
        .filter(
            ProjectCost.project_id == project.id,
            ProjectCost.source_type == "CHANGE_REQUEST",
            ProjectCost.source_id == change.id,
        )
        .count()
    )

    assert project.planned_end_date == date(2026, 3, 31)
    assert project.actual_cost == Decimal("100.00")
    assert cost_count == 0
