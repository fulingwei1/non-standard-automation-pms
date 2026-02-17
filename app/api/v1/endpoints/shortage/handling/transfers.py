# -*- coding: utf-8 -*-
"""
物料调拨 - transfers.py

合并来源:
- app/api/v1/endpoints/shortage/transfers/crud.py
- app/api/v1/endpoints/shortage/transfers/operations.py
- app/api/v1/endpoints/shortage/transfers/utils.py
- app/api/v1/endpoints/shortage_alerts/transfers/crud.py

路由:
- GET    /                          调拨列表
- POST   /                          创建调拨
- GET    /{id}                      调拨详情
- PUT    /{id}/approve              审批
- PUT    /{id}/execute              执行
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.material import Material
from app.models.project import Project
from app.models.shortage import MaterialTransfer
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.shortage import MaterialTransferCreate, MaterialTransferResponse
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


# ============================================================
# 工具函数
# ============================================================

def _generate_transfer_no(db: Session) -> str:
    """生成调拨单号：TRF-yymmdd-xxx"""
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


def _build_transfer_response(transfer: MaterialTransfer, db: Session) -> MaterialTransferResponse:
    """构建调拨响应对象"""
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


# ============================================================
# CRUD 操作
# ============================================================

@router.get("", response_model=PaginatedResponse)
def list_transfers(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（调拨单号/物料编码）"),
    transfer_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    from_project_id: Optional[int] = Query(None, description="调出项目ID筛选"),
    to_project_id: Optional[int] = Query(None, description="调入项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """调拨申请列表"""
    query = db.query(MaterialTransfer)

    # 应用关键词过滤（调拨单号/物料编码）
    query = apply_keyword_filter(query, MaterialTransfer, keyword, ["transfer_no", "material_code"])

    if transfer_status:
        query = query.filter(MaterialTransfer.status == transfer_status)
    if from_project_id:
        query = query.filter(MaterialTransfer.from_project_id == from_project_id)
    if to_project_id:
        query = query.filter(MaterialTransfer.to_project_id == to_project_id)

    total = query.count()
    transfers = apply_pagination(query.order_by(desc(MaterialTransfer.created_at)), pagination.offset, pagination.limit).all()

    items = [_build_transfer_response(transfer, db) for transfer in transfers]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("", response_model=MaterialTransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_in: MaterialTransferCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建调拨申请"""
    # 验证调入项目
    to_project = get_or_404(db, Project, transfer_in.to_project_id, "调入项目不存在")

    # 验证调出项目（如果有）
    if transfer_in.from_project_id:
        from_project = get_or_404(db, Project, transfer_in.from_project_id, "调出项目不存在")

    # 验证物料
    material = get_or_404(db, Material, transfer_in.material_id, "物料不存在")

    # 检查可调拨数量
    available_qty = Decimal("0")
    stock_source = "未知"
    if transfer_in.from_project_id:
        try:
            from app.services.material_transfer_service import material_transfer_service
            stock_info = material_transfer_service.get_project_material_stock(
                db, transfer_in.from_project_id, transfer_in.material_id
            )
            available_qty = stock_info.get("available_qty", Decimal("0"))
            stock_source = stock_info.get("source", "未知")
        except Exception:
            pass  # 库存服务不可用时允许继续

    # 检查数量是否充足（如果有可用库存）
    if available_qty > 0 and transfer_in.transfer_qty > available_qty:
        raise HTTPException(
            status_code=400,
            detail=f"可调拨数量不足，当前可用：{available_qty}（来源：{stock_source}）"
        )

    transfer = MaterialTransfer(
        transfer_no=_generate_transfer_no(db),
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

    save_obj(db, transfer)

    return _build_transfer_response(transfer, db)


@router.get("/{transfer_id}", response_model=MaterialTransferResponse)
def get_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """调拨申请详情"""
    transfer = get_or_404(db, MaterialTransfer, transfer_id, "调拨申请不存在")

    return _build_transfer_response(transfer, db)


# ============================================================
# 审批与执行
# ============================================================

@router.put("/{transfer_id}/approve", response_model=MaterialTransferResponse)
def approve_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """调拨审批"""
    transfer = get_or_404(db, MaterialTransfer, transfer_id, "调拨申请不存在")

    if transfer.status not in ['DRAFT', 'PENDING']:
        raise HTTPException(status_code=400, detail="只有草稿或待审批状态的申请才能审批")

    transfer.approver_id = current_user.id
    transfer.approved_at = datetime.now()
    transfer.approval_note = approval_note

    if approved:
        transfer.status = 'APPROVED'
    else:
        transfer.status = 'REJECTED'

    save_obj(db, transfer)

    return _build_transfer_response(transfer, db)


@router.put("/{transfer_id}/execute", response_model=MaterialTransferResponse)
def execute_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    actual_qty: Decimal = Body(..., description="实际调拨数量"),
    execution_note: Optional[str] = Body(None, description="执行说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """执行调拨"""
    transfer = get_or_404(db, MaterialTransfer, transfer_id, "调拨申请不存在")

    if transfer.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只有已批准的申请才能执行")

    transfer.status = 'EXECUTED'
    transfer.executed_at = datetime.now()
    transfer.executed_by = current_user.id
    transfer.actual_qty = actual_qty
    transfer.execution_note = execution_note

    # Note: 更新库存记录需要与库存管理系统集成

    save_obj(db, transfer)

    return _build_transfer_response(transfer, db)
