# -*- coding: utf-8 -*-
"""
物料调拨 - 自动生成
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

router = APIRouter(tags=["transfers"])

# 共 8 个路由

@router.get("/transfers", response_model=PaginatedResponse, status_code=200)
def read_material_transfers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    from_project_id: Optional[int] = Query(None, description="调出项目ID筛选"),
    to_project_id: Optional[int] = Query(None, description="调入项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    调拨申请列表
    """
    query = db.query(MaterialTransfer)
    
    if from_project_id:
        query = query.filter(MaterialTransfer.from_project_id == from_project_id)
    if to_project_id:
        query = query.filter(MaterialTransfer.to_project_id == to_project_id)
    if status:
        query = query.filter(MaterialTransfer.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    transfers = query.order_by(desc(MaterialTransfer.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for transfer in transfers:
        from_project = None
        if transfer.from_project_id:
            from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
        to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
        approver_name = None
        if transfer.approver_id:
            approver = db.query(User).filter(User.id == transfer.approver_id).first()
            approver_name = approver.real_name or approver.username if approver else None
        
        items.append(MaterialTransferResponse(
            id=transfer.id,
            transfer_no=transfer.transfer_no,
            from_project_id=transfer.from_project_id,
            from_project_name=from_project.project_name if from_project else None,
            from_location=transfer.from_location,
            to_project_id=transfer.to_project_id,
            to_project_name=to_project.project_name if to_project else None,
            to_location=transfer.to_location,
            material_id=transfer.material_id,
            material_code=transfer.material_code,
            material_name=transfer.material_name,
            transfer_qty=transfer.transfer_qty,
            available_qty=transfer.available_qty or Decimal("0"),
            transfer_reason=transfer.transfer_reason,
            urgent_level=transfer.urgent_level,
            status=transfer.status,
            approver_id=transfer.approver_id,
            approver_name=approver_name,
            approved_at=transfer.approved_at,
            executed_at=transfer.executed_at,
            actual_qty=transfer.actual_qty,
            remark=transfer.remark,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/transfers", response_model=MaterialTransferResponse, status_code=201)
def create_material_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_in: MaterialTransferCreate,
    current_user: User = Depends(security.require_permission("shortage_alert:create")),
) -> Any:
    """
    创建调拨申请
    """
    to_project = db.query(Project).filter(Project.id == transfer_in.to_project_id).first()
    if not to_project:
        raise HTTPException(status_code=404, detail="调入项目不存在")
    
    if transfer_in.from_project_id:
        from_project = db.query(Project).filter(Project.id == transfer_in.from_project_id).first()
        if not from_project:
            raise HTTPException(status_code=404, detail="调出项目不存在")
    
    material = db.query(Material).filter(Material.id == transfer_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    # 检查可调拨数量（从调出项目的库存）
    available_qty = Decimal("0")
    if transfer_in.from_project_id:
        # 查询调出项目的物料库存
        from app.services.material_transfer_service import material_transfer_service
        stock_info = material_transfer_service.get_project_material_stock(
            db, transfer_in.from_project_id, transfer_in.material_id
        )
        available_qty = stock_info["available_qty"]

    if transfer_in.transfer_qty > available_qty:
        raise HTTPException(status_code=400, detail=f"可调拨数量不足，当前可用：{available_qty}（来源：{stock_info.get('source', '未知')}）")
    
    transfer_no = generate_transfer_no(db)
    
    transfer = MaterialTransfer(
        transfer_no=transfer_no,
        shortage_report_id=transfer_in.shortage_report_id,
        from_project_id=transfer_in.from_project_id,
        from_location=transfer_in.from_location,
        to_project_id=transfer_in.to_project_id,
        to_location=transfer_in.to_location,
        material_id=transfer_in.material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        transfer_qty=transfer_in.transfer_qty,
        available_qty=available_qty,
        transfer_reason=transfer_in.transfer_reason,
        urgent_level=transfer_in.urgent_level,
        status="DRAFT",
        created_by=current_user.id,
        remark=transfer_in.remark
    )
    
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    
    return read_material_transfer(transfer.id, db, current_user)


@router.get("/transfers/{transfer_id}", response_model=MaterialTransferResponse, status_code=200)
def read_material_transfer(
    transfer_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    物料调拨详情
    """
    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")
    
    from_project = None
    if transfer.from_project_id:
        from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    approver_name = None
    if transfer.approver_id:
        approver = db.query(User).filter(User.id == transfer.approver_id).first()
        approver_name = approver.real_name or approver.username if approver else None
    
    return MaterialTransferResponse(
        id=transfer.id,
        transfer_no=transfer.transfer_no,
        from_project_id=transfer.from_project_id,
        from_project_name=from_project.project_name if from_project else None,
        from_location=transfer.from_location,
        to_project_id=transfer.to_project_id,
        to_project_name=to_project.project_name if to_project else None,
        to_location=transfer.to_location,
        material_id=transfer.material_id,
        material_code=transfer.material_code,
        material_name=transfer.material_name,
        transfer_qty=transfer.transfer_qty,
        available_qty=transfer.available_qty or Decimal("0"),
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=approver_name,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at
    )


@router.put("/transfers/{transfer_id}/approve", response_model=MaterialTransferResponse, status_code=200)
def approve_material_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    调拨审批
    """
    from app.services.material_transfer_service import material_transfer_service
    from app.services.notification_service import notification_service, NotificationType, NotificationPriority

    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")

    if transfer.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能审批草稿状态的调拨申请")

    # 执行前校验（确保调拨后库存足够）
    validation = material_transfer_service.validate_transfer_before_execute(db, transfer)
    if not validation["is_valid"]:
        raise HTTPException(status_code=400, detail="; ".join(validation["errors"]))

    transfer.status = "APPROVED"
    transfer.approver_id = current_user.id
    transfer.approved_at = datetime.now()
    transfer.approval_note = approval_note

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # 发送审批通过通知
    try:
        notification_service.send_notification(
            db=db,
            recipient_id=transfer.created_by,
            notification_type=NotificationType.TASK_APPROVED,
            title=f"物料调拨申请已批准: {transfer.material_name}",
            content=f"调拨单号: {transfer.transfer_no}\n审批人: {current_user.real_name or current_user.username}",
            priority=NotificationPriority.NORMAL,
            link="/shortage-alerts/transfers/{transfer_id}".format(transfer_id=transfer.id),
        )
    except Exception:
        pass

    # 如果有调出项目，也通知调出项目负责人
    if transfer.from_project_id:
        try:
            from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
            if from_project and from_project.pm_id:
                notification_service.send_notification(
                    db=db,
                    recipient_id=from_project.pm_id,
                    notification_type=NotificationType.TASK_ASSIGNED,
                    title=f"物料调出申请已批准: {transfer.material_name}",
                    content=f"调拨单号: {transfer.transfer_no}\n调入项目: {transfer.to_project_id}",
                    priority=NotificationPriority.HIGH,
                    link="/shortage-alerts/transfers/{transfer_id}".format(transfer_id=transfer.id)
                )
        except Exception:
            pass

    return read_material_transfer(transfer_id, db, current_user)


@router.put("/transfers/{transfer_id}/execute", response_model=MaterialTransferResponse, status_code=200)
def execute_material_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    actual_qty: Optional[Decimal] = Query(None, description="实际调拨数量"),
    execution_note: Optional[str] = Query(None, description="执行说明"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    执行调拨
    """
    from app.services.material_transfer_service import material_transfer_service

    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")

    if transfer.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只能执行已审批状态的调拨申请")

    # 执行前校验
    validation = material_transfer_service.validate_transfer_before_execute(db, transfer)
    if not validation["is_valid"]:
        raise HTTPException(status_code=400, detail="; ".join(validation["errors"]))

    # 更新状态和执行信息
    transfer.status = "EXECUTED"
    transfer.executed_at = datetime.now()
    transfer.executed_by = current_user.id
    transfer.actual_qty = actual_qty or transfer.transfer_qty
    transfer.execution_note = execution_note

    # 更新项目库存（从调出项目减少，调入项目增加）
    stock_updates = material_transfer_service.execute_stock_update(
        db, transfer, actual_qty
    )

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # 发送通知
    from app.services.notification_service import notification_service, NotificationType, NotificationPriority
    try:
        # 通知调入项目负责人
        notification_service.send_notification(
            db=db,
            recipient_id=transfer.created_by,
            notification_type=NotificationType.TASK_COMPLETED,
            title=f"物料调拨已完成: {transfer.material_name}",
            content=f"调拨单号: {transfer.transfer_no}\n实际调拨数量: {transfer.actual_qty}",
            priority=NotificationPriority.NORMAL,
            link="/shortage-alerts/transfers/{transfer_id}".format(transfer_id=transfer.id)
        )
    except Exception:
        pass

    result = read_material_transfer(transfer_id, db, current_user)
    # 添加库存更新信息
    result.stock_updates = stock_updates

    return result


@router.get("/transfers/suggest-sources", response_model=ResponseModel, status_code=200)
def suggest_transfer_sources(
    *,
    db: Session = Depends(deps.get_db),
    to_project_id: int = Query(..., description="调入项目ID"),
    material_id: int = Query(..., description="物料ID"),
    required_qty: Decimal = Query(..., description="需要数量"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    推荐物料调拨来源

    根据需要的物料和数量，推荐有库存的项目或仓库
    """
    from app.services.material_transfer_service import material_transfer_service

    suggestions = material_transfer_service.suggest_transfer_sources(
        db, to_project_id, material_id, required_qty
    )

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "to_project_id": to_project_id,
            "material_id": material_id,
            "required_qty": float(required_qty),
            "suggestions": suggestions,
            "total_sources": len(suggestions),
            "can_fully_supply": sum(1 for s in suggestions if s["can_fully_supply"])
        }
    )


@router.get("/transfers/{transfer_id}/stock-check", response_model=ResponseModel, status_code=200)
def check_transfer_stock(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    检查调拨单的库存状态

    返回调出项目的当前可用库存，用于确认是否可以执行调拨
    """
    from app.services.material_transfer_service import material_transfer_service

    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")

    if not transfer.from_project_id:
        return ResponseModel(
            code=200,
            message="无调出项目（从仓库调拨）",
            data={"from_project": None, "stock_info": None}
        )

    stock_info = material_transfer_service.get_project_material_stock(
        db, transfer.from_project_id, transfer.material_id
    )

    check_result = material_transfer_service.check_transfer_available(
        db,
        transfer.from_project_id,
        transfer.material_id,
        transfer.transfer_qty
    )

    return ResponseModel(
        code=200,
        message="库存检查完成",
        data={
            "from_project_id": transfer.from_project_id,
            "material_id": transfer.material_id,
            "material_code": transfer.material_code,
            "material_name": transfer.material_name,
            "stock_info": stock_info,
            "transfer_qty": float(transfer.transfer_qty),
            "check_result": check_result
        }
    )


@router.put("/transfers/{transfer_id}/reject", response_model=MaterialTransferResponse, status_code=200)
def reject_material_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    驳回调拨申请
    """
    from app.services.notification_service import notification_service, NotificationType, NotificationPriority

    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")

    if transfer.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能驳回草稿状态的调拨申请")

    transfer.status = "REJECTED"
    transfer.approver_id = current_user.id
    transfer.approved_at = datetime.now()
    transfer.approval_note = rejection_reason

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # 发送驳回通知
    try:
        notification_service.send_notification(
            db=db,
            recipient_id=transfer.created_by,
            notification_type=NotificationType.TASK_REJECTED,
            title=f"物料调拨申请已驳回: {transfer.material_name}",
            content=f"调拨单号: {transfer.transfer_no}\n驳回原因: {rejection_reason}",
            priority=NotificationPriority.HIGH,
            link="/shortage-alerts/transfers/{transfer_id}".format(transfer_id=transfer.id)
        )
    except Exception:
        pass

    return read_material_transfer(transfer_id, db, current_user)
