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
from app.core import security
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.presale import (
    PresaleSolution,
    PresaleSolutionCost,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.presale import (
    SolutionCostResponse,
    SolutionCreate,
    SolutionResponse,
    SolutionReviewRequest,
    SolutionUpdate,
)

router = APIRouter()

# 使用统一的编码生成工具
from app.utils.domain_codes import presale as presale_codes

generate_ticket_no = presale_codes.generate_ticket_no
generate_solution_no = presale_codes.generate_solution_no
generate_tender_no = presale_codes.generate_tender_no


from fastapi import APIRouter

router = APIRouter(
    prefix="/presale/proposals",
    tags=["proposals"]
)

# 共 7 个路由

# ==================== 技术方案管理 ====================

@router.get("/presale/solutions", response_model=PaginatedResponse)
def read_solutions(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（方案编号/名称）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    solution_type: Optional[str] = Query(None, description="方案类型筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    ticket_id: Optional[int] = Query(None, description="工单ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案列表
    """
    query = db.query(PresaleSolution)

    query = apply_keyword_filter(query, PresaleSolution, keyword, ["solution_no", "name"])

    if status:
        query = query.filter(PresaleSolution.status == status)

    if solution_type:
        query = query.filter(PresaleSolution.solution_type == solution_type)

    if industry:
        query = query.filter(PresaleSolution.industry == industry)

    if ticket_id:
        query = query.filter(PresaleSolution.ticket_id == ticket_id)

    total = query.count()
    solutions = apply_pagination(query.order_by(desc(PresaleSolution.created_at)), pagination.offset, pagination.limit).all()

    items = []
    for solution in solutions:
        items.append(SolutionResponse(
            id=solution.id,
            solution_no=solution.solution_no,
            name=solution.name,
            solution_type=solution.solution_type,
            industry=solution.industry,
            test_type=solution.test_type,
            ticket_id=solution.ticket_id,
            customer_id=solution.customer_id,
            opportunity_id=solution.opportunity_id,
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
            review_time=solution.review_time,
            review_status=solution.review_status,
            review_comment=solution.review_comment,
            created_at=solution.created_at,
            updated_at=solution.updated_at,
        ))

    return pagination.to_response(items, total)


@router.post("/presale/solutions", response_model=SolutionResponse, status_code=status.HTTP_201_CREATED)
def create_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_in: SolutionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建方案
    """
    solution = PresaleSolution(
        solution_no=generate_solution_no(db),
        name=solution_in.name,
        solution_type=solution_in.solution_type,
        industry=solution_in.industry,
        test_type=solution_in.test_type,
        ticket_id=solution_in.ticket_id,
        customer_id=solution_in.customer_id,
        opportunity_id=solution_in.opportunity_id,
        requirement_summary=solution_in.requirement_summary,
        solution_overview=solution_in.solution_overview,
        technical_spec=solution_in.technical_spec,
        estimated_cost=solution_in.estimated_cost,
        suggested_price=solution_in.suggested_price,
        estimated_hours=solution_in.estimated_hours,
        estimated_duration=solution_in.estimated_duration,
        status='DRAFT',
        version='V1.0',
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username
    )

    db.add(solution)
    db.commit()
    db.refresh(solution)

    return SolutionResponse(
        id=solution.id,
        solution_no=solution.solution_no,
        name=solution.name,
        solution_type=solution.solution_type,
        industry=solution.industry,
        test_type=solution.test_type,
        ticket_id=solution.ticket_id,
        customer_id=solution.customer_id,
        opportunity_id=solution.opportunity_id,
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
        review_time=solution.review_time,
        review_status=solution.review_status,
        review_comment=solution.review_comment,
        created_at=solution.created_at,
        updated_at=solution.updated_at,
    )


@router.get("/presale/solutions/{solution_id}", response_model=SolutionResponse)
def read_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案详情
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")

    return SolutionResponse(
        id=solution.id,
        solution_no=solution.solution_no,
        name=solution.name,
        solution_type=solution.solution_type,
        industry=solution.industry,
        test_type=solution.test_type,
        ticket_id=solution.ticket_id,
        customer_id=solution.customer_id,
        opportunity_id=solution.opportunity_id,
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
        review_time=solution.review_time,
        review_status=solution.review_status,
        review_comment=solution.review_comment,
        created_at=solution.created_at,
        updated_at=solution.updated_at,
    )


@router.put("/presale/solutions/{solution_id}", response_model=SolutionResponse)
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
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")

    if solution.status not in ['DRAFT', 'REJECTED']:
        raise HTTPException(status_code=400, detail="只有草稿或已驳回状态的方案才能修改")

    update_data = solution_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(solution, field, value)

    db.add(solution)
    db.commit()
    db.refresh(solution)

    return read_solution(db=db, solution_id=solution_id, current_user=current_user)


@router.get("/presale/solutions/{solution_id}/cost", response_model=SolutionCostResponse)
def get_solution_cost(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本估算
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")

    # 获取成本明细
    cost_items = db.query(PresaleSolutionCost).filter(
        PresaleSolutionCost.solution_id == solution_id
    ).order_by(PresaleSolutionCost.sort_order).all()

    breakdown = []
    total_cost = 0.0

    for item in cost_items:
        amount = float(item.amount) if item.amount else 0.0
        total_cost += amount
        breakdown.append({
            'id': item.id,
            'category': item.category,
            'item_name': item.item_name,
            'specification': item.specification,
            'unit': item.unit,
            'quantity': float(item.quantity) if item.quantity else 0.0,
            'unit_price': float(item.unit_price) if item.unit_price else 0.0,
            'amount': amount,
            'remark': item.remark
        })

    # 如果没有明细，使用方案中的预估成本
    if total_cost == 0 and solution.estimated_cost:
        total_cost = float(solution.estimated_cost)

    return SolutionCostResponse(
        solution_id=solution_id,
        total_cost=total_cost,
        breakdown=breakdown
    )


@router.put("/presale/solutions/{solution_id}/review", response_model=SolutionResponse)
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
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")

    solution.review_status = review_request.review_status
    solution.review_comment = review_request.review_comment
    solution.reviewer_id = current_user.id
    solution.review_time = datetime.now()

    if review_request.review_status == 'APPROVED':
        solution.status = 'APPROVED'
    elif review_request.review_status == 'REJECTED':
        solution.status = 'REJECTED'

    db.add(solution)
    db.commit()
    db.refresh(solution)

    return read_solution(db=db, solution_id=solution_id, current_user=current_user)



@router.get("/presale/solutions/{solution_id}/versions", response_model=List[SolutionResponse])
def get_solution_versions(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案版本历史
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")

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
    child_versions = db.query(PresaleSolution).filter(
        PresaleSolution.parent_id == solution_id
    ).order_by(PresaleSolution.created_at).all()
    versions.extend(child_versions)

    result = []
    for sol in versions:
        result.append(SolutionResponse(
            id=sol.id,
            solution_no=sol.solution_no,
            name=sol.name,
            solution_type=sol.solution_type,
            industry=sol.industry,
            test_type=sol.test_type,
            ticket_id=sol.ticket_id,
            customer_id=sol.customer_id,
            opportunity_id=sol.opportunity_id,
            requirement_summary=sol.requirement_summary,
            solution_overview=sol.solution_overview,
            technical_spec=sol.technical_spec,
            estimated_cost=float(sol.estimated_cost) if sol.estimated_cost else None,
            suggested_price=float(sol.suggested_price) if sol.suggested_price else None,
            cost_breakdown=sol.cost_breakdown,
            estimated_hours=sol.estimated_hours,
            estimated_duration=sol.estimated_duration,
            status=sol.status,
            version=sol.version,
            parent_id=sol.parent_id,
            reviewer_id=sol.reviewer_id,
            review_time=sol.review_time,
            review_status=sol.review_status,
            review_comment=sol.review_comment,
            created_at=sol.created_at,
            updated_at=sol.updated_at,
        ))

    return result



