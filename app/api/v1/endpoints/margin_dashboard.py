# -*- coding: utf-8 -*-
"""
毛利率 Dashboard API

端点：
  GET /pmo/margin-dashboard          全局毛利率看板（KPI + 分布 + 异常清单）
  GET /pmo/margin-dashboard/trend    全局毛利率趋势（每日均值的 health 分布）
  GET /pmo/margin-dashboard/{id}/trend  单项目毛利率趋势
  POST /pmo/margin-dashboard/snapshot/run  手动触发快照（管理员）
"""
from datetime import date
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.otd import _require_pmo_or_admin
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/pmo/margin-dashboard", tags=["毛利率Dashboard"])


@router.get("", response_model=ResponseModel, summary="全局毛利率看板")
def margin_dashboard(
    target_margin: float = Query(25.0, description="目标毛利率(%)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """全局毛利率 Dashboard：KPI 卡 + 分布 + 异常清单。"""
    from app.services.dashboard.margin_dashboard_service import (
        MarginDashboardService,
    )

    result = MarginDashboardService(db).get_dashboard(target_margin)
    return ResponseModel(
        code=200,
        message=(
            f"毛利率看板：{result['summary']['total_projects']} 个项目，"
            f"平均毛利率 {result['summary']['avg_margin_rate']}%"
        ),
        data=result,
    )


@router.get(
    "/levels",
    response_model=ResponseModel,
    summary="项目等级毛利率底线（对应手册红线）",
)
def margin_level_floors(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """项目等级 S/A/B/C 的毛利率底线（首次访问自动初始化手册红线值）。

    对应《项目经理毛利率提升操作手册》Sheet9：
    S>=40% / A>=35% / B>=30% / C>=25% / 红线>=20%
    """
    from app.services.dashboard.margin_level_service import get_level_summary

    levels = get_level_summary(db)
    return ResponseModel(
        code=200,
        message=f"项目等级毛利率底线（{len(levels)} 个等级）",
        data={"levels": levels, "floor_margin": 20.0},
    )


@router.get("/trend", response_model=ResponseModel, summary="全局毛利率趋势")
def margin_global_trend(
    days: int = Query(30, description="趋势天数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """全局毛利率趋势：每日平均毛利率 + 各 health 分布。"""
    from app.services.dashboard.margin_trend_service import MarginTrendService

    result = MarginTrendService(db).get_global_trend(days)
    return ResponseModel(
        code=200,
        message=f"全局毛利率趋势（{days} 天，{result['total_snapshots']} 条快照）",
        data=result,
    )


@router.get(
    "/export",
    summary="导出毛利率 Dashboard 到 Excel",
    response_class=StreamingResponse,
)
def margin_dashboard_export(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """导出毛利率 Dashboard 到 Excel。

    生成包含汇总指标和项目详情的 Excel 文件。
    项目详情按健康度排序（critical 在前），颜色标识。
    """
    from app.services.otd.margin_export_service import MarginExportService
    from app.services.dashboard.margin_dashboard_service import (
        MarginDashboardService,
    )
    from app.services.profit_analysis_service import ProfitAnalysisService

    dashboard = MarginDashboardService(db).get_dashboard()
    analyses = ProfitAnalysisService(db).batch_margin_analysis()
    dashboard["projects"] = analyses

    excel_file = MarginExportService.export_dashboard_to_excel(dashboard)
    excel_file.seek(0)
    filename = f"毛利率看板_{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get(
    "/{project_id}/trend", response_model=ResponseModel, summary="单项目毛利率趋势"
)
def margin_project_trend(
    project_id: int,
    days: int = Query(30, description="趋势天数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """单项目毛利率趋势：current_margin_rate + margin_gap + health 随时间。"""
    from app.services.dashboard.margin_trend_service import MarginTrendService

    result = MarginTrendService(db).get_project_trend(project_id, days)
    if "error" in result:
        return ResponseModel(code=404, message=result["error"], data=result)
    return ResponseModel(
        code=200,
        message=f"项目毛利率趋势（{days} 天，{result.get('snapshot_count', 0)} 条快照）",
        data=result,
    )


@router.post(
    "/snapshot/run", response_model=ResponseModel, summary="手动触发毛利率快照"
)
def margin_snapshot_run(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """手动触发毛利率快照（PMO/管理员）。"""
    _require_pmo_or_admin(current_user)
    from app.services.dashboard.margin_trend_service import MarginTrendService

    result = MarginTrendService(db).batch_create_snapshots()
    return ResponseModel(
        code=200,
        message=f"快照完成：扫描 {result['total']}，新建 {result['created']} 条",
        data=result,
    )
