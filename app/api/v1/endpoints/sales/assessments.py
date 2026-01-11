# -*- coding: utf-8 -*-
"""
技术评估管理 API endpoints

包含技术评估、评分规则、失败案例、待办事项等相关端点
"""

from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.sales import (
    Lead, Opportunity,
    TechnicalAssessment, ScoringRule, FailureCase, OpenItem
)
from app.models.enums import (
    AssessmentSourceTypeEnum, AssessmentStatusEnum, AssessmentDecisionEnum,
    OpenItemStatusEnum
)
from app.schemas.sales import (
    TechnicalAssessmentApplyRequest, TechnicalAssessmentEvaluateRequest, TechnicalAssessmentResponse,
    ScoringRuleCreate, ScoringRuleResponse,
    FailureCaseCreate, FailureCaseResponse,
    OpenItemCreate, OpenItemResponse
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.services.technical_assessment_service import TechnicalAssessmentService
from app.services.ai_assessment_service import AIAssessmentService

router = APIRouter()


# ==================== 技术评估 ====================


@router.post("/leads/{lead_id}/assessments/apply", response_model=ResponseModel, status_code=201)
def apply_lead_assessment(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: TechnicalAssessmentApplyRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """申请技术评估（线索）"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

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
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

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
    assessment = db.query(TechnicalAssessment).filter(TechnicalAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="技术评估不存在")

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
    assessment = db.query(TechnicalAssessment).filter(TechnicalAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="技术评估不存在")

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


# ==================== 失败案例 ====================


@router.get("/failure-cases/similar", response_model=List[FailureCaseResponse])
def find_similar_cases(
    *,
    db: Session = Depends(deps.get_db),
    industry: Optional[str] = Query(None, description="行业"),
    product_types: Optional[str] = Query(None, description="产品类型(JSON Array)"),
    takt_time_s: Optional[int] = Query(None, description="节拍时间(秒)"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查找相似失败案例"""
    query = db.query(FailureCase)

    if industry:
        query = query.filter(FailureCase.industry == industry)

    cases = query.limit(10).all()

    result = []
    for case in cases:
        creator_name = None
        if case.created_by:
            creator = db.query(User).filter(User.id == case.created_by).first()
            creator_name = creator.real_name if creator else None

        result.append(FailureCaseResponse(
            **{c.name: getattr(case, c.name) for c in case.__table__.columns},
            creator_name=creator_name
        ))

    return result


@router.get("/failure-cases", response_model=PaginatedResponse[FailureCaseResponse])
def list_failure_cases(
    *,
    db: Session = Depends(deps.get_db),
    industry: Optional[str] = Query(None, description="行业"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取失败案例列表"""
    query = db.query(FailureCase)

    if industry:
        query = query.filter(FailureCase.industry == industry)

    if keyword:
        query = query.filter(
            or_(
                FailureCase.project_name.like(f"%{keyword}%"),
                FailureCase.core_failure_reason.like(f"%{keyword}%")
            )
        )

    total = query.count()
    cases = query.order_by(desc(FailureCase.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for case in cases:
        creator_name = None
        if case.created_by:
            creator = db.query(User).filter(User.id == case.created_by).first()
            creator_name = creator.real_name if creator else None

        result.append(FailureCaseResponse(
            **{c.name: getattr(case, c.name) for c in case.__table__.columns},
            creator_name=creator_name
        ))

    return PaginatedResponse(
        items=result,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/failure-cases", response_model=FailureCaseResponse, status_code=201)
def create_failure_case(
    *,
    db: Session = Depends(deps.get_db),
    request: FailureCaseCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建失败案例"""
    # 检查案例编号是否已存在
    existing = db.query(FailureCase).filter(FailureCase.case_code == request.case_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="案例编号已存在")

    case = FailureCase(
        case_code=request.case_code,
        project_name=request.project_name,
        industry=request.industry,
        product_types=request.product_types,
        processes=request.processes,
        takt_time_s=request.takt_time_s,
        annual_volume=request.annual_volume,
        budget_status=request.budget_status,
        customer_project_status=request.customer_project_status,
        spec_status=request.spec_status,
        price_sensitivity=request.price_sensitivity,
        delivery_months=request.delivery_months,
        failure_tags=request.failure_tags,
        core_failure_reason=request.core_failure_reason,
        early_warning_signals=request.early_warning_signals,
        final_result=request.final_result,
        lesson_learned=request.lesson_learned,
        keywords=request.keywords,
        created_by=current_user.id
    )

    db.add(case)
    db.commit()
    db.refresh(case)

    return FailureCaseResponse(
        id=case.id,
        case_code=case.case_code,
        project_name=case.project_name,
        industry=case.industry,
        product_types=case.product_types,
        processes=case.processes,
        takt_time_s=case.takt_time_s,
        annual_volume=case.annual_volume,
        budget_status=case.budget_status,
        customer_project_status=case.customer_project_status,
        spec_status=case.spec_status,
        price_sensitivity=case.price_sensitivity,
        delivery_months=case.delivery_months,
        failure_tags=case.failure_tags,
        core_failure_reason=case.core_failure_reason,
        early_warning_signals=case.early_warning_signals,
        final_result=case.final_result,
        lesson_learned=case.lesson_learned,
        keywords=case.keywords,
        created_by=case.created_by,
        created_at=case.created_at,
        updated_at=case.updated_at,
        creator_name=current_user.real_name
    )


# ==================== 待办事项 ====================


@router.get("/open-items", response_model=PaginatedResponse[OpenItemResponse])
def list_open_items(
    *,
    db: Session = Depends(deps.get_db),
    source_type: Optional[str] = Query(None, description="来源类型"),
    source_id: Optional[int] = Query(None, description="来源ID"),
    status: Optional[str] = Query(None, description="状态"),
    blocks_quotation: Optional[bool] = Query(None, description="是否阻塞报价"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取未决事项列表"""
    query = db.query(OpenItem)

    if source_type:
        query = query.filter(OpenItem.source_type == source_type)
    if source_id:
        query = query.filter(OpenItem.source_id == source_id)
    if status:
        query = query.filter(OpenItem.status == status)
    if blocks_quotation is not None:
        query = query.filter(OpenItem.blocks_quotation == blocks_quotation)

    total = query.count()
    items = query.order_by(desc(OpenItem.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for item in items:
        responsible_person_name = None
        if item.responsible_person_id:
            person = db.query(User).filter(User.id == item.responsible_person_id).first()
            responsible_person_name = person.real_name if person else None

        result.append(OpenItemResponse(
            id=item.id,
            source_type=item.source_type,
            source_id=item.source_id,
            item_code=item.item_code,
            item_type=item.item_type,
            description=item.description,
            responsible_party=item.responsible_party,
            responsible_person_id=item.responsible_person_id,
            due_date=item.due_date,
            status=item.status,
            close_evidence=item.close_evidence,
            blocks_quotation=item.blocks_quotation,
            closed_at=item.closed_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
            responsible_person_name=responsible_person_name
        ))

    return PaginatedResponse(
        items=result,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/leads/{lead_id}/open-items", response_model=OpenItemResponse, status_code=201)
def create_open_item(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: OpenItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建未决事项（线索）"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # 生成编号
    item_code = f"OI-{datetime.now().strftime('%y%m%d')}-{lead_id:03d}"

    open_item = OpenItem(
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead_id,
        item_code=item_code,
        item_type=request.item_type,
        description=request.description,
        responsible_party=request.responsible_party,
        responsible_person_id=request.responsible_person_id,
        due_date=request.due_date,
        blocks_quotation=request.blocks_quotation
    )

    db.add(open_item)
    db.commit()
    db.refresh(open_item)

    responsible_person_name = None
    if open_item.responsible_person_id:
        person = db.query(User).filter(User.id == open_item.responsible_person_id).first()
        responsible_person_name = person.real_name if person else None

    return OpenItemResponse(
        id=open_item.id,
        source_type=open_item.source_type,
        source_id=open_item.source_id,
        item_code=open_item.item_code,
        item_type=open_item.item_type,
        description=open_item.description,
        responsible_party=open_item.responsible_party,
        responsible_person_id=open_item.responsible_person_id,
        due_date=open_item.due_date,
        status=open_item.status,
        close_evidence=open_item.close_evidence,
        blocks_quotation=open_item.blocks_quotation,
        closed_at=open_item.closed_at,
        created_at=open_item.created_at,
        updated_at=open_item.updated_at,
        responsible_person_name=responsible_person_name
    )


@router.post("/opportunities/{opp_id}/open-items", response_model=OpenItemResponse, status_code=201)
def create_open_item_for_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: OpenItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建未决事项（商机）"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 生成编号
    item_code = f"OI-{datetime.now().strftime('%y%m%d')}-{opp_id:03d}"

    open_item = OpenItem(
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        item_code=item_code,
        item_type=request.item_type,
        description=request.description,
        responsible_party=request.responsible_party,
        responsible_person_id=request.responsible_person_id,
        due_date=request.due_date,
        blocks_quotation=request.blocks_quotation
    )

    db.add(open_item)
    db.commit()
    db.refresh(open_item)

    responsible_person_name = None
    if open_item.responsible_person_id:
        person = db.query(User).filter(User.id == open_item.responsible_person_id).first()
        responsible_person_name = person.real_name if person else None

    return OpenItemResponse(
        id=open_item.id,
        source_type=open_item.source_type,
        source_id=open_item.source_id,
        item_code=open_item.item_code,
        item_type=open_item.item_type,
        description=open_item.description,
        responsible_party=open_item.responsible_party,
        responsible_person_id=open_item.responsible_person_id,
        due_date=open_item.due_date,
        status=open_item.status,
        close_evidence=open_item.close_evidence,
        blocks_quotation=open_item.blocks_quotation,
        closed_at=open_item.closed_at,
        created_at=open_item.created_at,
        updated_at=open_item.updated_at,
        responsible_person_name=responsible_person_name
    )


@router.put("/open-items/{item_id}", response_model=OpenItemResponse)
def update_open_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    request: OpenItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新未决事项"""
    open_item = db.query(OpenItem).filter(OpenItem.id == item_id).first()
    if not open_item:
        raise HTTPException(status_code=404, detail="未决事项不存在")

    open_item.item_type = request.item_type
    open_item.description = request.description
    open_item.responsible_party = request.responsible_party
    open_item.responsible_person_id = request.responsible_person_id
    open_item.due_date = request.due_date
    open_item.blocks_quotation = request.blocks_quotation

    db.commit()
    db.refresh(open_item)

    responsible_person_name = None
    if open_item.responsible_person_id:
        person = db.query(User).filter(User.id == open_item.responsible_person_id).first()
        responsible_person_name = person.real_name if person else None

    return OpenItemResponse(
        id=open_item.id,
        source_type=open_item.source_type,
        source_id=open_item.source_id,
        item_code=open_item.item_code,
        item_type=open_item.item_type,
        description=open_item.description,
        responsible_party=open_item.responsible_party,
        responsible_person_id=open_item.responsible_person_id,
        due_date=open_item.due_date,
        status=open_item.status,
        close_evidence=open_item.close_evidence,
        blocks_quotation=open_item.blocks_quotation,
        closed_at=open_item.closed_at,
        created_at=open_item.created_at,
        updated_at=open_item.updated_at,
        responsible_person_name=responsible_person_name
    )


@router.post("/open-items/{item_id}/close", response_model=ResponseModel)
def close_open_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    close_evidence: Optional[str] = Query(None, description="关闭证据"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """关闭未决事项"""
    open_item = db.query(OpenItem).filter(OpenItem.id == item_id).first()
    if not open_item:
        raise HTTPException(status_code=404, detail="未决事项不存在")

    open_item.status = OpenItemStatusEnum.CLOSED.value
    open_item.close_evidence = close_evidence
    open_item.closed_at = datetime.now()

    db.commit()

    return ResponseModel(message="未决事项已关闭")


# ==================== 评分规则 ====================


@router.get("/scoring-rules", response_model=List[ScoringRuleResponse])
def list_scoring_rules(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取评分规则列表"""
    rules = db.query(ScoringRule).order_by(desc(ScoringRule.created_at)).all()

    result = []
    for rule in rules:
        creator_name = None
        if rule.created_by:
            creator = db.query(User).filter(User.id == rule.created_by).first()
            creator_name = creator.real_name if creator else None

        result.append(ScoringRuleResponse(
            id=rule.id,
            version=rule.version,
            is_active=rule.is_active,
            description=rule.description,
            created_by=rule.created_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            creator_name=creator_name
        ))

    return result


@router.post("/scoring-rules", response_model=ScoringRuleResponse, status_code=201)
def create_scoring_rule(
    *,
    db: Session = Depends(deps.get_db),
    request: ScoringRuleCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评分规则"""
    # 检查版本号是否已存在
    existing = db.query(ScoringRule).filter(ScoringRule.version == request.version).first()
    if existing:
        raise HTTPException(status_code=400, detail="版本号已存在")

    rule = ScoringRule(
        version=request.version,
        rules_json=request.rules_json,
        description=request.description,
        created_by=current_user.id
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ScoringRuleResponse(
        id=rule.id,
        version=rule.version,
        is_active=rule.is_active,
        description=rule.description,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        creator_name=current_user.real_name
    )


@router.put("/scoring-rules/{rule_id}/activate", response_model=ResponseModel)
def activate_scoring_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """激活评分规则版本"""
    rule = db.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="评分规则不存在")

    # 取消其他规则的激活状态
    db.query(ScoringRule).update({ScoringRule.is_active: False})

    # 激活当前规则
    rule.is_active = True
    db.commit()

    return ResponseModel(message="评分规则已激活")
