# -*- coding: utf-8 -*-
"""
项目工作日志查询（使用统一统计服务）

提供项目相关工作日志的只读视图
工作日志本身属于用户，这里只展示提及了该项目的日志
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.work_log import WorkLog, WorkLogMention
from app.schemas.common import ResponseModel
from app.services.project_statistics_service import WorkLogStatisticsService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=ResponseModel)
def list_project_work_logs(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取提及该项目的工作日志

    工作日志属于用户，此接口展示所有提及该项目的日志
    """
    check_project_access_or_raise(db, current_user, project_id)

    # 查询提及该项目的工作日志
    query = (
        db.query(WorkLog)
        .join(WorkLogMention, WorkLog.id == WorkLogMention.work_log_id)
        .filter(
            WorkLogMention.mention_type == "PROJECT",
            WorkLogMention.mention_id == project_id,
        )
    )

    if start_date:
        query = query.filter(WorkLog.work_date >= start_date)
    if end_date:
        query = query.filter(WorkLog.work_date <= end_date)

    total = query.count()
    logs = (
        query.order_by(desc(WorkLog.work_date), desc(WorkLog.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    # 构建响应
    items = []
    for log in logs:
        items.append(
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "work_date": log.work_date,
                "content": log.content,
                "status": log.status,
                "created_at": log.created_at,
            }
        )

    return ResponseModel(
        data={
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    )


@router.get("/summary", response_model=ResponseModel)
def get_project_work_log_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取项目工作日志汇总（使用统一统计服务）

    统计最近N天内该项目被提及的日志数量和参与人数
    """
    check_project_access_or_raise(db, current_user, project_id)
    
    service = WorkLogStatisticsService(db)
    summary = service.get_summary(project_id, days=days)
    
    return ResponseModel(data=summary)
