# -*- coding: utf-8 -*-
"""
预警与异常管理 API endpoints (重构版)
包含：预警规则、预警记录、异常事件、项目健康度
"""

from typing import Any, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.alert import (
    AlertRule, AlertRecord, ExceptionEvent, AlertSubscription
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

# 导入重构后的服务
from app.services.alert.alert_rules_service import AlertRulesService
from app.services.alert.alert_records_service import AlertRecordsService
from app.services.alert.exception_events_service import ExceptionEventsService
from app.services.alert.alert_statistics_service import AlertStatisticsService

router = APIRouter()


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
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取预警规则列表"""
    service = AlertRulesService(db)
    return service.get_alert_rules(
        page=page,
        page_size=page_size,
        keyword=keyword,
        rule_type=rule_type,
        target_type=target_type,
        is_enabled=is_enabled
    )


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse, status_code=status.HTTP_200_OK)
def read_alert_rule(
    rule_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取单个预警规则"""
    service = AlertRulesService(db)
    alert_rule = service.get_alert_rule(rule_id)
    if not alert_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警规则不存在"
        )
    return AlertRuleResponse.from_orm(alert_rule)


@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """创建预警规则"""
    service = AlertRulesService(db)
    alert_rule = service.create_alert_rule(rule_data, current_user)
    return AlertRuleResponse.from_orm(alert_rule)


@router.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse, status_code=status.HTTP_200_OK)
def update_alert_rule(
    rule_id: int,
    rule_data: AlertRuleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """更新预警规则"""
    service = AlertRulesService(db)
    alert_rule = service.update_alert_rule(rule_id, rule_data, current_user)
    if not alert_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警规则不存在"
        )
    return AlertRuleResponse.from_orm(alert_rule)


@router.put("/alert-rules/{rule_id}/toggle", response_model=AlertRuleResponse, status_code=status.HTTP_200_OK)
def toggle_alert_rule(
    rule_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """切换预警规则状态"""
    service = AlertRulesService(db)
    alert_rule = service.toggle_alert_rule(rule_id, current_user)
    if not alert_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警规则不存在"
        )
    return AlertRuleResponse.from_orm(alert_rule)


@router.delete("/alert-rules/{rule_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """删除预警规则"""
    service = AlertRulesService(db)
    if not service.delete_alert_rule(rule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警规则不存在"
        )
    return ResponseModel(message="预警规则删除成功")


@router.get("/alert-rule-templates", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_alert_rule_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取预警规则模板"""
    service = AlertRulesService(db)
    return service.get_alert_rule_templates()


# ==================== 告警记录管理 ====================

@router.get("/alerts", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_alert_records(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    rule_type: Optional[str] = Query(None, description="规则类型筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取告警记录列表"""
    service = AlertRecordsService(db)
    return service.get_alert_records(
        page=page,
        page_size=page_size,
        keyword=keyword,
        severity=severity,
        status=status,
        rule_type=rule_type,
        start_date=start_date,
        end_date=end_date,
        project_id=project_id
    )


@router.get("/alerts/{alert_id}", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def read_alert_record(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取单个告警记录"""
    service = AlertRecordsService(db)
    alert_record = service.get_alert_record(alert_id)
    if not alert_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警记录不存在"
        )
    return AlertRecordResponse.from_orm(alert_record)


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def acknowledge_alert(
    alert_id: int,
    handle_data: AlertRecordHandle,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """确认告警"""
    service = AlertRecordsService(db)
    alert_record = service.acknowledge_alert(alert_id, handle_data, current_user)
    if not alert_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警记录不存在"
        )
    return AlertRecordResponse.from_orm(alert_record)


@router.put("/alerts/{alert_id}/resolve", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def resolve_alert(
    alert_id: int,
    handle_data: AlertRecordHandle,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """解决告警"""
    service = AlertRecordsService(db)
    alert_record = service.resolve_alert(alert_id, handle_data, current_user)
    if not alert_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警记录不存在"
        )
    return AlertRecordResponse.from_orm(alert_record)


@router.put("/alerts/{alert_id}/close", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def close_alert(
    alert_id: int,
    handle_data: AlertRecordHandle,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """关闭告警"""
    service = AlertRecordsService(db)
    alert_record = service.close_alert(alert_id, handle_data, current_user)
    if not alert_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警记录不存在"
        )
    return AlertRecordResponse.from_orm(alert_record)


@router.put("/alerts/{alert_id}/ignore", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def ignore_alert(
    alert_id: int,
    handle_data: AlertRecordHandle,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """忽略告警"""
    service = AlertRecordsService(db)
    alert_record = service.ignore_alert(alert_id, handle_data, current_user)
    if not alert_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警记录不存在"
        )
    return AlertRecordResponse.from_orm(alert_record)


# ==================== 异常事件管理 ====================

@router.get("/exceptions", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_exception_events(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    event_type: Optional[str] = Query(None, description="事件类型筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取异常事件列表"""
    service = ExceptionEventsService(db)
    return service.get_exception_events(
        page=page,
        page_size=page_size,
        keyword=keyword,
        severity=severity,
        status=status,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        project_id=project_id
    )


@router.post("/exceptions", response_model=ExceptionEventResponse, status_code=status.HTTP_201_CREATED)
def create_exception_event(
    event_data: ExceptionEventCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """创建异常事件"""
    service = ExceptionEventsService(db)
    exception_event = service.create_exception_event(event_data, current_user)
    return ExceptionEventResponse.from_orm(exception_event)


@router.get("/exceptions/{event_id}", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def read_exception_event(
    event_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取单个异常事件"""
    service = ExceptionEventsService(db)
    exception_event = service.get_exception_event(event_id)
    if not exception_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="异常事件不存在"
        )
    return ExceptionEventResponse.from_orm(exception_event)


@router.put("/exceptions/{event_id}/status", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def update_exception_event_status(
    event_id: int,
    event_data: ExceptionEventUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """更新异常事件状态"""
    service = ExceptionEventsService(db)
    exception_event = service.update_exception_event(event_id, event_data, current_user)
    if not exception_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="异常事件不存在"
        )
    return ExceptionEventResponse.from_orm(exception_event)


@router.post("/exceptions/{event_id}/actions", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_exception_action(
    event_id: int,
    action_data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """添加异常事件处理动作"""
    service = ExceptionEventsService(db)
    action = service.add_exception_action(event_id, action_data, current_user)
    return ResponseModel(message="处理动作添加成功", data={"action_id": action.id})


@router.post("/exceptions/{event_id}/escalate", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def escalate_exception_event(
    event_id: int,
    escalation_data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """升级异常事件"""
    service = ExceptionEventsService(db)
    exception_event = service.escalate_exception_event(event_id, escalation_data, current_user)
    if not exception_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="异常事件不存在"
        )
    return ExceptionEventResponse.from_orm(exception_event)


@router.post("/exceptions/from-issue", response_model=ExceptionEventResponse, status_code=status.HTTP_201_CREATED)
def create_exception_from_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """从问题创建异常事件"""
    service = ExceptionEventsService(db)
    exception_event = service.create_exception_from_issue(issue_id, current_user)
    return ExceptionEventResponse.from_orm(exception_event)


# ==================== 告警统计 ====================

@router.get("/alerts/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_alert_statistics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取告警统计信息"""
    service = AlertStatisticsService(db)
    return service.get_alert_statistics(start_date, end_date, project_id)


@router.get("/alerts/statistics/trends", response_model=dict, status_code=status.HTTP_200_OK)
def get_alert_trends(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    period: str = Query("daily", description="统计周期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取告警趋势数据"""
    service = AlertStatisticsService(db)
    return service.get_alert_trends(start_date, end_date, period, project_id)


@router.get("/alerts/statistics/dashboard", response_model=dict, status_code=status.HTTP_200_OK)
def get_alert_dashboard_data(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取告警仪表板数据"""
    service = AlertStatisticsService(db)
    return service.get_alert_dashboard_data(project_id)


@router.get("/alerts/statistics/response-metrics", response_model=dict, status_code=status.HTTP_200_OK)
def get_response_metrics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取响应时间指标"""
    service = AlertStatisticsService(db)
    return service.get_response_metrics(start_date, end_date, project_id)


@router.get("/alerts/statistics/efficiency-metrics", response_model=dict, status_code=status.HTTP_200_OK)
def get_efficiency_metrics(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取效率指标"""
    service = AlertStatisticsService(db)
    return service.get_efficiency_metrics(start_date, end_date, project_id)


# ==================== 项目健康度 ====================

@router.get("/projects/{project_id}/health-history", response_model=List[dict], status_code=status.HTTP_200_OK)
def get_project_health_history(
    project_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取项目健康度历史"""
    # 这里可以添加项目健康度相关的逻辑
    return []