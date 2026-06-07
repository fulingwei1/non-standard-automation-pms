# -*- coding: utf-8 -*-
"""
失败案例管理 API endpoints

包含失败案例的查询、创建、相似案例查找等端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.sales import FailureCase
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import FailureCaseCreate, FailureCaseResponse, FailureCaseUpdate
from app.utils.db_helpers import save_obj

router = APIRouter()


def _build_failure_case_response(db: Session, case: FailureCase) -> FailureCaseResponse:
    creator_name = None
    if case.created_by:
        creator = db.query(User).filter(User.id == case.created_by).first()
        creator_name = creator.real_name if creator else None

    return FailureCaseResponse(
        **{c.name: getattr(case, c.name) for c in case.__table__.columns},
        creator_name=creator_name,
    )


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

    return [_build_failure_case_response(db, case) for case in cases]


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

    # 应用关键词过滤（项目名称/核心失败原因）
    from app.common.query_filters import apply_keyword_filter

    query = apply_keyword_filter(
        query, FailureCase, keyword, ["project_name", "core_failure_reason"]
    )

    total = query.count()
    cases = apply_pagination(
        query.order_by(desc(FailureCase.created_at)), pagination.offset, pagination.limit
    ).all()

    result = [_build_failure_case_response(db, case) for case in cases]

    return PaginatedResponse(
        items=result, total=total, page=pagination.page, page_size=pagination.page_size
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
        created_by=current_user.id,
    )

    save_obj(db, case)

    return _build_failure_case_response(db, case)


@router.get("/failure-cases/{case_id}", response_model=FailureCaseResponse)
def get_failure_case(
    *,
    db: Session = Depends(deps.get_db),
    case_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取失败案例详情"""
    case = db.query(FailureCase).filter(FailureCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="失败案例不存在")

    return _build_failure_case_response(db, case)


@router.put("/failure-cases/{case_id}", response_model=FailureCaseResponse)
def update_failure_case(
    *,
    db: Session = Depends(deps.get_db),
    case_id: int,
    request: FailureCaseUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新失败案例"""
    case = db.query(FailureCase).filter(FailureCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="失败案例不存在")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    save_obj(db, case)
    return _build_failure_case_response(db, case)
