# -*- coding: utf-8 -*-
"""
智能缺料预警系统 - API接口

Team 3: 智能缺料预警系统
提供10个API接口
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.shortage.smart_alert import (
    ShortageAlert,
    ShortageHandlingPlan,
    MaterialDemandForecast
)
from app.services.shortage.smart_alert_engine import SmartAlertEngine
from app.services.shortage.demand_forecast_engine import DemandForecastEngine
from app.schemas.shortage_smart import (
    ShortageAlertResponse,
    ShortageAlertListResponse,
    ScanShortageRequest,
    ScanShortageResponse,
    ResolveAlertRequest,
    HandlingPlanResponse,
    HandlingPlanListResponse,
    DemandForecastRequest,
    DemandForecastResponse,
    ValidateForecastRequest,
    ValidateForecastResponse,
    ShortageTrendResponse,
    RootCauseResponse,
    RootCauseAnalysis,
    ProjectImpactResponse,
    ProjectImpactItem,
    NotificationSubscribeRequest,
    NotificationSubscribeResponse
)
from app.core.exceptions import BusinessException

router = APIRouter()


# ==================== 1. 缺料预警列表 ====================

@router.get("/alerts", response_model=ShortageAlertListResponse)
async def get_shortage_alerts(
    project_id: Optional[int] = Query(None, description="项目ID"),
    material_id: Optional[int] = Query(None, description="物料ID"),
    alert_level: Optional[str] = Query(None, description="预警级别"),
    status: Optional[str] = Query(None, description="状态"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取缺料预警列表
    
    支持多维度筛选和分页
    """
    query = db.query(ShortageAlert)
    
    # 过滤条件
    filters = []
    
    if project_id:
        filters.append(ShortageAlert.project_id == project_id)
    if material_id:
        filters.append(ShortageAlert.material_id == material_id)
    if alert_level:
        filters.append(ShortageAlert.alert_level == alert_level)
    if status:
        filters.append(ShortageAlert.status == status)
    if start_date:
        filters.append(ShortageAlert.alert_date >= start_date)
    if end_date:
        filters.append(ShortageAlert.alert_date <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # 总数
    total = query.count()
    
    # 分页
    alerts = query.order_by(desc(ShortageAlert.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return ShortageAlertListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ShortageAlertResponse.from_orm(alert) for alert in alerts]
    )


# ==================== 2. 预警详情 ====================

@router.get("/alerts/{alert_id}", response_model=ShortageAlertResponse)
async def get_shortage_alert_detail(
    alert_id: int = Path(..., description="预警ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取缺料预警详情
    """
    alert = db.query(ShortageAlert).filter(ShortageAlert.id == alert_id).first()
    
    if not alert:
        raise BusinessException("预警不存在")
    
    return ShortageAlertResponse.from_orm(alert)


# ==================== 3. 触发扫描 ====================

@router.post("/scan", response_model=ScanShortageResponse)
async def trigger_shortage_scan(
    request: ScanShortageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    触发缺料扫描
    
    主动扫描并生成预警
    """
    engine = SmartAlertEngine(db)
    
    alerts = engine.scan_and_alert(
        project_id=request.project_id,
        material_id=request.material_id,
        days_ahead=request.days_ahead
    )
    
    return ScanShortageResponse(
        scanned_at=datetime.now(),
        alerts_generated=len(alerts),
        alerts=[ShortageAlertResponse.from_orm(alert) for alert in alerts]
    )


# ==================== 4. 获取处理方案 ====================

@router.get("/alerts/{alert_id}/solutions", response_model=HandlingPlanListResponse)
async def get_handling_solutions(
    alert_id: int = Path(..., description="预警ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取预警的处理方案
    
    返回AI生成的多个处理方案，按评分排序
    """
    alert = db.query(ShortageAlert).filter(ShortageAlert.id == alert_id).first()
    
    if not alert:
        raise BusinessException("预警不存在")
    
    # 查询处理方案
    plans = db.query(ShortageHandlingPlan).filter(
        ShortageHandlingPlan.alert_id == alert_id
    ).order_by(desc(ShortageHandlingPlan.ai_score)).all()
    
    # 如果没有方案，自动生成
    if not plans:
        engine = SmartAlertEngine(db)
        plans = engine.generate_solutions(alert)
    
    return HandlingPlanListResponse(
        alert_id=alert_id,
        total=len(plans),
        items=[HandlingPlanResponse.from_orm(plan) for plan in plans]
    )


# ==================== 5. 标记解决 ====================

@router.post("/alerts/{alert_id}/resolve")
async def resolve_shortage_alert(
    alert_id: int = Path(..., description="预警ID"),
    request: ResolveAlertRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    标记预警已解决
    """
    alert = db.query(ShortageAlert).filter(ShortageAlert.id == alert_id).first()
    
    if not alert:
        raise BusinessException("预警不存在")
    
    if alert.status == 'RESOLVED':
        raise BusinessException("预警已解决")
    
    # 更新状态
    alert.status = 'RESOLVED'
    alert.resolved_at = datetime.now()
    alert.handler_id = current_user.id
    
    if request:
        alert.resolution_type = request.resolution_type
        alert.resolution_note = request.resolution_note
        alert.actual_cost_impact = request.actual_cost_impact
        alert.actual_delay_days = request.actual_delay_days
    
    db.commit()
    db.refresh(alert)
    
    return {
        "success": True,
        "alert_id": alert_id,
        "resolved_at": alert.resolved_at,
        "message": "预警已标记为解决"
    }


# ==================== 6. 需求预测 ====================

@router.get("/forecast/{material_id}", response_model=DemandForecastResponse)
async def get_material_forecast(
    material_id: int = Path(..., description="物料ID"),
    forecast_horizon_days: int = Query(30, description="预测周期（天）", ge=1, le=365),
    algorithm: str = Query('EXP_SMOOTHING', description="预测算法"),
    historical_days: int = Query(90, description="历史数据周期（天）", ge=7, le=365),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取物料需求预测
    
    支持多种预测算法：MOVING_AVERAGE、EXP_SMOOTHING、LINEAR_REGRESSION
    """
    engine = DemandForecastEngine(db)
    
    forecast = engine.forecast_material_demand(
        material_id=material_id,
        forecast_horizon_days=forecast_horizon_days,
        algorithm=algorithm,
        historical_days=historical_days,
        project_id=project_id
    )
    
    return DemandForecastResponse.from_orm(forecast)


# ==================== 7. 缺料趋势分析 ====================

@router.get("/analysis/trend", response_model=ShortageTrendResponse)
async def get_shortage_trend(
    days: int = Query(30, description="统计天数", ge=1, le=365),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    缺料趋势分析
    
    统计指定周期内的缺料趋势、分布和解决时效
    """
    start_date = datetime.now().date() - timedelta(days=days)
    
    query = db.query(ShortageAlert).filter(
        ShortageAlert.alert_date >= start_date
    )
    
    if project_id:
        query = query.filter(ShortageAlert.project_id == project_id)
    
    alerts = query.all()
    
    # 统计
    total_alerts = len(alerts)
    
    by_level = {}
    by_status = {}
    total_resolution_hours = 0
    resolved_count = 0
    total_cost_impact = 0
    
    for alert in alerts:
        # 按级别统计
        level = alert.alert_level
        by_level[level] = by_level.get(level, 0) + 1
        
        # 按状态统计
        status = alert.status
        by_status[status] = by_status.get(status, 0) + 1
        
        # 解决时长
        if alert.resolved_at and alert.detected_at:
            hours = (alert.resolved_at - alert.detected_at).total_seconds() / 3600
            total_resolution_hours += hours
            resolved_count += 1
        
        # 成本影响
        total_cost_impact += float(alert.estimated_cost_impact or 0)
    
    avg_resolution_hours = (
        total_resolution_hours / resolved_count if resolved_count > 0 else 0
    )
    
    # 每日趋势数据
    trend_data = []
    current_date = start_date
    while current_date <= datetime.now().date():
        daily_alerts = [
            a for a in alerts
            if a.alert_date == current_date
        ]
        
        trend_data.append({
            'date': current_date.isoformat(),
            'count': len(daily_alerts),
            'urgent': sum(1 for a in daily_alerts if a.alert_level == 'URGENT'),
            'critical': sum(1 for a in daily_alerts if a.alert_level == 'CRITICAL'),
            'warning': sum(1 for a in daily_alerts if a.alert_level == 'WARNING'),
            'info': sum(1 for a in daily_alerts if a.alert_level == 'INFO'),
        })
        
        current_date += timedelta(days=1)
    
    return ShortageTrendResponse(
        period_start=start_date,
        period_end=datetime.now().date(),
        total_alerts=total_alerts,
        by_level=by_level,
        by_status=by_status,
        avg_resolution_hours=round(avg_resolution_hours, 2),
        total_cost_impact=total_cost_impact,
        trend_data=trend_data
    )


# ==================== 8. 根因分析 ====================

@router.get("/analysis/root-cause", response_model=RootCauseResponse)
async def get_root_cause_analysis(
    days: int = Query(30, description="分析天数", ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    缺料根因分析
    
    分析缺料的主要原因和改进建议
    """
    start_date = datetime.now().date() - timedelta(days=days)
    
    alerts = db.query(ShortageAlert).filter(
        ShortageAlert.alert_date >= start_date
    ).all()
    
    total_analyzed = len(alerts)
    
    # 简化的根因分类（实际应该更复杂）
    cause_map = {
        '供应商交期延误': [],
        '需求预测不准': [],
        '库存管理不当': [],
        '采购流程延迟': [],
        '计划变更频繁': [],
        '其他原因': []
    }
    
    for alert in alerts:
        # 根据预警数据推断根因（简化逻辑）
        if alert.in_transit_qty > 0:
            cause_map['供应商交期延误'].append(alert)
        elif alert.available_qty == 0:
            cause_map['库存管理不当'].append(alert)
        elif alert.estimated_delay_days > 7:
            cause_map['采购流程延迟'].append(alert)
        else:
            cause_map['需求预测不准'].append(alert)
    
    # 构建结果
    top_causes = []
    for cause, alert_list in cause_map.items():
        if alert_list:
            count = len(alert_list)
            percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
            avg_cost = sum(float(a.estimated_cost_impact or 0) for a in alert_list) / count
            
            top_causes.append(RootCauseAnalysis(
                cause=cause,
                count=count,
                percentage=round(percentage, 2),
                avg_cost_impact=avg_cost,
                examples=[a.alert_no for a in alert_list[:3]]
            ))
    
    # 按数量排序
    top_causes.sort(key=lambda x: x.count, reverse=True)
    
    # 生成改进建议
    recommendations = []
    if top_causes:
        top_cause = top_causes[0].cause
        if '供应商' in top_cause:
            recommendations.append("加强供应商管理，建立备用供应商")
            recommendations.append("与供应商签订SLA协议，明确交期保障")
        elif '预测' in top_cause:
            recommendations.append("优化需求预测算法，提高预测准确率")
            recommendations.append("引入AI预测模型，考虑季节性因素")
        elif '库存' in top_cause:
            recommendations.append("建立安全库存机制，设置最低库存预警")
            recommendations.append("优化库存周转率，避免积压和缺货")
        elif '采购' in top_cause:
            recommendations.append("简化采购流程，提高审批效率")
            recommendations.append("对紧急采购建立快速通道")
    
    return RootCauseResponse(
        period_start=start_date,
        period_end=datetime.now().date(),
        total_analyzed=total_analyzed,
        top_causes=top_causes[:5],  # 返回前5个原因
        recommendations=recommendations
    )


# ==================== 9. 缺料对项目的影响 ====================

@router.get("/impact/projects", response_model=ProjectImpactResponse)
async def get_project_impact(
    alert_level: Optional[str] = Query(None, description="预警级别过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    缺料对项目的影响分析
    
    统计各项目的缺料情况和影响
    """
    query = db.query(
        ShortageAlert.project_id,
        func.count(ShortageAlert.id).label('alert_count'),
        func.sum(ShortageAlert.shortage_qty).label('total_shortage_qty'),
        func.max(ShortageAlert.estimated_delay_days).label('max_delay_days'),
        func.sum(ShortageAlert.estimated_cost_impact).label('total_cost_impact')
    ).filter(
        ShortageAlert.status.in_(['PENDING', 'PROCESSING'])
    )
    
    if alert_level:
        query = query.filter(ShortageAlert.alert_level == alert_level)
    if status:
        query = query.filter(ShortageAlert.status == status)
    
    query = query.group_by(ShortageAlert.project_id)
    
    results = query.all()
    
    # 构建项目影响列表
    from app.models.project import Project
    
    items = []
    for row in results:
        project = db.query(Project).filter(Project.id == row.project_id).first()
        
        # 获取关键物料
        critical_materials_query = db.query(ShortageAlert.material_name).filter(
            and_(
                ShortageAlert.project_id == row.project_id,
                ShortageAlert.alert_level.in_(['URGENT', 'CRITICAL'])
            )
        ).limit(5).all()
        
        critical_materials = [m[0] for m in critical_materials_query]
        
        items.append(ProjectImpactItem(
            project_id=row.project_id,
            project_name=project.project_name if project else f"项目{row.project_id}",
            alert_count=row.alert_count,
            total_shortage_qty=row.total_shortage_qty or 0,
            estimated_delay_days=row.max_delay_days or 0,
            estimated_cost_impact=row.total_cost_impact or 0,
            critical_materials=critical_materials
        ))
    
    # 按成本影响排序
    items.sort(key=lambda x: x.estimated_cost_impact, reverse=True)
    
    return ProjectImpactResponse(
        total_projects=len(items),
        items=items
    )


# ==================== 10. 订阅预警通知 ====================

@router.post("/notifications/subscribe", response_model=NotificationSubscribeResponse)
async def subscribe_shortage_notifications(
    request: NotificationSubscribeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    订阅缺料预警通知
    
    用户可以订阅特定级别、项目、物料的预警通知
    """
    # 简化实现：直接返回订阅信息
    # 实际应该存储到数据库的notification_subscriptions表
    
    subscription_id = int(datetime.now().timestamp())
    
    return NotificationSubscribeResponse(
        subscription_id=subscription_id,
        user_id=current_user.id,
        alert_levels=request.alert_levels,
        project_ids=request.project_ids,
        material_ids=request.material_ids,
        notification_channels=request.notification_channels,
        enabled=request.enabled,
        created_at=datetime.now()
    )
