# -*- coding: utf-8 -*-
"""
BOM 管理 API endpoints
"""
from typing import Any, List, Optional, Dict
from decimal import Decimal
from datetime import datetime
import json
from pathlib import Path
import io

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.material import BomHeader, BomItem, Material, Supplier
from app.models.purchase import PurchaseRequest, PurchaseRequestItem
from app.models.project import Project, Machine
from app.schemas.material import (
    BomCreate,
    BomUpdate,
    BomResponse,
    BomItemCreate,
    BomItemResponse,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()

# 尝试导入Excel处理库
try:
    import pandas as pd
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


def generate_bom_no(db: Session, project_id: int) -> str:
    """生成BOM编号：BOM-PJxxx-xxx"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 使用项目编码的前缀
    project_prefix = project.project_code[:8] if project.project_code else f"PJ{project_id:06d}"
    
    # 查询该项目下最大的序号
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
        except:
            seq = 1
    else:
        seq = 1
    
    return f"BOM-{project_prefix}-{seq:03d}"


@router.get("/machines/{machine_id}/bom", response_model=List[BomResponse])
def get_machine_bom_list(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取机台的BOM列表
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    
    bom_headers = (
        db.query(BomHeader)
        .filter(BomHeader.machine_id == machine_id)
        .order_by(desc(BomHeader.created_at))
        .all()
    )
    
    result = []
    for bom in bom_headers:
        # 获取BOM明细
        items = []
        for item in bom.items.order_by(BomItem.item_no).all():
            items.append(BomItemResponse(
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
            ))
        
        result.append(BomResponse(
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
        ))
    
    return result


@router.post("/machines/{machine_id}/bom", response_model=BomResponse)
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
            material = db.query(Material).filter(Material.id == item_in.material_id).first()
            if not material:
                raise HTTPException(status_code=404, detail=f"物料ID {item_in.material_id} 不存在")
        
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
    return get_bom_detail(db=db, bom_id=bom.id, current_user=current_user)


@router.get("/{bom_id}", response_model=BomResponse)
def get_bom_detail(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取BOM详情
    """
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    # 获取BOM明细
    items = []
    for item in bom.items.order_by(BomItem.item_no).all():
        items.append(BomItemResponse(
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
        ))
    
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


@router.put("/{bom_id}", response_model=BomResponse)
def update_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    bom_in: BomUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新BOM（仅草稿状态可更新）
    """
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    # 只有草稿状态才能更新
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能更新")
    
    update_data = bom_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bom, field, value)
    
    db.add(bom)
    db.commit()
    db.refresh(bom)
    
    return get_bom_detail(db=db, bom_id=bom.id, current_user=current_user)


@router.get("/{bom_id}/items", response_model=List[BomItemResponse])
def get_bom_items(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取BOM明细列表
    """
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    items = []
    for item in bom.items.order_by(BomItem.item_no).all():
        items.append(BomItemResponse(
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
        ))
    
    return items


@router.post("/{bom_id}/items", response_model=BomItemResponse)
def add_bom_item(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    item_in: BomItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加BOM明细
    """
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    # 只有草稿状态才能添加明细
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能添加明细")
    
    # 如果提供了物料ID，获取物料信息
    material = None
    if item_in.material_id:
        material = db.query(Material).filter(Material.id == item_in.material_id).first()
        if not material:
            raise HTTPException(status_code=404, detail=f"物料ID {item_in.material_id} 不存在")
    
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
        amount=item.amount or 0,
        source_type=item.source_type,
        required_date=item.required_date,
        purchased_qty=item.purchased_qty or 0,
        received_qty=item.received_qty or 0,
        is_key_item=item.is_key_item,
    )


@router.put("/items/{item_id}", response_model=BomItemResponse)
def update_bom_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    item_in: BomItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新BOM明细
    """
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
            raise HTTPException(status_code=404, detail=f"物料ID {item_in.material_id} 不存在")
    
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
    """
    删除BOM明细
    """
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


@router.post("/{bom_id}/release", response_model=BomResponse)
def release_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    change_note: Optional[str] = Query(None, description="变更说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发布BOM版本
    将BOM状态从DRAFT改为RELEASED，并标记为最新版本
    """
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    # 只有草稿状态才能发布
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能发布")
    
    # 检查是否有明细
    item_count = bom.items.count()
    if item_count == 0:
        raise HTTPException(status_code=400, detail="BOM没有明细，无法发布")
    
    # 将同一BOM编号的其他版本标记为非最新版本
    db.query(BomHeader).filter(
        BomHeader.bom_no == bom.bom_no,
        BomHeader.id != bom_id
    ).update({"is_latest": False})
    
    # 更新BOM状态和版本信息
    bom.status = "RELEASED"
    bom.is_latest = True
    bom.approved_by = current_user.id
    bom.approved_at = datetime.now()
    if change_note:
        bom.remark = change_note
    
    db.add(bom)
    
    # BOM发布时自动归集材料成本
    try:
        from app.services.cost_collection_service import CostCollectionService
        CostCollectionService.collect_from_bom(
            db, bom_id, created_by=current_user.id
        )
    except Exception as e:
        # 成本归集失败不影响BOM发布，只记录错误
        import logging
        logging.warning(f"BOM发布后成本归集失败：{str(e)}")
    
    # Issue 1.2: BOM发布后自动触发阶段流转检查（S4→S5）
    if bom.project_id:
        try:
            from app.services.status_transition_service import StatusTransitionService
            transition_service = StatusTransitionService(db)
            
            # 调用BOM发布完成处理
            transition_service.handle_bom_published(bom.project_id, bom.machine_id)
            
            # 检查是否可以自动推进阶段
            project = db.query(Project).filter(Project.id == bom.project_id).first()
            if project and project.stage == "S4":
                auto_transition_result = transition_service.check_auto_stage_transition(
                    bom.project_id,
                    auto_advance=True  # 自动推进
                )
                
                if auto_transition_result.get("auto_advanced"):
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"BOM发布后自动推进项目 {bom.project_id} 至 {auto_transition_result.get('target_stage')} 阶段")
        except Exception as e:
            # 自动流转失败不影响BOM发布，记录日志
            import logging
            logging.warning(f"BOM发布后自动阶段流转失败：{str(e)}", exc_info=True)
    
    db.commit()
    db.refresh(bom)
    
    return get_bom_detail(db=db, bom_id=bom.id, current_user=current_user)


@router.get("/{bom_id}/versions", response_model=List[BomResponse])
def get_bom_versions(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取BOM的所有版本列表
    基于BOM编号查找所有版本
    """
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    # 查找相同BOM编号的所有版本
    versions = (
        db.query(BomHeader)
        .filter(BomHeader.bom_no == bom.bom_no)
        .order_by(desc(BomHeader.created_at))
        .all()
    )
    
    result = []
    for version in versions:
        # 获取BOM明细数量（简化版，不加载完整明细）
        item_count = version.items.count()
        
        result.append(BomResponse(
            id=version.id,
            bom_no=version.bom_no,
            bom_name=version.bom_name,
            project_id=version.project_id,
            project_name=version.project.project_name if version.project else None,
            machine_id=version.machine_id,
            machine_name=version.machine.machine_name if version.machine else None,
            version=version.version,
            is_latest=version.is_latest,
            status=version.status,
            total_items=version.total_items,
            total_amount=version.total_amount or 0,
            items=[],  # 版本列表不包含明细，需要时调用详情接口
            created_at=version.created_at,
            updated_at=version.updated_at,
        ))
    
    return result


@router.get("/{bom_id}/versions/compare", response_model=dict)
def compare_bom_versions(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    version1_id: Optional[int] = Query(None, description="版本1的BOM ID"),
    version2_id: Optional[int] = Query(None, description="版本2的BOM ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    对比BOM的两个版本
    如果不提供version1_id和version2_id，则对比当前版本和最新发布版本
    """
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
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
                BomHeader.is_latest == True
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
            deleted.append({
                "material_code": material_code,
                "material_name": items1[material_code].material_name,
                "quantity": float(items1[material_code].quantity),
                "unit_price": float(items1[material_code].unit_price) if items1[material_code].unit_price else 0,
            })
        elif material_code not in items1 and material_code in items2:
            added.append({
                "material_code": material_code,
                "material_name": items2[material_code].material_name,
                "quantity": float(items2[material_code].quantity),
                "unit_price": float(items2[material_code].unit_price) if items2[material_code].unit_price else 0,
            })
        else:
            item1 = items1[material_code]
            item2 = items2[material_code]
            if (item1.quantity != item2.quantity or 
                item1.unit_price != item2.unit_price or
                item1.specification != item2.specification):
                modified.append({
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
                })
            else:
                unchanged.append({
                    "material_code": material_code,
                    "material_name": item1.material_name,
                    "quantity": float(item1.quantity),
                })
    
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
            }
        }
    }


@router.post("/{bom_id}/import", response_model=ResponseModel)
async def import_bom_from_excel(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从Excel导入BOM明细
    支持格式：物料编码、物料名称、规格型号、数量、单价、单位等
    """
    if not EXCEL_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Excel处理库未安装，请安装pandas和openpyxl"
        )
    
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    # 只有草稿状态才能导入
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能导入")
    
    try:
        # 读取Excel文件
        file_content = await file.read()
        df = pd.read_excel(io.BytesIO(file_content))
        
        # 验证必需的列
        required_columns = ['物料编码', '物料名称', '数量']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
            )
        
        # 清空现有明细（可选，也可以追加）
        # db.query(BomItem).filter(BomItem.bom_id == bom_id).delete()
        
        # 导入明细
        imported_count = 0
        error_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                material_code = str(row.get('物料编码', '')).strip()
                material_name = str(row.get('物料名称', '')).strip()
                quantity = float(row.get('数量', 0))
                
                if not material_code or not material_name or quantity <= 0:
                    error_count += 1
                    errors.append(f"第{idx+2}行：数据不完整或数量无效")
                    continue
                
                # 尝试查找物料
                material = db.query(Material).filter(Material.material_code == material_code).first()
                material_id = material.id if material else None
                
                # 获取当前最大行号
                max_item = (
                    db.query(BomItem)
                    .filter(BomItem.bom_id == bom_id)
                    .order_by(desc(BomItem.item_no))
                    .first()
                )
                item_no = (max_item.item_no + 1) if max_item else imported_count + 1
                
                # 获取其他字段
                specification = str(row.get('规格型号', '')).strip() if pd.notna(row.get('规格型号')) else None
                unit = str(row.get('单位', '件')).strip() if pd.notna(row.get('单位')) else '件'
                unit_price = float(row.get('单价', 0)) if pd.notna(row.get('单价')) else 0
                amount = quantity * unit_price
                
                # 创建BOM明细
                item = BomItem(
                    bom_id=bom_id,
                    item_no=item_no,
                    material_id=material_id,
                    material_code=material_code,
                    material_name=material_name,
                    specification=specification,
                    unit=unit,
                    quantity=Decimal(str(quantity)),
                    unit_price=Decimal(str(unit_price)),
                    amount=Decimal(str(amount)),
                    source_type=row.get('来源类型', 'PURCHASE') if pd.notna(row.get('来源类型')) else 'PURCHASE',
                    is_key_item=bool(row.get('是否关键', False)) if pd.notna(row.get('是否关键')) else False,
                )
                db.add(item)
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"第{idx+2}行：{str(e)}")
        
        # 更新BOM统计
        bom.total_items = bom.items.count()
        total_amount = db.query(func.sum(BomItem.amount)).filter(BomItem.bom_id == bom_id).scalar() or 0
        bom.total_amount = total_amount
        
        db.commit()
        
        return ResponseModel(
            code=200,
            message=f"导入完成：成功{imported_count}条，失败{error_count}条",
            data={
                "imported_count": imported_count,
                "error_count": error_count,
                "errors": errors[:10] if errors else []  # 只返回前10个错误
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"导入失败：{str(e)}")


@router.get("/{bom_id}/export")
def export_bom_to_excel(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    导出BOM明细到Excel
    """
    if not EXCEL_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Excel处理库未安装，请安装pandas和openpyxl"
        )
    
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    # 获取BOM明细
    items = bom.items.order_by(BomItem.item_no).all()
    
    # 构建DataFrame
    data = []
    for item in items:
        data.append({
            '行号': item.item_no,
            '物料编码': item.material_code,
            '物料名称': item.material_name,
            '规格型号': item.specification or '',
            '图号': item.drawing_no or '',
            '单位': item.unit,
            '数量': float(item.quantity),
            '单价': float(item.unit_price) if item.unit_price else 0,
            '金额': float(item.amount) if item.amount else 0,
            '来源类型': item.source_type,
            '需求日期': item.required_date.strftime('%Y-%m-%d') if item.required_date else '',
            '已采购数量': float(item.purchased_qty) if item.purchased_qty else 0,
            '已到货数量': float(item.received_qty) if item.received_qty else 0,
            '是否关键': '是' if item.is_key_item else '否',
            '备注': item.remark or '',
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='BOM明细', index=False)
        
        # 设置列宽
        worksheet = writer.sheets['BOM明细']
        column_widths = {
            'A': 8,   # 行号
            'B': 15,  # 物料编码
            'C': 30,  # 物料名称
            'D': 20,  # 规格型号
            'E': 15,  # 图号
            'F': 8,   # 单位
            'G': 10,  # 数量
            'H': 12,  # 单价
            'I': 12,  # 金额
            'J': 12,  # 来源类型
            'K': 12,  # 需求日期
            'L': 12,  # 已采购数量
            'M': 12,  # 已到货数量
            'N': 10,  # 是否关键
            'O': 30,  # 备注
        }
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width
    
    output.seek(0)
    
    # 生成文件名
    filename = f"BOM_{bom.bom_no}_v{bom.version}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/template/download")
def download_bom_import_template(
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载BOM导入模板
    """
    if not EXCEL_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Excel处理库未安装，请安装pandas和openpyxl"
        )
    
    # 创建模板DataFrame
    template_data = {
        '物料编码': ['MAT-001', 'MAT-002'],
        '物料名称': ['示例物料1', '示例物料2'],
        '规格型号': ['规格1', '规格2'],
        '单位': ['件', '件'],
        '数量': [10, 20],
        '单价': [1.5, 2.0],
        '来源类型': ['PURCHASE', 'PURCHASE'],
        '是否关键': [False, True],
        '备注': ['', ''],
    }
    
    df = pd.DataFrame(template_data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='BOM明细', index=False)
        
        # 设置列宽
        worksheet = writer.sheets['BOM明细']
        column_widths = {
            'A': 15,  # 物料编码
            'B': 30,  # 物料名称
            'C': 20,  # 规格型号
            'D': 8,   # 单位
            'E': 10,  # 数量
            'F': 12,  # 单价
            'G': 12,  # 来源类型
            'H': 10,  # 是否关键
            'I': 30,  # 备注
        }
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=BOM导入模板.xlsx"}
    )


@router.post("/{bom_id}/generate-pr", response_model=ResponseModel)
def generate_purchase_request_from_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    supplier_id: Optional[int] = Query(None, description="默认供应商（可选）"),
    create_requests: bool = Query(True, description="是否直接创建采购申请"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    从BOM生成采购需求/采购申请
    """
    from collections import defaultdict
    from app.api.v1.endpoints.purchase import generate_request_no  # 避免循环导入

    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    bom_items = bom.items.filter(BomItem.source_type == "PURCHASE").all()
    if not bom_items:
        raise HTTPException(status_code=400, detail="BOM中没有需要采购的物料")
    
    supplier_items = defaultdict(list)
    for item in bom_items:
        target_supplier_id = supplier_id
        if not target_supplier_id and item.supplier_id:
            target_supplier_id = item.supplier_id
        elif not target_supplier_id and item.material_id:
            material = db.query(Material).filter(Material.id == item.material_id).first()
            if material and material.default_supplier_id:
                target_supplier_id = material.default_supplier_id
        
        if not target_supplier_id:
            target_supplier_id = 0
        
        supplier_items[target_supplier_id].append(item)
    
    purchase_requests = []
    created_requests = []
    
    for supplier_id_key, items in supplier_items.items():
        supplier_name = "未指定供应商"
        if supplier_id_key != 0:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id_key).first()
            supplier_name = supplier.supplier_name if supplier else f"供应商ID {supplier_id_key}"
        
        request_items = []
        total_amount = Decimal(0)
        
        for item in items:
            remaining_qty = (item.quantity or Decimal(0)) - (item.purchased_qty or Decimal(0))
            if remaining_qty <= 0:
                continue
            
            unit_price = item.unit_price or Decimal(0)
            amount = remaining_qty * unit_price
            total_amount += amount
            
            request_items.append({
                "bom_item_id": item.id,
                "material_id": item.material_id,
                "material_code": item.material_code,
                "material_name": item.material_name,
                "specification": item.specification,
                "unit": item.unit or "件",
                "quantity": remaining_qty,
                "unit_price": unit_price,
                "amount": amount,
                "required_date": item.required_date,
                "is_key_item": item.is_key_item,
            })
        
        if not request_items:
            continue
        
        formatted_items = []
        for it in request_items:
            formatted_items.append({
                "bom_item_id": it["bom_item_id"],
                "material_id": it["material_id"],
                "material_code": it["material_code"],
                "material_name": it["material_name"],
                "specification": it["specification"],
                "unit": it["unit"],
                "quantity": float(it["quantity"]),
                "unit_price": float(it["unit_price"]),
                "amount": float(it["amount"]),
                "required_date": it["required_date"].isoformat() if it["required_date"] else None,
                "is_key_item": it["is_key_item"],
            })
        
        purchase_requests.append({
            "supplier_id": supplier_id_key if supplier_id_key != 0 else None,
            "supplier_name": supplier_name,
            "items": formatted_items,
            "total_amount": float(total_amount),
            "item_count": len(formatted_items),
        })
        
        if create_requests:
            request_no = generate_request_no(db)
            pr = PurchaseRequest(
                request_no=request_no,
                project_id=bom.project_id,
                machine_id=bom.machine_id,
                supplier_id=supplier_id_key if supplier_id_key != 0 else None,
                request_type="NORMAL",
                source_type="BOM",
                source_id=bom.id,
                request_reason=f"来自BOM {bom.bom_no} 的采购需求",
                required_date=bom.required_date,
                status="DRAFT",
                total_amount=total_amount,
                created_by=current_user.id,
            )
            db.add(pr)
            db.flush()
            
            for it in request_items:
                pr_item = PurchaseRequestItem(
                    request_id=pr.id,
                    bom_item_id=it["bom_item_id"],
                    material_id=it["material_id"],
                    material_code=it["material_code"],
                    material_name=it["material_name"],
                    specification=it["specification"],
                    unit=it["unit"],
                    quantity=it["quantity"],
                    unit_price=it["unit_price"],
                    amount=it["amount"],
                    required_date=it["required_date"],
                )
                db.add(pr_item)
            
            created_requests.append({
                "request_id": pr.id,
                "request_no": pr.request_no,
                "supplier_id": pr.supplier_id,
                "supplier_name": supplier_name,
                "total_amount": float(total_amount),
                "item_count": len(request_items),
            })
    
    if create_requests and created_requests:
        db.commit()
    elif create_requests:
        db.rollback()
    
    return ResponseModel(
        code=200,
        message=f"已生成采购需求，共{len(purchase_requests)}个供应商",
        data={
            "bom_id": bom_id,
            "bom_no": bom.bom_no,
            "project_id": bom.project_id,
            "machine_id": bom.machine_id,
            "purchase_requests": purchase_requests,
            "created_requests": created_requests if create_requests else None,
            "summary": {
                "total_suppliers": len(purchase_requests),
                "total_items": sum(len(req["items"]) for req in purchase_requests),
                "total_amount": sum(req["total_amount"] for req in purchase_requests),
                "created_count": len(created_requests) if create_requests else 0,
            }
        }
    )
