# -*- coding: utf-8 -*-
"""
销售管理模块 API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Customer, Project, ProjectMilestone, ProjectPaymentPlan
from app.models.sales import (
    Lead, LeadFollowUp, Opportunity, OpportunityRequirement, Quote, QuoteVersion, QuoteItem,
    Contract, ContractDeliverable, ContractAmendment, Invoice, ReceivableDispute,
    QuoteApproval, ContractApproval, InvoiceApproval
)
from app.schemas.sales import (
    LeadCreate, LeadUpdate, LeadResponse, LeadFollowUpResponse, LeadFollowUpCreate,
    OpportunityCreate, OpportunityUpdate, OpportunityResponse, OpportunityRequirementResponse,
    GateSubmitRequest,
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteVersionCreate, QuoteVersionResponse,
    QuoteItemCreate, QuoteItemResponse, QuoteApproveRequest,
    ContractCreate, ContractUpdate, ContractResponse, ContractDeliverableResponse,
    ContractAmendmentCreate, ContractAmendmentResponse,
    ContractSignRequest, ContractProjectCreateRequest,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceIssueRequest,
    ReceivableDisputeCreate, ReceivableDisputeUpdate, ReceivableDisputeResponse,
    QuoteApprovalResponse, QuoteApprovalCreate,
    ContractApprovalResponse, ContractApprovalCreate,
    InvoiceApprovalResponse, InvoiceApprovalCreate
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


# ==================== 阶段门验证函数 ====================


def validate_g1_lead_to_opportunity(lead: Lead, requirement: Optional[OpportunityRequirement] = None) -> tuple[bool, List[str]]:
    """
    G1：线索 → 商机 验证
    需求模板必填：行业/产品对象/节拍/接口/现场约束/验收依据
    客户基本信息与联系人齐全
    """
    errors = []
    
    # 检查客户基本信息
    if not lead.customer_name:
        errors.append("客户名称不能为空")
    if not lead.contact_name:
        errors.append("联系人不能为空")
    if not lead.contact_phone:
        errors.append("联系电话不能为空")
    
    # 检查需求模板必填项
    if requirement:
        if not requirement.product_object:
            errors.append("产品对象不能为空")
        if not requirement.ct_seconds:
            errors.append("节拍(秒)不能为空")
        if not requirement.interface_desc:
            errors.append("接口/通信协议不能为空")
        if not requirement.site_constraints:
            errors.append("现场约束不能为空")
        if not requirement.acceptance_criteria:
            errors.append("验收依据不能为空")
    else:
        errors.append("需求信息不能为空")
    
    return len(errors) == 0, errors


def validate_g2_opportunity_to_quote(opportunity: Opportunity) -> tuple[bool, List[str]]:
    """
    G2：商机 → 报价 验证
    预算范围、决策链、交付窗口、验收标准明确
    技术可行性初评通过
    """
    errors = []
    
    if not opportunity.budget_range:
        errors.append("预算范围不能为空")
    if not opportunity.decision_chain:
        errors.append("决策链不能为空")
    if not opportunity.delivery_window:
        errors.append("交付窗口不能为空")
    if not opportunity.acceptance_basis:
        errors.append("验收标准不能为空")
    
    # 技术可行性初评（简化：检查是否有评分）
    if opportunity.score is None or opportunity.score < 60:
        errors.append("技术可行性初评未通过（评分需≥60分）")
    
    return len(errors) == 0, errors


def validate_g3_quote_to_contract(quote: Quote, version: QuoteVersion, items: List[QuoteItem]) -> tuple[bool, List[str], Optional[str]]:
    """
    G3：报价 → 合同 验证
    成本拆解齐备，毛利率低于阈值自动预警
    交期校验通过（关键物料交期 + 设计/装配/调试周期）
    风险条款与边界条款已补充
    """
    errors = []
    warnings = []
    
    # 检查成本拆解
    if not items or len(items) == 0:
        errors.append("报价明细不能为空")
    else:
        total_cost = sum(float(item.cost or 0) * float(item.qty or 0) for item in items)
        if total_cost == 0:
            errors.append("成本拆解不完整，总成本不能为0")
    
    # 检查毛利率
    total_price = float(version.total_price or 0)
    total_cost = float(version.cost_total or 0)
    if total_price > 0:
        gross_margin = (total_price - total_cost) / total_price * 100
        if gross_margin < 10:
            errors.append(f"毛利率过低（{gross_margin:.2f}%），低于最低阈值10%")
        elif gross_margin < 20:
            warnings.append(f"毛利率较低（{gross_margin:.2f}%），建议重新评估")
    
    # 检查交期
    if not version.lead_time_days or version.lead_time_days <= 0:
        errors.append("交期不能为空或必须大于0")
    elif version.lead_time_days < 30:
        warnings.append(f"交期较短（{version.lead_time_days}天），请确认关键物料交期和设计/装配/调试周期")
    
    # 检查风险条款
    if not version.risk_terms:
        warnings.append("风险条款未补充，建议补充风险条款与边界条款")
    
    warning_msg = "; ".join(warnings) if warnings else None
    return len(errors) == 0, errors, warning_msg


def validate_g4_contract_to_project(contract: Contract, deliverables: List[ContractDeliverable]) -> tuple[bool, List[str]]:
    """
    G4：合同 → 项目 验证
    付款节点与可交付物绑定
    SOW/验收标准/BOM初版/里程碑基线冻结
    """
    errors = []
    
    # 检查交付物
    if not deliverables or len(deliverables) == 0:
        errors.append("合同交付物不能为空")
    else:
        # 检查交付物是否必需（required_for_payment字段）
        # 注意：ContractDeliverable模型中没有payment_node字段，简化验证
        required_deliverables = [d for d in deliverables if d.required_for_payment]
        if len(required_deliverables) == 0:
            errors.append("至少需要一个付款必需的交付物")
    
    # 检查合同关键信息
    if not contract.contract_amount or contract.contract_amount <= 0:
        errors.append("合同金额不能为空或必须大于0")
    
    # 检查验收标准（简化：检查是否有验收摘要）
    if not contract.acceptance_summary:
        errors.append("验收摘要不能为空")
    
    # 检查合同是否已签订
    if contract.status != "SIGNED":
        errors.append("只有已签订的合同才能生成项目")
    
    return len(errors) == 0, errors


# ==================== 编码生成函数 ====================


def generate_lead_code(db: Session) -> str:
    """生成线索编码：L2507-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m")
    prefix = f"L{month_str}-"
    
    max_lead = (
        db.query(Lead)
        .filter(Lead.lead_code.like(f"{prefix}%"))
        .order_by(desc(Lead.lead_code))
        .first()
    )
    
    if max_lead:
        try:
            seq = int(max_lead.lead_code.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def generate_opportunity_code(db: Session) -> str:
    """生成商机编码：O2507-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m")
    prefix = f"O{month_str}-"
    
    max_opp = (
        db.query(Opportunity)
        .filter(Opportunity.opp_code.like(f"{prefix}%"))
        .order_by(desc(Opportunity.opp_code))
        .first()
    )
    
    if max_opp:
        try:
            seq = int(max_opp.opp_code.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def generate_quote_code(db: Session) -> str:
    """生成报价编码：Q2507-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m")
    prefix = f"Q{month_str}-"
    
    max_quote = (
        db.query(Quote)
        .filter(Quote.quote_code.like(f"{prefix}%"))
        .order_by(desc(Quote.quote_code))
        .first()
    )
    
    if max_quote:
        try:
            seq = int(max_quote.quote_code.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def generate_contract_code(db: Session) -> str:
    """生成合同编码：HT2507-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m")
    prefix = f"HT{month_str}-"
    
    max_contract = (
        db.query(Contract)
        .filter(Contract.contract_code.like(f"{prefix}%"))
        .order_by(desc(Contract.contract_code))
        .first()
    )
    
    if max_contract:
        try:
            seq = int(max_contract.contract_code.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def generate_amendment_no(db: Session, contract_code: str) -> str:
    """
    生成合同变更编号
    格式：{合同编码}-BG{序号}
    """
    prefix = f"{contract_code}-BG"
    
    # 查询该合同已有的变更记录数量
    count = db.query(ContractAmendment).filter(
        ContractAmendment.amendment_no.like(f"{prefix}%")
    ).count()
    
    seq = count + 1
    return f"{prefix}{seq:03d}"


def generate_invoice_code(db: Session) -> str:
    """生成发票编码：INV-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"INV-{today}-"
    
    max_invoice = (
        db.query(Invoice)
        .filter(Invoice.invoice_code.like(f"{prefix}%"))
        .order_by(desc(Invoice.invoice_code))
        .first()
    )
    
    if max_invoice:
        try:
            seq = int(max_invoice.invoice_code.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


# ==================== 线索 ====================


@router.get("/leads", response_model=PaginatedResponse[LeadResponse])
def read_leads(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索列表
    """
    query = db.query(Lead)

    if keyword:
        query = query.filter(
            or_(
                Lead.lead_code.contains(keyword),
                Lead.customer_name.contains(keyword),
                Lead.contact_name.contains(keyword),
            )
        )

    if status:
        query = query.filter(Lead.status == status)

    if owner_id:
        query = query.filter(Lead.owner_id == owner_id)

    total = query.count()
    offset = (page - 1) * page_size
    leads = query.order_by(desc(Lead.created_at)).offset(offset).limit(page_size).all()

    # 填充负责人名称
    lead_responses = []
    for lead in leads:
        lead_dict = {
            **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
            "owner_name": lead.owner.real_name if lead.owner else None,
        }
        lead_responses.append(LeadResponse(**lead_dict))

    return PaginatedResponse(
        items=lead_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/leads", response_model=LeadResponse, status_code=201)
def create_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_in: LeadCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建线索
    """
    # 如果没有提供编码，自动生成
    lead_data = lead_in.model_dump()
    if not lead_data.get("lead_code"):
        lead_data["lead_code"] = generate_lead_code(db)
    else:
        # 检查编码是否已存在
        existing = db.query(Lead).filter(Lead.lead_code == lead_data["lead_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="线索编码已存在")

    # 如果没有指定负责人，默认使用当前用户
    if not lead_data.get("owner_id"):
        lead_data["owner_id"] = current_user.id

    lead = Lead(**lead_data)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }
    return LeadResponse(**lead_dict)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def read_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索详情
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }
    return LeadResponse(**lead_dict)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    lead_in: LeadUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新线索
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    update_data = lead_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }
    return LeadResponse(**lead_dict)


@router.get("/leads/{lead_id}/follow-ups", response_model=List[LeadFollowUpResponse])
def get_lead_follow_ups(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索跟进记录列表
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    follow_ups = db.query(LeadFollowUp).filter(
        LeadFollowUp.lead_id == lead_id
    ).order_by(desc(LeadFollowUp.created_at)).all()

    result = []
    for follow_up in follow_ups:
        result.append({
            "id": follow_up.id,
            "lead_id": follow_up.lead_id,
            "follow_up_type": follow_up.follow_up_type,
            "content": follow_up.content,
            "next_action": follow_up.next_action,
            "next_action_at": follow_up.next_action_at,
            "created_by": follow_up.created_by,
            "attachments": follow_up.attachments,
            "created_at": follow_up.created_at,
            "updated_at": follow_up.updated_at,
            "creator_name": follow_up.creator.real_name if follow_up.creator else None,
        })

    return result


@router.post("/leads/{lead_id}/follow-ups", response_model=LeadFollowUpResponse, status_code=201)
def create_lead_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    follow_up_in: LeadFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加线索跟进记录
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    follow_up = LeadFollowUp(
        lead_id=lead_id,
        follow_up_type=follow_up_in.follow_up_type,
        content=follow_up_in.content,
        next_action=follow_up_in.next_action,
        next_action_at=follow_up_in.next_action_at,
        created_by=current_user.id,
        attachments=follow_up_in.attachments,
    )

    db.add(follow_up)
    
    # 如果设置了下次行动时间，更新线索的next_action_at
    if follow_up_in.next_action_at:
        lead.next_action_at = follow_up_in.next_action_at
    
    db.commit()
    db.refresh(follow_up)

    return {
        "id": follow_up.id,
        "lead_id": follow_up.lead_id,
        "follow_up_type": follow_up.follow_up_type,
        "content": follow_up.content,
        "next_action": follow_up.next_action,
        "next_action_at": follow_up.next_action_at,
        "created_by": follow_up.created_by,
        "attachments": follow_up.attachments,
        "created_at": follow_up.created_at,
        "updated_at": follow_up.updated_at,
        "creator_name": follow_up.creator.real_name if follow_up.creator else None,
    }


@router.post("/leads/{lead_id}/convert", response_model=OpportunityResponse, status_code=201)
def convert_lead_to_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    customer_id: int = Query(..., description="客户ID"),
    requirement_data: Optional[dict] = None,  # 需求数据，可以通过请求体传入
    skip_validation: bool = Query(False, description="跳过G1验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    线索转商机（G1阶段门验证）
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # G1验证
    requirement = None
    if requirement_data:
        requirement = OpportunityRequirement(**requirement_data)
    
    if not skip_validation:
        is_valid, errors = validate_g1_lead_to_opportunity(lead, requirement)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"G1阶段门验证失败: {', '.join(errors)}"
            )

    # 生成商机编码
    opp_code = generate_opportunity_code(db)

    opportunity = Opportunity(
        opp_code=opp_code,
        lead_id=lead_id,
        customer_id=customer_id,
        opp_name=f"{lead.customer_name} - {lead.demand_summary[:50] if lead.demand_summary else '商机'}",
        owner_id=lead.owner_id,
        stage="DISCOVERY",
        gate_status="PASS" if not skip_validation else "PENDING",
        gate_passed_at=datetime.now() if not skip_validation else None
    )

    db.add(opportunity)
    db.flush()

    # 创建需求信息
    if requirement:
        requirement.opportunity_id = opportunity.id
        db.add(requirement)

    # 更新线索状态
    lead.status = "CONVERTED"

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


# ==================== 商机 ====================


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
    """
    query = db.query(Opportunity).options(joinedload(Opportunity.customer))

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
    opportunities = query.options(
        joinedload(Opportunity.customer),
        joinedload(Opportunity.owner),
        joinedload(Opportunity.requirements)
    ).order_by(desc(Opportunity.created_at)).offset(offset).limit(page_size).all()

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
        from app.schemas.sales import OpportunityRequirementResponse
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
        from app.schemas.sales import OpportunityRequirementResponse
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
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

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
        from app.schemas.sales import OpportunityRequirementResponse
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
    # G1在转换时验证，G3在报价转合同时验证，G4在合同转项目时验证

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


# ==================== 报价 ====================


@router.get("/quotes", response_model=PaginatedResponse[QuoteResponse])
def read_quotes(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    opportunity_id: Optional[int] = Query(None, description="商机ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价列表
    """
    query = db.query(Quote).options(
        joinedload(Quote.opportunity),
        joinedload(Quote.customer),
        joinedload(Quote.owner)
    )

    if keyword:
        query = query.filter(Quote.quote_code.contains(keyword))

    if status:
        query = query.filter(Quote.status == status)

    if opportunity_id:
        query = query.filter(Quote.opportunity_id == opportunity_id)

    total = query.count()
    offset = (page - 1) * page_size
    quotes = query.order_by(desc(Quote.created_at)).offset(offset).limit(page_size).all()

    quote_responses = []
    for quote in quotes:
        versions = db.query(QuoteVersion).options(
            joinedload(QuoteVersion.creator),
            joinedload(QuoteVersion.approver)
        ).filter(QuoteVersion.quote_id == quote.id).all()
        quote_dict = {
            **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
            "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
            "customer_name": quote.customer.customer_name if quote.customer else None,
            "owner_name": quote.owner.real_name if quote.owner else None,
            "versions": [],
        }
        for v in versions:
            items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
            v_dict = {
                **{c.name: getattr(v, c.name) for c in v.__table__.columns},
                "created_by_name": v.creator.real_name if v.creator else None,
                "approved_by_name": v.approver.real_name if v.approver else None,
                "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
            }
            quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        quote_responses.append(QuoteResponse(**quote_dict))

    return PaginatedResponse(
        items=quote_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/quotes", response_model=QuoteResponse, status_code=201)
def create_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_in: QuoteCreate,
    skip_g2_validation: bool = Query(False, description="跳过G2验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建报价（G2阶段门验证）
    """
    # 检查商机是否存在
    opportunity = db.query(Opportunity).filter(Opportunity.id == quote_in.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")
    
    # G2验证
    if not skip_g2_validation:
        is_valid, errors = validate_g2_opportunity_to_quote(opportunity)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"G2阶段门验证失败: {', '.join(errors)}"
            )
    
    quote_data = quote_in.model_dump(exclude={"version"})
    
    # 如果没有提供编码，自动生成
    if not quote_data.get("quote_code"):
        quote_data["quote_code"] = generate_quote_code(db)
    else:
        existing = db.query(Quote).filter(Quote.quote_code == quote_data["quote_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="报价编码已存在")
    
    if not quote_data.get("owner_id"):
        quote_data["owner_id"] = current_user.id

    quote = Quote(**quote_data)
    db.add(quote)
    db.flush()

    # 创建报价版本
    if quote_in.version:
        version_data = quote_in.version.model_dump(exclude={"items"})
        version_data["quote_id"] = quote.id
        version_data["created_by"] = current_user.id
        version = QuoteVersion(**version_data)
        db.add(version)
        db.flush()

        quote.current_version_id = version.id

        # 创建报价明细
        if quote_in.version.items:
            for item_data in quote_in.version.items:
                item_dict = item_data.model_dump()
                item_dict["quote_version_id"] = version.id
                item = QuoteItem(**item_dict)
                db.add(item)

    db.commit()
    db.refresh(quote)

    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first() if quote.current_version_id else None
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all() if version else []
    
    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": opportunity.opp_code if opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }
    
    if version:
        version_dict = {
            **{c.name: getattr(version, c.name) for c in version.__table__.columns},
            "created_by_name": version.creator.real_name if version.creator else None,
            "approved_by_name": version.approver.real_name if version.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"] = [QuoteVersionResponse(**version_dict)]
    
    return QuoteResponse(**quote_dict)


@router.post("/quotes/{quote_id}/versions", response_model=QuoteVersionResponse, status_code=201)
def create_quote_version(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_in: QuoteVersionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建报价版本
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version_data = version_in.model_dump()
    version_data["quote_id"] = quote_id
    version_data["created_by"] = current_user.id
    version = QuoteVersion(**version_data)
    db.add(version)
    db.flush()

    # 创建报价明细
    if version_in.items:
        for item_data in version_in.items:
            item = QuoteItem(quote_version_id=version.id, **item_data.model_dump())
            db.add(item)

    db.commit()
    db.refresh(version)

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    version_dict = {
        **{c.name: getattr(version, c.name) for c in version.__table__.columns},
        "created_by_name": version.creator.real_name if version.creator else None,
        "approved_by_name": version.approver.real_name if version.approver else None,
        "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
    }
    return QuoteVersionResponse(**version_dict)


@router.post("/quotes/{quote_id}/approve", response_model=ResponseModel)
def approve_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approve_request: QuoteApproveRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批报价（单级审批，兼容旧接口）
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if not quote.current_version_id:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    if approve_request.approved:
        quote.status = "APPROVED"
        version.approved_by = current_user.id
        version.approved_at = datetime.now()
    else:
        quote.status = "REJECTED"

    db.commit()

    return ResponseModel(
        code=200,
        message="报价审批完成" if approve_request.approved else "报价已驳回"
    )


@router.get("/quotes/{quote_id}/approvals", response_model=List[QuoteApprovalResponse])
def get_quote_approvals(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价审批记录列表
    """
    approvals = db.query(QuoteApproval).filter(QuoteApproval.quote_id == quote_id).order_by(QuoteApproval.approval_level).all()
    
    result = []
    for approval in approvals:
        approver_name = None
        if approval.approver_id:
            approver = db.query(User).filter(User.id == approval.approver_id).first()
            approver_name = approver.real_name if approver else None
        
        result.append(QuoteApprovalResponse(
            id=approval.id,
            quote_id=approval.quote_id,
            approval_level=approval.approval_level,
            approval_role=approval.approval_role,
            approver_id=approval.approver_id,
            approver_name=approver_name,
            approval_result=approval.approval_result,
            approval_opinion=approval.approval_opinion,
            status=approval.status,
            approved_at=approval.approved_at,
            due_date=approval.due_date,
            is_overdue=approval.is_overdue or False,
            created_at=approval.created_at,
            updated_at=approval.updated_at
        ))
    
    return result


@router.put("/quote-approvals/{approval_id}/approve", response_model=QuoteApprovalResponse)
def approve_quote_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    approval_opinion: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过（多级审批）
    """
    approval = db.query(QuoteApproval).filter(QuoteApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限（简化版：检查用户角色）
    # TODO: 实现更严格的权限检查

    approval.approval_result = "APPROVED"
    approval.approval_opinion = approval_opinion
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 检查是否所有审批都已完成
    quote = db.query(Quote).filter(Quote.id == approval.quote_id).first()
    if quote:
        pending_approvals = db.query(QuoteApproval).filter(
            QuoteApproval.quote_id == approval.quote_id,
            QuoteApproval.status == "PENDING"
        ).count()

        if pending_approvals == 0:
            # 所有审批都已完成，更新报价状态
            quote.status = "APPROVED"
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            if version:
                version.approved_by = current_user.id
                version.approved_at = datetime.now()

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return QuoteApprovalResponse(
        id=approval.id,
        quote_id=approval.quote_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/quote-approvals/{approval_id}/reject", response_model=QuoteApprovalResponse)
def reject_quote_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回（多级审批）
    """
    approval = db.query(QuoteApproval).filter(QuoteApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    approval.approval_result = "REJECTED"
    approval.approval_opinion = rejection_reason
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 驳回后，报价状态变为被拒
    quote = db.query(Quote).filter(Quote.id == approval.quote_id).first()
    if quote:
        quote.status = "REJECTED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return QuoteApprovalResponse(
        id=approval.id,
        quote_id=approval.quote_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


# ==================== 合同 ====================


@router.get("/contracts", response_model=PaginatedResponse[ContractResponse])
def read_contracts(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同列表
    """
    query = db.query(Contract).options(
        joinedload(Contract.customer),
        joinedload(Contract.project),
        joinedload(Contract.opportunity),
        joinedload(Contract.owner)
    )

    if keyword:
        query = query.filter(Contract.contract_code.contains(keyword))

    if status:
        query = query.filter(Contract.status == status)

    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)

    total = query.count()
    offset = (page - 1) * page_size
    contracts = query.order_by(desc(Contract.created_at)).offset(offset).limit(page_size).all()

    contract_responses = []
    for contract in contracts:
        deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
        contract_dict = {
            **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
            "opportunity_code": contract.opportunity.opp_code if contract.opportunity else None,
            "customer_name": contract.customer.customer_name if contract.customer else None,
            "project_code": contract.project.project_code if contract.project else None,
            "owner_name": contract.owner.real_name if contract.owner else None,
            "deliverables": [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables],
        }
        contract_responses.append(ContractResponse(**contract_dict))

    return PaginatedResponse(
        items=contract_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/contracts", response_model=ContractResponse, status_code=201)
def create_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_in: ContractCreate,
    skip_g3_validation: bool = Query(False, description="跳过G3验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建合同（G3阶段门验证）
    """
    contract_data = contract_in.model_dump(exclude={"deliverables"})
    
    # 检查报价是否存在（如果提供了quote_version_id）
    quote = None
    version = None
    items = []
    if contract_data.get("quote_version_id"):
        quote = db.query(Quote).join(QuoteVersion).filter(QuoteVersion.id == contract_data["quote_version_id"]).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价不存在")
        
        version = db.query(QuoteVersion).filter(QuoteVersion.id == contract_data["quote_version_id"]).first()
        if version:
            items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
        
        # G3验证
        if not skip_g3_validation and version:
            is_valid, errors, warning = validate_g3_quote_to_contract(quote, version, items)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"G3阶段门验证失败: {', '.join(errors)}"
                )
            if warning:
                # 警告信息可以通过响应返回，但不阻止创建
                pass
    
    # 如果没有提供编码，自动生成
    if not contract_data.get("contract_code"):
        contract_data["contract_code"] = generate_contract_code(db)
    else:
        existing = db.query(Contract).filter(Contract.contract_code == contract_data["contract_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="合同编码已存在")
    
    # 如果没有指定负责人，默认使用当前用户
    if not contract_data.get("owner_id"):
        contract_data["owner_id"] = current_user.id

    opportunity = db.query(Opportunity).filter(Opportunity.id == contract_data["opportunity_id"]).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    customer = db.query(Customer).filter(Customer.id == contract_data["customer_id"]).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    contract = Contract(**contract_data)
    db.add(contract)
    db.flush()

    # 创建交付物清单
    if contract_in.deliverables:
        for deliverable_data in contract_in.deliverables:
            deliverable = ContractDeliverable(contract_id=contract.id, **deliverable_data.model_dump())
            db.add(deliverable)

    db.commit()
    db.refresh(contract)

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    contract_dict = {
        **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
        "opportunity_code": opportunity.opp_code,
        "customer_name": customer.customer_name,
        "project_code": contract.project.project_code if contract.project else None,
        "owner_name": contract.owner.real_name if contract.owner else None,
        "deliverables": [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables],
    }
    return ContractResponse(**contract_dict)


@router.post("/contracts/{contract_id}/sign", response_model=ResponseModel)
def sign_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    sign_request: ContractSignRequest,
    auto_generate_payment_plans: bool = Query(True, description="自动生成收款计划"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同签订（自动生成收款计划）
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    contract.signed_date = sign_request.signed_date
    contract.status = "SIGNED"
    
    # 自动生成收款计划
    if auto_generate_payment_plans and contract.project_id:
        _generate_payment_plans_from_contract(db, contract)
    
    db.commit()
    
    # 发送合同签订通知
    try:
        from app.services.sales_reminder_service import notify_contract_signed
        notify_contract_signed(db, contract.id)
        db.commit()
    except Exception as e:
        # 通知失败不影响主流程
        pass

    return ResponseModel(code=200, message="合同签订成功")


def _generate_payment_plans_from_contract(db: Session, contract: Contract) -> List[ProjectPaymentPlan]:
    """
    根据合同自动生成收款计划
    默认规则：
    - 预付款：30%（合同签订后）
    - 发货款：40%（发货里程碑）
    - 验收款：25%（验收里程碑）
    - 质保款：5%（质保结束）
    """
    if not contract.project_id:
        return []
    
    project = db.query(Project).filter(Project.id == contract.project_id).first()
    if not project:
        return []
    
    contract_amount = float(contract.contract_amount or 0)
    if contract_amount <= 0:
        return []
    
    # 检查是否已有收款计划
    existing_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.contract_id == contract.id
    ).count()
    if existing_plans > 0:
        return []  # 已有计划，不重复生成
    
    # 默认收款计划配置
    payment_configs = [
        {
            "payment_no": 1,
            "payment_name": "预付款",
            "payment_type": "ADVANCE",
            "payment_ratio": 30.0,
            "trigger_milestone": "合同签订",
            "trigger_condition": "合同签订后"
        },
        {
            "payment_no": 2,
            "payment_name": "发货款",
            "payment_type": "DELIVERY",
            "payment_ratio": 40.0,
            "trigger_milestone": "发货",
            "trigger_condition": "设备发货后"
        },
        {
            "payment_no": 3,
            "payment_name": "验收款",
            "payment_type": "ACCEPTANCE",
            "payment_ratio": 25.0,
            "trigger_milestone": "终验通过",
            "trigger_condition": "终验通过后"
        },
        {
            "payment_no": 4,
            "payment_name": "质保款",
            "payment_type": "WARRANTY",
            "payment_ratio": 5.0,
            "trigger_milestone": "质保结束",
            "trigger_condition": "质保期结束后"
        }
    ]
    
    # 如果合同有付款条款摘要，可以解析自定义的付款计划
    # 这里简化处理，使用默认配置
    
    plans = []
    from datetime import timedelta
    
    for config in payment_configs:
        planned_amount = contract_amount * config["payment_ratio"] / 100
        
        # 计算计划收款日期（基于合同签订日期和项目计划）
        planned_date = None
        if config["payment_no"] == 1:
            # 预付款：合同签订后7天
            planned_date = contract.signed_date + timedelta(days=7) if contract.signed_date else None
        elif config["payment_no"] == 2:
            # 发货款：预计项目中期
            if project.planned_end_date and project.planned_start_date:
                days = (project.planned_end_date - project.planned_start_date).days
                planned_date = project.planned_start_date + timedelta(days=int(days * 0.6)) if days > 0 else None
        elif config["payment_no"] == 3:
            # 验收款：项目结束前
            planned_date = project.planned_end_date
        elif config["payment_no"] == 4:
            # 质保款：项目结束后1年
            if project.planned_end_date:
                planned_date = project.planned_end_date + timedelta(days=365)
        
        plan = ProjectPaymentPlan(
            project_id=contract.project_id,
            contract_id=contract.id,
            payment_no=config["payment_no"],
            payment_name=config["payment_name"],
            payment_type=config["payment_type"],
            payment_ratio=config["payment_ratio"],
            planned_amount=planned_amount,
            planned_date=planned_date,
            trigger_milestone=config["trigger_milestone"],
            trigger_condition=config["trigger_condition"],
            status="PENDING"
        )
        db.add(plan)
        plans.append(plan)
    
    return plans


@router.post("/contracts/{contract_id}/project", response_model=ResponseModel)
def create_contract_project(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    project_request: ContractProjectCreateRequest,
    skip_g4_validation: bool = Query(False, description="跳过G4验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同生成项目（G4阶段门验证）
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 获取交付物清单
    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()
    
    # G4验证
    if not skip_g4_validation:
        is_valid, errors = validate_g4_contract_to_project(contract, deliverables)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"G4阶段门验证失败: {', '.join(errors)}"
            )

    # 检查项目编码是否已存在
    existing = db.query(Project).filter(Project.project_code == project_request.project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")

    # 创建项目
    project = Project(
        project_code=project_request.project_code,
        project_name=project_request.project_name,
        customer_id=contract.customer_id,
        contract_no=contract.contract_code,
        contract_amount=contract.contract_amount,
        contract_date=contract.signed_date,
        pm_id=project_request.pm_id,
        planned_start_date=project_request.planned_start_date,
        planned_end_date=project_request.planned_end_date,
    )

    # 填充客户信息
    customer = db.query(Customer).filter(Customer.id == contract.customer_id).first()
    if customer:
        project.customer_name = customer.customer_name
        project.customer_contact = customer.contact_person
        project.customer_phone = customer.contact_phone

    db.add(project)
    db.flush()

    # 关联合同和项目
    contract.project_id = project.id
    db.commit()

    return ResponseModel(code=200, message="项目创建成功", data={"project_id": project.id})


# ==================== 发票 ====================


@router.get("/invoices", response_model=PaginatedResponse[InvoiceResponse])
def read_invoices(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    获取发票列表
    """
    query = db.query(Invoice).options(
        joinedload(Invoice.contract).joinedload(Contract.customer),
        joinedload(Invoice.project)
    )

    if keyword:
        query = query.filter(Invoice.invoice_code.contains(keyword))

    if status:
        query = query.filter(Invoice.status == status)

    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)

    total = query.count()
    offset = (page - 1) * page_size
    invoices = query.order_by(desc(Invoice.created_at)).offset(offset).limit(page_size).all()

    invoice_responses = []
    for invoice in invoices:
        contract = invoice.contract
        project = invoice.project
        customer = contract.customer if contract else None
        invoice_dict = {
            **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
            "contract_code": contract.contract_code if contract else None,
            "project_code": project.project_code if project else None,
            "project_name": project.project_name if project else None,
            "customer_name": customer.customer_name if customer else None,
        }
        invoice_responses.append(InvoiceResponse(**invoice_dict))

    return PaginatedResponse(
        items=invoice_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_in: InvoiceCreate,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    创建发票
    """
    invoice_data = invoice_in.model_dump()
    
    # 如果没有提供编码，自动生成
    if not invoice_data.get("invoice_code"):
        invoice_data["invoice_code"] = generate_invoice_code(db)
    else:
        existing = db.query(Invoice).filter(Invoice.invoice_code == invoice_data["invoice_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="发票编码已存在")

    contract = db.query(Contract).filter(Contract.id == invoice_data["contract_id"]).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    invoice = Invoice(**invoice_data)
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    project = invoice.project
    customer = contract.customer if contract else None
    invoice_dict = {
        **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
        "contract_code": contract.contract_code,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "customer_name": customer.customer_name if customer else None,
    }
    return InvoiceResponse(**invoice_dict)


@router.post("/invoices/{invoice_id}/issue", response_model=ResponseModel)
def issue_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    issue_request: InvoiceIssueRequest,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    开票
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    invoice.issue_date = issue_request.issue_date
    invoice.status = "ISSUED"
    invoice.payment_status = "PENDING"
    
    # 如果没有设置到期日期，默认设置为开票日期后30天
    if not invoice.due_date and invoice.issue_date:
        from datetime import timedelta
        invoice.due_date = invoice.issue_date + timedelta(days=30)
    
    db.commit()
    
    # 发送发票开具通知
    try:
        from app.services.sales_reminder_service import notify_invoice_issued
        notify_invoice_issued(db, invoice.id)
        db.commit()
    except Exception as e:
        # 通知失败不影响主流程
        pass

    return ResponseModel(code=200, message="发票开票成功")


@router.delete("/invoices/{invoice_id}", status_code=200)
def delete_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    删除发票（仅限草稿状态）
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 只有草稿状态才能删除
    if invoice.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的发票才能删除")

    db.delete(invoice)
    db.commit()

    return ResponseModel(code=200, message="发票已删除")


@router.post("/invoices/{invoice_id}/receive-payment", response_model=ResponseModel)
def receive_payment(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    paid_amount: str = Query(..., description="收款金额"),
    paid_date: date = Query(..., description="收款日期"),
    remark: Optional[str] = Query(None, description="备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    记录发票收款
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if invoice.status != "ISSUED":
        raise HTTPException(status_code=400, detail="只有已开票的发票才能记录收款")

    # 更新收款信息
    current_paid = invoice.paid_amount or Decimal("0")
    paid_amount_decimal = Decimal(str(paid_amount))
    new_paid = current_paid + paid_amount_decimal
    invoice.paid_amount = new_paid
    invoice.paid_date = paid_date

    # 更新收款状态
    total = invoice.total_amount or invoice.amount or Decimal("0")
    if new_paid >= total:
        invoice.payment_status = "PAID"
    elif new_paid > Decimal("0"):
        invoice.payment_status = "PARTIAL"
    else:
        invoice.payment_status = "PENDING"

    if remark:
        invoice.remark = (invoice.remark or "") + f"\n收款备注: {remark}"

    db.commit()

    return ResponseModel(code=200, message="收款记录成功", data={
        "paid_amount": float(new_paid),
        "payment_status": invoice.payment_status
    })


# ==================== 回款争议 ====================


@router.get("/disputes", response_model=PaginatedResponse[ReceivableDisputeResponse])
def read_disputes(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取回款争议列表
    """
    query = db.query(ReceivableDispute)

    if status:
        query = query.filter(ReceivableDispute.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    disputes = query.order_by(desc(ReceivableDispute.created_at)).offset(offset).limit(page_size).all()

    dispute_responses = []
    for dispute in disputes:
        dispute_dict = {
            **{c.name: getattr(dispute, c.name) for c in dispute.__table__.columns},
            "responsible_name": dispute.responsible.real_name if dispute.responsible else None,
        }
        dispute_responses.append(ReceivableDisputeResponse(**dispute_dict))

    return PaginatedResponse(
        items=dispute_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/disputes", response_model=ReceivableDisputeResponse, status_code=201)
def create_dispute(
    *,
    db: Session = Depends(deps.get_db),
    dispute_in: ReceivableDisputeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建回款争议
    """
    dispute = ReceivableDispute(**dispute_in.model_dump())
    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    dispute_dict = {
        **{c.name: getattr(dispute, c.name) for c in dispute.__table__.columns},
        "responsible_name": dispute.responsible.real_name if dispute.responsible else None,
    }
    return ReceivableDisputeResponse(**dispute_dict)


# ==================== 统计报表 ====================


@router.get("/statistics/funnel", response_model=ResponseModel)
def get_sales_funnel(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取销售漏斗统计
    """
    query_leads = db.query(Lead)
    query_opps = db.query(Opportunity)
    query_quotes = db.query(Quote)
    query_contracts = db.query(Contract)

    if start_date:
        query_leads = query_leads.filter(Lead.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_quotes = query_quotes.filter(Quote.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_leads = query_leads.filter(Lead.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_quotes = query_quotes.filter(Quote.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))

    # 统计各阶段数量
    leads_count = query_leads.count()
    opps_count = query_opps.count()
    quotes_count = query_quotes.count()
    contracts_count = query_contracts.count()
    
    # 统计金额
    won_opps = query_opps.filter(Opportunity.stage == "WON").all()
    total_opp_amount = sum([float(opp.est_amount or 0) for opp in won_opps])
    
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    total_contract_amount = sum([float(contract.contract_amount or 0) for contract in signed_contracts])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "leads": leads_count,
            "opportunities": opps_count,
            "quotes": quotes_count,
            "contracts": contracts_count,
            "total_opportunity_amount": total_opp_amount,
            "total_contract_amount": total_contract_amount,
            "conversion_rates": {
                "lead_to_opp": round(opps_count / leads_count * 100, 2) if leads_count > 0 else 0,
                "opp_to_quote": round(quotes_count / opps_count * 100, 2) if opps_count > 0 else 0,
                "quote_to_contract": round(contracts_count / quotes_count * 100, 2) if quotes_count > 0 else 0,
            }
        }
    )


@router.get("/statistics/opportunities-by-stage", response_model=ResponseModel)
def get_opportunities_by_stage(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按阶段统计商机
    """
    stages = ["DISCOVERY", "QUALIFIED", "PROPOSAL", "NEGOTIATION", "WON", "LOST", "ON_HOLD"]
    result = {}
    
    for stage in stages:
        count = db.query(Opportunity).filter(Opportunity.stage == stage).count()
        total_amount = db.query(func.sum(Opportunity.est_amount)).filter(Opportunity.stage == stage).scalar() or 0
        result[stage] = {
            "count": count,
            "total_amount": float(total_amount)
        }
    
    return ResponseModel(code=200, message="success", data=result)


@router.get("/statistics/revenue-forecast", response_model=ResponseModel)
def get_revenue_forecast(
    db: Session = Depends(deps.get_db),
    months: int = Query(3, ge=1, le=12, description="预测月数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    收入预测（基于已签订合同和进行中的商机）
    """
    from datetime import timedelta
    from calendar import monthrange
    
    today = date.today()
    forecast = []
    
    for i in range(months):
        forecast_date = today + timedelta(days=30 * (i + 1))
        month_start = forecast_date.replace(day=1)
        _, last_day = monthrange(forecast_date.year, forecast_date.month)
        month_end = forecast_date.replace(day=last_day)
        
        # 统计该月预计签约的合同金额（基于商机预计金额）
        opps_in_month = (
            db.query(Opportunity)
            .filter(Opportunity.stage.in_(["PROPOSAL", "NEGOTIATION"]))
            .all()
        )
        
        # 简化处理：假设进行中的商机在接下来几个月平均分布
        estimated_revenue = sum([float(opp.est_amount or 0) for opp in opps_in_month]) / months
        
        forecast.append({
            "month": forecast_date.strftime("%Y-%m"),
            "estimated_revenue": round(estimated_revenue, 2)
        })
    
    return ResponseModel(code=200, message="success", data={"forecast": forecast})


@router.get("/contracts/{contract_id}/deliverables", response_model=List[ContractDeliverableResponse])
def get_contract_deliverables(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同交付物清单
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()
    return [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables]


@router.get("/contracts/{contract_id}/amendments", response_model=List[ContractAmendmentResponse])
def get_contract_amendments(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同变更记录列表
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    query = db.query(ContractAmendment).filter(ContractAmendment.contract_id == contract_id)
    
    if status:
        query = query.filter(ContractAmendment.status == status)
    
    amendments = query.order_by(desc(ContractAmendment.request_date), desc(ContractAmendment.created_at)).all()

    result = []
    for amendment in amendments:
        result.append({
            "id": amendment.id,
            "contract_id": amendment.contract_id,
            "amendment_no": amendment.amendment_no,
            "amendment_type": amendment.amendment_type,
            "title": amendment.title,
            "description": amendment.description,
            "reason": amendment.reason,
            "old_value": amendment.old_value,
            "new_value": amendment.new_value,
            "amount_change": amendment.amount_change,
            "schedule_impact": amendment.schedule_impact,
            "other_impact": amendment.other_impact,
            "requestor_id": amendment.requestor_id,
            "requestor_name": amendment.requestor.real_name if amendment.requestor else None,
            "request_date": amendment.request_date,
            "status": amendment.status,
            "approver_id": amendment.approver_id,
            "approver_name": amendment.approver.real_name if amendment.approver else None,
            "approval_date": amendment.approval_date,
            "approval_comment": amendment.approval_comment,
            "attachments": amendment.attachments,
            "created_at": amendment.created_at,
            "updated_at": amendment.updated_at,
        })

    return result


@router.post("/contracts/{contract_id}/amendments", response_model=ContractAmendmentResponse, status_code=201)
def create_contract_amendment(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    amendment_in: ContractAmendmentCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建合同变更记录
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 生成变更编号
    amendment_no = generate_amendment_no(db, contract.contract_code)

    amendment = ContractAmendment(
        contract_id=contract_id,
        amendment_no=amendment_no,
        amendment_type=amendment_in.amendment_type,
        title=amendment_in.title,
        description=amendment_in.description,
        reason=amendment_in.reason,
        old_value=amendment_in.old_value,
        new_value=amendment_in.new_value,
        amount_change=amendment_in.amount_change,
        schedule_impact=amendment_in.schedule_impact,
        other_impact=amendment_in.other_impact,
        requestor_id=current_user.id,
        request_date=amendment_in.request_date,
        status="PENDING",
        attachments=amendment_in.attachments,
    )

    db.add(amendment)
    db.commit()
    db.refresh(amendment)

    return {
        "id": amendment.id,
        "contract_id": amendment.contract_id,
        "amendment_no": amendment.amendment_no,
        "amendment_type": amendment.amendment_type,
        "title": amendment.title,
        "description": amendment.description,
        "reason": amendment.reason,
        "old_value": amendment.old_value,
        "new_value": amendment.new_value,
        "amount_change": amendment.amount_change,
        "schedule_impact": amendment.schedule_impact,
        "other_impact": amendment.other_impact,
        "requestor_id": amendment.requestor_id,
        "requestor_name": amendment.requestor.real_name if amendment.requestor else None,
        "request_date": amendment.request_date,
        "status": amendment.status,
        "approver_id": amendment.approver_id,
        "approver_name": amendment.approver.real_name if amendment.approver else None,
        "approval_date": amendment.approval_date,
        "approval_comment": amendment.approval_comment,
        "attachments": amendment.attachments,
        "created_at": amendment.created_at,
        "updated_at": amendment.updated_at,
    }


@router.get("/quotes/{quote_id}/versions", response_model=List[QuoteVersionResponse])
def get_quote_versions(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价的所有版本
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote_id).order_by(desc(QuoteVersion.created_at)).all()
    
    version_responses = []
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        version_responses.append(QuoteVersionResponse(**v_dict))
    
    return version_responses


@router.get("/statistics/summary", response_model=ResponseModel)
def get_sales_summary(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取销售汇总统计
    """
    query_leads = db.query(Lead)
    query_opps = db.query(Opportunity)
    query_contracts = db.query(Contract)
    query_invoices = db.query(Invoice)

    if start_date:
        query_leads = query_leads.filter(Lead.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_invoices = query_invoices.filter(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_leads = query_leads.filter(Lead.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_invoices = query_invoices.filter(Invoice.created_at <= datetime.combine(end_date, datetime.max.time()))

    # 线索统计
    total_leads = query_leads.count()
    converted_leads = query_leads.filter(Lead.status == "CONVERTED").count()

    # 商机统计
    total_opportunities = query_opps.count()
    won_opportunities = query_opps.filter(Opportunity.stage == "WON").count()

    # 合同统计
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    total_contract_amount = sum([float(c.contract_amount or 0) for c in signed_contracts])

    # 发票统计
    paid_invoices = query_invoices.filter(Invoice.payment_status == "PAID").all()
    paid_amount = sum([float(inv.paid_amount or 0) for inv in paid_invoices])

    # 计算转化率
    conversion_rate = round((converted_leads / total_leads * 100), 2) if total_leads > 0 else 0
    win_rate = round((won_opportunities / total_opportunities * 100), 2) if total_opportunities > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "total_opportunities": total_opportunities,
            "won_opportunities": won_opportunities,
            "total_contract_amount": total_contract_amount,
            "paid_amount": paid_amount,
            "conversion_rate": conversion_rate,
            "win_rate": win_rate,
        }
    )


# ==================== 线索管理补充 ====================


@router.put("/leads/{lead_id}/invalid", response_model=ResponseModel)
def mark_lead_invalid(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    reason: Optional[str] = Query(None, description="无效原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记线索无效
    """
    from app.models.enums import LeadStatusEnum
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    if lead.status == LeadStatusEnum.CONVERTED:
        raise HTTPException(status_code=400, detail="已转商机的线索不能标记为无效")

    lead.status = LeadStatusEnum.INVALID
    db.commit()

    # 可选：记录一条跟进记录说明无效原因
    if reason:
        follow_up = LeadFollowUp(
            lead_id=lead_id,
            follow_up_type="OTHER",
            content=f"标记为无效：{reason}",
            created_by=current_user.id,
        )
        db.add(follow_up)
        db.commit()

    return ResponseModel(code=200, message="线索已标记为无效")


# ==================== 商机管理补充 ====================


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
        from app.schemas.sales import OpportunityRequirementResponse
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
    评分标准：
    - 90-100分：优秀，优先跟进
    - 70-89分：良好，正常跟进
    - 60-69分：一般，谨慎跟进
    - 0-59分：较差，需要评估是否继续
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    old_score = opportunity.score
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
        from app.schemas.sales import OpportunityRequirementResponse
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
        from app.schemas.sales import OpportunityRequirementResponse
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
        from app.schemas.sales import OpportunityRequirementResponse
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
    from app.models.enums import OpportunityStageEnum
    
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


# ==================== 报价管理补充 ====================


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
def read_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价详情
    """
    quote = db.query(Quote).options(joinedload(Quote.opportunity), joinedload(Quote.customer)).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote.id).all()
    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        if v.id == quote.current_version_id:
            quote_dict["current_version"] = QuoteVersionResponse(**v_dict)

    return QuoteResponse(**quote_dict)


@router.put("/quotes/{quote_id}", response_model=QuoteResponse)
def update_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    quote_in: QuoteUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新报价
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    update_data = quote_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quote, field, value)

    db.commit()
    db.refresh(quote)

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote.id).all()
    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        if v.id == quote.current_version_id:
            quote_dict["current_version"] = QuoteVersionResponse(**v_dict)

    return QuoteResponse(**quote_dict)


@router.get("/quotes/{quote_id}/items", response_model=List[QuoteItemResponse])
def get_quote_items(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价明细列表
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    return [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items]


@router.post("/quotes/{quote_id}/items", response_model=QuoteItemResponse, status_code=201)
def create_quote_item(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    item_in: QuoteItemCreate,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加报价明细
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    item = QuoteItem(quote_version_id=target_version_id, **item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    return QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.get("/quotes/{quote_id}/cost-breakdown", response_model=ResponseModel)
def get_quote_cost_breakdown(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价成本拆解
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()

    total_price = float(version.total_price or 0)
    total_cost = float(version.cost_total or 0)
    gross_margin = float(version.gross_margin or 0) if version.gross_margin else (total_price - total_cost) / total_price * 100 if total_price > 0 else 0

    cost_breakdown = []
    for item in items:
        item_price = float(item.qty or 0) * float(item.unit_price or 0)
        item_cost = float(item.cost or 0) * float(item.qty or 0)
        item_margin = (item_price - item_cost) / item_price * 100 if item_price > 0 else 0
        cost_breakdown.append({
            "item_name": item.item_name,
            "item_type": item.item_type,
            "qty": float(item.qty or 0),
            "unit_price": float(item.unit_price or 0),
            "total_price": item_price,
            "unit_cost": float(item.cost or 0),
            "total_cost": item_cost,
            "margin": round(item_margin, 2)
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_price": total_price,
            "total_cost": total_cost,
            "gross_margin": round(gross_margin, 2),
            "breakdown": cost_breakdown
        }
    )


@router.put("/quotes/{quote_id}/submit", response_model=ResponseModel)
def submit_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交审批
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if not quote.current_version_id:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    quote.status = "PENDING_APPROVAL"
    db.commit()

    return ResponseModel(code=200, message="报价已提交审批")


@router.put("/quotes/{quote_id}/reject", response_model=ResponseModel)
def reject_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    reason: Optional[str] = Query(None, description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    quote.status = "REJECTED"
    db.commit()

    return ResponseModel(code=200, message="报价已驳回")


@router.put("/quotes/{quote_id}/send", response_model=ResponseModel)
def send_quote_to_customer(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    send_method: Optional[str] = Query("EMAIL", description="发送方式：EMAIL/PRINT/OTHER"),
    send_to: Optional[str] = Query(None, description="发送对象（邮箱/联系人等）"),
    remark: Optional[str] = Query(None, description="发送备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发送报价给客户
    只有已审批通过的报价才能发送给客户
    """
    from app.models.enums import QuoteStatusEnum
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status != QuoteStatusEnum.APPROVED:
        raise HTTPException(status_code=400, detail="只有已审批通过的报价才能发送给客户")

    # 更新报价状态为已发送（如果有SENT状态，否则保持APPROVED）
    # 这里简化处理，不改变状态，只记录发送操作
    
    # 可选：记录发送日志或通知
    
    return ResponseModel(
        code=200,
        message="报价已发送给客户",
        data={
            "quote_id": quote_id,
            "send_method": send_method,
            "send_to": send_to,
            "sent_at": datetime.now().isoformat()
        }
    )


# ==================== 合同管理补充 ====================


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
def read_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同详情
    """
    contract = db.query(Contract).options(
        joinedload(Contract.customer),
        joinedload(Contract.project),
        joinedload(Contract.opportunity),
        joinedload(Contract.owner)
    ).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    contract_dict = {
        **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
        "opportunity_code": contract.opportunity.opp_code if contract.opportunity else None,
        "customer_name": contract.customer.customer_name if contract.customer else None,
        "project_code": contract.project.project_code if contract.project else None,
        "owner_name": contract.owner.real_name if contract.owner else None,
        "deliverables": [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables],
    }
    return ContractResponse(**contract_dict)


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
def update_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    contract_in: ContractUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新合同
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    update_data = contract_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)

    db.commit()
    db.refresh(contract)

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    contract_dict = {
        **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
        "opportunity_code": contract.opportunity.opp_code if contract.opportunity else None,
        "customer_name": contract.customer.customer_name if contract.customer else None,
        "project_code": contract.project.project_code if contract.project else None,
        "owner_name": contract.owner.real_name if contract.owner else None,
        "deliverables": [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables],
    }
    return ContractResponse(**contract_dict)


@router.put("/contracts/{contract_id}/approve", response_model=ResponseModel)
def approve_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    approved: bool = Query(..., description="是否批准"),
    remark: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同审批
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    if approved:
        contract.status = "APPROVED"
    else:
        contract.status = "REJECTED"

    db.commit()

    return ResponseModel(code=200, message="合同审批完成" if approved else "合同已驳回")


# ==================== 开票管理补充 ====================


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def read_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票详情
    """
    invoice = db.query(Invoice).options(
        joinedload(Invoice.contract).joinedload(Contract.customer),
        joinedload(Invoice.project)
    ).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    contract = invoice.contract
    project = invoice.project
    customer = contract.customer if contract else None
    invoice_dict = {
        **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
        "contract_code": contract.contract_code if contract else None,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "customer_name": customer.customer_name if customer else None,
    }
    return InvoiceResponse(**invoice_dict)


@router.put("/invoices/{invoice_id}/approve", response_model=ResponseModel)
def approve_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    approved: bool = Query(..., description="是否批准"),
    remark: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开票审批（单级审批，兼容旧接口）
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if approved:
        invoice.status = "APPROVED"
    else:
        invoice.status = "REJECTED"

    db.commit()

    return ResponseModel(code=200, message="发票审批完成" if approved else "发票已驳回")


@router.put("/invoices/{invoice_id}/submit-approval", response_model=ResponseModel)
def submit_invoice_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交发票审批（创建多级审批记录）
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 检查是否已有审批记录
    existing_approvals = db.query(InvoiceApproval).filter(InvoiceApproval.invoice_id == invoice_id).count()
    if existing_approvals > 0:
        raise HTTPException(status_code=400, detail="发票已提交审批，请勿重复提交")

    # 根据发票金额确定审批流程
    invoice_amount = float(invoice.total_amount or invoice.amount or 0)
    
    # 审批流程：根据金额确定审批层级
    # 小于10万：财务（1级）
    # 10-50万：财务（1级）+ 财务经理（2级）
    # 大于50万：财务（1级）+ 财务经理（2级）+ 财务总监（3级）
    
    approval_levels = []
    if invoice_amount < 100000:
        approval_levels = [1]  # 财务
    elif invoice_amount < 500000:
        approval_levels = [1, 2]  # 财务 + 财务经理
    else:
        approval_levels = [1, 2, 3]  # 财务 + 财务经理 + 财务总监

    # 创建审批记录
    from datetime import timedelta
    role_map = {1: "财务", 2: "财务经理", 3: "财务总监"}
    for level in approval_levels:
        approval = InvoiceApproval(
            invoice_id=invoice_id,
            approval_level=level,
            approval_role=role_map.get(level, "审批人"),
            status="PENDING",
            due_date=datetime.now() + timedelta(days=2)  # 默认2天审批期限
        )
        db.add(approval)

    invoice.status = "APPLIED"
    db.commit()

    return ResponseModel(code=200, message="发票已提交审批", data={"approval_levels": len(approval_levels)})


@router.get("/invoices/{invoice_id}/approvals", response_model=List[InvoiceApprovalResponse])
def get_invoice_approvals(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批记录列表
    """
    approvals = db.query(InvoiceApproval).filter(InvoiceApproval.invoice_id == invoice_id).order_by(InvoiceApproval.approval_level).all()
    
    result = []
    for approval in approvals:
        approver_name = None
        if approval.approver_id:
            approver = db.query(User).filter(User.id == approval.approver_id).first()
            approver_name = approver.real_name if approver else None
        
        result.append(InvoiceApprovalResponse(
            id=approval.id,
            invoice_id=approval.invoice_id,
            approval_level=approval.approval_level,
            approval_role=approval.approval_role,
            approver_id=approval.approver_id,
            approver_name=approver_name,
            approval_result=approval.approval_result,
            approval_opinion=approval.approval_opinion,
            status=approval.status,
            approved_at=approval.approved_at,
            due_date=approval.due_date,
            is_overdue=approval.is_overdue or False,
            created_at=approval.created_at,
            updated_at=approval.updated_at
        ))
    
    return result


@router.put("/invoice-approvals/{approval_id}/approve", response_model=InvoiceApprovalResponse)
def approve_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    approval_opinion: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过（多级审批）
    """
    approval = db.query(InvoiceApproval).filter(InvoiceApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    approval.approval_result = "APPROVED"
    approval.approval_opinion = approval_opinion
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 检查是否所有审批都已完成
    invoice = db.query(Invoice).filter(Invoice.id == approval.invoice_id).first()
    if invoice:
        pending_approvals = db.query(InvoiceApproval).filter(
            InvoiceApproval.invoice_id == approval.invoice_id,
            InvoiceApproval.status == "PENDING"
        ).count()

        if pending_approvals == 0:
            # 所有审批都已完成，更新发票状态
            invoice.status = "APPROVED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return InvoiceApprovalResponse(
        id=approval.id,
        invoice_id=approval.invoice_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/invoice-approvals/{approval_id}/reject", response_model=InvoiceApprovalResponse)
def reject_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回（多级审批）
    """
    approval = db.query(InvoiceApproval).filter(InvoiceApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    approval.approval_result = "REJECTED"
    approval.approval_opinion = rejection_reason
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 驳回后，发票状态变为被拒
    invoice = db.query(Invoice).filter(Invoice.id == approval.invoice_id).first()
    if invoice:
        invoice.status = "REJECTED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return InvoiceApprovalResponse(
        id=approval.id,
        invoice_id=approval.invoice_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/invoices/{invoice_id}/void", response_model=ResponseModel)
def void_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    reason: Optional[str] = Query(None, description="作废原因"),
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    作废发票
    """
    from app.models.enums import InvoiceStatusEnum
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 只有已开票或已审批的发票才能作废
    if invoice.status not in [InvoiceStatusEnum.ISSUED, InvoiceStatusEnum.APPROVED]:
        raise HTTPException(status_code=400, detail="只有已开票或已审批的发票才能作废")

    # 如果已收款，不能作废
    if invoice.paid_amount and invoice.paid_amount > 0:
        raise HTTPException(status_code=400, detail="已收款的发票不能作废，请先处理收款")

    invoice.status = InvoiceStatusEnum.VOIDED
    if reason:
        invoice.remark = (invoice.remark or "") + f"\n作废原因: {reason}"
    
    db.commit()

    return ResponseModel(code=200, message="发票已作废")


# ==================== 销售报表补充 ====================


@router.get("/reports/sales-funnel", response_model=ResponseModel)
def get_sales_funnel_report(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售漏斗报表
    """
    # 复用已有的统计逻辑
    return get_sales_funnel(db, start_date, end_date, current_user)


@router.get("/reports/win-loss", response_model=ResponseModel)
def get_win_loss_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    赢单/丢单分析
    """
    query = db.query(Opportunity)

    if start_date:
        query = query.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))

    won_opps = query.filter(Opportunity.stage == "WON").all()
    lost_opps = query.filter(Opportunity.stage == "LOST").all()

    won_count = len(won_opps)
    lost_count = len(lost_opps)
    total_count = won_count + lost_count
    win_rate = round(won_count / total_count * 100, 2) if total_count > 0 else 0

    won_amount = sum([float(opp.est_amount or 0) for opp in won_opps])
    lost_amount = sum([float(opp.est_amount or 0) for opp in lost_opps])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "won": {
                "count": won_count,
                "amount": won_amount
            },
            "lost": {
                "count": lost_count,
                "amount": lost_amount
            },
            "win_rate": win_rate,
            "total_count": total_count
        }
    )


@router.get("/reports/sales-performance", response_model=ResponseModel)
def get_sales_performance(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    owner_id: Optional[int] = Query(None, description="负责人ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售业绩统计
    """
    query_opps = db.query(Opportunity)
    query_contracts = db.query(Contract)
    query_invoices = db.query(Invoice)

    if start_date:
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_invoices = query_invoices.filter(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_invoices = query_invoices.filter(Invoice.created_at <= datetime.combine(end_date, datetime.max.time()))

    if owner_id:
        query_opps = query_opps.filter(Opportunity.owner_id == owner_id)
        query_contracts = query_contracts.filter(Contract.owner_id == owner_id)

    won_opps = query_opps.filter(Opportunity.stage == "WON").all()
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    issued_invoices = query_invoices.filter(Invoice.status == "ISSUED").all()

    total_opp_amount = sum([float(opp.est_amount or 0) for opp in won_opps])
    total_contract_amount = sum([float(c.contract_amount or 0) for c in signed_contracts])
    total_invoice_amount = sum([float(inv.amount or 0) for inv in issued_invoices])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "won_opportunities": len(won_opps),
            "total_opportunity_amount": total_opp_amount,
            "signed_contracts": len(signed_contracts),
            "total_contract_amount": total_contract_amount,
            "issued_invoices": len(issued_invoices),
            "total_invoice_amount": total_invoice_amount
        }
    )


@router.get("/reports/customer-contribution", response_model=ResponseModel)
def get_customer_contribution(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    top_n: int = Query(10, ge=1, le=50, description="返回前N名"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户贡献分析
    """
    query_contracts = db.query(Contract).filter(Contract.status == "SIGNED")

    if start_date:
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))

    contracts = query_contracts.all()

    # 按客户统计
    customer_stats = {}
    for contract in contracts:
        customer_id = contract.customer_id
        if customer_id not in customer_stats:
            customer = contract.customer
            customer_stats[customer_id] = {
                "customer_id": customer_id,
                "customer_name": customer.customer_name if customer else None,
                "contract_count": 0,
                "total_amount": 0
            }
        customer_stats[customer_id]["contract_count"] += 1
        customer_stats[customer_id]["total_amount"] += float(contract.contract_amount or 0)

    # 排序并取前N名
    sorted_customers = sorted(customer_stats.values(), key=lambda x: x["total_amount"], reverse=True)[:top_n]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "customers": sorted_customers,
            "total_customers": len(customer_stats)
        }
    )


@router.get("/reports/o2c-pipeline", response_model=ResponseModel)
def get_o2c_pipeline(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    O2C流程全链路统计
    """
    from datetime import date as date_type
    today = date_type.today()

    # 线索统计
    query_leads = db.query(Lead)
    if start_date:
        query_leads = query_leads.filter(Lead.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_leads = query_leads.filter(Lead.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    total_leads = query_leads.count()
    converted_leads = query_leads.filter(Lead.status == "CONVERTED").count()

    # 商机统计
    query_opps = db.query(Opportunity)
    if start_date:
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    total_opps = query_opps.count()
    won_opps = query_opps.filter(Opportunity.stage == "WON").all()
    won_count = len(won_opps)
    won_amount = sum([float(opp.est_amount or 0) for opp in won_opps])

    # 报价统计
    query_quotes = db.query(Quote)
    if start_date:
        query_quotes = query_quotes.filter(Quote.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_quotes = query_quotes.filter(Quote.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    total_quotes = query_quotes.count()
    approved_quotes = query_quotes.filter(Quote.status == "APPROVED").all()
    approved_amount = sum([float(q.total_price or 0) for q in approved_quotes])

    # 合同统计
    query_contracts = db.query(Contract)
    if start_date:
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    total_contracts = query_contracts.count()
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    signed_amount = sum([float(c.contract_amount or 0) for c in signed_contracts])

    # 发票统计
    query_invoices = db.query(Invoice)
    if start_date:
        query_invoices = query_invoices.filter(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_invoices = query_invoices.filter(Invoice.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    total_invoices = query_invoices.filter(Invoice.status == "ISSUED").count()
    issued_invoices = query_invoices.filter(Invoice.status == "ISSUED").all()
    issued_amount = sum([float(inv.total_amount or inv.amount or 0) for inv in issued_invoices])

    # 收款统计
    paid_invoices = query_invoices.filter(Invoice.payment_status == "PAID").all()
    paid_amount = sum([float(inv.paid_amount or 0) for inv in paid_invoices])
    
    partial_invoices = query_invoices.filter(Invoice.payment_status == "PARTIAL").all()
    partial_amount = sum([float(inv.paid_amount or 0) for inv in partial_invoices])
    
    pending_invoices = query_invoices.filter(Invoice.payment_status == "PENDING").all()
    pending_amount = sum([float(inv.total_amount or inv.amount or 0) - float(inv.paid_amount or 0) for inv in pending_invoices])
    
    # 逾期统计
    overdue_invoices = query_invoices.filter(
        Invoice.status == "ISSUED",
        Invoice.due_date < today,
        Invoice.payment_status.in_(["PENDING", "PARTIAL"])
    ).all()
    overdue_amount = sum([float(inv.total_amount or inv.amount or 0) - float(inv.paid_amount or 0) for inv in overdue_invoices])

    # 计算转化率
    conversion_rate = round(converted_leads / total_leads * 100, 2) if total_leads > 0 else 0
    win_rate = round(won_count / total_opps * 100, 2) if total_opps > 0 else 0
    quote_to_contract_rate = round(total_contracts / total_quotes * 100, 2) if total_quotes > 0 else 0
    contract_to_invoice_rate = round(total_invoices / len(signed_contracts) * 100, 2) if signed_contracts else 0
    collection_rate = round(paid_amount / issued_amount * 100, 2) if issued_amount > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "leads": {
                "total": total_leads,
                "converted": converted_leads,
                "conversion_rate": conversion_rate
            },
            "opportunities": {
                "total": total_opps,
                "won": won_count,
                "won_amount": won_amount,
                "win_rate": win_rate
            },
            "quotes": {
                "total": total_quotes,
                "approved": len(approved_quotes),
                "approved_amount": approved_amount
            },
            "contracts": {
                "total": total_contracts,
                "signed": len(signed_contracts),
                "signed_amount": signed_amount,
                "quote_to_contract_rate": quote_to_contract_rate
            },
            "invoices": {
                "total": total_invoices,
                "issued_amount": issued_amount,
                "contract_to_invoice_rate": contract_to_invoice_rate
            },
            "receivables": {
                "paid_amount": paid_amount,
                "partial_amount": partial_amount,
                "pending_amount": pending_amount,
                "overdue_count": len(overdue_invoices),
                "overdue_amount": overdue_amount,
                "collection_rate": collection_rate
            },
            "pipeline_health": {
                "lead_to_opp_rate": round(total_opps / total_leads * 100, 2) if total_leads > 0 else 0,
                "opp_to_quote_rate": round(total_quotes / total_opps * 100, 2) if total_opps > 0 else 0,
                "quote_to_contract_rate": quote_to_contract_rate,
                "contract_to_invoice_rate": contract_to_invoice_rate,
                "collection_rate": collection_rate
            }
        }
    )


# ==================== 回款管理 ====================


@router.get("/payments", response_model=PaginatedResponse)
def get_payment_records(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    payment_status: Optional[str] = Query(None, description="收款状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取回款记录列表（基于发票）
    """
    query = db.query(Invoice).filter(Invoice.status == "ISSUED")
    
    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)
    
    if project_id:
        query = query.filter(Invoice.project_id == project_id)
    
    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)
    
    if payment_status:
        query = query.filter(Invoice.payment_status == payment_status)
    
    if start_date:
        query = query.filter(Invoice.paid_date >= start_date)
    
    if end_date:
        query = query.filter(Invoice.paid_date <= end_date)
    
    total = query.count()
    offset = (page - 1) * page_size
    invoices = query.order_by(desc(Invoice.paid_date)).offset(offset).limit(page_size).all()
    
    items = []
    for invoice in invoices:
        contract = invoice.contract
        items.append({
            "id": invoice.id,
            "invoice_code": invoice.invoice_code,
            "contract_id": invoice.contract_id,
            "contract_code": contract.contract_code if contract else None,
            "project_id": invoice.project_id,
            "project_code": invoice.project.project_code if invoice.project else None,
            "customer_id": contract.customer_id if contract else None,
            "customer_name": contract.customer.customer_name if contract and contract.customer else None,
            "invoice_amount": float(invoice.total_amount or invoice.amount or 0),
            "paid_amount": float(invoice.paid_amount or 0),
            "unpaid_amount": float((invoice.total_amount or invoice.amount or 0) - (invoice.paid_amount or 0)),
            "payment_status": invoice.payment_status,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "paid_date": invoice.paid_date,
            "overdue_days": (date.today() - invoice.due_date).days if invoice.due_date and invoice.due_date < date.today() and invoice.payment_status in ["PENDING", "PARTIAL"] else None,
        })
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/payments", response_model=ResponseModel)
def create_payment_record(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int = Query(..., description="发票ID"),
    paid_amount: Decimal = Query(..., description="收款金额"),
    paid_date: date = Query(..., description="收款日期"),
    payment_method: Optional[str] = Query(None, description="收款方式"),
    bank_account: Optional[str] = Query(None, description="收款账户"),
    remark: Optional[str] = Query(None, description="备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    登记回款
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    if invoice.status != "ISSUED":
        raise HTTPException(status_code=400, detail="只有已开票的发票才能登记回款")
    
    # 更新收款信息
    current_paid = invoice.paid_amount or Decimal("0")
    new_paid = current_paid + paid_amount
    invoice.paid_amount = new_paid
    invoice.paid_date = paid_date
    
    # 更新收款状态
    total = invoice.total_amount or invoice.amount or Decimal("0")
    if new_paid >= total:
        invoice.payment_status = "PAID"
    elif new_paid > Decimal("0"):
        invoice.payment_status = "PARTIAL"
    else:
        invoice.payment_status = "PENDING"
    
    # 更新备注
    payment_note = f"收款记录: {paid_date}, 金额: {paid_amount}"
    if payment_method:
        payment_note += f", 方式: {payment_method}"
    if bank_account:
        payment_note += f", 账户: {bank_account}"
    if remark:
        payment_note += f", 备注: {remark}"
    
    invoice.remark = (invoice.remark or "") + f"\n{payment_note}"
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message="回款登记成功",
        data={
            "invoice_id": invoice.id,
            "paid_amount": float(new_paid),
            "payment_status": invoice.payment_status,
            "unpaid_amount": float(total - new_paid)
        }
    )


@router.get("/payments/{payment_id}", response_model=ResponseModel)
def get_payment_detail(
    *,
    db: Session = Depends(deps.get_db),
    payment_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取回款详情（基于发票ID）
    """
    invoice = db.query(Invoice).options(
        joinedload(Invoice.contract),
        joinedload(Invoice.project)
    ).filter(Invoice.id == payment_id).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    contract = invoice.contract
    project = invoice.project
    
    total = invoice.total_amount or invoice.amount or Decimal("0")
    paid = invoice.paid_amount or Decimal("0")
    unpaid = total - paid
    
    overdue_days = None
    if invoice.due_date and invoice.due_date < date.today() and invoice.payment_status in ["PENDING", "PARTIAL"]:
        overdue_days = (date.today() - invoice.due_date).days
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": invoice.id,
            "invoice_code": invoice.invoice_code,
            "contract_id": invoice.contract_id,
            "contract_code": contract.contract_code if contract else None,
            "project_id": invoice.project_id,
            "project_code": project.project_code if project else None,
            "customer_id": contract.customer_id if contract else None,
            "customer_name": contract.customer.customer_name if contract and contract.customer else None,
            "invoice_amount": float(total),
            "paid_amount": float(paid),
            "unpaid_amount": float(unpaid),
            "payment_status": invoice.payment_status,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "paid_date": invoice.paid_date,
            "overdue_days": overdue_days,
            "remark": invoice.remark,
        }
    )


@router.put("/payments/{payment_id}/match-invoice", response_model=ResponseModel)
def match_payment_to_invoice(
    *,
    db: Session = Depends(deps.get_db),
    payment_id: int,
    invoice_id: int = Query(..., description="发票ID"),
    match_amount: Optional[Decimal] = Query(None, description="核销金额，不指定则核销全部未收金额"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    核销发票（将回款记录与发票关联）
    注意：这里 payment_id 实际上是发票ID，用于保持API路径一致性
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    
    if invoice.status != "ISSUED":
        raise HTTPException(status_code=400, detail="只有已开票的发票才能核销")
    
    total = invoice.total_amount or invoice.amount or Decimal("0")
    current_paid = invoice.paid_amount or Decimal("0")
    unpaid = total - current_paid
    
    if match_amount:
        if match_amount > unpaid:
            raise HTTPException(status_code=400, detail=f"核销金额不能超过未收金额 {unpaid}")
        new_paid = current_paid + match_amount
    else:
        # 核销全部未收金额
        new_paid = total
    
    invoice.paid_amount = new_paid
    invoice.paid_date = date.today()
    
    # 更新收款状态
    if new_paid >= total:
        invoice.payment_status = "PAID"
    elif new_paid > Decimal("0"):
        invoice.payment_status = "PARTIAL"
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message="发票核销成功",
        data={
            "invoice_id": invoice.id,
            "matched_amount": float(match_amount or unpaid),
            "paid_amount": float(new_paid),
            "payment_status": invoice.payment_status
        }
    )


@router.get("/receivables/aging", response_model=ResponseModel)
def get_receivables_aging(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应收账龄分析
    """
    query = db.query(Invoice).filter(
        Invoice.status == "ISSUED",
        Invoice.payment_status.in_(["PENDING", "PARTIAL"])
    )
    
    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)
    
    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)
    
    invoices = query.all()
    
    today = date.today()
    aging_buckets = {
        "0-30": {"count": 0, "amount": Decimal("0")},
        "31-60": {"count": 0, "amount": Decimal("0")},
        "61-90": {"count": 0, "amount": Decimal("0")},
        "90+": {"count": 0, "amount": Decimal("0")},
    }
    
    total_unpaid = Decimal("0")
    
    for invoice in invoices:
        if not invoice.due_date:
            continue
        
        unpaid = (invoice.total_amount or invoice.amount or Decimal("0")) - (invoice.paid_amount or Decimal("0"))
        if unpaid <= 0:
            continue
        
        total_unpaid += unpaid
        days_overdue = (today - invoice.due_date).days
        
        if days_overdue <= 30:
            aging_buckets["0-30"]["count"] += 1
            aging_buckets["0-30"]["amount"] += unpaid
        elif days_overdue <= 60:
            aging_buckets["31-60"]["count"] += 1
            aging_buckets["31-60"]["amount"] += unpaid
        elif days_overdue <= 90:
            aging_buckets["61-90"]["count"] += 1
            aging_buckets["61-90"]["amount"] += unpaid
        else:
            aging_buckets["90+"]["count"] += 1
            aging_buckets["90+"]["amount"] += unpaid
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_unpaid": float(total_unpaid),
            "aging_buckets": {
                "0-30": {
                    "count": aging_buckets["0-30"]["count"],
                    "amount": float(aging_buckets["0-30"]["amount"])
                },
                "31-60": {
                    "count": aging_buckets["31-60"]["count"],
                    "amount": float(aging_buckets["31-60"]["amount"])
                },
                "61-90": {
                    "count": aging_buckets["61-90"]["count"],
                    "amount": float(aging_buckets["61-90"]["amount"])
                },
                "90+": {
                    "count": aging_buckets["90+"]["count"],
                    "amount": float(aging_buckets["90+"]["amount"])
                }
            }
        }
    )


@router.get("/receivables/overdue", response_model=PaginatedResponse)
def get_overdue_receivables(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    min_overdue_days: Optional[int] = Query(None, description="最小逾期天数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    逾期应收列表
    """
    today = date.today()
    
    query = db.query(Invoice).filter(
        Invoice.status == "ISSUED",
        Invoice.payment_status.in_(["PENDING", "PARTIAL"]),
        Invoice.due_date.isnot(None),
        Invoice.due_date < today
    )
    
    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)
    
    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    invoices = query.order_by(Invoice.due_date).offset(offset).limit(page_size).all()
    
    items = []
    for invoice in invoices:
        contract = invoice.contract
        unpaid = (invoice.total_amount or invoice.amount or Decimal("0")) - (invoice.paid_amount or Decimal("0"))
        overdue_days = (today - invoice.due_date).days
        
        if min_overdue_days and overdue_days < min_overdue_days:
            continue
        
        items.append({
            "id": invoice.id,
            "invoice_code": invoice.invoice_code,
            "contract_id": invoice.contract_id,
            "contract_code": contract.contract_code if contract else None,
            "customer_id": contract.customer_id if contract else None,
            "customer_name": contract.customer.customer_name if contract and contract.customer else None,
            "invoice_amount": float(invoice.total_amount or invoice.amount or 0),
            "paid_amount": float(invoice.paid_amount or 0),
            "unpaid_amount": float(unpaid),
            "due_date": invoice.due_date,
            "overdue_days": overdue_days,
            "payment_status": invoice.payment_status,
        })
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/receivables/summary", response_model=ResponseModel)
def get_receivables_summary(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应收账款统计
    """
    query = db.query(Invoice).filter(Invoice.status == "ISSUED")
    
    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)
    
    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)
    
    invoices = query.all()
    
    total_amount = Decimal("0")
    paid_amount = Decimal("0")
    unpaid_amount = Decimal("0")
    partial_amount = Decimal("0")
    overdue_amount = Decimal("0")
    overdue_count = 0
    
    today = date.today()
    
    for invoice in invoices:
        total = invoice.total_amount or invoice.amount or Decimal("0")
        paid = invoice.paid_amount or Decimal("0")
        unpaid = total - paid
        
        total_amount += total
        paid_amount += paid
        unpaid_amount += unpaid
        
        if invoice.payment_status == "PARTIAL":
            partial_amount += unpaid
        
        if invoice.due_date and invoice.due_date < today and invoice.payment_status in ["PENDING", "PARTIAL"]:
            overdue_amount += unpaid
            overdue_count += 1
    
    collection_rate = (paid_amount / total_amount * 100) if total_amount > 0 else Decimal("0")
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_amount": float(total_amount),
            "paid_amount": float(paid_amount),
            "unpaid_amount": float(unpaid_amount),
            "partial_amount": float(partial_amount),
            "overdue_amount": float(overdue_amount),
            "overdue_count": overdue_count,
            "collection_rate": float(collection_rate),
            "invoice_count": len(invoices),
            "paid_count": len([inv for inv in invoices if inv.payment_status == "PAID"]),
            "partial_count": len([inv for inv in invoices if inv.payment_status == "PARTIAL"]),
            "pending_count": len([inv for inv in invoices if inv.payment_status == "PENDING"]),
        }
    )
