# -*- coding: utf-8 -*-
"""
通知CRUD操作（重构版）
使用统一响应格式
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.schemas import list_response, paginated_response, success_response
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    BatchReadRequest,
    NotificationResponse,
)

router = APIRouter()


@router.get("/")
def read_notifications(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
    notification_type: Optional[str] = Query(None, description="通知类型筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    current_user: User = Depends(security.require_permission("notification:read")),
) -> Any:
    """
    获取通知列表（分页+已读筛选）
    """
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    # 已读筛选
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    # 通知类型筛选
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)

    # 优先级筛选
    if priority:
        query = query.filter(Notification.priority == priority)

    # 总数
    total = query.count()

    # 分页
    notifications = query.order_by(desc(Notification.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    # 构建响应数据
    items = []
    for notification in notifications:
        items.append(NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            source_type=notification.source_type,
            source_id=notification.source_id,
            title=notification.title,
            content=notification.content,
            link_url=notification.link_url,
            link_params=notification.extra_data if notification.extra_data else None,
            is_read=notification.is_read,
            read_at=notification.read_at,
            priority=notification.priority,
            extra_data=notification.extra_data,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        ))

    # 使用统一响应格式
    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/unread-count")
def get_unread_count(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("notification:read")),
) -> Any:
    """
    获取未读数量（角标数字）
    """
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .filter(Notification.is_read == False)
        .count()
    )

    # 使用统一响应格式
    return success_response(
        data={"unread_count": count},
        message="获取未读数量成功"
    )


@router.put("/{notification_id}/read")
def mark_notification_read(
    *,
    db: Session = Depends(deps.get_db),
    notification_id: int,
    current_user: User = Depends(security.require_permission("notification:read")),
) -> Any:
    """
    标记单条通知已读
    """
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .filter(Notification.user_id == current_user.id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now()
        db.add(notification)
        db.commit()

    # 使用统一响应格式
    return success_response(
        data=None,
        message="通知已标记为已读"
    )


@router.put("/batch-read")
def batch_mark_read(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchReadRequest = Body(...),
    current_user: User = Depends(security.require_permission("notification:read")),
) -> Any:
    """
    批量标记已读
    """
    if not request.notification_ids:
        raise HTTPException(status_code=400, detail="通知ID列表不能为空")

    notifications = (
        db.query(Notification)
        .filter(Notification.id.in_(request.notification_ids))
        .filter(Notification.user_id == current_user.id)
        .all()
    )

    if len(notifications) != len(request.notification_ids):
        raise HTTPException(status_code=400, detail="部分通知不存在或不属于当前用户")

    read_time = datetime.now()

    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = read_time
            db.add(notification)

    db.commit()

    # 使用统一响应格式
    return success_response(
        data={"count": len(notifications)},
        message=f"已标记 {len(notifications)} 条通知为已读"
    )


@router.put("/read-all")
def mark_all_read(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("notification:read")),
) -> Any:
    """
    全部标记已读
    """
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .filter(Notification.is_read == False)
        .update({
            Notification.is_read: True,
            Notification.read_at: datetime.now()
        })
    )

    db.commit()

    # 使用统一响应格式
    return success_response(
        data={"count": count},
        message=f"已标记 {count} 条通知为已读"
    )


@router.delete("/{notification_id}")
def delete_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_id: int,
    current_user: User = Depends(security.require_permission("notification:delete")),
) -> Any:
    """
    删除通知
    """
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .filter(Notification.user_id == current_user.id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    db.delete(notification)
    db.commit()

    # 使用统一响应格式
    return success_response(
        data=None,
        message="通知已删除"
    )
