# -*- coding: utf-8 -*-
"""
BOM版本管理 - 从 bom.py 拆分
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader, BomItem
from app.models.user import User
from app.schemas.material import BomItemResponse, BomResponse, BomRevisionCreate
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _build_bom_response(bom: BomHeader) -> BomResponse:
    items = [
        BomItemResponse(
            id=item.id,
            bom_id=item.bom_id,
            item_no=item.item_no,
            parent_item_id=item.parent_item_id,
            material_id=item.material_id,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            drawing_no=item.drawing_no,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price or 0,
            amount=item.amount or 0,
            source_type=item.source_type,
            supplier_id=item.supplier_id,
            required_date=item.required_date,
            purchased_qty=item.purchased_qty or 0,
            received_qty=item.received_qty or 0,
            level=item.level,
            sort_order=item.sort_order,
            is_key_item=item.is_key_item,
            remark=item.remark,
        )
        for item in bom.items.order_by(BomItem.item_no).all()
    ]

    return BomResponse(
        id=bom.id,
        bom_no=bom.bom_no,
        bom_name=bom.bom_name,
        project_id=bom.project_id,
        project_name=bom.project.project_name if bom.project else None,
        machine_id=bom.machine_id,
        machine_name=bom.machine.machine_name if bom.machine else None,
        version=bom.version,
        is_latest=bom.is_latest,
        status=bom.status,
        total_items=bom.total_items,
        total_amount=bom.total_amount or 0,
        approved_by=bom.approved_by,
        approved_at=bom.approved_at.isoformat() if bom.approved_at else None,
        created_by=bom.created_by,
        remark=bom.remark,
        items=items,
        created_at=bom.created_at,
        updated_at=bom.updated_at,
    )


@router.get("/{bom_id}/versions", response_model=List[BomResponse])
def get_bom_versions(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
):
    """获取BOM的所有版本列表
    基于BOM编号查找所有版本
    """
    bom = get_or_404(db, BomHeader, bom_id, "BOM不存在")

    # 查找相同BOM编号的所有版本
    versions = (
        db.query(BomHeader)
        .filter(BomHeader.bom_no == bom.bom_no)
        .order_by(BomHeader.created_at.desc())
        .all()
    )

    return [_build_bom_response(version) for version in versions]


@router.post("/{bom_id}/versions", response_model=BomResponse, status_code=201)
def create_bom_revision(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    revision_in: BomRevisionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> BomResponse:
    """从已发布 BOM 克隆一个新的草稿修订版本。"""
    source_bom = get_or_404(db, BomHeader, bom_id, "BOM不存在")

    if source_bom.status != "RELEASED":
        raise HTTPException(status_code=400, detail="只有已发布BOM才能创建修订版本")

    existing_version = (
        db.query(BomHeader)
        .filter(
            BomHeader.bom_no == source_bom.bom_no,
            BomHeader.version == revision_in.version,
        )
        .first()
    )
    if existing_version:
        raise HTTPException(status_code=400, detail="该BOM版本号已存在")

    source_items = source_bom.items.order_by(BomItem.item_no).all()
    if not source_items:
        raise HTTPException(status_code=400, detail="BOM没有明细，无法创建修订版本")

    revision = BomHeader(
        bom_no=source_bom.bom_no,
        bom_name=source_bom.bom_name,
        project_id=source_bom.project_id,
        machine_id=source_bom.machine_id,
        version=revision_in.version,
        is_latest=False,
        status="DRAFT",
        total_items=source_bom.total_items,
        total_amount=source_bom.total_amount,
        remark=revision_in.change_note or source_bom.remark,
        created_by=current_user.id,
    )
    db.add(revision)
    db.flush()

    copied_items: list[tuple[BomItem, BomItem]] = []
    old_to_new_id: dict[int, int] = {}
    for source_item in source_items:
        copied_item = BomItem(
            bom_id=revision.id,
            item_no=source_item.item_no,
            material_id=source_item.material_id,
            material_code=source_item.material_code,
            material_name=source_item.material_name,
            specification=source_item.specification,
            drawing_no=source_item.drawing_no,
            unit=source_item.unit,
            quantity=source_item.quantity,
            unit_price=source_item.unit_price or 0,
            amount=source_item.amount or 0,
            source_type=source_item.source_type,
            supplier_id=source_item.supplier_id,
            required_date=source_item.required_date,
            purchased_qty=0,
            received_qty=0,
            kitting_status="PENDING",
            level=source_item.level,
            sort_order=source_item.sort_order,
            is_key_item=source_item.is_key_item,
            remark=source_item.remark,
        )
        db.add(copied_item)
        db.flush()
        copied_items.append((source_item, copied_item))
        old_to_new_id[source_item.id] = copied_item.id

    for source_item, copied_item in copied_items:
        if source_item.parent_item_id in old_to_new_id:
            copied_item.parent_item_id = old_to_new_id[source_item.parent_item_id]

    db.commit()
    db.refresh(revision)
    return _build_bom_response(revision)


@router.get("/{bom_id}/versions/compare", response_model=dict)
def compare_bom_versions(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    version1_id: Optional[int] = Query(None, description="版本1的BOM ID"),
    version2_id: Optional[int] = Query(None, description="版本2的BOM ID"),
    current_user: User = Depends(security.get_current_active_user),
):
    """对比BOM的两个版本
    如果不提供version1_id和version2_id，则对比当前版本和最新发布版本
    """
    bom = get_or_404(db, BomHeader, bom_id, "BOM不存在")

    # 确定要对比的两个版本
    if version1_id and version2_id:
        v1 = db.query(BomHeader).filter(BomHeader.id == version1_id).first()
        v2 = db.query(BomHeader).filter(BomHeader.id == version2_id).first()
    else:
        # 默认对比当前版本和最新发布版本
        v1 = bom
        v2 = (
            db.query(BomHeader)
            .filter(
                BomHeader.bom_no == bom.bom_no,
                BomHeader.status == "RELEASED",
                BomHeader.is_latest,
            )
            .first()
        )
        if not v2:
            v2 = bom

    if not v1 or not v2:
        raise HTTPException(status_code=404, detail="要对比的版本不存在")

    # 获取两个版本的明细
    items1 = {item.material_code: item for item in v1.items.all()}
    items2 = {item.material_code: item for item in v2.items.all()}

    # 找出新增、删除、修改的物料
    added = []
    deleted = []
    modified = []
    unchanged = []

    all_materials = set(items1.keys()) | set(items2.keys())

    for material_code in all_materials:
        if material_code in items1 and material_code not in items2:
            deleted.append(
                {
                    "material_code": material_code,
                    "material_name": items1[material_code].material_name,
                    "quantity": float(items1[material_code].quantity),
                    "unit_price": (
                        float(items1[material_code].unit_price)
                        if items1[material_code].unit_price
                        else 0
                    ),
                }
            )
        elif material_code not in items1 and material_code in items2:
            added.append(
                {
                    "material_code": material_code,
                    "material_name": items2[material_code].material_name,
                    "quantity": float(items2[material_code].quantity),
                    "unit_price": (
                        float(items2[material_code].unit_price)
                        if items2[material_code].unit_price
                        else 0
                    ),
                }
            )
        else:
            item1 = items1[material_code]
            item2 = items2[material_code]
            if (
                item1.quantity != item2.quantity
                or item1.unit_price != item2.unit_price
                or item1.specification != item2.specification
            ):
                modified.append(
                    {
                        "material_code": material_code,
                        "material_name": item1.material_name,
                        "v1": {
                            "quantity": float(item1.quantity),
                            "unit_price": float(item1.unit_price) if item1.unit_price else 0,
                            "specification": item1.specification,
                        },
                        "v2": {
                            "quantity": float(item2.quantity),
                            "unit_price": float(item2.unit_price) if item2.unit_price else 0,
                            "specification": item2.specification,
                        },
                    }
                )
            else:
                unchanged.append(
                    {
                        "material_code": material_code,
                        "material_name": item1.material_name,
                        "quantity": float(item1.quantity),
                        "unit_price": float(item1.unit_price) if item1.unit_price else 0,
                    }
                )

    return {
        "version1": {
            "id": v1.id,
            "version": v1.version,
            "status": v1.status,
            "total_items": v1.total_items,
            "total_amount": float(v1.total_amount) if v1.total_amount else 0,
        },
        "version2": {
            "id": v2.id,
            "version": v2.version,
            "status": v2.status,
            "total_items": v2.total_items,
            "total_amount": float(v2.total_amount) if v2.total_amount else 0,
        },
        "comparison": {
            "added": added,
            "deleted": deleted,
            "modified": modified,
            "unchanged": unchanged,
            "summary": {
                "added_count": len(added),
                "deleted_count": len(deleted),
                "modified_count": len(modified),
                "unchanged_count": len(unchanged),
            },
        },
    }
