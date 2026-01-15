# -*- coding: utf-8 -*-
"""
物料替代 - 自动生成
从 shortage_alerts.py 拆分
"""

from typing import Any, List, Optional

from datetime import date, datetime

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from sqlalchemy.orm import Session

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.material import MaterialShortage, Material, BomItem

from app.models.project import Project, Machine

from app.models.shortage import (
    ShortageReport,
    MaterialArrival,
    ArrivalFollowUp,
    MaterialSubstitution,
    MaterialTransfer,
)
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.production import WorkOrder
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.shortage import (
    ShortageReportCreate,
    ShortageReportResponse,
    ShortageReportListResponse,
    MaterialArrivalResponse,
    MaterialArrivalListResponse,
    ArrivalFollowUpCreate,
    MaterialSubstitutionCreate,
    MaterialSubstitutionResponse,
    MaterialSubstitutionListResponse,
    MaterialTransferCreate,
    MaterialTransferResponse,
    MaterialTransferListResponse,
)

router = APIRouter(tags=["substitutions"])

# 共 6 个路由

@router.get("/substitutions", response_model=PaginatedResponse, status_code=200)
def read_material_substitutions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    替代申请列表
    """
    query = db.query(MaterialSubstitution)
    
    if project_id:
        query = query.filter(MaterialSubstitution.project_id == project_id)
    if status:
        query = query.filter(MaterialSubstitution.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    substitutions = query.order_by(desc(MaterialSubstitution.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for sub in substitutions:
        project = db.query(Project).filter(Project.id == sub.project_id).first()
        tech_approver_name = None
        if sub.tech_approver_id:
            tech_approver = db.query(User).filter(User.id == sub.tech_approver_id).first()
            tech_approver_name = tech_approver.real_name or tech_approver.username if tech_approver else None
        prod_approver_name = None
        if sub.prod_approver_id:
            prod_approver = db.query(User).filter(User.id == sub.prod_approver_id).first()
            prod_approver_name = prod_approver.real_name or prod_approver.username if prod_approver else None
        
        items.append(MaterialSubstitutionResponse(
            id=sub.id,
            substitution_no=sub.substitution_no,
            project_id=sub.project_id,
            project_name=project.project_name if project else None,
            original_material_id=sub.original_material_id,
            original_material_code=sub.original_material_code,
            original_material_name=sub.original_material_name,
            original_qty=sub.original_qty,
            substitute_material_id=sub.substitute_material_id,
            substitute_material_code=sub.substitute_material_code,
            substitute_material_name=sub.substitute_material_name,
            substitute_qty=sub.substitute_qty,
            substitution_reason=sub.substitution_reason,
            technical_impact=sub.technical_impact,
            cost_impact=sub.cost_impact or Decimal("0"),
            status=sub.status,
            tech_approver_id=sub.tech_approver_id,
            tech_approver_name=tech_approver_name,
            tech_approved_at=sub.tech_approved_at,
            prod_approver_id=sub.prod_approver_id,
            prod_approver_name=prod_approver_name,
            prod_approved_at=sub.prod_approved_at,
            executed_at=sub.executed_at,
            remark=sub.remark,
            created_at=sub.created_at,
            updated_at=sub.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/substitutions", response_model=MaterialSubstitutionResponse, status_code=201)
def create_material_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_in: MaterialSubstitutionCreate,
    current_user: User = Depends(security.require_permission("shortage_alert:create")),
) -> Any:
    """
    创建替代申请
    """
    project = db.query(Project).filter(Project.id == sub_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    original_material = db.query(Material).filter(Material.id == sub_in.original_material_id).first()
    if not original_material:
        raise HTTPException(status_code=404, detail="原物料不存在")
    
    substitute_material = db.query(Material).filter(Material.id == sub_in.substitute_material_id).first()
    if not substitute_material:
        raise HTTPException(status_code=404, detail="替代物料不存在")
    
    if sub_in.original_material_id == sub_in.substitute_material_id:
        raise HTTPException(status_code=400, detail="原物料和替代物料不能相同")
    
    substitution_no = generate_substitution_no(db)
    
    substitution = MaterialSubstitution(
        substitution_no=substitution_no,
        shortage_report_id=sub_in.shortage_report_id,
        project_id=sub_in.project_id,
        bom_item_id=sub_in.bom_item_id,
        original_material_id=sub_in.original_material_id,
        original_material_code=original_material.material_code,
        original_material_name=original_material.material_name,
        original_qty=sub_in.original_qty,
        substitute_material_id=sub_in.substitute_material_id,
        substitute_material_code=substitute_material.material_code,
        substitute_material_name=substitute_material.material_name,
        substitute_qty=sub_in.substitute_qty,
        substitution_reason=sub_in.substitution_reason,
        technical_impact=sub_in.technical_impact,
        cost_impact=sub_in.cost_impact or Decimal("0"),
        status="DRAFT",
        created_by=current_user.id,
        remark=sub_in.remark
    )
    
    db.add(substitution)
    db.commit()
    db.refresh(substitution)
    
    return read_material_substitution(substitution.id, db, current_user)


@router.get("/substitutions/{sub_id}", response_model=MaterialSubstitutionResponse, status_code=200)
def read_material_substitution(
    sub_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    物料替代详情
    """
    sub = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="物料替代不存在")
    
    project = db.query(Project).filter(Project.id == sub.project_id).first()
    tech_approver_name = None
    if sub.tech_approver_id:
        tech_approver = db.query(User).filter(User.id == sub.tech_approver_id).first()
        tech_approver_name = tech_approver.real_name or tech_approver.username if tech_approver else None
    prod_approver_name = None
    if sub.prod_approver_id:
        prod_approver = db.query(User).filter(User.id == sub.prod_approver_id).first()
        prod_approver_name = prod_approver.real_name or prod_approver.username if prod_approver else None
    
    return MaterialSubstitutionResponse(
        id=sub.id,
        substitution_no=sub.substitution_no,
        project_id=sub.project_id,
        project_name=project.project_name if project else None,
        original_material_id=sub.original_material_id,
        original_material_code=sub.original_material_code,
        original_material_name=sub.original_material_name,
        original_qty=sub.original_qty,
        substitute_material_id=sub.substitute_material_id,
        substitute_material_code=sub.substitute_material_code,
        substitute_material_name=sub.substitute_material_name,
        substitute_qty=sub.substitute_qty,
        substitution_reason=sub.substitution_reason,
        technical_impact=sub.technical_impact,
        cost_impact=sub.cost_impact or Decimal("0"),
        status=sub.status,
        tech_approver_id=sub.tech_approver_id,
        tech_approver_name=tech_approver_name,
        tech_approved_at=sub.tech_approved_at,
        prod_approver_id=sub.prod_approver_id,
        prod_approver_name=prod_approver_name,
        prod_approved_at=sub.prod_approved_at,
        executed_at=sub.executed_at,
        remark=sub.remark,
        created_at=sub.created_at,
        updated_at=sub.updated_at
    )


@router.put("/substitutions/{sub_id}/tech-approve", response_model=MaterialSubstitutionResponse, status_code=200)
def tech_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_id: int,
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    技术审批
    """
    sub = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="物料替代不存在")
    
    if sub.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能审批草稿状态的替代申请")
    
    sub.status = "TECH_PENDING"
    sub.tech_approver_id = current_user.id
    sub.tech_approved_at = datetime.now()
    sub.tech_approval_note = approval_note
    
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return read_material_substitution(sub_id, db, current_user)


@router.put("/substitutions/{sub_id}/prod-approve", response_model=MaterialSubstitutionResponse, status_code=200)
def prod_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_id: int,
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    生产审批
    """
    sub = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="物料替代不存在")
    
    if sub.status != "TECH_PENDING":
        raise HTTPException(status_code=400, detail="只能审批技术已审批状态的替代申请")
    
    sub.status = "PROD_PENDING"
    sub.prod_approver_id = current_user.id
    sub.prod_approved_at = datetime.now()
    sub.prod_approval_note = approval_note
    
    # 如果技术审批和生产审批都完成，自动更新为已审批
    if sub.tech_approved_at and sub.prod_approved_at:
        sub.status = "APPROVED"
    
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return read_material_substitution(sub_id, db, current_user)


@router.put("/substitutions/{sub_id}/execute", response_model=MaterialSubstitutionResponse, status_code=200)
def execute_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_id: int,
    execution_note: Optional[str] = Query(None, description="执行说明"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    执行替代
    """
    sub = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="物料替代不存在")

    if sub.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只能执行已审批状态的替代申请")

    sub.status = "EXECUTED"
    sub.executed_at = datetime.now()
    sub.executed_by = current_user.id
    sub.execution_note = execution_note

    # 更新BOM中的物料信息
    if sub.bom_item_id:
        from app.models.material import BomItem
        bom_item = db.query(BomItem).filter(BomItem.id == sub.bom_item_id).first()
        if bom_item:
            # 记录原物料信息
            old_material_id = bom_item.material_id
            old_material_code = bom_item.material_code

            # 更新为替代物料
            bom_item.material_id = sub.substitute_material_id
            bom_item.material_code = sub.substitute_material_code
            bom_item.material_name = sub.substitute_material_name
            # 更新替代物料的价格
            bom_item.unit_price = sub.substitute_unit_price or bom_item.unit_price

            db.add(bom_item)

            # 记录物料变更历史
            from app.models.material import MaterialChangeHistory
            try:
                change_history = MaterialChangeHistory(
                    bom_item_id=sub.bom_item_id,
                    change_type="SUBSTITUTION",
                    old_material_id=old_material_id,
                    old_material_code=old_material_code,
                    new_material_id=sub.substitute_material_id,
                    new_material_code=sub.substitute_material_code,
                    change_reason=sub.substitute_reason or "物料替代",
                    changed_by=current_user.id,
                    substitution_id=sub.id
                )
                db.add(change_history)
            except Exception:
                # 历史表可能不存在，不影响主流程
                pass

    db.add(sub)
    db.commit()
    db.refresh(sub)

    # 发送通知
    from app.services.notification_service import notification_service, NotificationType, NotificationPriority
    try:
        # 通知项目物料员
        if sub.project_id:
            project = db.query(Project).filter(Project.id == sub.project_id).first()
            if project and project.pm_id:
                notification_service.send_notification(
                    db=db,
                    recipient_id=project.pm_id,
                    notification_type=NotificationType.PROJECT_UPDATE,
                    title=f"物料替代已执行: {sub.original_material_name}",
                    content=f"替代物料: {sub.substitute_material_name}\n替代数量: {sub.substitute_qty}",
                    priority=NotificationPriority.NORMAL,
                    link=f"/shortage-alerts/substitutions/{sub.id}"
                )
    except Exception:
        pass

    return read_material_substitution(sub_id, db, current_user)


