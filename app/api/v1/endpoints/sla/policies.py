# -*- coding: utf-8 -*-
"""
SLA策略管理端点
"""

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.query_filters import apply_keyword_filter
from app.core.config import settings
from app.models.sla import SLAMonitor, SLAPolicy
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sla import (
    SLAPolicyCreate,
    SLAPolicyResponse,
    SLAPolicyUpdate,
)

router = APIRouter()


@router.get(
    "/policies", response_model=PaginatedResponse, status_code=status.HTTP_200_OK
)
def get_sla_policies(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量",
    ),
    problem_type: Optional[str] = Query(None, description="问题类型筛选"),
    urgency: Optional[str] = Query(None, description="紧急程度筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（策略名称、编码）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取SLA策略列表
    """
    query = db.query(SLAPolicy)

    if problem_type:
        query = query.filter(
            or_(
                SLAPolicy.problem_type == problem_type, SLAPolicy.problem_type.is_(None)
            )
        )
    if urgency:
        query = query.filter(
            or_(SLAPolicy.urgency == urgency, SLAPolicy.urgency.is_(None))
        )
    if is_active is not None:
        query = query.filter(SLAPolicy.is_active == is_active)
    query = apply_keyword_filter(query, SLAPolicy, keyword, ["policy_name", "policy_code"])

    total = query.count()
    offset = (page - 1) * page_size
    policies = (
        query.order_by(SLAPolicy.priority, desc(SLAPolicy.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    policy_list = []
    for policy in policies:
        policy_list.append(SLAPolicyResponse.model_validate(policy).model_dump())

    return PaginatedResponse(
        items=policy_list,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/policies/{policy_id}",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_sla_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_id: int = Path(..., description="策略ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取SLA策略详情
    """
    policy = db.query(SLAPolicy).filter(SLAPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SLA策略不存在"
        )

    return ResponseModel(
        code=200,
        message="获取成功",
        data=SLAPolicyResponse.model_validate(policy).model_dump(),
    )


@router.post(
    "/policies", response_model=ResponseModel, status_code=status.HTTP_201_CREATED
)
def create_sla_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_data: SLAPolicyCreate = Body(...),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建SLA策略
    """
    # 检查策略编码是否已存在
    existing = (
        db.query(SLAPolicy)
        .filter(SLAPolicy.policy_code == policy_data.policy_code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="策略编码已存在"
        )

    policy = SLAPolicy(
        policy_name=policy_data.policy_name,
        policy_code=policy_data.policy_code,
        problem_type=policy_data.problem_type,
        urgency=policy_data.urgency,
        response_time_hours=policy_data.response_time_hours,
        resolve_time_hours=policy_data.resolve_time_hours,
        warning_threshold_percent=policy_data.warning_threshold_percent
        or Decimal("80"),
        priority=policy_data.priority or 100,
        description=policy_data.description,
        remark=policy_data.remark,
        is_active=True,
        created_by=current_user.id,
        created_by_name=current_user.real_name or current_user.username,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    return ResponseModel(
        code=200,
        message="SLA策略创建成功",
        data=SLAPolicyResponse.model_validate(policy).model_dump(),
    )


@router.put(
    "/policies/{policy_id}",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def update_sla_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_id: int = Path(..., description="策略ID"),
    policy_data: SLAPolicyUpdate = Body(...),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新SLA策略
    """
    policy = db.query(SLAPolicy).filter(SLAPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SLA策略不存在"
        )

    update_data = policy_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(policy, key, value)

    db.commit()
    db.refresh(policy)

    return ResponseModel(
        code=200,
        message="SLA策略更新成功",
        data=SLAPolicyResponse.model_validate(policy).model_dump(),
    )


@router.delete(
    "/policies/{policy_id}",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def delete_sla_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_id: int = Path(..., description="策略ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除SLA策略（软删除：设置为不启用）
    """
    policy = db.query(SLAPolicy).filter(SLAPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SLA策略不存在"
        )

    # 检查是否有监控记录在使用此策略
    monitor_count = (
        db.query(SLAMonitor).filter(SLAMonitor.policy_id == policy_id).count()
    )
    if monitor_count > 0:
        # 如果有监控记录，只设置为不启用
        policy.is_active = False
        db.commit()
        return ResponseModel(
            code=200, message="SLA策略已禁用（存在监控记录）", data=None
        )
    else:
        # 如果没有监控记录，可以删除
        db.delete(policy)
        db.commit()
        return ResponseModel(code=200, message="SLA策略删除成功", data=None)
