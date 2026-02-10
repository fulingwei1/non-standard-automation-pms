# -*- coding: utf-8 -*-
"""
NOTIFICATIONS - 自动生成
从 alerts.py 拆分
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.alert import (
    AlertNotification,
    AlertRecord,
    AlertRule,
    AlertRuleTemplate,
    AlertStatistics,
    AlertSubscription,
    ExceptionAction,
    ExceptionEscalation,
    ExceptionEvent,
    ProjectHealthSnapshot,
)
from app.models.issue import Issue
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.alert import (
    AlertRecordHandle,
    AlertRecordListResponse,
    AlertRecordResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertStatisticsResponse,
    AlertSubscriptionCreate,
    AlertSubscriptionResponse,
    AlertSubscriptionUpdate,
    ExceptionEventCreate,
    ExceptionEventListResponse,
    ExceptionEventResolve,
    ExceptionEventResponse,
    ExceptionEventUpdate,
    ExceptionEventVerify,
    ProjectHealthResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter(tags=["notifications"])

# ==================== 路由定义 ====================
# 共 4 个路由

@router.get("/alert-notifications", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_alert_notifications(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取预警通知列表（当前用户的）
    """
    from app.services.notification_service import AlertNotificationService

    service = AlertNotificationService(db)
    result = service.get_user_notifications(
        user_id=current_user.id,
        is_read=is_read,
        limit=page_size,
        offset=offset
    )

    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('message', '获取通知列表失败'))

    return PaginatedResponse(
        items=result.get('items', []),
        total=result.get('total', 0),
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(result.get('total', 0) + page_size - 1) // page_size
    )


@router.put("/alert-notifications/{notification_id}/read", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记通知已读
    """
    from app.services.notification_service import AlertNotificationService

    service = AlertNotificationService(db)
    success = service.mark_notification_read(notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="通知不存在或无权操作")

    return ResponseModel(code=200, message="已标记为已读")


@router.get("/alert-notifications/unread-count", response_model=dict, status_code=status.HTTP_200_OK)
def get_unread_notification_count(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取未读通知数量
    """
    from app.services.notification_service import AlertNotificationService

    service = AlertNotificationService(db)
    count = service.get_unread_count(current_user.id)

    return {
        "unread_count": count,
        "user_id": current_user.id
    }


@router.post("/alert-notifications/batch-read", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_mark_notifications_read(
    notification_ids: List[int] = Body(..., description="通知ID列表"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量标记通知为已读
    """
    from app.services.notification_service import AlertNotificationService

    service = AlertNotificationService(db)
    result = service.batch_mark_read(notification_ids, current_user.id)

    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('message', '批量标记失败'))

    return ResponseModel(
        code=200,
        message=f"成功标记 {result.get('success_count', 0)} 条通知为已读",
        data=result
    )


# ==================== 异常事件管理 ====================

def generate_exception_no(db: Session) -> str:
    """生成异常事件编号：EXC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_event = (
        db.query(ExceptionEvent)
        .filter(ExceptionEvent.event_no.like(f"EXC-{today}-%"))
        .order_by(ExceptionEvent.event_no.desc())
        .first()
    )

    if max_event:
        seq = int(max_event.event_no.split("-")[-1]) + 1
