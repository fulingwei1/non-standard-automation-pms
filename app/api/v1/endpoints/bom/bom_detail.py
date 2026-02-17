# -*- coding: utf-8 -*-
"""
BOM详情 - 从 bom.py 拆分
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api import deps
from app.core import security
from app.models.material import BomHeader, BomItem, Material
from app.models.user import User
from app.schemas.material import BomResponse, BomUpdate
from app.utils.db_helpers import get_or_404, save_obj
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


def get_bom_item(db: Session, bom_id: int, material_id: int) -> dict:
    """获取BOM项目信息"""
    bom = (
        db.query(BomHeader)
        .options(selectinload(BomHeader.project), joinedload(BomHeader.machine))
        .filter(BomHeader.id == bom_id)
        .first()
    )
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    material = db.query(Material).filter(Material.id == material_id).first()

    return {
        "material_id": material.id if material else None,
        "material_code": material.material_code if material else None,
        "material_name": material.material_name if material else None,
        "specification": material.specification if material else None,
        "unit": material.unit if material else None,
        "unit_price": float(material.unit_price) if material.unit_price else 0,
        "supplier_id": material.supplier_id if material else None,
        "supplier_name": material.supplier.supplier_name
        if material and material.supplier
        else None,
    }


@router.get("/{bom_id}", response_model=BomResponse)
def get_bom_detail(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> BomResponse:
    """
    获取BOM详情
    """
    bom = (
        db.query(BomHeader)
        .options(
            joinedload(BomHeader.project),
            joinedload(BomHeader.machine),
        )
        .filter(BomHeader.id == bom_id)
        .first()
    )
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # BomHeader.items 为 dynamic relationship，不能 eager load
    items = []
    for item in bom.items.order_by(BomItem.item_no).all():
        material = item.material
        items.append(
            {
                "id": item.id,
                "item_no": item.item_no,
                "material_id": item.material_id,
                "material_code": material.material_code if material else None,
                "material_name": material.material_name if material else None,
                "specification": material.specification if material else None,
                "unit": material.unit if material else None,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "amount": float(item.amount) if item.amount else 0,
                "source_type": item.source_type,
                "required_date": item.required_date.strftime("%Y-%m-%d")
                if item.required_date
                else None,
                "purchased_qty": item.purchased_qty or 0,
                "received_qty": item.received_qty or 0,
                "is_key_item": item.is_key_item,
            }
        )

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
        total_amount=float(bom.total_amount) if bom.total_amount else 0,
        items=items,
        created_at=bom.created_at,
        updated_at=bom.updated_at,
    )


@router.put("/{bom_id}", response_model=BomResponse)
def update_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    bom_in: BomUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> BomResponse:
    """
    更新BOM（仅草稿状态可更新）
    """
    bom = get_or_404(db, BomHeader, bom_id, "BOM不存在")

    # 只有草稿状态才能更新
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能更新")

    update_data = bom_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bom, field, value)

    save_obj(db, bom)

    bom = (
        db.query(BomHeader)
        .options(
            joinedload(BomHeader.project),
            joinedload(BomHeader.machine),
        )
        .filter(BomHeader.id == bom.id)
        .first()
    )

    # BomHeader.items 为 dynamic relationship，不能 eager load
    items = []
    for item in bom.items.order_by(BomItem.item_no).all():
        material = item.material
        items.append(
            {
                "id": item.id,
                "item_no": item.item_no,
                "material_id": item.material_id,
                "material_code": material.material_code if material else None,
                "material_name": material.material_name if material else None,
                "specification": material.specification if material else None,
                "unit": material.unit if material else None,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "amount": float(item.amount) if item.amount else 0,
                "source_type": item.source_type,
                "required_date": item.required_date.strftime("%Y-%m-%d")
                if item.required_date
                else None,
                "purchased_qty": item.purchased_qty or 0,
                "received_qty": item.received_qty or 0,
                "is_key_item": item.is_key_item,
            }
        )

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
        total_amount=float(bom.total_amount) if bom.total_amount else 0,
        items=items,
        created_at=bom.created_at,
        updated_at=bom.updated_at,
    )
