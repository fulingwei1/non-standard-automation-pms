# -*- coding: utf-8 -*-
"""
齐套率看板和趋势分析端点
"""

from datetime import date, timedelta
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
        project_id_list = [int(id.strip()) for id in project_ids.split(",") if id.strip()]
        projects = db.query(Project).filter(Project.id.in_(project_id_list)).all()
    else:
        # 查询所有活跃项目
        projects = db.query(Project).filter(Project.is_active == True).all()

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
            current_user=current_user
        )

        dashboard_data.append({
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "kit_rate": kit_rate_data["kit_rate"],
            "kit_status": kit_rate_data["kit_status"],
            "total_items": kit_rate_data["total_items"],
            "fulfilled_items": kit_rate_data["fulfilled_items"],
            "shortage_items": kit_rate_data["shortage_items"],
        })

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
    project_id: Optional[int] = Query(None, description="项目ID（可选，不提供则查询所有项目）"),
    start_date: Optional[date] = Query(None, description="开始日期（可选，默认30天前）"),
    end_date: Optional[date] = Query(None, description="结束日期（可选，默认今天）"),
    group_by: str = Query("day", description="分组方式：day/week/month"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取齐套趋势分析
    按时间分组统计齐套率变化趋势
    """
    # 设置默认日期范围
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    if group_by not in ["day", "week", "month"]:
        raise HTTPException(status_code=400, detail="group_by 必须是 day、week 或 month")

    # 确定要查询的项目
    if project_id:
        projects = db.query(Project).filter(Project.id == project_id).all()
    else:
        projects = db.query(Project).filter(Project.is_active == True).all()

    # 生成日期范围
    date_list = []
    current = start_date
    while current <= end_date:
        date_list.append(current)
        if group_by == "day":
            current += timedelta(days=1)
        elif group_by == "week":
            current += timedelta(days=7)
        else:  # month
            # 计算下个月的同一天
            if current.month == 12:
                current = date(current.year + 1, 1, current.day)
            else:
                current = date(current.year, current.month + 1, current.day)

    # 查询历史数据（这里简化处理，实际应该从历史记录表查询）
    # 由于没有历史记录表，我们使用当前数据模拟趋势
    trend_data = []

    for date_item in date_list:
        # 计算该日期的齐套率（简化：使用当前数据）
        # 实际应该从历史记录表查询该日期的快照数据
        total_kit_rate = 0.0
        project_count = 0

        for project in projects:
            try:
                kit_rate_data = get_project_kit_rate(
                    db=db,
                    project_id=project.id,
                    calculate_by="quantity",
                    current_user=current_user
                )
                total_kit_rate += kit_rate_data["kit_rate"]
                project_count += 1
            except (ValueError, TypeError, KeyError):
                pass

        avg_kit_rate = total_kit_rate / project_count if project_count > 0 else 0.0

        trend_data.append({
            "date": date_item.isoformat(),
            "kit_rate": round(avg_kit_rate, 2),
            "project_count": project_count,
        })

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "group_by": group_by,
        "trend_data": trend_data,
        "summary": {
            "avg_kit_rate": round(sum(d["kit_rate"] for d in trend_data) / len(trend_data) if trend_data else 0, 2),
            "max_kit_rate": round(max((d["kit_rate"] for d in trend_data), default=0), 2),
            "min_kit_rate": round(min((d["kit_rate"] for d in trend_data), default=0), 2),
        }
    }
