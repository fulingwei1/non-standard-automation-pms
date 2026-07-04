# -*- coding: utf-8 -*-
"""工单创建时应绑定 BOM 并固化工单 BOM 快照。"""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app.models.material import BomHeader, BomItem
from app.models.project import Machine, Project
from app.models.production import WorkOrder
from app.models.shortage import WorkOrderBom
from app.schemas.production import WorkOrderCreate, WorkOrderUpdate
from app.services.production.work_order_service import WorkOrderService


def _seed_released_bom(db_session):
    suffix = uuid.uuid4().hex[:8]
    project = Project(
        project_code=f"PJ-WO-BOM-{suffix}",
        project_name="工单BOM快照测试项目",
        stage="S4",
        status="ST04",
        health="H1",
    )
    db_session.add(project)
    db_session.flush()

    machine = Machine(
        project_id=project.id,
        machine_code=f"M-WO-BOM-{suffix}",
        machine_name="工单BOM快照测试机台",
        machine_type="TEST",
        status="DESIGN",
    )
    db_session.add(machine)
    db_session.flush()

    bom = BomHeader(
        bom_no=f"BOM-WO-{suffix}",
        bom_name="工单BOM快照测试",
        project_id=project.id,
        machine_id=machine.id,
        version="2.3",
        is_latest=True,
        status="RELEASED",
        total_items=1,
        total_amount=Decimal("20.00"),
    )
    db_session.add(bom)
    db_session.flush()

    item = BomItem(
        bom_id=bom.id,
        item_no=1,
        material_code=f"MAT-WO-{suffix}",
        material_name="快照物料",
        specification="SNAP-SPEC",
        unit="件",
        quantity=Decimal("2.0000"),
        unit_price=Decimal("10.0000"),
        amount=Decimal("20.00"),
        source_type="PURCHASE",
        required_date=date(2026, 7, 20),
        is_key_item=True,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(bom)
    return project, machine, bom, item


def test_create_work_order_with_bom_persists_link_and_bom_snapshot(db_session):
    project, machine, bom, item = _seed_released_bom(db_session)
    service = WorkOrderService(db_session)
    order_in = WorkOrderCreate(
        task_name="按BOM装配",
        task_type="ASSEMBLY",
        project_id=project.id,
        machine_id=machine.id,
        bom_id=bom.id,
        plan_qty=3,
        plan_start_date=date(2026, 7, 10),
        plan_end_date=date(2026, 7, 25),
    )

    with patch(
        "app.api.v1.endpoints.production.utils.generate_work_order_no",
        return_value="WO-BOM-SNAPSHOT-001",
    ):
        response = service.create_work_order(order_in, current_user_id=1)

    order = (
        db_session.query(WorkOrder)
        .filter(WorkOrder.work_order_no == response.work_order_no)
        .one()
    )
    assert order.bom_id == bom.id
    assert order.bom_no == bom.bom_no
    assert order.bom_version == bom.version

    snapshots = db_session.query(WorkOrderBom).filter_by(work_order_id=order.id).all()
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.work_order_no == "WO-BOM-SNAPSHOT-001"
    assert snapshot.project_id == project.id
    assert snapshot.material_code == item.material_code
    assert snapshot.material_name == item.material_name
    assert snapshot.specification == item.specification
    assert snapshot.unit == item.unit
    assert snapshot.bom_qty == Decimal("2.0000")
    assert snapshot.required_qty == Decimal("6.0000")
    assert snapshot.required_date == item.required_date
    assert snapshot.material_type == "purchase"
    assert snapshot.is_key_material is True


def test_update_work_order_bom_replaces_and_clears_snapshot(db_session):
    project, machine, bom, item = _seed_released_bom(db_session)
    order = WorkOrder(
        work_order_no=f"WO-BOM-UPDATE-{uuid.uuid4().hex[:8]}",
        task_name="待绑定BOM工单",
        task_type="ASSEMBLY",
        project_id=project.id,
        machine_id=machine.id,
        plan_qty=2,
        status="PENDING",
        priority="NORMAL",
        progress=0,
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    service = WorkOrderService(db_session)

    response = service.update_work_order(order.id, WorkOrderUpdate(bom_id=bom.id))

    assert response.bom_id == bom.id
    assert response.bom_no == bom.bom_no
    assert response.bom_version == bom.version
    snapshots = db_session.query(WorkOrderBom).filter_by(work_order_id=order.id).all()
    assert len(snapshots) == 1
    assert snapshots[0].material_code == item.material_code
    assert snapshots[0].required_qty == Decimal("4.0000")

    response = service.update_work_order(order.id, WorkOrderUpdate(bom_id=None))

    assert response.bom_id is None
    assert response.bom_no is None
    assert response.bom_version is None
    assert db_session.query(WorkOrderBom).filter_by(work_order_id=order.id).count() == 0
