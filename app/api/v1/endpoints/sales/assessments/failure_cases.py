# -*- coding: utf-8 -*-
"""
失败案例管理 API endpoints

包含失败案例的查询、创建、相似案例查找等端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import FailureCase
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import FailureCaseCreate, FailureCaseResponse
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


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
    pagination: PaginationParams = Depends(get_pagination_query),
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
    cases = query.order_by(desc(FailureCase.created_at)).offset(pagination.offset).limit(pagination.limit).all()

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
        page=pagination.page,
        page_size=pagination.page_size
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
