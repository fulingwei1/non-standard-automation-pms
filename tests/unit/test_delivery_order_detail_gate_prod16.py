# -*- coding: utf-8 -*-
"""PROD-16: 发货单必须有明细、发货必须通过齐套/质检门禁。"""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.business_support_orders.delivery_orders.crud import (
    create_delivery_order,
    receive_delivery_order,
    ship_delivery_order,
)
from app.models.business_support import (
    DeliveryOrder,
    DeliveryOrderItem,
    SalesOrder,
    SalesOrderItem,
)
from app.models.production import QualityInspection, WorkOrder
from app.models.project import Customer, Project
from app.schemas.business_support import DeliveryOrderCreate


def _current_user():
    return SimpleNamespace(id=1, username="admin", real_name="系统管理员")


def _business_seed(db: Session, *, ready: bool = False):
    suffix = uuid.uuid4().hex[:8].upper()
    customer = Customer(
        customer_code=f"CUS-PROD16-{suffix}",
        customer_name=f"PROD16客户-{suffix}",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()

    project = Project(
        project_code=f"PJ-PROD16-{suffix}",
        project_name=f"PROD16项目-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S7",
        status="ST23",
        material_status="齐套" if ready else "缺料",
        kitting_rate=Decimal("100.0") if ready else Decimal("60.0"),
        shortage_items_count=0 if ready else 2,
    )
    db.add(project)
    db.flush()

    order = SalesOrder(
        order_no=f"SO-PROD16-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_id=project.id,
        project_no=project.project_code,
        order_amount=Decimal("120000.00"),
        order_status="ready",
    )
    db.add(order)
    db.flush()

    order_item = SalesOrderItem(
        sales_order_id=order.id,
        item_name="非标自动化整机",
        item_spec="ATE-01",
        qty=Decimal("1"),
        unit="台",
        unit_price=Decimal("120000.00"),
        amount=Decimal("120000.00"),
    )
    db.add(order_item)
    db.commit()
    return customer, project, order, order_item


def _add_final_quality_pass(db: Session, project: Project):
    suffix = uuid.uuid4().hex[:8].upper()
    work_order = WorkOrder(
        work_order_no=f"WO-PROD16-{suffix}",
        task_name="整机装配联调",
        task_type="ASSEMBLY",
        project_id=project.id,
        plan_qty=1,
        completed_qty=1,
        qualified_qty=1,
        status="COMPLETED",
        progress=100,
        created_by=1,
    )
    db.add(work_order)
    db.flush()

    inspection = QualityInspection(
        inspection_no=f"QI-PROD16-{suffix}",
        work_order_id=work_order.id,
        inspection_type="FQC",
        inspection_date=datetime.now(),
        inspector_id=1,
        inspection_qty=1,
        qualified_qty=1,
        defect_qty=0,
        inspection_result="PASS",
        created_by=1,
    )
    db.add(inspection)
    db.commit()


@pytest.mark.asyncio
async def test_create_delivery_order_copies_sales_order_items_to_real_lines(db_session: Session):
    _, project, order, order_item = _business_seed(db_session, ready=True)

    result = await create_delivery_order(
        DeliveryOrderCreate(
            order_id=order.id,
            delivery_date=date.today() + timedelta(days=1),
            delivery_type="logistics",
            delivery_amount=Decimal("120000.00"),
        ),
        db=db_session,
        current_user=_current_user(),
    )

    assert result.data.project_id == project.id
    assert result.data.items is not None
    assert len(result.data.items) == 1
    assert result.data.items[0].sales_order_item_id == order_item.id
    assert result.data.items[0].delivery_qty == Decimal("1.00")

    db_item = db_session.query(DeliveryOrderItem).filter_by(delivery_order_id=result.data.id).one()
    assert db_item.item_name == "非标自动化整机"
    assert db_item.sales_order_item_id == order_item.id


@pytest.mark.asyncio
async def test_ship_delivery_order_requires_lines_kitting_quality_and_updates_project(
    db_session: Session,
):
    customer, project, order, order_item = _business_seed(db_session, ready=False)
    delivery = DeliveryOrder(
        delivery_no=f"DO-PROD16-{uuid.uuid4().hex[:8].upper()}",
        order_id=order.id,
        order_no=order.order_no,
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_id=project.id,
        delivery_date=date.today(),
        delivery_type="logistics",
        delivery_amount=Decimal("120000.00"),
        approval_status="approved",
        delivery_status="approved",
    )
    db_session.add(delivery)
    db_session.flush()
    db_session.add(
        DeliveryOrderItem(
            delivery_order_id=delivery.id,
            sales_order_item_id=order_item.id,
            item_name=order_item.item_name,
            item_spec=order_item.item_spec,
            delivery_qty=Decimal("1.00"),
            unit=order_item.unit,
            unit_price=order_item.unit_price,
            amount=order_item.amount,
        )
    )
    db_session.commit()

    with pytest.raises(HTTPException) as not_ready:
        await ship_delivery_order(delivery.id, db=db_session, current_user=_current_user())
    assert not_ready.value.status_code == 400
    assert "齐套" in not_ready.value.detail

    project.material_status = "齐套"
    project.kitting_rate = Decimal("100.0")
    project.shortage_items_count = 0
    db_session.commit()

    with pytest.raises(HTTPException) as no_quality:
        await ship_delivery_order(delivery.id, db=db_session, current_user=_current_user())
    assert no_quality.value.status_code == 400
    assert "质检" in no_quality.value.detail

    _add_final_quality_pass(db_session, project)
    shipped = await ship_delivery_order(delivery.id, db=db_session, current_user=_current_user())
    assert shipped.data.delivery_status == "shipped"
    db_session.refresh(project)
    assert project.stage == "S8"
    assert project.status == "ST24"

    received = await receive_delivery_order(
        delivery.id,
        db=db_session,
        current_user=_current_user(),
    )
    assert received.data.delivery_status == "received"
    db_session.refresh(project)
    assert project.stage == "S8"
    assert project.status == "ST25"
