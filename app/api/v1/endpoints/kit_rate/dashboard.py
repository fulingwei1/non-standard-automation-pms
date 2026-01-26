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
from app.schemas.common import ResponseModel
from app.services.kit_rate import KitRateService
from app.models.user import User

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
    project_id_list = None
    if project_ids:
        project_id_list = [int(id.strip()) for id in project_ids.split(",") if id.strip()]

    service = KitRateService(db)
    return service.get_dashboard(project_id_list)


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


    # 设置默认日期范围
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - td(days=90)  # 默认90天

    if group_by not in ["day", "month"]:
        raise HTTPException(
            status_code=400, detail="group_by 必须是 day 或 month"
        )

    service = KitRateService(db)
    trend = service.get_trend(
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
        project_id=project_id,
    )
    return ResponseModel(code=200, message="success", data=trend)


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

    # 设置默认日期范围
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - td(days=30)

    service = KitRateService(db)
    snapshot_data = service.get_snapshots(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        snapshot_type=snapshot_type,
    )
    return ResponseModel(code=200, message="success", data=snapshot_data)
