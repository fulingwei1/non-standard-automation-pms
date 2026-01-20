# -*- coding: utf-8 -*-
"""
齐套率看板和趋势分析端点
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User

from .project import get_project_kit_rate

router = APIRouter()


@router.get("/kit-rate/dashboard")
def get_kit_rate_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取齐套看板数据（全局看板）
    """
    # 如果指定了项目ID，只查询这些项目
    if project_ids:
        project_id_list = [
            int(id.strip()) for id in project_ids.split(",") if id.strip()
        ]
        projects = db.query(Project).filter(Project.id.in_(project_id_list)).all()
    else:
        from sqlalchemy import true

        # 查询所有活跃项目
        projects = db.query(Project).filter(Project.is_active == true()).all()

    dashboard_data = []
    total_projects = 0
    complete_projects = 0
    partial_projects = 0
    shortage_projects = 0

    for project in projects:
        kit_rate_data = get_project_kit_rate(
            db=db,
            project_id=project.id,
            calculate_by="quantity",
            current_user=current_user,
        )

        dashboard_data.append(
            {
                "project_id": project.id,
                "project_code": project.project_code,
                "project_name": project.project_name,
                "kit_rate": kit_rate_data["kit_rate"],
                "kit_status": kit_rate_data["kit_status"],
                "total_items": kit_rate_data["total_items"],
                "fulfilled_items": kit_rate_data["fulfilled_items"],
                "shortage_items": kit_rate_data["shortage_items"],
            }
        )

        total_projects += 1
        if kit_rate_data["kit_status"] == "complete":
            complete_projects += 1
        elif kit_rate_data["kit_status"] == "partial":
            partial_projects += 1
        else:
            shortage_projects += 1

    return {
        "summary": {
            "total_projects": total_projects,
            "complete_projects": complete_projects,
            "partial_projects": partial_projects,
            "shortage_projects": shortage_projects,
        },
        "projects": dashboard_data,
    }


@router.get("/kit-rate/trend")
def get_kit_rate_trend(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(
        None, description="项目ID（可选，不提供则查询所有项目）"
    ),
    start_date: Optional[date] = Query(
        None, description="开始日期（可选，默认30天前）"
    ),
    end_date: Optional[date] = Query(None, description="结束日期（可选，默认今天）"),
    group_by: str = Query("month", description="分组方式：month"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取齐套趋势分析

    注意：此端点返回当前项目状态，不提供历史趋势数据。
    历史快照功能待实现（需要创建 KitRateSnapshot 模型）。
    """
    from datetime import timedelta as td

    # 设置默认日期范围
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - td(days=90)  # 默认90天（3个月）

    if group_by != "month":
        raise HTTPException(
            status_code=400, detail="当前仅支持按月分组（group_by=month）"
        )

    # 确定要查询的项目
    if project_id:
        projects = db.query(Project).filter(Project.id == project_id).all()
    else:
        projects = db.query(Project).filter(Project.is_active == True).all()

    # 生成月份范围
    months_list = []
    current = end_date

    # 从结束日期往前推算月份，直到覆盖 start_date
    while current >= start_date:
        months_list.insert(0, current.replace(day=1))
        if current.month == 1:
            current = date(current.year - 1, 12, 1)
        else:
            current = date(current.year, current.month - 1, 1)

    # 查询每个月份的项目数据
    trend_data = []

    for month_date in months_list:
        month_start = month_date
        if month_date.month == 12:
            next_month_start = date(month_date.year + 1, 1, 1)
        else:
            next_month_start = date(month_date.year, month_date.month + 1, 1)

        # 查询该月份创建的项目
        month_projects = [
            p
            for p in projects
            if p.created_at and month_start <= p.created_at.date() < next_month_start
        ]

        total_kit_rate = 0.0
        project_count = len(month_projects)

        for project in month_projects:
            try:
                kit_rate_data = get_project_kit_rate(
                    db=db,
                    project_id=project.id,
                    calculate_by="quantity",
                    current_user=current_user,
                )
                total_kit_rate += kit_rate_data["kit_rate"]
            except (ValueError, TypeError, KeyError):
                pass

        avg_kit_rate = total_kit_rate / project_count if project_count > 0 else 0.0

        trend_data.append(
            {
                "date": month_date.strftime("%Y-%m"),
                "kit_rate": round(avg_kit_rate, 2),
                "project_count": project_count,
            }
        )

    # 计算汇总统计
    if trend_data:
        avg_rate = sum(d["kit_rate"] for d in trend_data) / len(trend_data)
        max_rate = max(d["kit_rate"] for d in trend_data)
        min_rate = min(d["kit_rate"] for d in trend_data)
    else:
        avg_rate = 0.0
        max_rate = 0.0
        min_rate = 0.0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by,
            "trend_data": trend_data,
            "summary": {
                "avg_kit_rate": round(avg_rate, 2),
                "max_kit_rate": round(max_rate, 2),
                "min_kit_rate": round(min_rate, 2),
                "data_points": len(trend_data),
            },
            "note": "当前返回项目创建月份的实际齐套率。历史快照功能待实现。",
        },
    )
