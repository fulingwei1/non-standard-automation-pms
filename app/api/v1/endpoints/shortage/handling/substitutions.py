# -*- coding: utf-8 -*-
"""
物料替代 - substitutions.py

合并来源:
- app/api/v1/endpoints/shortage/substitution_crud.py
- app/api/v1/endpoints/shortage/substitution_workflow.py
- app/api/v1/endpoints/shortage_alerts/substitutions.py

路由:
- GET    /                          替代列表
- POST   /                          创建替代申请
- GET    /{id}                      替代详情
- PUT    /{id}/tech-approve         技术审批
- PUT    /{id}/prod-approve         生产审批
- PUT    /{id}/execute              执行替代
"""
import logging
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
from app.models.shortage import MaterialSubstitution
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.shortage import MaterialSubstitutionCreate, MaterialSubstitutionResponse
from app.utils.db_helpers import get_or_404, save_obj

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 工具函数
# ============================================================

def _generate_substitution_no(db: Session) -> str:
    """生成替代单号：SUB-yymmdd-xxx"""
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


def _build_substitution_response(sub: MaterialSubstitution, db: Session) -> MaterialSubstitutionResponse:
    """构建替代响应对象"""
    project = db.query(Project).filter(Project.id == sub.project_id).first()
    tech_approver = db.query(User).filter(User.id == sub.tech_approver_id).first() if sub.tech_approver_id else None
    prod_approver = db.query(User).filter(User.id == sub.prod_approver_id).first() if sub.prod_approver_id else None

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
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=sub.tech_approved_at,
        prod_approver_id=sub.prod_approver_id,
        prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
        prod_approved_at=sub.prod_approved_at,
        executed_at=sub.executed_at,
        remark=sub.remark,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


# ============================================================
# CRUD 操作
# ============================================================

@router.get("", response_model=PaginatedResponse)
def list_substitutions(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（替代单号/物料编码）"),
    substitution_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """替代申请列表"""
    query = db.query(MaterialSubstitution)

    # 应用关键词过滤（替代单号/原物料编码/替代物料编码）
    query = apply_keyword_filter(query, MaterialSubstitution, keyword, ["substitution_no", "original_material_code", "substitute_material_code"])

    if substitution_status:
        query = query.filter(MaterialSubstitution.status == substitution_status)
    if project_id:
        query = query.filter(MaterialSubstitution.project_id == project_id)

    total = query.count()
    substitutions = apply_pagination(query.order_by(desc(MaterialSubstitution.created_at)), pagination.offset, pagination.limit).all()

    items = [_build_substitution_response(sub, db) for sub in substitutions]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("", response_model=MaterialSubstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_in: MaterialSubstitutionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建替代申请"""
    # 验证项目
    project = get_or_404(db, Project, sub_in.project_id, "项目不存在")

    # 验证原物料
    original_material = get_or_404(db, Material, sub_in.original_material_id, "原物料不存在")

    # 验证替代物料
    substitute_material = get_or_404(db, Material, sub_in.substitute_material_id, "替代物料不存在")

    if sub_in.original_material_id == sub_in.substitute_material_id:
        raise HTTPException(status_code=400, detail="原物料和替代物料不能相同")

    substitution = MaterialSubstitution(
        substitution_no=_generate_substitution_no(db),
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

    save_obj(db, substitution)

    return _build_substitution_response(substitution, db)


@router.get("/{substitution_id}", response_model=MaterialSubstitutionResponse)
def get_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """替代申请详情"""
    sub = get_or_404(db, MaterialSubstitution, substitution_id, "替代申请不存在")

    return _build_substitution_response(sub, db)


# ============================================================
# 审批流程
# ============================================================

@router.put("/{substitution_id}/tech-approve", response_model=MaterialSubstitutionResponse)
def tech_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """技术审批"""
    sub = get_or_404(db, MaterialSubstitution, substitution_id, "替代申请不存在")

    if sub.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只有草稿状态的申请才能进行技术审批")

    sub.tech_approver_id = current_user.id
    sub.tech_approved_at = datetime.now()
    sub.tech_approval_note = approval_note

    if approved:
        sub.status = 'PROD_PENDING'  # 转为待生产审批
    else:
        sub.status = 'REJECTED'

    save_obj(db, sub)

    return _build_substitution_response(sub, db)


@router.put("/{substitution_id}/prod-approve", response_model=MaterialSubstitutionResponse)
def prod_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """生产审批"""
    sub = get_or_404(db, MaterialSubstitution, substitution_id, "替代申请不存在")

    if sub.status != 'PROD_PENDING':
        raise HTTPException(status_code=400, detail="只有待生产审批状态的申请才能进行生产审批")

    sub.prod_approver_id = current_user.id
    sub.prod_approved_at = datetime.now()
    sub.prod_approval_note = approval_note

    if approved:
        sub.status = 'APPROVED'
    else:
        sub.status = 'REJECTED'

    save_obj(db, sub)

    return _build_substitution_response(sub, db)


@router.put("/{substitution_id}/execute", response_model=MaterialSubstitutionResponse)
def execute_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    execution_note: Optional[str] = Body(None, description="执行说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """执行替代"""
    sub = get_or_404(db, MaterialSubstitution, substitution_id, "替代申请不存在")

    if sub.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只能执行已批准的申请")

    sub.status = 'EXECUTED'
    sub.executed_at = datetime.now()
    sub.executed_by = current_user.id
    sub.execution_note = execution_note

    # 更新BOM中的物料信息
    if sub.bom_item_id:
        from app.models.material import BomItem
        bom_item = db.query(BomItem).filter(BomItem.id == sub.bom_item_id).first()
        if bom_item:
            old_material_id = bom_item.material_id
            old_material_code = bom_item.material_code

            bom_item.material_id = sub.substitute_material_id
            bom_item.material_code = sub.substitute_material_code
            bom_item.material_name = sub.substitute_material_name
            if hasattr(sub, 'substitute_unit_price') and sub.substitute_unit_price:
                bom_item.unit_price = sub.substitute_unit_price

            db.add(bom_item)

            # 记录物料变更历史
            try:
                from app.models.material import MaterialChangeHistory
                change_history = MaterialChangeHistory(
                    bom_item_id=sub.bom_item_id,
                    change_type="SUBSTITUTION",
                    old_material_id=old_material_id,
                    old_material_code=old_material_code,
                    new_material_id=sub.substitute_material_id,
                    new_material_code=sub.substitute_material_code,
                    change_reason=sub.substitution_reason or "物料替代",
                    changed_by=current_user.id,
                    substitution_id=sub.id
                )
                db.add(change_history)
            except Exception:
                logger.debug("MaterialChangeHistory 写入失败，已忽略", exc_info=True)

    save_obj(db, sub)

    # 发送通知
    try:
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationRequest, NotificationPriority
        if sub.project_id:
            project = db.query(Project).filter(Project.id == sub.project_id).first()
            if project and project.pm_id:
                dispatcher = NotificationDispatcher(db)
                request = NotificationRequest(
                    recipient_id=project.pm_id,
                    notification_type="PROJECT_UPDATE",
                    category="project",
                    title=f"物料替代已执行: {sub.original_material_name}",
                    content=f"替代物料: {sub.substitute_material_name}\n替代数量: {sub.substitute_qty}",
                    priority=NotificationPriority.NORMAL,
                    source_type="substitution",
                    source_id=sub.id,
                    link_url=f"/shortage/handling/substitutions/{sub.id}",
                )
                dispatcher.send_notification_request(request)
    except Exception:
        logger.warning("物料替代通知发送失败，不影响主流程", exc_info=True)

    return _build_substitution_response(sub, db)
