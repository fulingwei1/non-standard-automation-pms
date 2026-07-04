# -*- coding: utf-8 -*-
"""APPR-12: 旧增强合同审批入口不能绕过统一审批引擎。"""

import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.sales.contracts.enhanced import (
    approve_contract,
    reject_contract,
    submit_contract_for_approval,
)
from app.models.approval import ApprovalInstance
from app.models.project import Customer
from app.models.sales import Contract, ContractApproval
from app.models.user import User
from app.schemas.sales.contract_enhanced import (
    ContractApprovalUpdate,
    ContractSubmitApproval,
)
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


def _draft_contract(db: Session) -> Contract:
    suffix = uuid.uuid4().hex[:8].upper()
    customer = Customer(
        customer_code=f"CUS-APPR12-{suffix}",
        customer_name=f"APPR12客户-{suffix}",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()

    contract = Contract(
        contract_code=f"CON-APPR12-{suffix}",
        contract_name=f"APPR12合同-{suffix}",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=Decimal("120000.00"),
        status="draft",
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def test_enhanced_submit_uses_unified_approval_instance(db_session: Session):
    admin = _admin_user(db_session)
    init_approval_workflow_seeds(db_session)
    contract = _draft_contract(db_session)

    submitted = submit_contract_for_approval(
        contract_id=contract.id,
        submit_data=ContractSubmitApproval(comment="走统一审批"),
        db=db_session,
        current_user=admin,
    )

    db_session.refresh(contract)
    instance = (
        db_session.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "CONTRACT",
            ApprovalInstance.entity_id == contract.id,
        )
        .one()
    )

    assert submitted.id == contract.id
    assert instance.status in {"PENDING", "IN_PROGRESS"}
    assert contract.status == "PENDING_APPROVAL"
    assert db_session.query(ContractApproval).filter_by(contract_id=contract.id).count() == 0


def test_enhanced_approve_and_reject_routes_are_blocked_from_legacy_records(
    db_session: Session,
):
    admin = _admin_user(db_session)
    contract = _draft_contract(db_session)
    legacy_approval = ContractApproval(
        contract_id=contract.id,
        approval_level=1,
        approval_role="sales_manager",
        approval_status="pending",
    )
    db_session.add(legacy_approval)
    db_session.commit()

    with pytest.raises(HTTPException) as approve_exc:
        approve_contract(
            contract_id=contract.id,
            approval_id=legacy_approval.id,
            approval_data=ContractApprovalUpdate(
                approval_status="approved",
                approval_opinion="旧入口不应自审",
            ),
            db=db_session,
            current_user=admin,
        )

    assert approve_exc.value.status_code == 400
    assert "统一审批" in approve_exc.value.detail

    with pytest.raises(HTTPException) as reject_exc:
        reject_contract(
            contract_id=contract.id,
            approval_id=legacy_approval.id,
            approval_data=ContractApprovalUpdate(
                approval_status="rejected",
                approval_opinion="旧入口不应驳回",
            ),
            db=db_session,
            current_user=admin,
        )

    assert reject_exc.value.status_code == 400
    assert "统一审批" in reject_exc.value.detail

    db_session.refresh(contract)
    db_session.refresh(legacy_approval)
    assert contract.status == "draft"
    assert legacy_approval.approval_status == "pending"
