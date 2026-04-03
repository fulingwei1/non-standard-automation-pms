# -*- coding: utf-8 -*-
"""
智能缺料预警系统 - API接口 (smart_alerts.py)

Team 3: 智能缺料预警系统
提供10个API接口

PURPOSE / SCOPE
---------------
This file is the **AI/intelligence layer** for shortage alerts. It exposes
endpoints that involve forecasting, algorithmic analysis, root-cause reasoning,
project-impact summaries, AI-generated handling plans, and user notification
subscriptions. It delegates all business logic to ShortageAlertService.

Registered under the prefix:  /shortage/smart/

DISTINCTION FROM detection/alerts.py
--------------------------------------
- detection/alerts.py  →  **Operational CRUD layer**: direct database operations
  on MaterialShortage records, lifecycle state transitions (OPEN → ACKNOWLEDGED →
  RESOLVED), manual updates, follow-up notes, and progress-integration side-effects
  (task blocking/unblocking). Canonical source for alert list/detail/resolve.
  Registered under: /shortage/detection/

- smart_alerts.py (this file)  →  **Intelligence layer**: demand forecasting,
  shortage-trend analysis, root-cause analysis, project-impact aggregation,
  AI-generated solution plans, and notification subscriptions. The three endpoints
  below that mirror detection/alerts.py (list, detail, resolve) are kept for
  backward compatibility only and are marked deprecated — prefer the canonical
  endpoints in detection/alerts.py for those operations.

DUPLICATE REGISTRATION WARNING
-------------------------------
This router must only be mounted once (via shortage/__init__.py at
/shortage/smart/). The legacy registration at /shortage/smart-alerts/ in
api.py / api_medium.py has been removed to avoid serving duplicate routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.shortage_smart import (
    DemandForecastResponse,
    HandlingPlanListResponse,
    HandlingPlanResponse,
    NotificationSubscribeRequest,
    NotificationSubscribeResponse,
    ProjectImpactItem,
    ProjectImpactResponse,
    ResolveAlertRequest,
    RootCauseAnalysis,
    RootCauseResponse,
    ScanShortageRequest,
    ScanShortageResponse,
    ShortageAlertListResponse,
    ShortageAlertResponse,
    ShortageTrendResponse,
)
from app.services.shortage_alerts import ShortageAlertService

router = APIRouter()


# ==================== 1. 缺料预警列表 ====================
# NOTE: Deprecated in favour of GET /shortage/detection/alerts which provides
# the same list through the canonical operational layer (detection/alerts.py).
# This endpoint is retained for backward compatibility only.


@router.get(
    "/alerts",
    response_model=ShortageAlertListResponse,
    deprecated=True,
)
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
    current_user: User = Depends(get_current_user),
):
    """
    [DEPRECATED] 获取缺料预警列表

    **Use GET /shortage/detection/alerts instead.**

    This endpoint is superseded by the canonical operational alert list in
    `detection/alerts.py` which provides richer filtering (handler_id),
    standard pagination, and is the single source of truth for alert records.

    支持多维度筛选和分页。
    """
    service = ShortageAlertService(db)
    alerts, total = service.get_alerts_with_filters(
        project_id=project_id,
        material_id=material_id,
        alert_level=alert_level,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return ShortageAlertListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ShortageAlertResponse.from_orm(alert) for alert in alerts],
    )


# ==================== 2. 预警详情 ====================
# NOTE: Deprecated in favour of GET /shortage/detection/alerts/{id} which is
# the canonical detail endpoint (detection/alerts.py) and includes additional
# fields such as bom_item_id, remark, and updated_at.


@router.get(
    "/alerts/{alert_id}",
    response_model=ShortageAlertResponse,
    deprecated=True,
)
async def get_shortage_alert_detail(
    alert_id: int = Path(..., description="预警ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    [DEPRECATED] 获取缺料预警详情

    **Use GET /shortage/detection/alerts/{alert_id} instead.**

    The canonical detail endpoint in `detection/alerts.py` returns additional
    fields (bom_item_id, remark, updated_at) and uses a consistent ResponseModel
    envelope shared across the rest of the detection layer.
    """
    service = ShortageAlertService(db)
    alert = service.get_alert_by_id(alert_id)

    return ShortageAlertResponse.from_orm(alert)


# ==================== 3. 触发扫描 ====================


@router.post("/scan", response_model=ScanShortageResponse)
async def trigger_shortage_scan(
    request: ScanShortageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    触发缺料扫描

    主动扫描并生成预警
    """
    service = ShortageAlertService(db)
    alerts, scanned_at = service.trigger_scan(
        project_id=request.project_id,
        material_id=request.material_id,
        days_ahead=request.days_ahead,
    )

    return ScanShortageResponse(
        scanned_at=scanned_at,
        alerts_generated=len(alerts),
        alerts=[ShortageAlertResponse.from_orm(alert) for alert in alerts],
    )


# ==================== 4. 获取处理方案 ====================


@router.get("/alerts/{alert_id}/solutions", response_model=HandlingPlanListResponse)
async def get_handling_solutions(
    alert_id: int = Path(..., description="预警ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取预警的处理方案

    返回AI生成的多个处理方案，按评分排序
    """
    service = ShortageAlertService(db)
    plans = service.get_handling_solutions(alert_id)

    return HandlingPlanListResponse(
        alert_id=alert_id,
        total=len(plans),
        items=[HandlingPlanResponse.from_orm(plan) for plan in plans],
    )


# ==================== 5. 标记解决 ====================
# NOTE: Deprecated in favour of POST /shortage/detection/alerts/{id}/resolve
# which is the canonical resolve endpoint (detection/alerts.py). That endpoint
# also handles progress-integration side-effects (unblocking blocked tasks) and
# enforces the RESOLVED status guard. Use it for all production resolve actions.


@router.post(
    "/alerts/{alert_id}/resolve",
    deprecated=True,
)
async def resolve_shortage_alert(
    alert_id: int = Path(..., description="预警ID"),
    request: ResolveAlertRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    [DEPRECATED] 标记预警已解决

    **Use POST /shortage/detection/alerts/{alert_id}/resolve instead.**

    The canonical resolve endpoint in `detection/alerts.py` additionally:
    - Guards against resolving an already-RESOLVED alert (400 error).
    - Triggers progress-integration side-effects to unblock dependent tasks.
    - Accepts a simple `solution` string body (no extra cost/delay metadata).

    This endpoint accepts richer metadata (resolution_type, actual_cost_impact,
    actual_delay_days) via ShortageAlertService; if those fields are required,
    keep using this endpoint until the canonical one is extended.
    """
    service = ShortageAlertService(db)

    alert = service.resolve_alert(
        alert_id=alert_id,
        handler_id=current_user.id,
        resolution_type=request.resolution_type if request else None,
        resolution_note=request.resolution_note if request else None,
        actual_cost_impact=request.actual_cost_impact if request else None,
        actual_delay_days=request.actual_delay_days if request else None,
    )

    return {
        "success": True,
        "alert_id": alert_id,
        "resolved_at": alert.resolved_at,
        "message": "预警已标记为解决",
    }


# ==================== 6. 需求预测 ====================


@router.get("/forecast/{material_id}", response_model=DemandForecastResponse)
async def get_material_forecast(
    material_id: int = Path(..., description="物料ID"),
    forecast_horizon_days: int = Query(30, description="预测周期（天）", ge=1, le=365),
    algorithm: str = Query("EXP_SMOOTHING", description="预测算法"),
    historical_days: int = Query(90, description="历史数据周期（天）", ge=7, le=365),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取物料需求预测

    支持多种预测算法：MOVING_AVERAGE、EXP_SMOOTHING、LINEAR_REGRESSION
    """
    service = ShortageAlertService(db)

    forecast = service.get_material_forecast(
        material_id=material_id,
        forecast_horizon_days=forecast_horizon_days,
        algorithm=algorithm,
        historical_days=historical_days,
        project_id=project_id,
    )

    return DemandForecastResponse.from_orm(forecast)


# ==================== 7. 缺料趋势分析 ====================


@router.get("/analysis/trend", response_model=ShortageTrendResponse)
async def get_shortage_trend(
    days: int = Query(30, description="统计天数", ge=1, le=365),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    缺料趋势分析

    统计指定周期内的缺料趋势、分布和解决时效
    """
    service = ShortageAlertService(db)
    result = service.analyze_shortage_trend(days=days, project_id=project_id)

    return ShortageTrendResponse(**result)


# ==================== 8. 根因分析 ====================


@router.get("/analysis/root-cause", response_model=RootCauseResponse)
async def get_root_cause_analysis(
    days: int = Query(30, description="分析天数", ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    缺料根因分析

    分析缺料的主要原因和改进建议
    """
    service = ShortageAlertService(db)
    result = service.analyze_root_cause(days=days)

    # 转换 top_causes 为 RootCauseAnalysis 对象
    top_causes = [RootCauseAnalysis(**cause) for cause in result["top_causes"]]

    return RootCauseResponse(
        period_start=result["period_start"],
        period_end=result["period_end"],
        total_analyzed=result["total_analyzed"],
        top_causes=top_causes,
        recommendations=result["recommendations"],
    )


# ==================== 9. 缺料对项目的影响 ====================


@router.get("/impact/projects", response_model=ProjectImpactResponse)
async def get_project_impact(
    alert_level: Optional[str] = Query(None, description="预警级别过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    缺料对项目的影响分析

    统计各项目的缺料情况和影响
    """
    service = ShortageAlertService(db)
    items = service.analyze_project_impact(alert_level=alert_level, status=status)

    # 转换为 ProjectImpactItem 对象
    impact_items = [ProjectImpactItem(**item) for item in items]

    return ProjectImpactResponse(total_projects=len(impact_items), items=impact_items)


# ==================== 10. 订阅预警通知 ====================


@router.post("/notifications/subscribe", response_model=NotificationSubscribeResponse)
async def subscribe_shortage_notifications(
    request: NotificationSubscribeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    订阅缺料预警通知

    用户可以订阅特定级别、项目、物料的预警通知
    """
    service = ShortageAlertService(db)

    result = service.create_notification_subscription(
        user_id=current_user.id,
        alert_levels=request.alert_levels,
        project_ids=request.project_ids,
        material_ids=request.material_ids,
        notification_channels=request.notification_channels,
        enabled=request.enabled,
    )

    return NotificationSubscribeResponse(**result)
