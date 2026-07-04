# -*- coding: utf-8 -*-
"""BOM版本管理回归测试"""

import uuid
from decimal import Decimal

from app.api.v1.endpoints.bom.bom_release import release_bom
from app.api.v1.endpoints.bom.bom_versions import create_bom_revision, get_bom_versions
from app.models.material import BomHeader, BomItem
from app.models.project import Machine, Project
from app.schemas.material import BomRevisionCreate


def _seed_released_bom(db_session, suffix: str | None = None) -> BomHeader:
    suffix = suffix or uuid.uuid4().hex[:8]
    project = Project(
        project_code=f"PJ-BOMVER-{suffix}",
        project_name="BOM版本测试项目",
        stage="S4",
        status="ST04",
        health="H1",
    )
    db_session.add(project)
    db_session.flush()

    machine = Machine(
        project_id=project.id,
        machine_code=f"M-BOMVER-{suffix}",
        machine_name="BOM版本测试机台",
        machine_type="TEST",
        status="DESIGN",
    )
    db_session.add(machine)
    db_session.flush()

    bom = BomHeader(
        bom_no=f"BOM-VER-{suffix}",
        bom_name="BOM版本测试",
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

    db_session.add(
        BomItem(
            bom_id=bom.id,
            item_no=1,
            material_code=f"MAT-BOMVER-{suffix}",
            material_name="版本复制物料",
            specification="OLD-SPEC",
            unit="件",
            quantity=Decimal("2.0000"),
            unit_price=Decimal("10.0000"),
            amount=Decimal("20.00"),
            source_type="PURCHASE",
            is_key_item=True,
        )
    )
    db_session.commit()
    db_session.refresh(bom)
    return bom


def test_create_revision_from_released_bom_copies_items_and_preserves_history(
    db_session,
    test_admin,
):
    source_bom = _seed_released_bom(db_session)

    revision = create_bom_revision(
        db=db_session,
        bom_id=source_bom.id,
        revision_in=BomRevisionCreate(version="1.1", change_note="设计修订"),
        current_user=test_admin,
    )

    assert revision.id != source_bom.id
    assert revision.bom_no == source_bom.bom_no
    assert revision.version == "1.1"
    assert revision.status == "DRAFT"
    assert revision.is_latest is False
    assert revision.total_items == 1
    assert revision.items[0].material_code == source_bom.items.first().material_code
    assert Decimal(str(revision.items[0].quantity)) == Decimal("2.0000")

    versions = get_bom_versions(db=db_session, bom_id=source_bom.id, current_user=test_admin)
    assert {item.version for item in versions} >= {"1.0", "1.1"}
    assert len([item for item in versions if item.bom_no == source_bom.bom_no]) == 2

    db_session.refresh(source_bom)
    assert source_bom.status == "RELEASED"
    assert source_bom.is_latest is True


def test_releasing_revision_marks_previous_version_not_latest(db_session, test_admin):
    source_bom = _seed_released_bom(db_session)
    revision = create_bom_revision(
        db=db_session,
        bom_id=source_bom.id,
        revision_in=BomRevisionCreate(version="2.0", change_note="大版本修订"),
        current_user=test_admin,
    )

    released_revision = release_bom(
        db=db_session,
        bom_id=revision.id,
        change_note="发布 2.0",
        current_user=test_admin,
    )

    db_session.refresh(source_bom)
    assert source_bom.is_latest is False
    assert released_revision.id == revision.id
    assert released_revision.status == "RELEASED"
    assert released_revision.is_latest is True
