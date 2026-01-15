# -*- coding: utf-8 -*-
"""
SUBSCRIPTIONS - 自动生成
从 alerts.py 拆分
"""

from typing import Any, List, Optional

from datetime import date, datetime, timedelta

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session, joinedload, selectinload

from sqlalchemy import or_, and_, func, case

from app.api import deps

from app.core import security

from app.core.config import settings

from app.models.user import User

from app.models.project import Project, Machine

from app.models.issue import Issue

from app.models.alert import (
    AlertRule, AlertRuleTemplate, AlertRecord, AlertNotification,
    ExceptionEvent, ExceptionAction, ExceptionEscalation,
    AlertStatistics, ProjectHealthSnapshot, AlertSubscription
)
from app.schemas.alert import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertRecordHandle, AlertRecordResponse, AlertRecordListResponse,
    ExceptionEventCreate, ExceptionEventUpdate, ExceptionEventResolve,
    ExceptionEventVerify, ExceptionEventResponse, ExceptionEventListResponse,
    ProjectHealthResponse, AlertStatisticsResponse,
    AlertSubscriptionCreate, AlertSubscriptionUpdate, AlertSubscriptionResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter(tags=["subscriptions"])

# ==================== 路由定义 ====================
# 共 5 个路由

@router.get("/alerts/subscriptions", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_alert_subscriptions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    alert_type: Optional[str] = Query(None, description="预警类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取我的预警订阅配置列表
    """
    query = db.query(AlertSubscription).filter(AlertSubscription.user_id == current_user.id)
    
    # 预警类型筛选
    if alert_type:
        query = query.filter(
            or_(
                AlertSubscription.alert_type == alert_type,
                AlertSubscription.alert_type.is_(None)  # 全部类型
            )
        )
    
    # 启用状态筛选
    if is_active is not None:
        query = query.filter(AlertSubscription.is_active == is_active)
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    subscriptions = query.order_by(AlertSubscription.created_at.desc()).offset(offset).limit(page_size).all()
    
    # 转换为响应格式
    items = []
    for sub in subscriptions:
        item = {
            "id": sub.id,
            "user_id": sub.user_id,
            "alert_type": sub.alert_type,
            "project_id": sub.project_id,
            "project_name": sub.project.project_name if sub.project else None,
            "min_level": sub.min_level,
            "notify_channels": sub.notify_channels or ["SYSTEM"],
            "quiet_start": sub.quiet_start,
            "quiet_end": sub.quiet_end,
            "is_active": sub.is_active,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
            "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
        }
        items.append(item)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/alerts/subscriptions/{subscription_id}", response_model=AlertSubscriptionResponse, status_code=status.HTTP_200_OK)
def read_alert_subscription(
    subscription_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取预警订阅配置详情
    """
    subscription = db.query(AlertSubscription).filter(
        AlertSubscription.id == subscription_id,
        AlertSubscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅配置不存在")
    
    return {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "alert_type": subscription.alert_type,
        "project_id": subscription.project_id,
        "project_name": subscription.project.project_name if subscription.project else None,
        "min_level": subscription.min_level,
        "notify_channels": subscription.notify_channels or ["SYSTEM"],
        "quiet_start": subscription.quiet_start,
        "quiet_end": subscription.quiet_end,
        "is_active": subscription.is_active,
        "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
        "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
    }


@router.post("/alerts/subscriptions", response_model=AlertSubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_alert_subscription(
    *,
    db: Session = Depends(deps.get_db),
    subscription_in: AlertSubscriptionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建预警订阅配置
    """
    # 验证预警类型（如果提供）
    if subscription_in.alert_type:
        from app.models.enums import AlertRuleTypeEnum
        valid_types = [e.value for e in AlertRuleTypeEnum]
        if subscription_in.alert_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"无效的预警类型: {subscription_in.alert_type}。支持的类型: {', '.join(valid_types)}"
            )
    
    # 验证预警级别
    from app.models.enums import AlertLevelEnum
    valid_levels = [e.value for e in AlertLevelEnum]
    if subscription_in.min_level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"无效的预警级别: {subscription_in.min_level}。支持的级别: {', '.join(valid_levels)}"
        )
    
    # 验证通知渠道
    valid_channels = ['SYSTEM', 'EMAIL', 'WECHAT', 'SMS']
    if subscription_in.notify_channels:
        for channel in subscription_in.notify_channels:
            if channel.upper() not in valid_channels:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的通知渠道: {channel}。支持的渠道: {', '.join(valid_channels)}"
                )
    
    # 验证免打扰时间格式
    if subscription_in.quiet_start or subscription_in.quiet_end:
        import re
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        if subscription_in.quiet_start and not re.match(time_pattern, subscription_in.quiet_start):
            raise HTTPException(status_code=400, detail="免打扰开始时间格式错误，应为 HH:mm 格式")
        if subscription_in.quiet_end and not re.match(time_pattern, subscription_in.quiet_end):
            raise HTTPException(status_code=400, detail="免打扰结束时间格式错误，应为 HH:mm 格式")
    
    # 检查是否已存在相同的订阅（相同用户、类型、项目）
    existing = db.query(AlertSubscription).filter(
        AlertSubscription.user_id == current_user.id,
        AlertSubscription.alert_type == (subscription_in.alert_type or None),
        AlertSubscription.project_id == (subscription_in.project_id or None)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="已存在相同的订阅配置")
    
    # 验证项目ID（如果提供）
    if subscription_in.project_id:
        project = db.query(Project).filter(Project.id == subscription_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    subscription = AlertSubscription(
        user_id=current_user.id,
        alert_type=subscription_in.alert_type,
        project_id=subscription_in.project_id,
        min_level=subscription_in.min_level,
        notify_channels=subscription_in.notify_channels or ["SYSTEM"],
        quiet_start=subscription_in.quiet_start,
        quiet_end=subscription_in.quiet_end,
        is_active=subscription_in.is_active
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "alert_type": subscription.alert_type,
        "project_id": subscription.project_id,
        "project_name": subscription.project.project_name if subscription.project else None,
        "min_level": subscription.min_level,
        "notify_channels": subscription.notify_channels or ["SYSTEM"],
        "quiet_start": subscription.quiet_start,
        "quiet_end": subscription.quiet_end,
        "is_active": subscription.is_active,
        "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
        "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
    }


@router.put("/alerts/subscriptions/{subscription_id}", response_model=AlertSubscriptionResponse, status_code=status.HTTP_200_OK)
def update_alert_subscription(
    *,
    db: Session = Depends(deps.get_db),
    subscription_id: int,
    subscription_in: AlertSubscriptionUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新预警订阅配置
    """
    subscription = db.query(AlertSubscription).filter(
        AlertSubscription.id == subscription_id,
        AlertSubscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅配置不存在")
    
    # 验证预警类型（如果提供）
    if subscription_in.alert_type is not None:
        from app.models.enums import AlertRuleTypeEnum
        valid_types = [e.value for e in AlertRuleTypeEnum]
        if subscription_in.alert_type and subscription_in.alert_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"无效的预警类型: {subscription_in.alert_type}"
            )
    
    # 验证预警级别（如果提供）
    if subscription_in.min_level is not None:
        from app.models.enums import AlertLevelEnum
        valid_levels = [e.value for e in AlertLevelEnum]
        if subscription_in.min_level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"无效的预警级别: {subscription_in.min_level}"
            )
    
    # 验证通知渠道（如果提供）
    if subscription_in.notify_channels is not None:
        valid_channels = ['SYSTEM', 'EMAIL', 'WECHAT', 'SMS']
        for channel in subscription_in.notify_channels:
            if channel.upper() not in valid_channels:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的通知渠道: {channel}"
                )
    
    # 验证免打扰时间格式（如果提供）
    if subscription_in.quiet_start or subscription_in.quiet_end:
        import re
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        if subscription_in.quiet_start and not re.match(time_pattern, subscription_in.quiet_start):
            raise HTTPException(status_code=400, detail="免打扰开始时间格式错误")
        if subscription_in.quiet_end and not re.match(time_pattern, subscription_in.quiet_end):
            raise HTTPException(status_code=400, detail="免打扰结束时间格式错误")
    
    # 验证项目ID（如果提供）
    if subscription_in.project_id is not None and subscription_in.project_id:
        project = db.query(Project).filter(Project.id == subscription_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否与其他订阅冲突（如果修改了类型或项目）
    if subscription_in.alert_type is not None or subscription_in.project_id is not None:
        new_type = subscription_in.alert_type if subscription_in.alert_type is not None else subscription.alert_type
        new_project_id = subscription_in.project_id if subscription_in.project_id is not None else subscription.project_id
        
        existing = db.query(AlertSubscription).filter(
            AlertSubscription.id != subscription_id,
            AlertSubscription.user_id == current_user.id,
            AlertSubscription.alert_type == (new_type or None),
            AlertSubscription.project_id == (new_project_id or None)
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="已存在相同的订阅配置")
    
    # 更新字段
    update_data = subscription_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "alert_type": subscription.alert_type,
        "project_id": subscription.project_id,
        "project_name": subscription.project.project_name if subscription.project else None,
        "min_level": subscription.min_level,
        "notify_channels": subscription.notify_channels or ["SYSTEM"],
        "quiet_start": subscription.quiet_start,
        "quiet_end": subscription.quiet_end,
        "is_active": subscription.is_active,
        "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
        "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
    }


@router.delete("/alerts/subscriptions/{subscription_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_alert_subscription(
    *,
    db: Session = Depends(deps.get_db),
    subscription_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除预警订阅配置
    """
    subscription = db.query(AlertSubscription).filter(
        AlertSubscription.id == subscription_id,
        AlertSubscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅配置不存在")
    
    db.delete(subscription)
    db.commit()
    
    return ResponseModel(code=200, message="订阅配置已删除")
