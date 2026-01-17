# -*- coding: utf-8 -*-
"""
机台BOM管理 - 从 bom.py 拆分
"""

from decimal import Decimal
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api import deps
from app.core import security
from app.models.material import BomHeader, BomItem, Material
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.material import BomCreate, BomItemCreate, BomItemResponse, BomResponse

router = APIRouter()


@router.get("/", response_model=List[BomResponse])
def get_machine_bom_list(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取机台的BOM列表
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    bom_headers = (
        db.query(BomHeader)
        .options(
            joinedload(BomHeader.project),
            joinedload(BomHeader.machine),
        )
        .filter(BomHeader.machine_id == machine_id)
        .order_by(BomHeader.created_at.desc())
        .all()
    )

    result = []
    for bom in bom_headers:
        # BomHeader.items 为 dynamic relationship，不能 eager load
        items = []
        for item in bom.items.order_by(BomItem.item_no).all():
            items.append(
                BomResponse(
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

        result.append(
            BomResponse(
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
                items=items,
                created_at=bom.created_at,
                updated_at=bom.updated_at,
            )
        )

    return result


def generate_bom_no(db: Session, project_id: int) -> str:
    """生成BOM编号：BOM-PJxxx-xxx"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 使用项目编码的前缀
    project_prefix = (
        project.project_code[:8] if project.project_code else f"PJ{project_id:06d}"
    )

    # 查询该项目下最大的序号
    from sqlalchemy import desc

    max_bom = (
        db.query(BomHeader)
        .filter(BomHeader.project_id == project_id)
        .filter(BomHeader.bom_no.like(f"BOM-{project_prefix}-%"))
        .order_by(desc(BomHeader.bom_no))
        .first()
    )

    if max_bom:
        # 提取序号并加1
        try:
            seq = int(max_bom.bom_no.split("-")[-1]) + 1
        except (ValueError, TypeError, IndexError):
            seq = 1
    else:
        seq = 1

    return f"BOM-{project_prefix}-{seq:03d}"


@router.post("/", response_model=BomResponse)
def create_bom(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    bom_in: BomCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为机台创建BOM
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == bom_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查机台是否属于该项目
    if machine.project_id != bom_in.project_id:
        raise HTTPException(status_code=400, detail="机台不属于该项目")

    # 生成BOM编号
    bom_no = generate_bom_no(db, bom_in.project_id)

    # 检查BOM编号是否已存在
    existing = db.query(BomHeader).filter(BomHeader.bom_no == bom_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="BOM编号已存在")

    # 创建BOM表头
    bom = BomHeader(
        bom_no=bom_no,
        bom_name=bom_in.bom_name,
        project_id=bom_in.project_id,
        machine_id=machine_id,
        version=bom_in.version,
        status="DRAFT",
        created_by=current_user.id,
        remark=bom_in.remark,
    )
    db.add(bom)
    db.flush()

    # 创建BOM明细
    total_amount = Decimal(0)
    for idx, item_in in enumerate(bom_in.items, start=1):
        # 如果提供了物料ID，获取物料信息
        material = None
        if item_in.material_id:
            material = (
                db.query(Material).filter(Material.id == item_in.material_id).first()
            )
            if not material:
                raise HTTPException(
                    status_code=404, detail=f"物料ID {item_in.material_id} 不存在"
                )

        # 计算金额
        amount = item_in.quantity * (item_in.unit_price or 0)
        total_amount += amount

        item = BomItem(
            bom_id=bom.id,
            item_no=idx,
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
    bom.total_items = len(bom_in.items)
    bom.total_amount = total_amount

    db.commit()
    db.refresh(bom)

    # 返回BOM详情
    bom = (
        db.query(BomHeader)
        .options(
            selectinload(BomHeader.items),
            joinedload(BomHeader.project),
            joinedload(BomHeader.machine),
        )
        .filter(BomHeader.id == bom.id)
        .first()
    )

    items = []
    for item in sorted(bom.items, key=lambda x: x.item_no or 0):
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
        items=items,
        created_at=bom.created_at,
        updated_at=bom.updated_at,
    )
