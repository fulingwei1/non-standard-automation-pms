# -*- coding: utf-8 -*-
"""
技术评估核心管理 API endpoints

包含技术评估的申请、执行、查询等核心端点
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import AssessmentSourceTypeEnum, AssessmentStatusEnum
from app.models.sales import Lead, Opportunity, TechnicalAssessment
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import (
    TechnicalAssessmentApplyRequest,
    TechnicalAssessmentEvaluateRequest,
    TechnicalAssessmentResponse,
)
from app.services.ai_assessment_service import AIAssessmentService
from app.services.technical_assessment_service import TechnicalAssessmentService
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.post("/leads/{lead_id}/assessments/apply", response_model=ResponseModel, status_code=201)
def apply_lead_assessment(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: TechnicalAssessmentApplyRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """申请技术评估（线索）"""
    lead = get_or_404(db, Lead, lead_id, detail="线索不存在")

    # 创建评估申请
    assessment = TechnicalAssessment(
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead_id,
        evaluator_id=request.evaluator_id or current_user.id,
        status=AssessmentStatusEnum.PENDING.value
    )

    db.add(assessment)
    db.flush()

    # 更新线索
    lead.assessment_id = assessment.id
    lead.assessment_status = AssessmentStatusEnum.PENDING.value

    db.commit()

    return ResponseModel(message="技术评估申请已提交", data={"assessment_id": assessment.id})


@router.post("/opportunities/{opp_id}/assessments/apply", response_model=ResponseModel, status_code=201)
def apply_opportunity_assessment(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: TechnicalAssessmentApplyRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """申请技术评估（商机）"""
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    # 创建评估申请
    assessment = TechnicalAssessment(
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        evaluator_id=request.evaluator_id or current_user.id,
        status=AssessmentStatusEnum.PENDING.value
    )

    db.add(assessment)
    db.flush()

    # 更新商机
    opportunity.assessment_id = assessment.id
    opportunity.assessment_status = AssessmentStatusEnum.PENDING.value

    db.commit()

    return ResponseModel(message="技术评估申请已提交", data={"assessment_id": assessment.id})


@router.post("/assessments/{assessment_id}/evaluate", response_model=TechnicalAssessmentResponse, status_code=200)
async def evaluate_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    request: TechnicalAssessmentEvaluateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """执行技术评估"""
    assessment = get_or_404(db, TechnicalAssessment, assessment_id, detail="技术评估不存在")

    if assessment.status != AssessmentStatusEnum.PENDING.value:
        raise HTTPException(status_code=400, detail="评估状态不正确")

    # 可选：AI分析
    ai_analysis = None
    if request.enable_ai:
        ai_service = AIAssessmentService()
        if ai_service.is_available():
            ai_analysis = await ai_service.analyze_requirement(request.requirement_data)

    # 执行评估
    service = TechnicalAssessmentService(db)
    assessment = service.evaluate(
        assessment.source_type,
        assessment.source_id,
        current_user.id,
        request.requirement_data,
        ai_analysis=ai_analysis
    )

    db.commit()

    db.refresh(assessment)

    # 构建响应
    evaluator_name = None
    if assessment.evaluator_id:
        evaluator = db.query(User).filter(User.id == assessment.evaluator_id).first()
        evaluator_name = evaluator.real_name if evaluator else None

    return TechnicalAssessmentResponse(
        id=assessment.id,
        source_type=assessment.source_type,
        source_id=assessment.source_id,
        evaluator_id=assessment.evaluator_id,
        status=assessment.status,
        total_score=assessment.total_score,
        dimension_scores=assessment.dimension_scores,
        veto_triggered=assessment.veto_triggered,
        veto_rules=assessment.veto_rules,
        decision=assessment.decision,
        risks=assessment.risks,
        similar_cases=assessment.similar_cases,
        ai_analysis=assessment.ai_analysis,
        conditions=assessment.conditions,
        evaluated_at=assessment.evaluated_at,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        evaluator_name=evaluator_name
    )


@router.get("/leads/{lead_id}/assessments", response_model=List[TechnicalAssessmentResponse])
def get_lead_assessments(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取线索的技术评估列表"""
    assessments = db.query(TechnicalAssessment).filter(
        and_(
            TechnicalAssessment.source_type == AssessmentSourceTypeEnum.LEAD.value,
            TechnicalAssessment.source_id == lead_id
        )
    ).order_by(desc(TechnicalAssessment.created_at)).all()

    result = []
    for assessment in assessments:
        evaluator_name = None
        if assessment.evaluator_id:
            evaluator = db.query(User).filter(User.id == assessment.evaluator_id).first()
            evaluator_name = evaluator.real_name if evaluator else None

        result.append(TechnicalAssessmentResponse(
            id=assessment.id,
            source_type=assessment.source_type,
            source_id=assessment.source_id,
            evaluator_id=assessment.evaluator_id,
            status=assessment.status,
            total_score=assessment.total_score,
            dimension_scores=assessment.dimension_scores,
            veto_triggered=assessment.veto_triggered,
            veto_rules=assessment.veto_rules,
            decision=assessment.decision,
            risks=assessment.risks,
            similar_cases=assessment.similar_cases,
            ai_analysis=assessment.ai_analysis,
            conditions=assessment.conditions,
            evaluated_at=assessment.evaluated_at,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            evaluator_name=evaluator_name
        ))

    return result


@router.get("/opportunities/{opp_id}/assessments", response_model=List[TechnicalAssessmentResponse])
def get_opportunity_assessments(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取商机的技术评估列表"""
    assessments = db.query(TechnicalAssessment).filter(
        and_(
            TechnicalAssessment.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value,
            TechnicalAssessment.source_id == opp_id
        )
    ).order_by(desc(TechnicalAssessment.created_at)).all()

    result = []
    for assessment in assessments:
        evaluator_name = None
        if assessment.evaluator_id:
            evaluator = db.query(User).filter(User.id == assessment.evaluator_id).first()
            evaluator_name = evaluator.real_name if evaluator else None

        result.append(TechnicalAssessmentResponse(
            id=assessment.id,
            source_type=assessment.source_type,
            source_id=assessment.source_id,
            evaluator_id=assessment.evaluator_id,
            status=assessment.status,
            total_score=assessment.total_score,
            dimension_scores=assessment.dimension_scores,
            veto_triggered=assessment.veto_triggered,
            veto_rules=assessment.veto_rules,
            decision=assessment.decision,
            risks=assessment.risks,
            similar_cases=assessment.similar_cases,
            ai_analysis=assessment.ai_analysis,
            conditions=assessment.conditions,
            evaluated_at=assessment.evaluated_at,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            evaluator_name=evaluator_name
        ))

    return result


@router.get("/assessments/{assessment_id}", response_model=TechnicalAssessmentResponse)
def get_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取技术评估详情"""
    assessment = get_or_404(db, TechnicalAssessment, assessment_id, detail="技术评估不存在")

    evaluator_name = None
    if assessment.evaluator_id:
        evaluator = db.query(User).filter(User.id == assessment.evaluator_id).first()
        evaluator_name = evaluator.real_name if evaluator else None

    return TechnicalAssessmentResponse(
        id=assessment.id,
        source_type=assessment.source_type,
        source_id=assessment.source_id,
        evaluator_id=assessment.evaluator_id,
        status=assessment.status,
        total_score=assessment.total_score,
        dimension_scores=assessment.dimension_scores,
        veto_triggered=assessment.veto_triggered,
        veto_rules=assessment.veto_rules,
        decision=assessment.decision,
        risks=assessment.risks,
        similar_cases=assessment.similar_cases,
        ai_analysis=assessment.ai_analysis,
        conditions=assessment.conditions,
        evaluated_at=assessment.evaluated_at,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        evaluator_name=evaluator_name
    )
