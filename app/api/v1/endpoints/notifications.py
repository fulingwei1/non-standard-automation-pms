# -*- coding: utf-8 -*-
"""
通知中心 API endpoints
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.notification import Notification, NotificationSettings
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    BatchReadRequest,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
def read_notifications(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
    notification_type: Optional[str] = Query(None, description="通知类型筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    current_user: User = Depends(security.get_current_active_user),
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
    offset = (page - 1) * page_size
    notifications = query.order_by(desc(Notification.created_at)).offset(offset).limit(page_size).all()
    
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
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/unread-count")
def get_unread_count(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
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
    
    return {
        "unread_count": count
    }


@router.put("/{notification_id}/read", response_model=ResponseModel)
def mark_notification_read(
    *,
    db: Session = Depends(deps.get_db),
    notification_id: int,
    current_user: User = Depends(security.get_current_active_user),
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
        from datetime import datetime
        notification.read_at = datetime.now()
        db.add(notification)
        db.commit()
    
    return ResponseModel(
        code=200,
        message="通知已标记为已读"
    )


@router.put("/batch-read", response_model=ResponseModel)
def batch_mark_read(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchReadRequest = Body(...),
    current_user: User = Depends(security.get_current_active_user),
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
    
    from datetime import datetime
    read_time = datetime.now()
    
    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = read_time
            db.add(notification)
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"已标记 {len(notifications)} 条通知为已读"
    )


@router.put("/read-all", response_model=ResponseModel)
def mark_all_read(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    全部标记已读
    """
    from datetime import datetime
    
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
    
    return ResponseModel(
        code=200,
        message=f"已标记 {count} 条通知为已读"
    )


@router.delete("/{notification_id}", response_model=ResponseModel)
def delete_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_id: int,
    current_user: User = Depends(security.get_current_active_user),
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
    
    return ResponseModel(
        code=200,
        message="通知已删除"
    )


@router.get("/settings", response_model=NotificationSettingsResponse)
def get_notification_settings(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取通知设置（用户偏好）
    """
    settings = (
        db.query(NotificationSettings)
        .filter(NotificationSettings.user_id == current_user.id)
        .first()
    )
    
    # 如果不存在，创建默认设置
    if not settings:
        settings = NotificationSettings(
            user_id=current_user.id,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return NotificationSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        wechat_enabled=settings.wechat_enabled,
        system_enabled=settings.system_enabled,
        task_notifications=settings.task_notifications,
        approval_notifications=settings.approval_notifications,
        alert_notifications=settings.alert_notifications,
        issue_notifications=settings.issue_notifications,
        project_notifications=settings.project_notifications,
        quiet_hours_start=settings.quiet_hours_start,
        quiet_hours_end=settings.quiet_hours_end,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.put("/settings", response_model=NotificationSettingsResponse)
def update_notification_settings(
    *,
    db: Session = Depends(deps.get_db),
    settings_in: NotificationSettingsUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新通知设置
    """
    settings = (
        db.query(NotificationSettings)
        .filter(NotificationSettings.user_id == current_user.id)
        .first()
    )
    
    # 如果不存在，创建
    if not settings:
        settings = NotificationSettings(user_id=current_user.id)
        db.add(settings)
    
    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.add(settings)
    db.commit()
    db.refresh(settings)
    
    return NotificationSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        wechat_enabled=settings.wechat_enabled,
        system_enabled=settings.system_enabled,
        task_notifications=settings.task_notifications,
        approval_notifications=settings.approval_notifications,
        alert_notifications=settings.alert_notifications,
        issue_notifications=settings.issue_notifications,
        project_notifications=settings.project_notifications,
        quiet_hours_start=settings.quiet_hours_start,
        quiet_hours_end=settings.quiet_hours_end,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )



