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
    group_by: str = Query("day", description="分组方式：day（每日）或 month（每月）"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取齐套率趋势分析（基于历史快照数据）

    - 支持按日（day）或按月（month）分组
    - 基于 KitRateSnapshot 快照表查询历史数据
    - 如果指定项目则返回该项目的趋势，否则返回所有活跃项目的平均趋势
    """
    from datetime import timedelta as td


    from app.models.assembly_kit import KitRateSnapshot
    from app.schemas.common import ResponseModel

    # 设置默认日期范围
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - td(days=90)  # 默认90天

    if group_by not in ["day", "month"]:
        raise HTTPException(
            status_code=400, detail="group_by 必须是 day 或 month"
        )

    # 构建快照查询
    query = db.query(KitRateSnapshot).filter(
        KitRateSnapshot.snapshot_date >= start_date,
        KitRateSnapshot.snapshot_date <= end_date,
    )

    if project_id:
        query = query.filter(KitRateSnapshot.project_id == project_id)

    snapshots = query.order_by(KitRateSnapshot.snapshot_date).all()

    # 如果没有快照数据，返回空趋势并提示
    if not snapshots:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "group_by": group_by,
                "trend_data": [],
                "summary": {
                    "avg_kit_rate": 0.0,
                    "max_kit_rate": 0.0,
                    "min_kit_rate": 0.0,
                    "data_points": 0,
                },
                "note": "暂无快照数据。定时任务会在每日凌晨自动生成快照。",
            },
        )

    # 按分组方式聚合数据
    trend_data = []

    if group_by == "day":
        # 按日分组
        daily_data = {}
        for snapshot in snapshots:
            day_key = snapshot.snapshot_date.isoformat()
            if day_key not in daily_data:
                daily_data[day_key] = {
                    "rates": [],
                    "total_items": 0,
                    "fulfilled_items": 0,
                    "shortage_items": 0,
                }
            daily_data[day_key]["rates"].append(float(snapshot.kit_rate))
            daily_data[day_key]["total_items"] += snapshot.total_items or 0
            daily_data[day_key]["fulfilled_items"] += snapshot.fulfilled_items or 0
            daily_data[day_key]["shortage_items"] += snapshot.shortage_items or 0

        for day_key in sorted(daily_data.keys()):
            data = daily_data[day_key]
            avg_rate = sum(data["rates"]) / len(data["rates"]) if data["rates"] else 0.0
            trend_data.append({
                "date": day_key,
                "kit_rate": round(avg_rate, 2),
                "project_count": len(data["rates"]),
                "total_items": data["total_items"],
                "fulfilled_items": data["fulfilled_items"],
                "shortage_items": data["shortage_items"],
            })

    else:  # month
        # 按月分组
        monthly_data = {}
        for snapshot in snapshots:
            month_key = snapshot.snapshot_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "rates": [],
                    "total_items": 0,
                    "fulfilled_items": 0,
                    "shortage_items": 0,
                }
            monthly_data[month_key]["rates"].append(float(snapshot.kit_rate))
            monthly_data[month_key]["total_items"] += snapshot.total_items or 0
            monthly_data[month_key]["fulfilled_items"] += snapshot.fulfilled_items or 0
            monthly_data[month_key]["shortage_items"] += snapshot.shortage_items or 0

        for month_key in sorted(monthly_data.keys()):
            data = monthly_data[month_key]
            avg_rate = sum(data["rates"]) / len(data["rates"]) if data["rates"] else 0.0
            trend_data.append({
                "date": month_key,
                "kit_rate": round(avg_rate, 2),
                "project_count": len(data["rates"]),
                "total_items": data["total_items"],
                "fulfilled_items": data["fulfilled_items"],
                "shortage_items": data["shortage_items"],
            })

    # 计算汇总统计
    if trend_data:
        all_rates = [d["kit_rate"] for d in trend_data]
        avg_rate = sum(all_rates) / len(all_rates)
        max_rate = max(all_rates)
        min_rate = min(all_rates)
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
        },
    )


@router.get("/kit-rate/snapshots")
def get_kit_rate_snapshots(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Query(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    snapshot_type: Optional[str] = Query(None, description="快照类型: DAILY/STAGE_CHANGE/MANUAL"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取项目的齐套率快照历史

    返回指定项目的所有快照记录，包括每日快照和阶段切换快照。
    """
    from datetime import timedelta as td

    from app.models.assembly_kit import KitRateSnapshot
    from app.schemas.common import ResponseModel

    # 设置默认日期范围
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - td(days=30)

    # 查询快照
    query = db.query(KitRateSnapshot).filter(
        KitRateSnapshot.project_id == project_id,
        KitRateSnapshot.snapshot_date >= start_date,
        KitRateSnapshot.snapshot_date <= end_date,
    )

    if snapshot_type:
        query = query.filter(KitRateSnapshot.snapshot_type == snapshot_type)

    snapshots = query.order_by(KitRateSnapshot.snapshot_time.desc()).all()

    # 获取项目信息
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    snapshot_list = []
    for s in snapshots:
        snapshot_list.append({
            "id": s.id,
            "snapshot_date": s.snapshot_date.isoformat(),
            "snapshot_time": s.snapshot_time.isoformat() if s.snapshot_time else None,
            "snapshot_type": s.snapshot_type,
            "trigger_event": s.trigger_event,
            "kit_rate": float(s.kit_rate) if s.kit_rate else 0.0,
            "kit_status": s.kit_status,
            "total_items": s.total_items,
            "fulfilled_items": s.fulfilled_items,
            "shortage_items": s.shortage_items,
            "in_transit_items": s.in_transit_items,
            "blocking_kit_rate": float(s.blocking_kit_rate) if s.blocking_kit_rate else 0.0,
            "project_stage": s.project_stage,
            "project_health": s.project_health,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_snapshots": len(snapshot_list),
            "snapshots": snapshot_list,
        },
    )
