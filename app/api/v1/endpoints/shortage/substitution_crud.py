# -*- coding: utf-8 -*-
"""
物料替代 - CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Project
from app.models.shortage import MaterialSubstitution
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.shortage import (
    MaterialSubstitutionCreate,
    MaterialSubstitutionResponse,
)

from .statistics_helpers import generate_substitution_no

router = APIRouter()


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
    创建物料替代申请
    """
    # 生成替代单号
    substitution_no = generate_substitution_no(db)

    # 获取物料信息
    from app.models.material import Material
    original_material = db.query(Material).filter(Material.id == substitution_in.original_material_id).first()
    if not original_material:
        raise HTTPException(status_code=404, detail="原物料不存在")

    substitute_material = db.query(Material).filter(Material.id == substitution_in.substitute_material_id).first()
    if not substitute_material:
        raise HTTPException(status_code=404, detail="替代物料不存在")

    substitution = MaterialSubstitution(
        substitution_no=substitution_no,
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
        cost_impact=substitution_in.cost_impact or 0,
        status="DRAFT",
        remark=substitution_in.remark,
        created_by=current_user.id
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
