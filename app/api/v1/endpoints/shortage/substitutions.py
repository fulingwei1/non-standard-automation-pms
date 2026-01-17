# -*- coding: utf-8 -*-
"""
物料替代 - 自动生成
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
    prefix="/shortage/substitutions",
    tags=["substitutions"]
)

# 共 6 个路由

# ==================== 物料替代 ====================

@router.get("/shortage/substitutions", response_model=PaginatedResponse)
def read_substitutions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（替代单号/物料编码）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    替代申请列表
    """
    query = db.query(MaterialSubstitution)

    if keyword:
        query = query.filter(
            or_(
                MaterialSubstitution.substitution_no.like(f"%{keyword}%"),
                MaterialSubstitution.original_material_code.like(f"%{keyword}%"),
                MaterialSubstitution.substitute_material_code.like(f"%{keyword}%"),
            )
        )

    if status:
        query = query.filter(MaterialSubstitution.status == status)

    if project_id:
        query = query.filter(MaterialSubstitution.project_id == project_id)

    total = query.count()
    offset = (page - 1) * page_size
    substitutions = query.order_by(desc(MaterialSubstitution.created_at)).offset(offset).limit(page_size).all()

    items = []
    for sub in substitutions:
        project = db.query(Project).filter(Project.id == sub.project_id).first()
        tech_approver = db.query(User).filter(User.id == sub.tech_approver_id).first() if sub.tech_approver_id else None
        prod_approver = db.query(User).filter(User.id == sub.prod_approver_id).first() if sub.prod_approver_id else None

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
            cost_impact=sub.cost_impact,
            status=sub.status,
            tech_approver_id=sub.tech_approver_id,
            tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
            tech_approved_at=sub.tech_approved_at,
            prod_approver_id=sub.prod_approver_id,
            prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
            prod_approved_at=sub.prod_approved_at,
            executed_at=sub.executed_at,
            remark=sub.remark,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/shortage/substitutions/{substitution_id}", response_model=MaterialSubstitutionResponse)
def read_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    替代申请详情
    """
    substitution = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == substitution_id).first()
    if not substitution:
        raise HTTPException(status_code=404, detail="替代申请不存在")

    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    tech_approver = db.query(User).filter(User.id == substitution.tech_approver_id).first() if substitution.tech_approver_id else None
    prod_approver = db.query(User).filter(User.id == substitution.prod_approver_id).first() if substitution.prod_approver_id else None

    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


@router.post("/shortage/substitutions", response_model=MaterialSubstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_in: MaterialSubstitutionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建替代申请
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == substitution_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证物料
    original_material = db.query(Material).filter(Material.id == substitution_in.original_material_id).first()
    if not original_material:
        raise HTTPException(status_code=404, detail="原物料不存在")

    substitute_material = db.query(Material).filter(Material.id == substitution_in.substitute_material_id).first()
    if not substitute_material:
        raise HTTPException(status_code=404, detail="替代物料不存在")

    substitution = MaterialSubstitution(
        substitution_no=generate_substitution_no(db),
        shortage_report_id=substitution_in.shortage_report_id,
        project_id=substitution_in.project_id,
        bom_item_id=substitution_in.bom_item_id,
        original_material_id=substitution_in.original_material_id,
        original_material_code=original_material.material_code,
        original_material_name=original_material.material_name,
        original_qty=substitution_in.original_qty,
        substitute_material_id=substitution_in.substitute_material_id,
        substitute_material_code=substitute_material.material_code,
        substitute_material_name=substitute_material.material_name,
        substitute_qty=substitution_in.substitute_qty,
        substitution_reason=substitution_in.substitution_reason,
        technical_impact=substitution_in.technical_impact,
        cost_impact=substitution_in.cost_impact,
        status='DRAFT',
        created_by=current_user.id,
        remark=substitution_in.remark
    )

    db.add(substitution)
    db.commit()
    db.refresh(substitution)

    project = db.query(Project).filter(Project.id == substitution.project_id).first()

    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


@router.put("/shortage/substitutions/{substitution_id}/tech-approve", response_model=MaterialSubstitutionResponse)
def tech_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    技术审批
    """
    substitution = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == substitution_id).first()
    if not substitution:
        raise HTTPException(status_code=404, detail="替代申请不存在")

    if substitution.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只有草稿状态的申请才能进行技术审批")

    if approved:
        substitution.status = 'TECH_APPROVED'
        substitution.tech_approver_id = current_user.id
        substitution.tech_approved_at = datetime.now()
        substitution.tech_approval_note = approval_note
        # 转为生产审批状态
        substitution.status = 'PROD_PENDING'
    else:
        substitution.status = 'REJECTED'
        substitution.tech_approver_id = current_user.id
        substitution.tech_approved_at = datetime.now()
        substitution.tech_approval_note = approval_note

    db.add(substitution)
    db.commit()
    db.refresh(substitution)

    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    tech_approver = db.query(User).filter(User.id == substitution.tech_approver_id).first() if substitution.tech_approver_id else None

    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


@router.put("/shortage/substitutions/{substitution_id}/prod-approve", response_model=MaterialSubstitutionResponse)
def prod_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生产审批
    """
    substitution = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == substitution_id).first()
    if not substitution:
        raise HTTPException(status_code=404, detail="替代申请不存在")

    if substitution.status != 'PROD_PENDING':
        raise HTTPException(status_code=400, detail="只有待生产审批状态的申请才能进行生产审批")

    if approved:
        substitution.status = 'APPROVED'
        substitution.prod_approver_id = current_user.id
        substitution.prod_approved_at = datetime.now()
        substitution.prod_approval_note = approval_note
    else:
        substitution.status = 'REJECTED'
        substitution.prod_approver_id = current_user.id
        substitution.prod_approved_at = datetime.now()
        substitution.prod_approval_note = approval_note

    db.add(substitution)
    db.commit()
    db.refresh(substitution)

    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    tech_approver = db.query(User).filter(User.id == substitution.tech_approver_id).first() if substitution.tech_approver_id else None
    prod_approver = db.query(User).filter(User.id == substitution.prod_approver_id).first() if substitution.prod_approver_id else None

    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


@router.put("/shortage/substitutions/{substitution_id}/execute", response_model=MaterialSubstitutionResponse)
def execute_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    execution_note: Optional[str] = Body(None, description="执行说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行替代
    """
    substitution = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == substitution_id).first()
    if not substitution:
        raise HTTPException(status_code=404, detail="替代申请不存在")

    if substitution.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只有已批准的申请才能执行")

    substitution.status = 'EXECUTED'
    substitution.executed_at = datetime.now()
    substitution.executed_by = current_user.id
    substitution.execution_note = execution_note

    # Note: 更新BOM或库存记录需要与BOM管理和库存管理系统集成
    # 如果substitution.bom_item_id存在，应更新对应BOM项的物料信息
    # 如果存在库存系统，应更新库存记录（减少原物料，增加替代物料）

    db.add(substitution)
    db.commit()
    db.refresh(substitution)

    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    tech_approver = db.query(User).filter(User.id == substitution.tech_approver_id).first() if substitution.tech_approver_id else None
    prod_approver = db.query(User).filter(User.id == substitution.prod_approver_id).first() if substitution.prod_approver_id else None

    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )

