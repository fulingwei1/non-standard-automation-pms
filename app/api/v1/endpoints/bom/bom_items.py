# -*- coding: utf-8 -*-
"""
BOM明细 - 从 bom.py 拆分
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.api import deps
from app.core import security
from app.models.material import BomHeader, BomItem, Material
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.material import BomItemCreate, BomItemResponse

router = APIRouter()


@router.post("/{bom_id}/items", response_model=BomItemResponse)
def add_bom_item(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    item_in: BomItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """添加BOM明细"""
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 只有草稿状态才能添加明细
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能添加明细")

    # 如果提供了物料ID，获取物料信息
    if item_in.material_id:
        material = db.query(Material).filter(Material.id == item_in.material_id).first()
        if not material:
            raise HTTPException(
                status_code=404, detail=f"物料ID {item_in.material_id} 不存在"
            )

    # 获取当前最大行号

    max_item = (
        db.query(BomItem)
        .filter(BomItem.bom_id == bom_id)
        .order_by(desc(BomItem.item_no))
        .first()
    )
    item_no = (max_item.item_no + 1) if max_item else 1

    # 计算金额
    amount = item_in.quantity * (item_in.unit_price or 0)

    # 添加明细
    item = BomItem(
        bom_id=bom_id,
        item_no=item_no,
        material_id=item_in.material_id,
        material_code=item_in.material_code,
        material_name=item_in.material_name,
        specification=item_in.specification,
        drawing_no=item_in.drawing_no,
        unit=item_in.unit,
        quantity=item_in.quantity,
        unit_price=item_in.unit_price or 0,
        amount=amount,
        source_type=item_in.source_type,
        supplier_id=item_in.supplier_id,
        required_date=item_in.required_date,
        is_key_item=item_in.is_key_item,
        remark=item_in.remark,
    )
    db.add(item)

    # 更新BOM统计
    bom.total_items = bom.items.count()
    bom.total_amount = (bom.total_amount or 0) + amount

    db.commit()
    db.refresh(item)

    return BomItemResponse(
        id=item.id,
        item_no=item.item_no,
        material_id=item.material_id,
        material_code=item.material_code,
        material_name=item.material_name,
        specification=item.specification,
        unit=item.unit,
        quantity=item.quantity,
        unit_price=item.unit_price or 0,
        amount=item.amount,
        source_type=item.source_type,
        required_date=item.required_date,
        purchased_qty=item.purchased_qty or 0,
        received_qty=item.received_qty or 0,
        is_key_item=item.is_key_item,
    )


@router.get("/{bom_id}/items", response_model=List[BomItemResponse])
def get_bom_items(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取BOM明细列表"""
    bom = (
        db.query(BomHeader)
        .filter(BomHeader.id == bom_id)
        .first()
    )
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    items = []
    for item in bom.items.order_by(BomItem.item_no).all():
        items.append(
            BomItemResponse(
                id=item.id,
                item_no=item.item_no,
                material_id=item.material_id,
                material_code=item.material_code,
                material_name=item.material_name,
                specification=item.specification,
                unit=item.unit,
                quantity=item.quantity,
                unit_price=item.unit_price or 0,
                amount=item.amount or 0,
                source_type=item.source_type,
                required_date=item.required_date,
                purchased_qty=item.purchased_qty or 0,
                received_qty=item.received_qty or 0,
                is_key_item=item.is_key_item,
            )
        )

    return items


@router.put("/items/{item_id}", response_model=BomItemResponse)
def update_bom_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    item_in: BomItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新BOM明细"""
    item = db.query(BomItem).filter(BomItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM明细不存在")

    bom = item.header
    # 只有草稿状态才能更新明细
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能更新明细")

    # 如果提供了物料ID，获取物料信息
    if item_in.material_id:
        material = db.query(Material).filter(Material.id == item_in.material_id).first()
        if not material:
            raise HTTPException(
                status_code=404, detail=f"物料ID {item_in.material_id} 不存在"
            )

    # 计算新金额
    old_amount = item.amount or 0
    new_amount = item_in.quantity * (item_in.unit_price or 0)

    # 更新明细
    item.material_id = item_in.material_id
    item.material_code = item_in.material_code
    item.material_name = item_in.material_name
    item.specification = item_in.specification
    item.drawing_no = item_in.drawing_no
    item.unit = item_in.unit
    item.quantity = item_in.quantity
    item.unit_price = item_in.unit_price or 0
    item.amount = new_amount
    item.source_type = item_in.source_type
    item.supplier_id = item_in.supplier_id
    item.required_date = item_in.required_date
    item.is_key_item = item_in.is_key_item
    if item_in.remark is not None:
        item.remark = item_in.remark

    # 更新BOM总金额
    bom.total_amount = (bom.total_amount or 0) - old_amount + new_amount

    db.add(item)
    db.commit()
    db.refresh(item)

    return BomItemResponse(
        id=item.id,
        item_no=item.item_no,
        material_id=item.material_id,
        material_code=item.material_code,
        material_name=item.material_name,
        specification=item.specification,
        unit=item.unit,
        quantity=item.quantity,
        unit_price=item.unit_price or 0,
        amount=item.amount or 0,
        source_type=item.source_type,
        required_date=item.required_date,
        purchased_qty=item.purchased_qty or 0,
        received_qty=item.received_qty or 0,
        is_key_item=item.is_key_item,
    )


@router.delete("/items/{item_id}", status_code=200)
def delete_bom_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除BOM明细"""
    item = db.query(BomItem).filter(BomItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM明细不存在")

    bom = item.header
    # 只有草稿状态才能删除明细
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能删除明细")

    # 记录旧金额
    old_amount = item.amount or 0

    # 删除明细
    db.delete(item)

    # 更新BOM统计
    bom.total_items = bom.items.count()
    bom.total_amount = max(0, (bom.total_amount or 0) - old_amount)

    db.commit()

    return ResponseModel(code=200, message="BOM明细已删除")
