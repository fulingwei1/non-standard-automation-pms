# -*- coding: utf-8 -*-
"""
RULES - 自动生成
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

router = APIRouter(tags=["rules"])

# ==================== 路由定义 ====================
# 共 6 个路由

# ==================== 预警规则管理 ====================

@router.get("/alert-rules", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_alert_rules(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（规则编码/名称）"),
    rule_type: Optional[str] = Query(None, description="规则类型筛选"),
    target_type: Optional[str] = Query(None, description="监控对象类型筛选"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取预警规则列表（支持分页和筛选）
    """
    query = db.query(AlertRule)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                AlertRule.rule_code.like(f"%{keyword}%"),
                AlertRule.rule_name.like(f"%{keyword}%"),
            )
        )
    
    # 规则类型筛选
    if rule_type:
        query = query.filter(AlertRule.rule_type == rule_type)
    
    # 监控对象类型筛选
    if target_type:
        query = query.filter(AlertRule.target_type == target_type)
    
    # 启用状态筛选
    if is_enabled is not None:
        query = query.filter(AlertRule.is_enabled == is_enabled)
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    rules = query.order_by(AlertRule.created_at.desc()).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=rules,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse, status_code=status.HTTP_200_OK)
def read_alert_rule(
    rule_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取预警规则详情
    """
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    
    return rule


@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
def create_alert_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_in: AlertRuleCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建预警规则
    """
    # 检查规则编码是否已存在
    existing = db.query(AlertRule).filter(AlertRule.rule_code == rule_in.rule_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="规则编码已存在")
    
    # 验证规则编码格式（字母、数字、下划线）
    import re
    if not re.match(r'^[A-Za-z0-9_]+$', rule_in.rule_code):
        raise HTTPException(status_code=400, detail="规则编码只能包含字母、数字和下划线")
    
    # 验证阈值格式（如果是数值类型）
    if rule_in.threshold_value:
        try:
            float(rule_in.threshold_value)
        except ValueError:
            # 如果不是纯数字，可能是表达式，允许通过
            pass
    
    # 验证阈值范围（如果有 min 和 max）
    if rule_in.threshold_min and rule_in.threshold_max:
        try:
            min_val = float(rule_in.threshold_min)
            max_val = float(rule_in.threshold_max)
            if min_val >= max_val:
                raise HTTPException(status_code=400, detail="阈值下限必须小于阈值上限")
        except ValueError:
            pass
    
    # 验证通知渠道
    valid_channels = ['SYSTEM', 'EMAIL', 'WECHAT', 'SMS']
    if rule_in.notify_channels:
        for channel in rule_in.notify_channels:
            if channel.upper() not in valid_channels:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的通知渠道: {channel}。支持的渠道: {', '.join(valid_channels)}"
                )
    
    # 验证检查频率
    valid_frequencies = ['REALTIME', 'HOURLY', 'DAILY', 'WEEKLY']
    if rule_in.check_frequency and rule_in.check_frequency.upper() not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"无效的检查频率: {rule_in.check_frequency}。支持的频率: {', '.join(valid_frequencies)}"
        )
    
    # 验证预警级别
    valid_levels = ['INFO', 'WARNING', 'CRITICAL', 'URGENT']
    if rule_in.alert_level and rule_in.alert_level.upper() not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"无效的预警级别: {rule_in.alert_level}。支持的级别: {', '.join(valid_levels)}"
        )
    
    rule = AlertRule(**rule_in.model_dump(), created_by=current_user.id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse, status_code=status.HTTP_200_OK)
def update_alert_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    rule_in: AlertRuleUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新预警规则
    """
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    
    # 系统预置规则不允许修改某些字段
    if rule.is_system:
        raise HTTPException(status_code=400, detail="系统预置规则不允许修改")
    
    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.put("/alert-rules/{rule_id}/toggle", response_model=AlertRuleResponse, status_code=status.HTTP_200_OK)
def toggle_alert_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    启用/禁用预警规则
    """
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    
    # 系统预置规则可以启用/禁用，但不能删除
    rule.is_enabled = not rule.is_enabled
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/alert-rules/{rule_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_alert_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除预警规则
    """
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    
    # 系统预置规则不允许删除
    if rule.is_system:
        raise HTTPException(status_code=400, detail="系统预置规则不允许删除")
    
    # 检查是否有预警记录使用此规则
    alert_count = db.query(AlertRecord).filter(AlertRecord.rule_id == rule_id).count()
    if alert_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该规则已被 {alert_count} 条预警记录使用，无法删除。请先处理相关预警记录。"
        )
    
    db.delete(rule)
    db.commit()
    
    return ResponseModel(code=200, message="预警规则已删除")


