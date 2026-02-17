# -*- coding: utf-8 -*-
"""
项目风险分析API

提供风险趋势、风险统计、风险报表等分析功能。
基于自动计算的风险等级和历史快照数据。
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project.risk_history import ProjectRiskHistory, ProjectRiskSnapshot
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.project.project_risk_service import ProjectRiskService
from app.common.pagination import PaginationParams, get_pagination_query

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{project_id}/risk-trend",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_project_risk_trend(
    project_id: int,
    days: int = Query(30, ge=7, le=365, description="查询天数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取项目风险趋势

    返回指定项目在过去N天的风险等级变化趋势，
    用于绘制风险趋势图表。

    Args:
        project_id: 项目ID
        days: 查询天数（默认30天）
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = ProjectRiskService(db)
    trend_data = service.get_risk_trend(project_id, days)

    return ResponseModel(
        code=200,
        message="获取风险趋势成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "days": days,
            "trend": trend_data,
            "summary": {
                "total_records": len(trend_data),
                "latest_level": trend_data[-1]["risk_level"] if trend_data else None,
            },
        },
    )


@router.get(
    "/{project_id}/risk-history",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_project_risk_history(
    project_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取项目风险变更历史

    返回项目风险等级的变更记录，包含每次变更的原因和时间。

    Args:
        project_id: 项目ID
        page: 页码
        page_size: 每页数量
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 查询总数
    total = (
        db.query(func.count(ProjectRiskHistory.id))
        .filter(ProjectRiskHistory.project_id == project_id)
        .scalar()
    )

    # 分页查询
    histories = (
        db.query(ProjectRiskHistory)
        .filter(ProjectRiskHistory.project_id == project_id)
        .order_by(ProjectRiskHistory.triggered_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    items = []
    for h in histories:
        items.append(
            {
                "id": h.id,
                "old_risk_level": h.old_risk_level,
                "new_risk_level": h.new_risk_level,
                "is_upgrade": (
                    ProjectRiskService.RISK_LEVEL_ORDER.get(h.new_risk_level, 0)
                    > ProjectRiskService.RISK_LEVEL_ORDER.get(h.old_risk_level, 0)
                ),
                "triggered_by": h.triggered_by,
                "triggered_at": h.triggered_at.isoformat() if h.triggered_at else None,
                "risk_factors": h.risk_factors,
                "remarks": h.remarks,
            }
        )

    return ResponseModel(
        code=200,
        message="获取风险历史成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0,
        },
    )


@router.get(
    "/{project_id}/risk-current",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_project_current_risk(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取项目当前风险状态

    返回项目的当前风险等级和详细风险因子。

    Args:
        project_id: 项目ID
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = ProjectRiskService(db)
    try:
        result = service.calculate_project_risk(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算风险失败: {str(e)}")

    return ResponseModel(
        code=200,
        message="获取当前风险状态成功",
        data={
            "project_id": project_id,
            "project_code": result["project_code"],
            "project_name": project.project_name,
            "risk_level": result["risk_level"],
            "risk_factors": result["risk_factors"],
        },
    )


@router.post(
    "/{project_id}/risk-calculate",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def trigger_risk_calculation(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """
    手动触发风险计算

    立即计算项目风险等级并记录历史。
    用于在项目发生重大变化后立即更新风险状态。

    Args:
        project_id: 项目ID
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = ProjectRiskService(db)
    try:
        result = service.auto_upgrade_risk_level(
            project_id, triggered_by=f"USER:{current_user.id}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"计算风险失败: {str(e)}")

    return ResponseModel(
        code=200,
        message="风险计算完成",
        data={
            "project_id": project_id,
            "project_code": result["project_code"],
            "old_risk_level": result["old_risk_level"],
            "new_risk_level": result["new_risk_level"],
            "is_upgrade": result["is_upgrade"],
            "risk_factors": result["risk_factors"],
        },
    )


@router.get(
    "/risk-report/summary",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_risk_summary_report(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取全局风险汇总报表

    返回所有活跃项目的风险分布统计。
    """
    # 统计各风险等级的项目数量
    # 使用最近的风险历史记录
    subquery = (
        db.query(
            ProjectRiskHistory.project_id,
            func.max(ProjectRiskHistory.triggered_at).label("latest_at"),
        )
        .group_by(ProjectRiskHistory.project_id)
        .subquery()
    )

    latest_risks = (
        db.query(ProjectRiskHistory)
        .join(
            subquery,
            and_(
                ProjectRiskHistory.project_id == subquery.c.project_id,
                ProjectRiskHistory.triggered_at == subquery.c.latest_at,
            ),
        )
        .all()
    )

    # 统计分布
    distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for risk in latest_risks:
        level = risk.new_risk_level
        if level in distribution:
            distribution[level] += 1

    # 获取高风险项目列表
    high_risk_projects = []
    for risk in latest_risks:
        if risk.new_risk_level in ("HIGH", "CRITICAL"):
            project = (
                db.query(Project).filter(Project.id == risk.project_id).first()
            )
            if project and project.is_active:
                high_risk_projects.append(
                    {
                        "project_id": project.id,
                        "project_code": project.project_code,
                        "project_name": project.project_name,
                        "risk_level": risk.new_risk_level,
                        "last_updated": risk.triggered_at.isoformat()
                        if risk.triggered_at
                        else None,
                    }
                )

    # 按风险等级排序（CRITICAL优先）
    level_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    high_risk_projects.sort(key=lambda x: level_order.get(x["risk_level"], 99))

    total_projects = sum(distribution.values())

    return ResponseModel(
        code=200,
        message="获取风险汇总报表成功",
        data={
            "distribution": distribution,
            "total_projects": total_projects,
            "high_risk_count": distribution["HIGH"] + distribution["CRITICAL"],
            "high_risk_projects": high_risk_projects[:20],  # 最多返回20个
            "generated_at": datetime.now().isoformat(),
        },
    )


@router.get(
    "/risk-report/trend",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_global_risk_trend(
    days: int = Query(30, ge=7, le=90, description="查询天数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取全局风险趋势报表

    返回过去N天所有项目的风险等级变化统计。
    """
    start_date = datetime.now() - timedelta(days=days)

    # 按日期统计风险升级数量
    upgrades_by_date = (
        db.query(
            func.date(ProjectRiskHistory.triggered_at).label("date"),
            func.count(ProjectRiskHistory.id).label("upgrade_count"),
        )
        .filter(
            ProjectRiskHistory.triggered_at >= start_date,
            ProjectRiskHistory.new_risk_level.in_(["HIGH", "CRITICAL"]),
        )
        .group_by(func.date(ProjectRiskHistory.triggered_at))
        .order_by(func.date(ProjectRiskHistory.triggered_at))
        .all()
    )

    # 按日期统计快照数据
    snapshots_by_date = (
        db.query(
            func.date(ProjectRiskSnapshot.snapshot_date).label("date"),
            ProjectRiskSnapshot.risk_level,
            func.count(ProjectRiskSnapshot.id).label("count"),
        )
        .filter(ProjectRiskSnapshot.snapshot_date >= start_date)
        .group_by(
            func.date(ProjectRiskSnapshot.snapshot_date),
            ProjectRiskSnapshot.risk_level,
        )
        .all()
    )

    # 构建趋势数据
    trend_data = {}
    for row in snapshots_by_date:
        date_str = row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date)
        if date_str not in trend_data:
            trend_data[date_str] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        if row.risk_level in trend_data[date_str]:
            trend_data[date_str][row.risk_level] = row.count

    # 转换为列表格式
    trend_list = [
        {"date": d, **levels} for d, levels in sorted(trend_data.items())
    ]

    # 升级事件列表
    upgrade_events = [
        {"date": row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date), "count": row.upgrade_count}
        for row in upgrades_by_date
    ]

    return ResponseModel(
        code=200,
        message="获取全局风险趋势成功",
        data={
            "days": days,
            "trend": trend_list,
            "upgrade_events": upgrade_events,
            "total_upgrades": sum(e["count"] for e in upgrade_events),
            "generated_at": datetime.now().isoformat(),
        },
    )
