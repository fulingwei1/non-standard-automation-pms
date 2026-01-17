# -*- coding: utf-8 -*-
"""
物料需求时间表
"""

from datetime import date, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader, BomItem
from app.models.project import Machine
from app.models.user import User

router = APIRouter()


@router.get("/material-demands/schedule", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_material_demand_schedule(
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表（逗号分隔）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: str = Query("day", description="分组方式：day/week/month"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    需求时间表（按日期需求）
    """
    # 解析项目ID列表
    project_id_list = None
    if project_ids:
        project_id_list = [int(p.strip()) for p in project_ids.split(",") if p.strip()]

    # 默认查询未来30天
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)

    # 从BOM明细查询需求
    query = (
        db.query(
            BomItem.required_date,
            BomItem.material_id,
            BomItem.material_code,
            BomItem.material_name,
            func.sum(BomItem.quantity).label('demand_qty')
        )
        .join(BomHeader, BomItem.bom_id == BomHeader.id)
        .join(Machine, BomHeader.machine_id == Machine.id)
        .filter(BomItem.required_date >= start_date)
        .filter(BomItem.required_date <= end_date)
    )

    if project_id_list:
        query = query.filter(Machine.project_id.in_(project_id_list))

    query = query.group_by(BomItem.required_date, BomItem.material_id, BomItem.material_code, BomItem.material_name)
    results = query.all()

    # 按日期分组
    schedule = {}
    for result in results:
        demand_date = result.required_date.isoformat() if result.required_date else None
        if not demand_date:
            continue

        # 根据分组方式调整日期
        if group_by == "week":
            # 获取该周的周一
            demand_date_obj = result.required_date
            days_since_monday = demand_date_obj.weekday()
            week_start = demand_date_obj - timedelta(days=days_since_monday)
            demand_date = week_start.isoformat()
        elif group_by == "month":
            # 使用月份的第一天
            demand_date_obj = result.required_date
            demand_date = date(demand_date_obj.year, demand_date_obj.month, 1).isoformat()

        if demand_date not in schedule:
            schedule[demand_date] = []

        schedule[demand_date].append({
            "material_id": result.material_id,
            "material_code": result.material_code,
            "material_name": result.material_name,
            "demand_qty": float(result.demand_qty)
        })

    # 转换为列表格式
    items = []
    for demand_date in sorted(schedule.keys()):
        items.append({
            "date": demand_date,
            "materials": schedule[demand_date],
            "total_materials": len(schedule[demand_date]),
            "total_demand": sum(m["demand_qty"] for m in schedule[demand_date])
        })

    return items
