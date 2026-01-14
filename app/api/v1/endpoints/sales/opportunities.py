# -*- coding: utf-8 -*-
"""
商机管理 API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Customer
from app.models.sales import Opportunity, OpportunityRequirement
from app.models.enums import OpportunityStageEnum
from app.schemas.sales import (
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    OpportunityRequirementResponse, GateSubmitRequest
)
from app.schemas.common import PaginatedResponse, ResponseModel
from .utils import (
    get_entity_creator_id,
    generate_opportunity_code,
    validate_g2_opportunity_to_quote
)

router = APIRouter()


@router.get("/opportunities", response_model=PaginatedResponse[OpportunityResponse])
def read_opportunities(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取商机列表
    Issue 7.1: 已集成数据权限过滤
    """
    query = db.query(Opportunity).options(joinedload(Opportunity.customer))

    # Issue 7.1: 应用数据权限过滤
    query = security.filter_sales_data_by_scope(query, current_user, db, Opportunity, 'owner_id')

    if keyword:
        query = query.filter(
            or_(
                Opportunity.opp_code.contains(keyword),
                Opportunity.opp_name.contains(keyword),
            )
        )

    if stage:
        query = query.filter(Opportunity.stage == stage)

    if customer_id:
        query = query.filter(Opportunity.customer_id == customer_id)

    if owner_id:
        query = query.filter(Opportunity.owner_id == owner_id)

    total = query.count()
    offset = (page - 1) * page_size
    # 使用 eager loading 避免 N+1 查询
    # 默认按优先级排序，如果没有优先级则按创建时间排序
    opportunities = query.options(
        joinedload(Opportunity.customer),
        joinedload(Opportunity.owner),
        joinedload(Opportunity.requirements)
    ).order_by(
        desc(Opportunity.priority_score).nullslast(),
        desc(Opportunity.created_at)
    ).offset(offset).limit(page_size).all()

    opp_responses = []
    for opp in opportunities:
        # 获取第一个 requirement（如果存在）
        req = opp.requirements[0] if opp.requirements else None
        opp_dict = {
            **{c.name: getattr(opp, c.name) for c in opp.__table__.columns},
            "customer_name": opp.customer.customer_name if opp.customer else None,
            "owner_name": opp.owner.real_name if opp.owner else None,
            "requirement": None,
        }
        if req:
            opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})
        opp_responses.append(OpportunityResponse(**opp_dict))

    return PaginatedResponse(
        items=opp_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/opportunities", response_model=OpportunityResponse, status_code=201)
def create_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_in: OpportunityCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建商机
    """
    opp_data = opp_in.model_dump(exclude={"requirement"})
    
    # 如果没有提供编码，自动生成
    if not opp_data.get("opp_code"):
        opp_data["opp_code"] = generate_opportunity_code(db)
    else:
        # 检查编码是否已存在
        existing = db.query(Opportunity).filter(Opportunity.opp_code == opp_data["opp_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="商机编码已存在")
    
    # 如果没有指定负责人，默认使用当前用户
    if not opp_data.get("owner_id"):
        opp_data["owner_id"] = current_user.id

    customer = db.query(Customer).filter(Customer.id == opp_data["customer_id"]).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    opportunity = Opportunity(**opp_data)
    db.add(opportunity)
    db.flush()

    # 创建需求信息
    if opp_in.requirement:
        req_data = opp_in.requirement.model_dump()
        req_data["opportunity_id"] = opportunity.id
        requirement = OpportunityRequirement(**req_data)
        db.add(requirement)

    db.commit()
    db.refresh(opportunity)

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": customer.customer_name,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

    return OpportunityResponse(**opp_dict)


@router.get("/opportunities/{opp_id}", response_model=OpportunityResponse)
def read_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取商机详情
    """
    opportunity = db.query(Opportunity).options(joinedload(Opportunity.customer)).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}", response_model=OpportunityResponse)
def update_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    opp_in: OpportunityUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新商机
    Issue 7.2: 已集成操作权限检查
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # Issue 7.2: 检查编辑权限
    if not security.check_sales_edit_permission(
        current_user,
        db,
        get_entity_creator_id(opportunity),
        opportunity.owner_id,
    ):
        raise HTTPException(status_code=403, detail="您没有权限编辑此商机")

    update_data = opp_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(opportunity, field, value)

    db.commit()
    db.refresh(opportunity)

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

    return OpportunityResponse(**opp_dict)


@router.post("/opportunities/{opp_id}/gate", response_model=ResponseModel)
def submit_opportunity_gate(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    gate_request: GateSubmitRequest,
    gate_type: str = Query("G2", description="阶段门类型: G1, G2, G3, G4"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交商机阶段门（带自动验证）
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 根据阶段门类型进行验证
    validation_errors = []
    if gate_type == "G2":
        is_valid, errors = validate_g2_opportunity_to_quote(opportunity)
        if not is_valid:
            validation_errors = errors

    if validation_errors and gate_request.gate_status == "PASS":
        raise HTTPException(
            status_code=400,
            detail=f"{gate_type}阶段门验证失败: {', '.join(validation_errors)}"
        )

    opportunity.gate_status = gate_request.gate_status
    if gate_request.gate_status == "PASS":
        opportunity.gate_passed_at = datetime.now()

    db.commit()

    return ResponseModel(
        code=200,
        message=f"{gate_type}阶段门{'通过' if gate_request.gate_status == 'PASS' else '拒绝'}",
        data={"validation_errors": validation_errors} if validation_errors else None
    )


@router.put("/opportunities/{opp_id}/stage", response_model=OpportunityResponse)
def update_opportunity_stage(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    stage: str = Query(..., description="新阶段"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新商机阶段
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    valid_stages = ["DISCOVERY", "QUALIFIED", "PROPOSAL", "NEGOTIATION", "WON", "LOST", "ON_HOLD"]
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"无效的阶段，必须是: {', '.join(valid_stages)}")

    opportunity.stage = stage
    db.commit()
    db.refresh(opportunity)

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/score", response_model=OpportunityResponse)
def update_opportunity_score(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    score: int = Query(..., ge=0, le=100, description="评分"),
    score_remark: Optional[str] = Query(None, description="评分说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    商机评分（准入评估）
    评分范围：0-100分
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    opportunity.score = score
    
    # 根据评分自动更新风险等级
    if score >= 80:
        opportunity.risk_level = "LOW"
    elif score >= 60:
        opportunity.risk_level = "MEDIUM"
    else:
        opportunity.risk_level = "HIGH"
    
    db.commit()
    db.refresh(opportunity)

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/win", response_model=OpportunityResponse)
def win_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    赢单
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    opportunity.stage = "WON"
    opportunity.gate_status = "PASS"
    opportunity.gate_passed_at = datetime.now()
    db.commit()
    db.refresh(opportunity)

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/lose", response_model=OpportunityResponse)
def lose_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    reason: Optional[str] = Query(None, description="丢单原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    丢单
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    opportunity.stage = "LOST"
    db.commit()
    db.refresh(opportunity)

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

    return OpportunityResponse(**opp_dict)


@router.get("/opportunities/funnel", response_model=ResponseModel)
def get_opportunity_funnel(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    商机漏斗统计
    按阶段统计商机数量和金额，计算转化率
    """
    query = db.query(Opportunity)
    
    if start_date:
        query = query.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
    if owner_id:
        query = query.filter(Opportunity.owner_id == owner_id)
    
    stages = [stage.value for stage in OpportunityStageEnum]
    funnel_data = {}
    total_count = 0
    total_amount = 0
    
    for stage in stages:
        stage_query = query.filter(Opportunity.stage == stage)
        count = stage_query.count()
        amount_query = db.query(func.sum(Opportunity.est_amount)).filter(Opportunity.stage == stage)
        if start_date:
            amount_query = amount_query.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            amount_query = amount_query.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        if owner_id:
            amount_query = amount_query.filter(Opportunity.owner_id == owner_id)
        amount_result = amount_query.scalar() or 0
        
        funnel_data[stage] = {
            "count": count,
            "total_amount": float(amount_result),
            "avg_amount": float(amount_result / count) if count > 0 else 0
        }
        total_count += count
        total_amount += float(amount_result)
    
    # 计算转化率（从前一阶段到当前阶段）
    conversion_rates = {}
    prev_count = None
    for stage in stages:
        current_count = funnel_data[stage]["count"]
        if prev_count is not None and prev_count > 0:
            conversion_rates[stage] = round((current_count / prev_count) * 100, 2)
        else:
            conversion_rates[stage] = 100.0 if current_count > 0 else 0.0
        prev_count = current_count
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "funnel": funnel_data,
            "conversion_rates": conversion_rates,
            "total_count": total_count,
            "total_amount": total_amount
        }
    )


@router.get("/opportunities/{opp_id}/win-probability", response_model=ResponseModel)
def get_opportunity_win_probability(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.3: 商机赢单概率预测
    基于商机阶段、金额、历史赢单率
    """
    from app.services.sales_prediction_service import SalesPredictionService

    service = SalesPredictionService(db)
    probability = service.predict_win_probability(opportunity_id=opp_id)

    return ResponseModel(
        code=200,
        message="success",
        data=probability
    )


@router.get("/opportunities/export")
def export_opportunities(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.2: 导出商机列表（Excel）
    """
    from app.services.excel_export_service import ExcelExportService, create_excel_response

    query = db.query(Opportunity)
    if keyword:
        query = query.filter(or_(Opportunity.opp_code.contains(keyword), Opportunity.opp_name.contains(keyword), Opportunity.customer.has(Customer.customer_name.contains(keyword))))
    if stage:
        query = query.filter(Opportunity.stage == stage)
    if status:
        query = query.filter(Opportunity.status == status)
    if owner_id:
        query = query.filter(Opportunity.owner_id == owner_id)

    opportunities = query.order_by(Opportunity.created_at.desc()).all()
    export_service = ExcelExportService()
    columns = [
        {"key": "opp_code", "label": "商机编码", "width": 15},
        {"key": "opp_name", "label": "商机名称", "width": 30},
        {"key": "customer_name", "label": "客户名称", "width": 25},
        {"key": "stage", "label": "阶段", "width": 15},
        {"key": "est_amount", "label": "预估金额", "width": 15, "format": export_service.format_currency},
        {"key": "est_margin", "label": "预估毛利率", "width": 12, "format": export_service.format_percentage},
        {"key": "score", "label": "评分", "width": 8},
        {"key": "risk_level", "label": "风险等级", "width": 10},
        {"key": "owner_name", "label": "负责人", "width": 12},
        {"key": "gate_status", "label": "阶段门状态", "width": 15},
        {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
    ]

    data = [{
        "opp_code": opp.opp_code,
        "opp_name": opp.opp_name,
        "customer_name": opp.customer.customer_name if opp.customer else '',
        "stage": opp.stage,
        "est_amount": float(opp.est_amount) if opp.est_amount else 0,
        "est_margin": float(opp.est_margin) if opp.est_margin else 0,
        "score": opp.score or 0,
        "risk_level": opp.risk_level or '',
        "owner_name": opp.owner.real_name if opp.owner else '',
        "gate_status": opp.gate_status,
        "created_at": opp.created_at,
    } for opp in opportunities]

    excel_data = export_service.export_to_excel(data=data, columns=columns, sheet_name="商机列表", title="商机列表")
    filename = f"商机列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)
