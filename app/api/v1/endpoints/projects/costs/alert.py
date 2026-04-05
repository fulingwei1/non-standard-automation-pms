# -*- coding: utf-8 -*-
"""
项目成本预警模块

提供项目预算执行预警功能。
路由: /projects/{project_id}/costs/alert
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.budget_alert import BudgetAlertConfig, BudgetMonitorRequest
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/check-budget-alert", response_model=ResponseModel)
def check_project_budget_alert(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    手动检查项目预算执行情况并生成预警（含通知推送）
    """
    from app.services.budget_alert_service import BudgetAlertService

    try:
        service = BudgetAlertService(db)
        alert = service.check_and_alert(project_id=project_id)
        db.commit()

        if alert:
            return ResponseModel(
                code=200,
                message="已生成成本预警",
                data={
                    "alert_id": alert.id,
                    "alert_no": alert.alert_no,
                    "alert_level": alert.alert_level,
                    "alert_title": alert.alert_title,
                    "alert_content": alert.alert_content,
                    "alert_data": alert.alert_data,
                },
            )
        else:
            return ResponseModel(code=200, message="预算执行情况正常，无需预警", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查预算预警失败：{str(e)}")


@router.get("/budget-status", response_model=ResponseModel)
def get_project_budget_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    include_trend: bool = False,
    yellow_threshold: float = 80,
    orange_threshold: float = 90,
    red_threshold: float = 100,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目预算执行状态

    返回 budget_status{execution_rate, forecast_variance, alert_level}
    含：已发生成本/已承诺成本/预计总成本 vs 预算，分级预警，成本趋势预测
    """
    from app.services.budget_alert_service import BudgetAlertService

    try:
        config = BudgetAlertConfig(
            yellow_threshold=yellow_threshold,
            orange_threshold=orange_threshold,
            red_threshold=red_threshold,
        )
        service = BudgetAlertService(db)
        status = service.get_budget_status(
            project_id, include_trend=include_trend, config=config
        )

        if not status:
            return ResponseModel(code=200, message="项目不存在或无有效预算", data=None)

        return ResponseModel(
            code=200,
            message="success",
            data=status.model_dump(mode="json"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算状态失败：{str(e)}")


@router.post("/budget-monitor", response_model=ResponseModel)
def batch_budget_monitor(
    *,
    db: Session = Depends(deps.get_db),
    request: BudgetMonitorRequest,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    批量监控项目预算执行

    支持指定项目列表或全量扫描活跃项目，返回各级预警统计和详情。
    """
    from app.services.budget_alert_service import BudgetAlertService

    try:
        service = BudgetAlertService(db)
        summary = service.monitor_all(
            project_ids=request.project_ids,
            include_trend=request.include_trend,
            config=request.alert_config,
        )
        return ResponseModel(
            code=200,
            message="success",
            data=summary.model_dump(mode="json"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量监控失败：{str(e)}")


@router.post("/budget-check-all", response_model=ResponseModel)
def check_all_projects_budget_alert(
    *,
    db: Session = Depends(deps.get_db),
    request: BudgetMonitorRequest,
    current_user: User = Depends(security.require_permission("cost:write")),
) -> Any:
    """
    批量检查并触发预算预警（含通知推送）

    对每个超阈值项目创建预警记录并通知项目负责人/财务/PMO。
    """
    from app.services.budget_alert_service import BudgetAlertService

    try:
        service = BudgetAlertService(db)
        summary = service.monitor_all(
            project_ids=request.project_ids,
            include_trend=True,
            config=request.alert_config,
        )

        alert_count = 0
        alert_results = []
        for project_status in summary.projects:
            if project_status.alert_level != "GREEN":
                alert = service.check_and_alert(
                    project_id=project_status.project_id,
                    config=request.alert_config,
                )
                if alert:
                    alert_count += 1
                    alert_results.append({
                        "project_id": project_status.project_id,
                        "project_code": project_status.project_code,
                        "alert_level": project_status.alert_level,
                        "alert_id": alert.id,
                    })

        db.commit()

        return ResponseModel(
            code=200,
            message=f"已检查 {summary.total_projects} 个项目，生成 {alert_count} 条预警",
            data={
                "checked_count": summary.total_projects,
                "alert_count": alert_count,
                "green": summary.green_count,
                "yellow": summary.yellow_count,
                "orange": summary.orange_count,
                "red": summary.red_count,
                "alerts": alert_results,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量预警检查失败：{str(e)}")
