# -*- coding: utf-8 -*-
"""MISC-19: 发货单审批必须接入统一审批引擎。"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.business_support_orders.delivery_orders.crud import (
    DELIVERY_ORDER_APPROVAL_ENTITY_TYPE,
    approve_delivery_order,
    submit_delivery_order_approval,
)
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.business_support import DeliveryOrder, SalesOrder
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.business_support import DeliveryApprovalRequest
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


def _delivery_order(db: Session) -> DeliveryOrder:
    suffix = uuid.uuid4().hex[:8].upper()
    customer = Customer(
        customer_code=f"CUS-MISC19-{suffix}",
        customer_name=f"MISC19客户-{suffix}",
        contact_person="测试联系人",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()

    project = Project(
        project_code=f"PJ-MISC19-{suffix}",
        project_name=f"MISC19项目-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_type="NEW",
        product_category="ICT",
        project_category="销售",
    )
    db.add(project)
    db.flush()

    sales_order = SalesOrder(
        order_no=f"SO-MISC19-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_id=project.id,
        project_no=project.project_code,
        order_type="standard",
        order_amount=Decimal("88000.00"),
        currency="CNY",
        order_status="ready",
    )
    db.add(sales_order)
    db.flush()

    delivery = DeliveryOrder(
        delivery_no=f"DO-MISC19-{suffix}",
        order_id=sales_order.id,
        order_no=sales_order.order_no,
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_id=project.id,
        delivery_date=date.today(),
        delivery_type="freight",
        delivery_amount=Decimal("88000.00"),
        approval_status="pending",
        delivery_status="draft",
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


@pytest.mark.asyncio
async def test_delivery_approve_requires_unified_approval_instance(db_session: Session):
    current_user = _admin_user(db_session)
    init_approval_workflow_seeds(db_session)
    delivery = _delivery_order(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await approve_delivery_order(
            delivery_id=delivery.id,
            approval_data=DeliveryApprovalRequest(
                approved=True,
                approval_comment="不能绕过统一审批",
            ),
            db=db_session,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 400
    assert "统一审批" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delivery_submit_then_approve_uses_unified_engine(db_session: Session):
    current_user = _admin_user(db_session)
    init_approval_workflow_seeds(db_session)
    delivery = _delivery_order(db_session)

    submitted = await submit_delivery_order_approval(
        delivery_id=delivery.id,
        db=db_session,
        current_user=current_user,
    )
    assert submitted.data["entity_type"] == DELIVERY_ORDER_APPROVAL_ENTITY_TYPE
    assert submitted.data["entity_id"] == delivery.id

    instance = (
        db_session.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == DELIVERY_ORDER_APPROVAL_ENTITY_TYPE,
            ApprovalInstance.entity_id == delivery.id,
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

    approved = await approve_delivery_order(
        delivery_id=delivery.id,
        approval_data=DeliveryApprovalRequest(
            approved=True,
            approval_comment="同意发货",
        ),
        db=db_session,
        current_user=current_user,
    )

    assert approved.data.approval_status == "approved"
    assert approved.data.delivery_status == "approved"

    db_session.refresh(instance)
    assert instance.status == "APPROVED"
