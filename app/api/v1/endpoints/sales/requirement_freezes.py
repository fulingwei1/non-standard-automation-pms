# -*- coding: utf-8 -*-
"""
需求管理 - 需求冻结管理

包含线索和商机的需求冻结管理
"""

from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import AssessmentSourceTypeEnum
from app.models.sales import Lead, LeadRequirementDetail, Opportunity, RequirementFreeze
from app.models.user import User
from app.schemas.sales import (
    RequirementFreezeCreate,
    RequirementFreezeResponse,
)

router = APIRouter()


@router.get("/leads/{lead_id}/requirement-freezes", response_model=List[RequirementFreezeResponse])
def list_lead_requirement_freezes(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索的需求冻结记录列表
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    freezes = db.query(RequirementFreeze).filter(
        and_(
            RequirementFreeze.source_type == AssessmentSourceTypeEnum.LEAD.value,
            RequirementFreeze.source_id == lead_id
        )
    ).order_by(desc(RequirementFreeze.freeze_time)).all()

    result = []
    for freeze in freezes:
        frozen_by_name = None
        if freeze.frozen_by:
            user = db.query(User).filter(User.id == freeze.frozen_by).first()
            frozen_by_name = user.real_name if user else None

        response_data = RequirementFreezeResponse.model_validate(freeze)
        if hasattr(response_data, 'frozen_by_name'):
            response_data.frozen_by_name = frozen_by_name
        result.append(response_data)

    return result


@router.post("/leads/{lead_id}/requirement-freezes", response_model=RequirementFreezeResponse, status_code=201)
def create_lead_requirement_freeze(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    freeze_in: RequirementFreezeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建线索需求冻结记录
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # 检查需求详情是否存在
    requirement_detail = db.query(LeadRequirementDetail).filter(
        LeadRequirementDetail.lead_id == lead_id
    ).first()

    if not requirement_detail:
        raise HTTPException(status_code=400, detail="需求详情不存在，请先创建需求详情")

    # 创建冻结记录
    freeze = RequirementFreeze(
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead_id,
        freeze_type=freeze_in.freeze_type,
        version_number=freeze_in.version_number,
        requires_ecr=freeze_in.requires_ecr,
        description=freeze_in.description,
        frozen_by=current_user.id
    )

    db.add(freeze)

    # 更新需求详情为冻结状态
    requirement_detail.is_frozen = True
    requirement_detail.frozen_at = datetime.now()
    requirement_detail.frozen_by = current_user.id
    requirement_detail.requirement_version = freeze_in.version_number

    db.commit()
    db.refresh(freeze)

    frozen_by_name = current_user.real_name
    response_data = RequirementFreezeResponse.model_validate(freeze)
    if hasattr(response_data, 'frozen_by_name'):
        response_data.frozen_by_name = frozen_by_name

    return response_data


@router.get("/opportunities/{opp_id}/requirement-freezes", response_model=List[RequirementFreezeResponse])
def list_opportunity_requirement_freezes(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取商机的需求冻结记录列表
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    freezes = db.query(RequirementFreeze).filter(
        and_(
            RequirementFreeze.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value,
            RequirementFreeze.source_id == opp_id
        )
    ).order_by(desc(RequirementFreeze.freeze_time)).all()

    result = []
    for freeze in freezes:
        frozen_by_name = None
        if freeze.frozen_by:
            user = db.query(User).filter(User.id == freeze.frozen_by).first()
            frozen_by_name = user.real_name if user else None

        response_data = RequirementFreezeResponse.model_validate(freeze)
        if hasattr(response_data, 'frozen_by_name'):
            response_data.frozen_by_name = frozen_by_name
        result.append(response_data)

    return result


@router.post("/opportunities/{opp_id}/requirement-freezes", response_model=RequirementFreezeResponse, status_code=201)
def create_opportunity_requirement_freeze(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    freeze_in: RequirementFreezeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建商机需求冻结记录
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 创建冻结记录
    freeze = RequirementFreeze(
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        freeze_type=freeze_in.freeze_type,
        version_number=freeze_in.version_number,
        requires_ecr=freeze_in.requires_ecr,
        description=freeze_in.description,
        frozen_by=current_user.id
    )

    db.add(freeze)
    db.commit()
    db.refresh(freeze)

    frozen_by_name = current_user.real_name
    response_data = RequirementFreezeResponse.model_validate(freeze)
    if hasattr(response_data, 'frozen_by_name'):
        response_data.frozen_by_name = frozen_by_name

    return response_data
