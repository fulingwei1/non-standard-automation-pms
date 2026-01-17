# -*- coding: utf-8 -*-
"""
需求管理 API endpoints

包含：
- 线索需求详情管理
- 需求冻结管理
- AI澄清管理
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import AssessmentSourceTypeEnum
from app.models.sales import (
    AIClarification,
    Lead,
    LeadRequirementDetail,
    Opportunity,
    RequirementFreeze,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    AIClarificationCreate,
    AIClarificationResponse,
    AIClarificationUpdate,
    LeadRequirementDetailCreate,
    LeadRequirementDetailResponse,
    RequirementFreezeCreate,
    RequirementFreezeResponse,
)

router = APIRouter()


# ==================== 需求详情管理 ====================

@router.get("/leads/{lead_id}/requirement-detail", response_model=LeadRequirementDetailResponse)
def get_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取线索的需求详情"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    requirement_detail = db.query(LeadRequirementDetail).filter(
        LeadRequirementDetail.lead_id == lead_id
    ).first()

    if not requirement_detail:
        raise HTTPException(status_code=404, detail="需求详情不存在")

    frozen_by_name = None
    if requirement_detail.frozen_by:
        user = db.query(User).filter(User.id == requirement_detail.frozen_by).first()
        frozen_by_name = user.real_name if user else None

    return LeadRequirementDetailResponse(
        id=requirement_detail.id,
        lead_id=requirement_detail.lead_id,
        customer_factory_location=requirement_detail.customer_factory_location,
        target_object_type=requirement_detail.target_object_type,
        application_scenario=requirement_detail.application_scenario,
        delivery_mode=requirement_detail.delivery_mode,
        expected_delivery_date=requirement_detail.expected_delivery_date,
        requirement_source=requirement_detail.requirement_source,
        participant_ids=requirement_detail.participant_ids,
        requirement_maturity=requirement_detail.requirement_maturity,
        has_sow=requirement_detail.has_sow,
        has_interface_doc=requirement_detail.has_interface_doc,
        has_drawing_doc=requirement_detail.has_drawing_doc,
        sample_availability=requirement_detail.sample_availability,
        customer_support_resources=requirement_detail.customer_support_resources,
        key_risk_factors=requirement_detail.key_risk_factors,
        veto_triggered=requirement_detail.veto_triggered,
        veto_reason=requirement_detail.veto_reason,
        target_capacity_uph=float(requirement_detail.target_capacity_uph) if requirement_detail.target_capacity_uph else None,
        target_capacity_daily=float(requirement_detail.target_capacity_daily) if requirement_detail.target_capacity_daily else None,
        target_capacity_shift=float(requirement_detail.target_capacity_shift) if requirement_detail.target_capacity_shift else None,
        cycle_time_seconds=float(requirement_detail.cycle_time_seconds) if requirement_detail.cycle_time_seconds else None,
        workstation_count=requirement_detail.workstation_count,
        changeover_method=requirement_detail.changeover_method,
        yield_target=float(requirement_detail.yield_target) if requirement_detail.yield_target else None,
        retest_allowed=requirement_detail.retest_allowed,
        retest_max_count=requirement_detail.retest_max_count,
        traceability_type=requirement_detail.traceability_type,
        data_retention_period=requirement_detail.data_retention_period,
        data_format=requirement_detail.data_format,
        test_scope=requirement_detail.test_scope,
        key_metrics_spec=requirement_detail.key_metrics_spec,
        coverage_boundary=requirement_detail.coverage_boundary,
        exception_handling=requirement_detail.exception_handling,
        acceptance_method=requirement_detail.acceptance_method,
        acceptance_basis=requirement_detail.acceptance_basis,
        delivery_checklist=requirement_detail.delivery_checklist,
        interface_types=requirement_detail.interface_types,
        io_point_estimate=requirement_detail.io_point_estimate,
        communication_protocols=requirement_detail.communication_protocols,
        upper_system_integration=requirement_detail.upper_system_integration,
        data_field_list=requirement_detail.data_field_list,
        it_security_restrictions=requirement_detail.it_security_restrictions,
        power_supply=requirement_detail.power_supply,
        air_supply=requirement_detail.air_supply,
        environment=requirement_detail.environment,
        safety_requirements=requirement_detail.safety_requirements,
        space_and_logistics=requirement_detail.space_and_logistics,
        customer_site_standards=requirement_detail.customer_site_standards,
        customer_supplied_materials=requirement_detail.customer_supplied_materials,
        restricted_brands=requirement_detail.restricted_brands,
        specified_brands=requirement_detail.specified_brands,
        long_lead_items=requirement_detail.long_lead_items,
        spare_parts_requirement=requirement_detail.spare_parts_requirement,
        after_sales_support=requirement_detail.after_sales_support,
        requirement_version=requirement_detail.requirement_version,
        is_frozen=requirement_detail.is_frozen,
        frozen_at=requirement_detail.frozen_at,
        frozen_by=requirement_detail.frozen_by,
        frozen_by_name=frozen_by_name,
        created_at=requirement_detail.created_at,
        updated_at=requirement_detail.updated_at
    )


@router.post("/leads/{lead_id}/requirement-detail", response_model=LeadRequirementDetailResponse, status_code=201)
def create_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: LeadRequirementDetailCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建线索的需求详情"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # 检查是否已存在
    existing = db.query(LeadRequirementDetail).filter(
        LeadRequirementDetail.lead_id == lead_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="需求详情已存在，请使用PUT方法更新")

    # 创建需求详情
    requirement_detail = LeadRequirementDetail(
        lead_id=lead_id,
        **request.dict(exclude_unset=True)
    )

    db.add(requirement_detail)
    db.commit()
    db.refresh(requirement_detail)

    # 更新线索的requirement_detail_id
    lead.requirement_detail_id = requirement_detail.id
    db.commit()

    return get_lead_requirement_detail(db=db, lead_id=lead_id, current_user=current_user)


@router.put("/leads/{lead_id}/requirement-detail", response_model=LeadRequirementDetailResponse)
def update_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: LeadRequirementDetailCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新线索的需求详情"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    requirement_detail = db.query(LeadRequirementDetail).filter(
        LeadRequirementDetail.lead_id == lead_id
    ).first()

    if not requirement_detail:
        raise HTTPException(status_code=404, detail="需求详情不存在")

    # 检查是否已冻结
    if requirement_detail.is_frozen:
        raise HTTPException(status_code=400, detail="需求已冻结，无法修改。如需修改，请先解冻或创建ECR/ECN")

    # 更新字段
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(requirement_detail, field, value)

    db.commit()
    db.refresh(requirement_detail)

    return get_lead_requirement_detail(db=db, lead_id=lead_id, current_user=current_user)


# ==================== 需求冻结管理 ====================

@router.get("/leads/{lead_id}/requirement-freezes", response_model=List[RequirementFreezeResponse])
def list_lead_requirement_freezes(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取线索的需求冻结记录列表"""
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

        result.append(RequirementFreezeResponse(
            id=freeze.id,
            source_type=freeze.source_type,
            source_id=freeze.source_id,
            freeze_type=freeze.freeze_type,
            freeze_time=freeze.freeze_time,
            frozen_by=freeze.frozen_by,
            version_number=freeze.version_number,
            requires_ecr=freeze.requires_ecr,
            description=freeze.description,
            created_at=freeze.created_at,
            updated_at=freeze.updated_at,
            frozen_by_name=frozen_by_name
        ))

    return result


@router.post("/leads/{lead_id}/requirement-freezes", response_model=RequirementFreezeResponse, status_code=201)
def create_lead_requirement_freeze(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: RequirementFreezeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建线索的需求冻结记录"""
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
        freeze_type=request.freeze_type,
        version_number=request.version_number,
        requires_ecr=request.requires_ecr,
        description=request.description,
        frozen_by=current_user.id
    )

    db.add(freeze)

    # 更新需求详情为冻结状态
    requirement_detail.is_frozen = True
    requirement_detail.frozen_at = datetime.now()
    requirement_detail.frozen_by = current_user.id
    requirement_detail.requirement_version = request.version_number

    db.commit()
    db.refresh(freeze)

    frozen_by_name = current_user.real_name

    return RequirementFreezeResponse(
        id=freeze.id,
        source_type=freeze.source_type,
        source_id=freeze.source_id,
        freeze_type=freeze.freeze_type,
        freeze_time=freeze.freeze_time,
        frozen_by=freeze.frozen_by,
        version_number=freeze.version_number,
        requires_ecr=freeze.requires_ecr,
        description=freeze.description,
        created_at=freeze.created_at,
        updated_at=freeze.updated_at,
        frozen_by_name=frozen_by_name
    )


@router.get("/opportunities/{opp_id}/requirement-freezes", response_model=List[RequirementFreezeResponse])
def list_opportunity_requirement_freezes(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取商机的需求冻结记录列表"""
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

        result.append(RequirementFreezeResponse(
            id=freeze.id,
            source_type=freeze.source_type,
            source_id=freeze.source_id,
            freeze_type=freeze.freeze_type,
            freeze_time=freeze.freeze_time,
            frozen_by=freeze.frozen_by,
            version_number=freeze.version_number,
            requires_ecr=freeze.requires_ecr,
            description=freeze.description,
            created_at=freeze.created_at,
            updated_at=freeze.updated_at,
            frozen_by_name=frozen_by_name
        ))

    return result


@router.post("/opportunities/{opp_id}/requirement-freezes", response_model=RequirementFreezeResponse, status_code=201)
def create_opportunity_requirement_freeze(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: RequirementFreezeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建商机的需求冻结记录"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 创建冻结记录
    freeze = RequirementFreeze(
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        freeze_type=request.freeze_type,
        version_number=request.version_number,
        requires_ecr=request.requires_ecr,
        description=request.description,
        frozen_by=current_user.id
    )

    db.add(freeze)
    db.commit()
    db.refresh(freeze)

    frozen_by_name = current_user.real_name

    return RequirementFreezeResponse(
        id=freeze.id,
        source_type=freeze.source_type,
        source_id=freeze.source_id,
        freeze_type=freeze.freeze_type,
        freeze_time=freeze.freeze_time,
        frozen_by=freeze.frozen_by,
        version_number=freeze.version_number,
        requires_ecr=freeze.requires_ecr,
        description=freeze.description,
        created_at=freeze.created_at,
        updated_at=freeze.updated_at,
        frozen_by_name=frozen_by_name
    )


# ==================== AI澄清管理 ====================

@router.get("/ai-clarifications", response_model=PaginatedResponse[AIClarificationResponse])
def list_ai_clarifications(
    *,
    db: Session = Depends(deps.get_db),
    source_type: Optional[str] = Query(None, description="来源类型"),
    source_id: Optional[int] = Query(None, description="来源ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取AI澄清记录列表"""
    query = db.query(AIClarification)

    if source_type:
        query = query.filter(AIClarification.source_type == source_type)
    if source_id:
        query = query.filter(AIClarification.source_id == source_id)

    total = query.count()
    clarifications = query.order_by(
        desc(AIClarification.source_type),
        desc(AIClarification.source_id),
        desc(AIClarification.round)
    ).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for clarification in clarifications:
        items.append(AIClarificationResponse(
            id=clarification.id,
            source_type=clarification.source_type,
            source_id=clarification.source_id,
            round=clarification.round,
            questions=clarification.questions,
            answers=clarification.answers,
            created_at=clarification.created_at,
            updated_at=clarification.updated_at
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/leads/{lead_id}/ai-clarifications", response_model=AIClarificationResponse, status_code=201)
def create_ai_clarification_for_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: AIClarificationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建AI澄清记录（线索）"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # 获取当前最大轮次
    max_round = db.query(func.max(AIClarification.round)).filter(
        and_(
            AIClarification.source_type == AssessmentSourceTypeEnum.LEAD.value,
            AIClarification.source_id == lead_id
        )
    ).scalar() or 0

    clarification = AIClarification(
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead_id,
        round=max_round + 1,
        questions=request.questions,
        answers=request.answers
    )

    db.add(clarification)
    db.commit()
    db.refresh(clarification)

    return AIClarificationResponse(
        id=clarification.id,
        source_type=clarification.source_type,
        source_id=clarification.source_id,
        round=clarification.round,
        questions=clarification.questions,
        answers=clarification.answers,
        created_at=clarification.created_at,
        updated_at=clarification.updated_at
    )


@router.post("/opportunities/{opp_id}/ai-clarifications", response_model=AIClarificationResponse, status_code=201)
def create_ai_clarification_for_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: AIClarificationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建AI澄清记录（商机）"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 获取当前最大轮次
    max_round = db.query(func.max(AIClarification.round)).filter(
        and_(
            AIClarification.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value,
            AIClarification.source_id == opp_id
        )
    ).scalar() or 0

    clarification = AIClarification(
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        round=max_round + 1,
        questions=request.questions,
        answers=request.answers
    )

    db.add(clarification)
    db.commit()
    db.refresh(clarification)

    return AIClarificationResponse(
        id=clarification.id,
        source_type=clarification.source_type,
        source_id=clarification.source_id,
        round=clarification.round,
        questions=clarification.questions,
        answers=clarification.answers,
        created_at=clarification.created_at,
        updated_at=clarification.updated_at
    )


@router.put("/ai-clarifications/{clarification_id}", response_model=AIClarificationResponse)
def update_ai_clarification(
    *,
    db: Session = Depends(deps.get_db),
    clarification_id: int,
    request: AIClarificationUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新AI澄清记录（回答）"""
    clarification = db.query(AIClarification).filter(
        AIClarification.id == clarification_id
    ).first()

    if not clarification:
        raise HTTPException(status_code=404, detail="AI澄清记录不存在")

    clarification.answers = request.answers

    db.commit()
    db.refresh(clarification)

    return AIClarificationResponse(
        id=clarification.id,
        source_type=clarification.source_type,
        source_id=clarification.source_id,
        round=clarification.round,
        questions=clarification.questions,
        answers=clarification.answers,
        created_at=clarification.created_at,
        updated_at=clarification.updated_at
    )


@router.get("/ai-clarifications/{clarification_id}", response_model=AIClarificationResponse)
def get_ai_clarification(
    *,
    db: Session = Depends(deps.get_db),
    clarification_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取AI澄清记录详情"""
    clarification = db.query(AIClarification).filter(
        AIClarification.id == clarification_id
    ).first()

    if not clarification:
        raise HTTPException(status_code=404, detail="AI澄清记录不存在")

    return AIClarificationResponse(
        id=clarification.id,
        source_type=clarification.source_type,
        source_id=clarification.source_id,
        round=clarification.round,
        questions=clarification.questions,
        answers=clarification.answers,
        created_at=clarification.created_at,
        updated_at=clarification.updated_at
    )
