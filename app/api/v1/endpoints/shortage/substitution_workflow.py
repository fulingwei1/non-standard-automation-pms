# -*- coding: utf-8 -*-
"""
物料替代 - 审批流程
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.shortage import MaterialSubstitution
from app.models.user import User
from app.schemas.shortage import MaterialSubstitutionResponse

router = APIRouter()


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
