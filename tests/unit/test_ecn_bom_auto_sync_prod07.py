# -*- coding: utf-8 -*-
"""PROD-07: approved ECN changes must automatically apply to BOM."""

import uuid
from decimal import Decimal

from app.api.v1.endpoints.ecn.execution import start_ecn_execution
from app.models.approval import ApprovalInstance
from app.models.ecn import Ecn, EcnAffectedMaterial, EcnBomChange
from app.models.material import BomHeader, BomItem
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.ecn import EcnStartExecution
from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter


def _seed_ecn_bom_change(db_session):
    suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"prod07-user-{suffix}",
        password_hash="x",
        real_name="PROD07 User",
        is_active=True,
        is_superuser=True,
    )
    project = Project(
        project_code=f"PROD07-PJ-{suffix}",
        project_name="PROD07 项目",
        stage="S4",
        status="ST04",
    )
    db_session.add_all([user, project])
    db_session.flush()

    machine = Machine(
        project_id=project.id,
        machine_code=f"PROD07-M-{suffix}",
        machine_name="PROD07 机台",
        machine_type="TEST",
        status="DESIGN",
    )
    db_session.add(machine)
    db_session.flush()

    bom = BomHeader(
        bom_no=f"PROD07-BOM-{suffix}",
        bom_name="PROD07 BOM",
        project_id=project.id,
        machine_id=machine.id,
        version="1.0",
        is_latest=True,
        status="RELEASED",
        total_items=1,
        total_amount=Decimal("20.00"),
    )
    db_session.add(bom)
    db_session.flush()

    bom_item = BomItem(
        bom_id=bom.id,
        item_no=1,
        material_code=f"PROD07-MAT-{suffix}",
        material_name="PROD07 物料",
        specification="OLD",
        unit="件",
        quantity=Decimal("2.0000"),
        unit_price=Decimal("10.0000"),
        amount=Decimal("20.00"),
        source_type="PURCHASE",
    )
    db_session.add(bom_item)
    db_session.flush()

    ecn = Ecn(
        ecn_no=f"PROD07-ECN-{suffix}",
        ecn_title="PROD07 ECN",
        ecn_type="DESIGN_CHANGE",
        project_id=project.id,
        machine_id=machine.id,
        change_reason="设计变更",
        change_description="数量和规格变化",
        status="PENDING_APPROVAL",
        created_by=user.id,
    )
    db_session.add(ecn)
    db_session.flush()

    affected = EcnAffectedMaterial(
        ecn_id=ecn.id,
        bom_item_id=bom_item.id,
        material_code=bom_item.material_code,
        material_name=bom_item.material_name,
        change_type="UPDATE",
        old_quantity=Decimal("2.0000"),
        new_quantity=Decimal("3.0000"),
        old_specification="OLD",
        new_specification="NEW",
        cost_impact=Decimal("10.00"),
        status="PENDING",
    )
    db_session.add(affected)
    db_session.commit()
    return user, ecn, bom_item, affected


def test_approved_ecn_auto_syncs_pending_bom_changes(db_session):
    user, ecn, bom_item, affected = _seed_ecn_bom_change(db_session)
    instance = ApprovalInstance(
        instance_no=f"PROD07-AP-{uuid.uuid4().hex[:8]}",
        template_id=1,
        flow_id=1,
        entity_type="ECN",
        entity_id=ecn.id,
        initiator_id=user.id,
        status="APPROVED",
        final_approver_id=user.id,
        final_comment="同意",
    )

    EcnApprovalAdapter(db_session).sync_from_approval_instance(instance, ecn)

    db_session.refresh(ecn)
    db_session.refresh(bom_item)
    db_session.refresh(affected)

    assert ecn.status == "APPROVED"
    assert bom_item.quantity == Decimal("3.0000")
    assert bom_item.specification == "NEW"
    assert affected.status == "PROCESSED"
    assert db_session.query(EcnBomChange).filter(EcnBomChange.ecn_id == ecn.id).count() == 1


def test_start_execution_auto_syncs_approved_ecn_bom_changes(db_session):
    user, ecn, bom_item, affected = _seed_ecn_bom_change(db_session)
    ecn.status = "APPROVED"
    db_session.add(ecn)
    db_session.commit()

    start_ecn_execution(
        db=db_session,
        ecn_id=ecn.id,
        execution_in=EcnStartExecution(remark="开始执行"),
        current_user=user,
    )

    db_session.refresh(ecn)
    db_session.refresh(bom_item)
    db_session.refresh(affected)

    assert ecn.status == "EXECUTING"
    assert bom_item.quantity == Decimal("3.0000")
    assert affected.status == "PROCESSED"
