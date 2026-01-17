# -*- coding: utf-8 -*-
"""
物料调拨 - 自动生成
从 shortage.py 拆分
"""

# -*- coding: utf-8 -*-
"""
缺料管理 API endpoints
包含：缺料上报、到货跟踪、物料替代、物料调拨、缺料统计
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import require_shortage_report_access
from app.models.machine import Machine
from app.models.material import Material
from app.models.project import Project
from app.models.purchase import PurchaseOrder
from app.models.shortage import (
    ArrivalFollowUp,
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageDailyReport,
    ShortageReport,
)
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.shortage import (
    ArrivalFollowUpCreate,
    ArrivalFollowUpResponse,
    MaterialArrivalCreate,
    MaterialArrivalResponse,
    MaterialSubstitutionCreate,
    MaterialSubstitutionResponse,
    MaterialTransferCreate,
    MaterialTransferResponse,
    ShortageReportCreate,
    ShortageReportResponse,
)

router = APIRouter()


def _build_shortage_daily_report(report: ShortageDailyReport) -> Dict[str, Any]:
    """序列化缺料日报"""
    return {
        "date": report.report_date.isoformat(),
        "alerts": {
            "new": report.new_alerts,
            "resolved": report.resolved_alerts,
            "pending": report.pending_alerts,
            "overdue": report.overdue_alerts,
            "levels": {
                "level1": report.level1_count,
                "level2": report.level2_count,
                "level3": report.level3_count,
                "level4": report.level4_count,
            }
        },
        "reports": {
            "new": report.new_reports,
            "resolved": report.resolved_reports,
        },
        "kit": {
            "total_work_orders": report.total_work_orders,
            "complete_count": report.kit_complete_count,
            "kit_rate": float(report.kit_rate) if report.kit_rate else 0.0,
        },
        "arrivals": {
            "expected": report.expected_arrivals,
            "actual": report.actual_arrivals,
            "delayed": report.delayed_arrivals,
            "on_time_rate": float(report.on_time_rate) if report.on_time_rate else 0.0,
        },
        "response": {
            "avg_response_minutes": report.avg_response_minutes,
            "avg_resolve_hours": float(report.avg_resolve_hours) if report.avg_resolve_hours else 0.0,
        },
        "stoppage": {
            "count": report.stoppage_count,
            "hours": float(report.stoppage_hours) if report.stoppage_hours else 0.0,
        },
    }


def generate_report_no(db: Session) -> str:
    """生成缺料上报单号：SR-yymmdd-xxx"""
    from app.models.shortage import ShortageReport
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=ShortageReport,
        no_field='report_no',
        prefix='SR',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_arrival_no(db: Session) -> str:
    """生成到货跟踪单号：ARR-yymmdd-xxx"""
    from app.models.shortage import MaterialArrival
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialArrival,
        no_field='arrival_no',
        prefix='ARR',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_substitution_no(db: Session) -> str:
    """生成替代单号：SUB-yymmdd-xxx"""
    from app.models.shortage import MaterialSubstitution
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialSubstitution,
        no_field='substitution_no',
        prefix='SUB',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_transfer_no(db: Session) -> str:
    """生成调拨单号：TRF-yymmdd-xxx"""
    from app.models.shortage import MaterialTransfer
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialTransfer,
        no_field='transfer_no',
        prefix='TRF',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )




from fastapi import APIRouter

router = APIRouter(
    prefix="/shortage/transfers",
    tags=["transfers"]
)

# 共 5 个路由

# ==================== 物料调拨 ====================

@router.get("/shortage/transfers", response_model=PaginatedResponse)
def read_transfers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（调拨单号/物料编码）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    from_project_id: Optional[int] = Query(None, description="调出项目ID筛选"),
    to_project_id: Optional[int] = Query(None, description="调入项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    调拨申请列表
    """
    query = db.query(MaterialTransfer)

    if keyword:
        query = query.filter(
            or_(
                MaterialTransfer.transfer_no.like(f"%{keyword}%"),
                MaterialTransfer.material_code.like(f"%{keyword}%"),
            )
        )

    if status:
        query = query.filter(MaterialTransfer.status == status)

    if from_project_id:
        query = query.filter(MaterialTransfer.from_project_id == from_project_id)

    if to_project_id:
        query = query.filter(MaterialTransfer.to_project_id == to_project_id)

    total = query.count()
    offset = (page - 1) * page_size
    transfers = query.order_by(desc(MaterialTransfer.created_at)).offset(offset).limit(page_size).all()

    items = []
    for transfer in transfers:
        from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
        to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
        approver = db.query(User).filter(User.id == transfer.approver_id).first() if transfer.approver_id else None

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
            available_qty=transfer.available_qty,
            transfer_reason=transfer.transfer_reason,
            urgent_level=transfer.urgent_level,
            status=transfer.status,
            approver_id=transfer.approver_id,
            approver_name=approver.real_name or approver.username if approver else None,
            approved_at=transfer.approved_at,
            executed_at=transfer.executed_at,
            actual_qty=transfer.actual_qty,
            remark=transfer.remark,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/shortage/transfers/{transfer_id}", response_model=MaterialTransferResponse)
def read_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    调拨申请详情
    """
    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="调拨申请不存在")

    from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    approver = db.query(User).filter(User.id == transfer.approver_id).first() if transfer.approver_id else None

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
        available_qty=transfer.available_qty,
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=approver.real_name or approver.username if approver else None,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.post("/shortage/transfers", response_model=MaterialTransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_in: MaterialTransferCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建调拨申请
    """
    # 验证调入项目
    to_project = db.query(Project).filter(Project.id == transfer_in.to_project_id).first()
    if not to_project:
        raise HTTPException(status_code=404, detail="调入项目不存在")

    # 验证物料
    material = db.query(Material).filter(Material.id == transfer_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # Note: 检查可调拨数量需要与库存管理系统集成
    # 应查询from_project_id对应项目的可用库存（账面库存 - 已分配 - 安全库存）
    # 如果from_project_id为None，应从总库存中查询
    # 目前暂时设置为0，后续需要根据实际库存系统实现
    available_qty = Decimal("0")

    transfer = MaterialTransfer(
        transfer_no=generate_transfer_no(db),
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
        status='DRAFT',
        created_by=current_user.id,
        remark=transfer_in.remark
    )

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()

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
        available_qty=transfer.available_qty,
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=None,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.put("/shortage/transfers/{transfer_id}/approve", response_model=MaterialTransferResponse)
def approve_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    调拨审批
    """
    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="调拨申请不存在")

    if transfer.status not in ['DRAFT', 'PENDING']:
        raise HTTPException(status_code=400, detail="只有草稿或待审批状态的申请才能审批")

    if approved:
        transfer.status = 'APPROVED'
        transfer.approver_id = current_user.id
        transfer.approved_at = datetime.now()
        transfer.approval_note = approval_note
    else:
        transfer.status = 'REJECTED'
        transfer.approver_id = current_user.id
        transfer.approved_at = datetime.now()
        transfer.approval_note = approval_note

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    approver = db.query(User).filter(User.id == transfer.approver_id).first() if transfer.approver_id else None

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
        available_qty=transfer.available_qty,
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=approver.real_name or approver.username if approver else None,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.put("/shortage/transfers/{transfer_id}/execute", response_model=MaterialTransferResponse)
def execute_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    actual_qty: Decimal = Body(..., description="实际调拨数量"),
    execution_note: Optional[str] = Body(None, description="执行说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行调拨
    """
    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="调拨申请不存在")

    if transfer.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只有已批准的申请才能执行")

    transfer.status = 'EXECUTED'
    transfer.executed_at = datetime.now()
    transfer.executed_by = current_user.id
    transfer.actual_qty = actual_qty
    transfer.execution_note = execution_note

    # Note: 更新库存记录需要与库存管理系统集成
    # 应从from_project_id对应项目减少actual_qty数量的库存
    # 应向to_project_id对应项目增加actual_qty数量的库存
    # 如果from_project_id为None，应从总库存中减少

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    approver = db.query(User).filter(User.id == transfer.approver_id).first() if transfer.approver_id else None

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
        available_qty=transfer.available_qty,
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=approver.real_name or approver.username if approver else None,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )

