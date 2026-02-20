# -*- coding: utf-8 -*-
"""
EXCEPTIONS - 自动生成
从 alerts.py 拆分
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.user import User
from app.schemas.alert import (
    ExceptionEventCreate,
    ExceptionEventResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.services.alert_exceptions import AlertExceptionsService

from .notifications import generate_exception_no

router = APIRouter(tags=["exceptions"])


@router.get("/exceptions", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_exception_events(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（异常编号/标题）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    event_type: Optional[str] = Query(None, description="异常类型筛选"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    responsible_user_id: Optional[int] = Query(None, description="责任人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取异常事件列表（支持分页和筛选）
    """
    service = AlertExceptionsService(db)

    # 获取异常事件列表
    events, total = service.get_exception_events(
        offset=pagination.offset,
        limit=pagination.limit,
        keyword=keyword,
        project_id=project_id,
        event_type=event_type,
        severity=severity,
        status=status,
        responsible_user_id=responsible_user_id,
    )

    # 构建响应数据
    items = [service.build_event_list_item(event) for event in events]

    return pagination.to_response(items, total)


@router.post("/exceptions", response_model=ExceptionEventResponse, status_code=status.HTTP_201_CREATED)
def create_exception_event(
    *,
    db: Session = Depends(deps.get_db),
    event_in: ExceptionEventCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建异常事件
    """
    service = AlertExceptionsService(db)

    # 生成异常编号
    event_no = generate_exception_no(db)

    try:
        # 创建异常事件
        event = service.create_exception_event(event_in, current_user.id, event_no)
        return service.get_exception_event_detail(event.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/exceptions/{event_id}", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def read_exception_event(
    event_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取异常事件详情
    """
    service = AlertExceptionsService(db)
    return service.get_exception_event_detail(event_id)


@router.put("/exceptions/{event_id}/status", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def update_exception_status(
    *,
    db: Session = Depends(deps.get_db),
    event_id: int,
    status: str = Query(..., description="新状态"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新异常状态
    """
    service = AlertExceptionsService(db)

    # 更新状态
    service.update_exception_status(event_id, status, current_user.id)

    # 返回更新后的详情
    return service.get_exception_event_detail(event_id)


@router.post("/exceptions/{event_id}/actions", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_exception_action(
    *,
    db: Session = Depends(deps.get_db),
    event_id: int,
    action_type: str = Query(..., description="操作类型"),
    action_content: str = Query(..., description="操作内容"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加处理记录
    """
    service = AlertExceptionsService(db)

    action = service.add_exception_action(
        event_id=event_id,
        action_type=action_type,
        action_content=action_content,
        current_user_id=current_user.id,
    )

    return ResponseModel(
        code=200,
        message="处理记录已添加",
        data={
            "action_id": action.id,
            "event_id": event_id,
        }
    )


@router.post("/exceptions/{event_id}/escalate", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def escalate_exception(
    *,
    db: Session = Depends(deps.get_db),
    event_id: int,
    escalate_to_user_id: Optional[int] = Query(None, description="升级到用户ID"),
    escalate_to_dept: Optional[str] = Query(None, description="升级到部门"),
    escalation_reason: Optional[str] = Query(None, description="升级原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    异常升级
    """
    service = AlertExceptionsService(db)

    # 执行升级
    service.escalate_exception(
        event_id=event_id,
        escalate_to_user_id=escalate_to_user_id,
        escalate_to_dept=escalate_to_dept,
        escalation_reason=escalation_reason,
        current_user_id=current_user.id,
    )

    # 返回更新后的详情
    return service.get_exception_event_detail(event_id)


@router.post("/exceptions/from-issue", response_model=ExceptionEventResponse, status_code=status.HTTP_201_CREATED)
def create_exception_from_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int = Query(..., description="问题ID"),
    event_type: str = Query(..., description="异常类型"),
    severity: str = Query(..., description="严重程度"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从问题创建异常事件
    """
    service = AlertExceptionsService(db)

    # 生成异常编号
    event_no = generate_exception_no(db)

    # 创建异常事件
    event = service.create_exception_from_issue(
        issue_id=issue_id,
        event_type=event_type,
        severity=severity,
        current_user_id=current_user.id,
        event_no=event_no,
    )

    return service.get_exception_event_detail(event.id)
