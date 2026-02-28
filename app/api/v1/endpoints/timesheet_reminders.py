# -*- coding: utf-8 -*-
"""
工时提醒管理API
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.auth import require_permission
from app.models.user import User
from app.schemas.timesheet_reminder import (
    AnomalyRecordListResponse,
    AnomalyRecordResponse,
    AnomalyResolveRequest,
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
from app.services.timesheet_reminders import TimesheetReminderService

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
    service = TimesheetReminderService(db)

    try:
        config = service.create_reminder_config(
            rule_code=config_data.rule_code,
            rule_name=config_data.rule_name,
            reminder_type=config_data.reminder_type,
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
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
    service = TimesheetReminderService(db)

    config = service.update_reminder_config(
        config_id=config_id, **config_data.model_dump(exclude_unset=True)
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="提醒规则不存在"
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
    service = TimesheetReminderService(db)

    configs, total = service.list_reminder_configs(
        reminder_type=reminder_type, is_active=is_active, limit=limit, offset=offset
    )

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
    service = TimesheetReminderService(db)

    reminders, total = service.list_pending_reminders(
        user_id=current_user.id,
        reminder_type=reminder_type,
        priority=priority,
        limit=limit,
        offset=offset,
    )

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
    service = TimesheetReminderService(db)

    reminders, total = service.list_reminder_history(
        user_id=current_user.id,
        reminder_type=reminder_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

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
    service = TimesheetReminderService(db)

    updated_reminder = service.dismiss_reminder(
        reminder_id=reminder_id,
        user_id=current_user.id,
        dismissed_by=current_user.id,
        reason=request_data.reason,
    )

    if not updated_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="提醒不存在或无权操作"
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
    service = TimesheetReminderService(db)

    updated_reminder = service.mark_reminder_read(
        reminder_id=reminder_id, user_id=current_user.id
    )

    if not updated_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="提醒不存在或无权操作"
        )

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
    service = TimesheetReminderService(db)

    anomalies, total = service.list_anomalies(
        user_id=current_user.id,
        anomaly_type=anomaly_type,
        is_resolved=is_resolved,
        limit=limit,
        offset=offset,
    )

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
    service = TimesheetReminderService(db)

    resolved_anomaly = service.resolve_anomaly(
        anomaly_id=anomaly_id,
        user_id=current_user.id,
        resolved_by=current_user.id,
        resolution_note=request_data.resolution_note,
    )

    if not resolved_anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="异常记录不存在或无权操作"
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
    service = TimesheetReminderService(db)
    return service.get_reminder_statistics(user_id=current_user.id)


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
    service = TimesheetReminderService(db)
    return service.get_dashboard(user_id=current_user.id)
