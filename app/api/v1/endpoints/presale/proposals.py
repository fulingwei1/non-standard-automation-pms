# -*- coding: utf-8 -*-
"""
技术方案管理 - 自动生成
从 presale.py 拆分
"""

# -*- coding: utf-8 -*-
"""
售前技术支持 API endpoints
包含：支持工单管理、技术方案管理、方案模板库、投标管理、售前统计
"""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.enums import AssessmentSourceTypeEnum, AssessmentStatusEnum
from app.models.presale import (
    PresaleSupportTicket,
    PresaleSolution,
    PresaleSolutionCost,
    TechnicalParameterTemplate,
)
from app.models.project import Customer
from app.models.sales import Lead, Opportunity
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.presale import (
    SolutionCostResponse,
    SolutionCreate,
    SolutionResponse,
    SolutionReviewRequest,
    SolutionUpdate,
)
from app.services.presale_assessment_completion import complete_presale_source_assessment
from app.utils.db_helpers import get_or_404, save_obj

# 使用统一的编码生成工具
from app.utils.domain_codes import presale as presale_codes

generate_ticket_no = presale_codes.generate_ticket_no
generate_solution_no = presale_codes.generate_solution_no
generate_tender_no = presale_codes.generate_tender_no


router = APIRouter(prefix="/proposals", tags=["proposals"])

# 共 7 个路由

# ==================== 技术方案管理 ====================


def get_user_display_name(user: Optional[User]) -> Optional[str]:
    if not user:
        return None
    return user.real_name or user.username


def resolve_solution_response_context(
    db: Session,
    solution: PresaleSolution,
) -> dict[str, Any]:
    ticket = solution.ticket
    customer_id = solution.customer_id or (ticket.customer_id if ticket else None)
    customer_name = ticket.customer_name if ticket else None
    opportunity_id = solution.opportunity_id or (ticket.opportunity_id if ticket else None)
    opportunity_name = None
    sales_person_id = None
    sales_person_name = None

    if opportunity_id:
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if opportunity:
            opportunity_name = opportunity.opp_name
            customer_id = customer_id or opportunity.customer_id
            if opportunity.customer:
                customer_name = customer_name or opportunity.customer.customer_name
            sales_person_id = opportunity.owner_id
            sales_person_name = get_user_display_name(opportunity.owner)

    if customer_id and not customer_name:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer_name = customer.customer_name

    if ticket and not sales_person_name:
        sales_person_id = ticket.applicant_id
        sales_person_name = ticket.applicant_name

    reviewer_name = None
    if solution.reviewer_id:
        reviewer = db.query(User).filter(User.id == solution.reviewer_id).first()
        reviewer_name = get_user_display_name(reviewer)

    return {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "opportunity_id": opportunity_id,
        "opportunity_name": opportunity_name,
        "sales_person_id": sales_person_id,
        "sales_person_name": sales_person_name,
        "reviewer_name": reviewer_name,
    }


def build_solution_response(db: Session, solution: PresaleSolution) -> SolutionResponse:
    context = resolve_solution_response_context(db, solution)

    return SolutionResponse(
        id=solution.id,
        solution_no=solution.solution_no,
        name=solution.name,
        author_name=solution.author_name,
        solution_type=solution.solution_type,
        industry=solution.industry,
        test_type=solution.test_type,
        ticket_id=solution.ticket_id,
        lead_id=solution.ticket.lead_id if solution.ticket else None,
        project_id=solution.project_id,
        customer_id=context["customer_id"],
        customer_name=context["customer_name"],
        opportunity_id=context["opportunity_id"],
        opportunity_name=context["opportunity_name"],
        sales_person_id=context["sales_person_id"],
        sales_person_name=context["sales_person_name"],
        template_id=solution.template_id,
        template_parameters=solution.template_parameters,
        requirement_summary=solution.requirement_summary,
        solution_overview=solution.solution_overview,
        technical_spec=solution.technical_spec,
        estimated_cost=float(solution.estimated_cost) if solution.estimated_cost else None,
        suggested_price=float(solution.suggested_price) if solution.suggested_price else None,
        cost_breakdown=solution.cost_breakdown,
        estimated_hours=solution.estimated_hours,
        estimated_duration=solution.estimated_duration,
        status=solution.status,
        version=solution.version,
        parent_id=solution.parent_id,
        reviewer_id=solution.reviewer_id,
        reviewer_name=context["reviewer_name"],
        review_time=solution.review_time,
        review_status=solution.review_status,
        review_comment=solution.review_comment,
        created_at=solution.created_at,
        updated_at=solution.updated_at,
    )


def resolve_solution_ticket_from_lead(
    db: Session,
    solution_in: SolutionCreate,
    current_user: User,
) -> Optional[PresaleSupportTicket]:
    if not solution_in.lead_id:
        return None

    ticket = (
        db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.lead_id == solution_in.lead_id)
        .order_by(desc(PresaleSupportTicket.created_at), desc(PresaleSupportTicket.id))
        .first()
    )
    if ticket:
        return ticket

    lead = get_or_404(db, Lead, solution_in.lead_id, detail="线索不存在")
    ticket = PresaleSupportTicket(
        ticket_no=generate_ticket_no(db),
        title=f"方案设计 - {solution_in.name}"[:200],
        ticket_type="SOLUTION_DESIGN",
        urgency="NORMAL",
        description=solution_in.requirement_summary,
        customer_id=solution_in.customer_id,
        customer_name=lead.customer_name,
        lead_id=lead.id,
        opportunity_id=solution_in.opportunity_id,
        project_id=solution_in.project_id,
        applicant_id=current_user.id,
        applicant_name=current_user.real_name or current_user.username,
        applicant_dept=current_user.department,
        apply_time=datetime.now(),
        status="PENDING",
        created_by=current_user.id,
    )
    db.add(ticket)
    db.flush()
    return ticket


def resolve_solution_ticket_from_opportunity(
    db: Session,
    solution_in: SolutionCreate,
    current_user: User,
) -> Optional[PresaleSupportTicket]:
    if not solution_in.opportunity_id:
        return None

    ticket = (
        db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.opportunity_id == solution_in.opportunity_id)
        .order_by(desc(PresaleSupportTicket.created_at), desc(PresaleSupportTicket.id))
        .first()
    )
    if ticket:
        return ticket

    opportunity = get_or_404(db, Opportunity, solution_in.opportunity_id, detail="商机不存在")
    customer_id = (
        solution_in.customer_id
        if solution_in.customer_id is not None
        else opportunity.customer_id
    )
    customer_name = None
    if customer_id == opportunity.customer_id and opportunity.customer:
        customer_name = opportunity.customer.customer_name
    elif customer_id:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        customer_name = customer.customer_name if customer else None

    ticket = PresaleSupportTicket(
        ticket_no=generate_ticket_no(db),
        title=f"方案设计 - {solution_in.name}"[:200],
        ticket_type="SOLUTION_DESIGN",
        urgency="NORMAL",
        description=solution_in.requirement_summary,
        customer_id=customer_id,
        customer_name=customer_name,
        lead_id=opportunity.lead_id,
        opportunity_id=opportunity.id,
        project_id=solution_in.project_id,
        applicant_id=current_user.id,
        applicant_name=current_user.real_name or current_user.username,
        applicant_dept=current_user.department,
        apply_time=datetime.now(),
        status="PENDING",
        created_by=current_user.id,
    )
    db.add(ticket)
    db.flush()
    return ticket


def complete_opportunity_assessment_for_solution(
    db: Session,
    solution: PresaleSolution,
    current_user: User,
) -> None:
    """方案评审通过后补齐商机 G2 所需的技术评估闭环。"""
    ticket = None
    if solution.ticket_id:
        ticket = (
            db.query(PresaleSupportTicket)
            .filter(PresaleSupportTicket.id == solution.ticket_id)
            .first()
        )

    opportunity_id = solution.opportunity_id or (ticket.opportunity_id if ticket else None)
    if not opportunity_id:
        return

    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id)
        .first()
    )
    if not opportunity:
        return

    assessment = complete_presale_source_assessment(
        db=db,
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opportunity.id,
        current_user=current_user,
        ticket=ticket,
        source_assessment_id=opportunity.assessment_id,
    )

    opportunity.assessment_id = assessment.id
    opportunity.assessment_status = AssessmentStatusEnum.COMPLETED.value
    opportunity.updated_by = current_user.id

    if ticket:
        ticket.assessment_status = AssessmentStatusEnum.COMPLETED.value
        ticket.current_assessment_id = assessment.id
        ticket.status = "COMPLETED"
        ticket.complete_time = ticket.complete_time or datetime.now()


@router.get("/solutions", response_model=PaginatedResponse)
def read_solutions(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（方案编号/名称）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    solution_type: Optional[str] = Query(None, description="方案类型筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    lead_id: Optional[int] = Query(None, description="线索ID筛选"),
    ticket_id: Optional[int] = Query(None, description="工单ID筛选"),
    opportunity_id: Optional[int] = Query(None, description="商机ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案列表
    """
    query = db.query(PresaleSolution)

    query = apply_keyword_filter(query, PresaleSolution, keyword, ["solution_no", "name"])

    if status:
        status_values = [item.strip() for item in status.split(",") if item.strip()]
        if len(status_values) == 1:
            query = query.filter(PresaleSolution.status == status_values[0])
        elif status_values:
            query = query.filter(PresaleSolution.status.in_(status_values))

    if solution_type:
        query = query.filter(PresaleSolution.solution_type == solution_type)

    if industry:
        query = query.filter(PresaleSolution.industry == industry)

    if lead_id:
        lead_ticket_ids = (
            db.query(PresaleSupportTicket.id)
            .filter(PresaleSupportTicket.lead_id == lead_id)
        )
        query = query.filter(PresaleSolution.ticket_id.in_(lead_ticket_ids))

    if ticket_id:
        query = query.filter(PresaleSolution.ticket_id == ticket_id)

    if opportunity_id:
        query = query.filter(PresaleSolution.opportunity_id == opportunity_id)

    if project_id:
        query = query.filter(PresaleSolution.project_id == project_id)

    total = query.count()
    solutions = apply_pagination(
        query.order_by(desc(PresaleSolution.created_at)), pagination.offset, pagination.limit
    ).all()

    items = [build_solution_response(db, solution) for solution in solutions]

    return pagination.to_response(items, total)


@router.post("/solutions", response_model=SolutionResponse, status_code=status.HTTP_201_CREATED)
def create_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_in: SolutionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建方案
    """
    ticket = None
    if solution_in.ticket_id:
        ticket = get_or_404(db, PresaleSupportTicket, solution_in.ticket_id, detail="工单不存在")
    elif solution_in.lead_id:
        ticket = resolve_solution_ticket_from_lead(db, solution_in, current_user)
    elif solution_in.opportunity_id:
        ticket = resolve_solution_ticket_from_opportunity(db, solution_in, current_user)

    if solution_in.template_id:
        get_or_404(
            db,
            TechnicalParameterTemplate,
            solution_in.template_id,
            detail="技术参数模板不存在",
        )

    solution = PresaleSolution(
        solution_no=generate_solution_no(db),
        name=solution_in.name,
        solution_type=solution_in.solution_type,
        industry=solution_in.industry,
        test_type=solution_in.test_type,
        ticket_id=ticket.id if ticket else solution_in.ticket_id,
        project_id=solution_in.project_id if solution_in.project_id is not None else (
            ticket.project_id if ticket else None
        ),
        customer_id=solution_in.customer_id if solution_in.customer_id is not None else (
            ticket.customer_id if ticket else None
        ),
        opportunity_id=solution_in.opportunity_id if solution_in.opportunity_id is not None else (
            ticket.opportunity_id if ticket else None
        ),
        template_id=solution_in.template_id,
        template_parameters=solution_in.template_parameters,
        requirement_summary=solution_in.requirement_summary,
        solution_overview=solution_in.solution_overview,
        technical_spec=solution_in.technical_spec,
        estimated_cost=solution_in.estimated_cost,
        suggested_price=solution_in.suggested_price,
        cost_breakdown=solution_in.cost_breakdown,
        estimated_hours=solution_in.estimated_hours,
        estimated_duration=solution_in.estimated_duration,
        status="DRAFT",
        version="V1.0",
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
    )

    save_obj(db, solution)

    return build_solution_response(db, solution)


@router.get("/solutions/{solution_id}", response_model=SolutionResponse)
def read_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案详情
    """
    solution = get_or_404(db, PresaleSolution, solution_id, detail="方案不存在")

    return build_solution_response(db, solution)


@router.put("/solutions/{solution_id}", response_model=SolutionResponse)
def update_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    solution_in: SolutionUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新方案
    """
    solution = get_or_404(db, PresaleSolution, solution_id, detail="方案不存在")

    if solution.status not in ["DRAFT", "REJECTED"]:
        raise HTTPException(status_code=400, detail="只有草稿或已驳回状态的方案才能修改")

    update_data = solution_in.model_dump(exclude_unset=True)
    if update_data.get("template_id"):
        get_or_404(
            db,
            TechnicalParameterTemplate,
            update_data["template_id"],
            detail="技术参数模板不存在",
        )

    ticket = None
    if update_data.get("ticket_id"):
        ticket = get_or_404(db, PresaleSupportTicket, update_data["ticket_id"], detail="工单不存在")
        update_data["ticket_id"] = ticket.id
        if "customer_id" not in update_data and ticket.customer_id is not None:
            update_data["customer_id"] = ticket.customer_id
        if "opportunity_id" not in update_data and ticket.opportunity_id is not None:
            update_data["opportunity_id"] = ticket.opportunity_id
        if "project_id" not in update_data and ticket.project_id is not None:
            update_data["project_id"] = ticket.project_id

    for field, value in update_data.items():
        setattr(solution, field, value)

    save_obj(db, solution)

    return read_solution(db=db, solution_id=solution_id, current_user=current_user)


@router.get("/solutions/{solution_id}/cost", response_model=SolutionCostResponse)
def get_solution_cost(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本估算
    """
    solution = get_or_404(db, PresaleSolution, solution_id, detail="方案不存在")

    # 获取成本明细
    cost_items = (
        db.query(PresaleSolutionCost)
        .filter(PresaleSolutionCost.solution_id == solution_id)
        .order_by(PresaleSolutionCost.sort_order)
        .all()
    )

    breakdown = []
    total_cost = 0.0

    for item in cost_items:
        amount = float(item.amount) if item.amount else 0.0
        total_cost += amount
        breakdown.append(
            {
                "id": item.id,
                "category": item.category,
                "item_name": item.item_name,
                "specification": item.specification,
                "unit": item.unit,
                "quantity": float(item.quantity) if item.quantity else 0.0,
                "unit_price": float(item.unit_price) if item.unit_price else 0.0,
                "amount": amount,
                "remark": item.remark,
            }
        )

    # 如果没有明细，使用方案中的预估成本
    if total_cost == 0 and solution.estimated_cost:
        total_cost = float(solution.estimated_cost)

    return SolutionCostResponse(solution_id=solution_id, total_cost=total_cost, breakdown=breakdown)


@router.put("/solutions/{solution_id}/review", response_model=SolutionResponse)
def review_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    review_request: SolutionReviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案审核
    """
    solution = get_or_404(db, PresaleSolution, solution_id, detail="方案不存在")

    review_status = (review_request.review_status or "").strip().upper()
    status_map = {
        "REVIEW": "REVIEW",
        "APPROVED": "APPROVED",
        "REJECTED": "REJECTED",
    }
    if review_status not in status_map:
        raise HTTPException(status_code=400, detail="不支持的方案审核状态")

    solution.review_status = review_status
    solution.review_comment = review_request.review_comment
    solution.reviewer_id = current_user.id
    solution.review_time = datetime.now()
    solution.status = status_map[review_status]

    if review_status == "APPROVED":
        complete_opportunity_assessment_for_solution(db, solution, current_user)

    save_obj(db, solution)

    return read_solution(db=db, solution_id=solution_id, current_user=current_user)


@router.get("/solutions/{solution_id}/versions", response_model=List[SolutionResponse])
def get_solution_versions(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案版本历史
    """
    solution = get_or_404(db, PresaleSolution, solution_id, detail="方案不存在")

    # 获取所有版本（包括当前版本和子版本）
    versions = []

    # 向上查找父版本
    current = solution
    while current.parent_id:
        parent = db.query(PresaleSolution).filter(PresaleSolution.id == current.parent_id).first()
        if parent:
            versions.insert(0, parent)
            current = parent
        else:
            break

    # 添加当前版本
    versions.append(solution)

    # 向下查找子版本
    child_versions = (
        db.query(PresaleSolution)
        .filter(PresaleSolution.parent_id == solution_id)
        .order_by(PresaleSolution.created_at)
        .all()
    )
    versions.extend(child_versions)

    return [build_solution_response(db, sol) for sol in versions]
