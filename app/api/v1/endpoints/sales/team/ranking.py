# -*- coding: utf-8 -*-
"""
销售排名配置和排名查询 API endpoints
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import SalesRankingConfigUpdateRequest
from app.services.sales_ranking_service import SalesRankingService

from ..utils import get_visible_sales_users, normalize_date_range
from .utils import ensure_sales_director_permission

router = APIRouter()


@router.get("/team/ranking/config", response_model=ResponseModel)
def get_sales_ranking_config(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取销售排名权重配置"""
    service = SalesRankingService(db)
    config = service.get_active_config()
    return ResponseModel(
        code=200,
        message="success",
        data={
            "metrics": config.metrics,
            "total_weight": sum(m.get("weight", 0) for m in config.metrics),
            "updated_at": config.updated_at,
        },
    )


@router.put("/team/ranking/config", response_model=ResponseModel, status_code=200)
def update_sales_ranking_config(
    *,
    request: SalesRankingConfigUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新销售排名权重配置（仅销售总监）"""
    ensure_sales_director_permission(current_user, db)
    service = SalesRankingService(db)
    try:
        config = service.save_config(request.metrics, operator_id=current_user.id)
    except ValueError as exc:  # 权重校验失败
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ResponseModel(
        code=200,
        message="配置已更新",
        data={
            "metrics": config.metrics,
            "total_weight": sum(m.get("weight", 0) for m in config.metrics),
            "updated_at": config.updated_at,
        },
    )


@router.get("/team/ranking", response_model=ResponseModel)
def get_sales_team_ranking(
    *,
    db: Session = Depends(deps.get_db),
    ranking_type: str = Query("score", description="排名类型：score 或具体指标（lead_count/opportunity_count/contract_amount/collection_amount 等）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    region: Optional[str] = Query(None, description="区域关键字筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取销售团队排名"""
    normalized_start, normalized_end = normalize_date_range(start_date, end_date)
    start_datetime = datetime.combine(normalized_start, datetime.min.time())
    end_datetime = datetime.combine(normalized_end, datetime.max.time())

    users = get_visible_sales_users(db, current_user, department_id, region)
    ranking_service = SalesRankingService(db)
    ranking_result = ranking_service.calculate_rankings(
        users, start_datetime, end_datetime, ranking_type=ranking_type
    )
    ranking_list = ranking_result.get("rankings", [])[:limit]
    total_count = len(ranking_result.get("rankings", []))

    return ResponseModel(
        code=200,
        message="success",
        data={
            "ranking_type": ranking_result.get("ranking_type"),
            "start_date": normalized_start.isoformat(),
            "end_date": normalized_end.isoformat(),
            "rankings": ranking_list,
            "total_count": total_count,
            "config": ranking_result.get("config"),
            "max_values": ranking_result.get("max_values"),
        }
    )
