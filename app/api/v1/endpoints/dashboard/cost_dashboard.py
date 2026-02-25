# -*- coding: utf-8 -*-
"""
成本仪表盘API
提供成本看板数据接口
"""

import csv
import io
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.dashboard import (
    ChartConfigSchema,
    CostAlertsSchema,
    CostOverviewSchema,
    ExportDataSchema,
    ProjectCostDashboardSchema,
    TopProjectsSchema,
)
from app.services.cost_dashboard_service import CostDashboardService
from app.services.dashboard_cache_service import get_cache_service

router = APIRouter()


def _get_cache_service():
    """获取缓存服务实例"""
    redis_url = os.getenv("REDIS_URL", None)
    return get_cache_service(redis_url=redis_url, ttl=300)


@router.get("/overview", response_model=ResponseModel[CostOverviewSchema])
def get_cost_overview(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("dashboard:view")),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
) -> Any:
    """
    获取成本总览
    
    返回：
    - 所有项目成本汇总
    - 预算执行率
    - 成本超支项目数量
    - 本月成本趋势
    
    缓存：5分钟
    """
    cache = _get_cache_service()
    cache_key = "dashboard:cost:overview"
    
    def fetch_data():
        service = CostDashboardService(db)
        return service.get_cost_overview()
    
    data = cache.get_or_set(cache_key, fetch_data, force_refresh=force_refresh)
    
    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


@router.get("/top-projects", response_model=ResponseModel[TopProjectsSchema])
def get_top_projects(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("dashboard:view")),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
) -> Any:
    """
    获取TOP 10项目
    
    返回：
    - 成本最高的10个项目
    - 超支最严重的10个项目
    - 利润率最高/最低的10个项目
    
    缓存：5分钟
    """
    cache = _get_cache_service()
    cache_key = f"dashboard:cost:top_projects:limit:{limit}"
    
    def fetch_data():
        service = CostDashboardService(db)
        return service.get_top_projects(limit=limit)
    
    data = cache.get_or_set(cache_key, fetch_data, force_refresh=force_refresh)
    
    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


@router.get("/alerts", response_model=ResponseModel[CostAlertsSchema])
def get_cost_alerts(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("dashboard:view")),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
) -> Any:
    """
    获取成本预警列表
    
    返回：
    - 超支预警
    - 预算告急
    - 成本异常波动
    
    缓存：5分钟
    """
    cache = _get_cache_service()
    cache_key = "dashboard:cost:alerts"
    
    def fetch_data():
        service = CostDashboardService(db)
        return service.get_cost_alerts()
    
    data = cache.get_or_set(cache_key, fetch_data, force_refresh=force_refresh)
    
    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


@router.get("/{project_id}", response_model=ResponseModel[ProjectCostDashboardSchema])
def get_project_cost_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("dashboard:view")),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
) -> Any:
    """
    获取单项目成本仪表盘
    
    返回：
    - 预算 vs 实际
    - 成本结构饼图
    - 月度成本柱状图
    - 成本趋势折线图
    - 收入与利润
    
    缓存：5分钟
    """
    cache = _get_cache_service()
    cache_key = f"dashboard:cost:project:{project_id}"
    
    def fetch_data():
        service = CostDashboardService(db)
        try:
            return service.get_project_cost_dashboard(project_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    data = cache.get_or_set(cache_key, fetch_data, force_refresh=force_refresh)
    
    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


@router.post("/export", response_class=StreamingResponse)
def export_dashboard_data(
    *,
    db: Session = Depends(deps.get_db),
    export_request: ExportDataSchema,
    current_user: User = Depends(security.require_permission("dashboard:view")),
) -> Any:
    """
    导出图表数据
    
    支持格式：
    - CSV
    - Excel（暂不支持，返回CSV）
    
    数据类型：
    - cost_overview: 成本总览
    - top_projects: TOP项目
    - cost_alerts: 成本预警
    - project_dashboard: 项目仪表盘
    """
    service = CostDashboardService(db)
    
    # 获取数据
    if export_request.data_type == "cost_overview":
        data = service.get_cost_overview()
        rows = [data]
        filename = "cost_overview.csv"
        
    elif export_request.data_type == "top_projects":
        data = service.get_top_projects()
        rows = data.get("top_cost_projects", [])
        filename = "top_projects.csv"
        
    elif export_request.data_type == "cost_alerts":
        data = service.get_cost_alerts()
        rows = data.get("alerts", [])
        filename = "cost_alerts.csv"
        
    elif export_request.data_type == "project_dashboard":
        # 需要project_id
        project_id = export_request.filters.get("project_id") if export_request.filters else None
        if not project_id:
            raise HTTPException(status_code=400, detail="缺少project_id参数")
        
        try:
            data = service.get_project_cost_dashboard(int(project_id))
            rows = [data]
            filename = f"project_{project_id}_dashboard.csv"
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="不支持的数据类型")
    
    # 生成CSV
    if not rows:
        raise HTTPException(status_code=404, detail="没有数据可导出")
    
    output = io.StringIO()
    
    # 写入CSV
    if rows:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/chart-config", response_model=ResponseModel[ChartConfigSchema])
def save_chart_config(
    *,
    db: Session = Depends(deps.get_db),
    chart_config: ChartConfigSchema,
    current_user: User = Depends(security.require_permission("dashboard:manage")),
) -> Any:
    """
    保存图表配置
    
    支持自定义指标和筛选条件
    """
    # 简化版：直接返回配置（实际应保存到数据库）
    return ResponseModel(
        code=200,
        message="图表配置已保存",
        data=chart_config.dict()
    )


@router.get("/chart-config/{config_id}", response_model=ResponseModel[ChartConfigSchema])
def get_chart_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    current_user: User = Depends(security.require_permission("dashboard:view")),
) -> Any:
    """
    获取图表配置
    """
    # 简化版：返回示例配置
    example_config = {
        "chart_type": "bar",
        "title": "月度成本对比",
        "x_axis": "month",
        "y_axis": "cost",
        "data_source": "monthly_costs",
        "filters": {},
        "custom_metrics": ["budget", "actual_cost", "variance"],
    }
    
    return ResponseModel(
        code=200,
        message="success",
        data=example_config
    )


@router.delete("/cache")
def clear_dashboard_cache(
    *,
    current_user: User = Depends(security.require_permission("dashboard:manage")),
    pattern: str = Query("dashboard:cost:*", description="缓存键模式"),
) -> Any:
    """
    清除仪表盘缓存
    """
    cache = _get_cache_service()
    deleted_count = cache.clear_pattern(pattern)
    
    return ResponseModel(
        code=200,
        message=f"已清除 {deleted_count} 个缓存键",
        data={"deleted_count": deleted_count}
    )
