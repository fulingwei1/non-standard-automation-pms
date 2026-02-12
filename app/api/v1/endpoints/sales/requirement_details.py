# -*- coding: utf-8 -*-
"""
需求管理 - 需求详情管理

包含线索需求详情的CRUD操作
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Lead, LeadRequirementDetail
from app.models.user import User
from app.schemas.sales import (
    LeadRequirementDetailCreate,
    LeadRequirementDetailResponse,
)

router = APIRouter()


@router.get("/leads/{lead_id}/requirement-detail", response_model=LeadRequirementDetailResponse)
def get_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索需求详情
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    detail = db.query(LeadRequirementDetail).filter(
        LeadRequirementDetail.lead_id == lead_id
    ).first()

    if not detail:
        raise HTTPException(status_code=404, detail="需求详情不存在")

    # 获取冻结人姓名
    frozen_by_name = None
    if detail.frozen_by:
        user = db.query(User).filter(User.id == detail.frozen_by).first()
        frozen_by_name = user.real_name if user else None

    # 构建响应，包含 frozen_by_name
    response_data = LeadRequirementDetailResponse.model_validate(detail)
    if hasattr(response_data, 'frozen_by_name'):
        response_data.frozen_by_name = frozen_by_name

    return response_data


@router.post("/leads/{lead_id}/requirement-detail", response_model=LeadRequirementDetailResponse, status_code=201)
def create_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    detail_in: LeadRequirementDetailCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建线索需求详情
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # 检查是否已存在
    existing = db.query(LeadRequirementDetail).filter(
        LeadRequirementDetail.lead_id == lead_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该线索已存在需求详情，请使用更新接口")

    detail = LeadRequirementDetail(
        lead_id=lead_id,
        **detail_in.model_dump()
    )

    db.add(detail)
    db.commit()
    db.refresh(detail)

    return LeadRequirementDetailResponse.model_validate(detail)


@router.put("/leads/{lead_id}/requirement-detail", response_model=LeadRequirementDetailResponse)
def update_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    detail_in: LeadRequirementDetailCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新线索需求详情
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    detail = db.query(LeadRequirementDetail).filter(
        LeadRequirementDetail.lead_id == lead_id
    ).first()

    if not detail:
        raise HTTPException(status_code=404, detail="需求详情不存在")

    # 更新字段
    update_data = detail_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(detail, field, value)

    db.add(detail)
    db.commit()
    db.refresh(detail)

    return LeadRequirementDetailResponse.model_validate(detail)
