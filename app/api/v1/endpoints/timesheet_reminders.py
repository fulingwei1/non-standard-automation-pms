# -*- coding: utf-8 -*-
"""
工时提醒管理API
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions.decorators import require_permission
from app.models.timesheet_reminder import (
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
    TimesheetAnomalyRecord,
)
from app.models.user import User
from app.schemas.timesheet_reminder import (
    AnomalyRecordListResponse,
    AnomalyRecordResponse,
    AnomalyResolveRequest,
    AnomalyStatistics,
    ReminderConfigCreate,
    ReminderConfigListResponse,
    ReminderConfigResponse,
    ReminderConfigUpdate,
    ReminderDashboard,
    ReminderDismissRequest,
    ReminderRecordListResponse,
    ReminderRecordResponse,
    ReminderStatistics,
)
from app.services.timesheet_reminder.anomaly_detector import TimesheetAnomalyDetector
from app.services.timesheet_reminder.notification_sender import NotificationSender
from app.services.timesheet_reminder.reminder_manager import TimesheetReminderManager

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== 提醒规则配置 ====================


@router.post(
    "/configure",
    response_model=ReminderConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="配置提醒规则",
)
@require_permission("timesheet:reminder:config")
def configure_reminder_rule(
    config_data: ReminderConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    配置工时提醒规则
    
    权限：timesheet:reminder:config
    """
    manager = TimesheetReminderManager(db)

    # 检查规则编码是否已存在
    existing = db.query(TimesheetReminderConfig).filter(
        TimesheetReminderConfig.rule_code == config_data.rule_code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"规则编码已存在: {config_data.rule_code}"
        )

    # 创建规则配置
    config = manager.create_reminder_config(
        rule_code=config_data.rule_code,
        rule_name=config_data.rule_name,
        reminder_type=ReminderTypeEnum(config_data.reminder_type),
        rule_parameters=config_data.rule_parameters,
        apply_to_departments=config_data.apply_to_departments,
        apply_to_roles=config_data.apply_to_roles,
        apply_to_users=config_data.apply_to_users,
        notification_channels=config_data.notification_channels,
        notification_template=config_data.notification_template,
        remind_frequency=config_data.remind_frequency,
        max_reminders_per_day=config_data.max_reminders_per_day,
        priority=config_data.priority,
        created_by=current_user.id,
    )

    return config


@router.put(
    "/configure/{config_id}",
    response_model=ReminderConfigResponse,
    summary="更新提醒规则",
)
@require_permission("timesheet:reminder:config")
def update_reminder_rule(
    config_id: int,
    config_data: ReminderConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    更新工时提醒规则
    
    权限：timesheet:reminder:config
    """
    manager = TimesheetReminderManager(db)

    config = manager.update_reminder_config(
        config_id=config_id,
        **config_data.model_dump(exclude_unset=True)
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒规则不存在"
        )

    return config


@router.get(
    "/configure",
    response_model=ReminderConfigListResponse,
    summary="获取提醒规则列表",
)
@require_permission("timesheet:reminder:view")
def list_reminder_configs(
    reminder_type: Optional[str] = Query(None, description="提醒类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取提醒规则配置列表
    
    权限：timesheet:reminder:view
    """
    query = db.query(TimesheetReminderConfig)

    if reminder_type:
        query = query.filter(TimesheetReminderConfig.reminder_type == reminder_type)

    if is_active is not None:
        query = query.filter(TimesheetReminderConfig.is_active == is_active)

    total = query.count()
    configs = query.order_by(
        desc(TimesheetReminderConfig.created_at)
    ).limit(limit).offset(offset).all()

    return {
        "items": configs,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit,
    }


# ==================== 待处理提醒 ====================


@router.get(
    "/pending",
    response_model=ReminderRecordListResponse,
    summary="获取待处理提醒列表",
)
@require_permission("timesheet:reminder:view")
def list_pending_reminders(
    reminder_type: Optional[str] = Query(None, description="提醒类型"),
    priority: Optional[str] = Query(None, description="优先级"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取待处理提醒列表
    
    权限：timesheet:reminder:view
    """
    query = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id,
        TimesheetReminderRecord.status.in_([
            ReminderStatusEnum.PENDING,
            ReminderStatusEnum.SENT
        ])
    )

    if reminder_type:
        query = query.filter(TimesheetReminderRecord.reminder_type == reminder_type)

    if priority:
        query = query.filter(TimesheetReminderRecord.priority == priority)

    total = query.count()
    reminders = query.order_by(
        desc(TimesheetReminderRecord.priority),
        desc(TimesheetReminderRecord.created_at)
    ).limit(limit).offset(offset).all()

    return {
        "items": reminders,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit,
    }


# ==================== 提醒历史 ====================


@router.get(
    "/history",
    response_model=ReminderRecordListResponse,
    summary="获取提醒历史",
)
@require_permission("timesheet:reminder:view")
def list_reminder_history(
    reminder_type: Optional[str] = Query(None, description="提醒类型"),
    status: Optional[str] = Query(None, description="状态"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取提醒历史记录
    
    权限：timesheet:reminder:view
    """
    query = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id
    )

    if reminder_type:
        query = query.filter(TimesheetReminderRecord.reminder_type == reminder_type)

    if status:
        query = query.filter(TimesheetReminderRecord.status == status)

    if start_date:
        query = query.filter(TimesheetReminderRecord.created_at >= start_date)

    if end_date:
        query = query.filter(TimesheetReminderRecord.created_at <= end_date)

    total = query.count()
    reminders = query.order_by(
        desc(TimesheetReminderRecord.created_at)
    ).limit(limit).offset(offset).all()

    return {
        "items": reminders,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit,
    }


# ==================== 提醒操作 ====================


@router.post(
    "/{reminder_id}/dismiss",
    response_model=ReminderRecordResponse,
    summary="忽略提醒",
)
@require_permission("timesheet:reminder:dismiss")
def dismiss_reminder(
    reminder_id: int,
    request_data: ReminderDismissRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    忽略提醒
    
    权限：timesheet:reminder:dismiss
    """
    manager = TimesheetReminderManager(db)

    # 检查提醒是否属于当前用户
    reminder = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.id == reminder_id,
        TimesheetReminderRecord.user_id == current_user.id
    ).first()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在或无权操作"
        )

    updated_reminder = manager.dismiss_reminder(
        reminder_id=reminder_id,
        dismissed_by=current_user.id,
        reason=request_data.reason
    )

    return updated_reminder


@router.post(
    "/{reminder_id}/read",
    response_model=ReminderRecordResponse,
    summary="标记提醒已读",
)
@require_permission("timesheet:reminder:view")
def mark_reminder_read(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    标记提醒已读
    
    权限：timesheet:reminder:view
    """
    manager = TimesheetReminderManager(db)

    # 检查提醒是否属于当前用户
    reminder = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.id == reminder_id,
        TimesheetReminderRecord.user_id == current_user.id
    ).first()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在或无权操作"
        )

    updated_reminder = manager.mark_reminder_read(reminder_id)

    return updated_reminder


# ==================== 异常记录 ====================


@router.get(
    "/anomalies",
    response_model=AnomalyRecordListResponse,
    summary="获取异常记录列表",
)
@require_permission("timesheet:reminder:view")
def list_anomalies(
    anomaly_type: Optional[str] = Query(None, description="异常类型"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取异常记录列表
    
    权限：timesheet:reminder:view
    """
    query = db.query(TimesheetAnomalyRecord).filter(
        TimesheetAnomalyRecord.user_id == current_user.id
    )

    if anomaly_type:
        query = query.filter(TimesheetAnomalyRecord.anomaly_type == anomaly_type)

    if is_resolved is not None:
        query = query.filter(TimesheetAnomalyRecord.is_resolved == is_resolved)

    total = query.count()
    anomalies = query.order_by(
        desc(TimesheetAnomalyRecord.detected_at)
    ).limit(limit).offset(offset).all()

    return {
        "items": anomalies,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit,
    }


@router.post(
    "/anomalies/{anomaly_id}/resolve",
    response_model=AnomalyRecordResponse,
    summary="解决异常",
)
@require_permission("timesheet:reminder:resolve")
def resolve_anomaly(
    anomaly_id: int,
    request_data: AnomalyResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    解决异常记录
    
    权限：timesheet:reminder:resolve
    """
    manager = TimesheetReminderManager(db)

    # 检查异常是否属于当前用户
    anomaly = db.query(TimesheetAnomalyRecord).filter(
        TimesheetAnomalyRecord.id == anomaly_id,
        TimesheetAnomalyRecord.user_id == current_user.id
    ).first()

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="异常记录不存在或无权操作"
        )

    resolved_anomaly = manager.resolve_anomaly(
        anomaly_id=anomaly_id,
        resolved_by=current_user.id,
        resolution_note=request_data.resolution_note
    )

    return resolved_anomaly


# ==================== 统计和Dashboard ====================


@router.get(
    "/statistics",
    response_model=ReminderStatistics,
    summary="获取提醒统计信息",
)
@require_permission("timesheet:reminder:view")
def get_reminder_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取提醒统计信息
    
    权限：timesheet:reminder:view
    """
    # 基础统计
    total = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id
    ).count()

    pending = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id,
        TimesheetReminderRecord.status.in_([
            ReminderStatusEnum.PENDING,
            ReminderStatusEnum.SENT
        ])
    ).count()

    sent = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id,
        TimesheetReminderRecord.status == ReminderStatusEnum.SENT
    ).count()

    dismissed = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id,
        TimesheetReminderRecord.status == ReminderStatusEnum.DISMISSED
    ).count()

    resolved = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id,
        TimesheetReminderRecord.status == ReminderStatusEnum.RESOLVED
    ).count()

    # 按类型统计
    by_type_query = db.query(
        TimesheetReminderRecord.reminder_type,
        func.count(TimesheetReminderRecord.id)
    ).filter(
        TimesheetReminderRecord.user_id == current_user.id
    ).group_by(TimesheetReminderRecord.reminder_type).all()

    by_type = {str(rt): count for rt, count in by_type_query}

    # 按优先级统计
    by_priority_query = db.query(
        TimesheetReminderRecord.priority,
        func.count(TimesheetReminderRecord.id)
    ).filter(
        TimesheetReminderRecord.user_id == current_user.id
    ).group_by(TimesheetReminderRecord.priority).all()

    by_priority = {p: count for p, count in by_priority_query}

    # 最近提醒
    recent_reminders = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id
    ).order_by(
        desc(TimesheetReminderRecord.created_at)
    ).limit(10).all()

    return {
        "total_reminders": total,
        "pending_reminders": pending,
        "sent_reminders": sent,
        "dismissed_reminders": dismissed,
        "resolved_reminders": resolved,
        "by_type": by_type,
        "by_priority": by_priority,
        "recent_reminders": recent_reminders,
    }


@router.get(
    "/dashboard",
    response_model=ReminderDashboard,
    summary="获取提醒Dashboard",
)
@require_permission("timesheet:reminder:view")
def get_reminder_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取提醒Dashboard（包含提醒和异常统计）
    
    权限：timesheet:reminder:view
    """
    # 提醒统计（复用上面的逻辑）
    reminder_stats = get_reminder_statistics(db, current_user)

    # 异常统计
    total_anomalies = db.query(TimesheetAnomalyRecord).filter(
        TimesheetAnomalyRecord.user_id == current_user.id
    ).count()

    unresolved_anomalies = db.query(TimesheetAnomalyRecord).filter(
        TimesheetAnomalyRecord.user_id == current_user.id,
        TimesheetAnomalyRecord.is_resolved == False
    ).count()

    resolved_anomalies = db.query(TimesheetAnomalyRecord).filter(
        TimesheetAnomalyRecord.user_id == current_user.id,
        TimesheetAnomalyRecord.is_resolved == True
    ).count()

    by_anomaly_type_query = db.query(
        TimesheetAnomalyRecord.anomaly_type,
        func.count(TimesheetAnomalyRecord.id)
    ).filter(
        TimesheetAnomalyRecord.user_id == current_user.id
    ).group_by(TimesheetAnomalyRecord.anomaly_type).all()

    by_anomaly_type = {str(at): count for at, count in by_anomaly_type_query}

    by_severity_query = db.query(
        TimesheetAnomalyRecord.severity,
        func.count(TimesheetAnomalyRecord.id)
    ).filter(
        TimesheetAnomalyRecord.user_id == current_user.id
    ).group_by(TimesheetAnomalyRecord.severity).all()

    by_severity = {s: count for s, count in by_severity_query}

    recent_anomalies = db.query(TimesheetAnomalyRecord).filter(
        TimesheetAnomalyRecord.user_id == current_user.id
    ).order_by(
        desc(TimesheetAnomalyRecord.detected_at)
    ).limit(10).all()

    anomaly_stats = {
        "total_anomalies": total_anomalies,
        "unresolved_anomalies": unresolved_anomalies,
        "resolved_anomalies": resolved_anomalies,
        "by_type": by_anomaly_type,
        "by_severity": by_severity,
        "recent_anomalies": recent_anomalies,
    }

    # 活跃规则配置
    active_configs = db.query(TimesheetReminderConfig).filter(
        TimesheetReminderConfig.is_active == True
    ).limit(20).all()

    # 紧急事项
    urgent_items = db.query(TimesheetReminderRecord).filter(
        TimesheetReminderRecord.user_id == current_user.id,
        TimesheetReminderRecord.status.in_([
            ReminderStatusEnum.PENDING,
            ReminderStatusEnum.SENT
        ]),
        TimesheetReminderRecord.priority.in_(['HIGH', 'URGENT'])
    ).order_by(
        desc(TimesheetReminderRecord.created_at)
    ).limit(10).all()

    return {
        "reminder_stats": reminder_stats,
        "anomaly_stats": anomaly_stats,
        "active_configs": active_configs,
        "urgent_items": urgent_items,
    }
