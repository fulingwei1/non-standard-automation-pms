# -*- coding: utf-8 -*-
"""MISC-21: 项目预算审批必须接入统一审批引擎。"""

import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.budget.budgets import (
    PROJECT_BUDGET_APPROVAL_ENTITY_TYPE,
    approve_budget,
    submit_budget,
)
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.budget import ProjectBudgetApproveRequest
from app.utils.init_approval_data import init_approval_workflow_seeds


def _admin_user(db: Session) -> User:
    user = db.query(User).filter(User.username == "admin").first()
    if user is None:
        user = User(
            username="admin",
            password_hash="test",
            real_name="系统管理员",
            department="系统",
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _budget(db: Session) -> ProjectBudget:
    suffix = uuid.uuid4().hex[:8].upper()
    customer = Customer(
        customer_code=f"CUS-MISC21-{suffix}",
        customer_name=f"MISC21客户-{suffix}",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()

    project = Project(
        project_code=f"PJ-MISC21-{suffix}",
        project_name=f"MISC21项目-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_type="NEW",
        product_category="ICT",
        project_category="销售",
    )
    db.add(project)
    db.flush()

    budget = ProjectBudget(
        budget_no=f"BUD-MISC21-{suffix}",
        project_id=project.id,
        budget_name="MISC21预算",
        budget_type="INITIAL",
        version="V1.0",
        total_amount=Decimal("1.00"),
        status="DRAFT",
        is_active=True,
    )
    db.add(budget)
    db.flush()
    db.add_all(
        [
            ProjectBudgetItem(
                budget_id=budget.id,
                item_no=1,
                cost_category="材料",
                cost_item="标准件",
                budget_amount=Decimal("700.00"),
            ),
            ProjectBudgetItem(
                budget_id=budget.id,
                item_no=2,
                cost_category="人工",
                cost_item="装配",
                budget_amount=Decimal("300.00"),
            ),
        ]
    )
    db.commit()
    db.refresh(budget)
    return budget


def test_budget_approve_requires_unified_approval_instance(db_session: Session):
    current_user = _admin_user(db_session)
    init_approval_workflow_seeds(db_session)
    budget = _budget(db_session)

    with pytest.raises(HTTPException) as exc_info:
        approve_budget(
            budget_id=budget.id,
            approve_request=ProjectBudgetApproveRequest(
                approved=True,
                approval_note="不能绕过统一审批",
            ),
            db=db_session,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 400
    assert "统一审批" in exc_info.value.detail


def test_budget_submit_then_approve_uses_unified_engine_and_item_total(db_session: Session):
    current_user = _admin_user(db_session)
    init_approval_workflow_seeds(db_session)
    budget = _budget(db_session)

    submitted = submit_budget(
        budget_id=budget.id,
        db=db_session,
        current_user=current_user,
    )
    assert submitted.status == "SUBMITTED"
    assert submitted.total_amount == Decimal("1000.00")

    instance = (
        db_session.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == PROJECT_BUDGET_APPROVAL_ENTITY_TYPE,
            ApprovalInstance.entity_id == budget.id,
        )
        .first()
    )
    assert instance is not None
    task = (
        db_session.query(ApprovalTask)
        .filter(
            ApprovalTask.instance_id == instance.id,
            ApprovalTask.assignee_id == current_user.id,
            ApprovalTask.status == "PENDING",
        )
        .first()
    )
    assert task is not None

    approved = approve_budget(
        budget_id=budget.id,
        approve_request=ProjectBudgetApproveRequest(
            approved=True,
            approval_note="同意预算",
        ),
        db=db_session,
        current_user=current_user,
    )

    assert approved.status == "APPROVED"
    assert approved.approved_by == current_user.id
    assert approved.total_amount == Decimal("1000.00")

    db_session.refresh(instance)
    db_session.refresh(budget.project)
    assert instance.status == "APPROVED"
    assert budget.project.budget_amount == Decimal("1000.00")
