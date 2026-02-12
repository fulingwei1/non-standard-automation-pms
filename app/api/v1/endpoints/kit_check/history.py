# -*- coding: utf-8 -*-
"""
齐套检查历史查询端点
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.production import WorkOrder
from app.models.project import Project
from app.models.shortage import KitCheck
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.query_filters import apply_pagination

router = APIRouter()


@router.get("/kit-check/history", response_model=ResponseModel)
def get_kit_check_history(
    db: Session = Depends(deps.get_db),
    work_order_id: Optional[int] = Query(None, description="工单ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    齐套检查历史
    获取历史齐套检查记录
    """
    query = db.query(KitCheck)

    # 筛选条件
    if work_order_id:
        query = query.filter(KitCheck.work_order_id == work_order_id)
    if project_id:
        query = query.filter(KitCheck.project_id == project_id)
    if start_date:
        query = query.filter(func.date(KitCheck.check_time) >= start_date)
    if end_date:
        query = query.filter(func.date(KitCheck.check_time) <= end_date)

    # 总数
    total = query.count()

    # 分页
    checks = apply_pagination(query.order_by(desc(KitCheck.check_time)), pagination.offset, pagination.limit).all()

    # 构建返回数据
    history = []
    for check in checks:
        # 获取关联信息
        work_order = db.query(WorkOrder).filter(WorkOrder.id == check.work_order_id).first() if check.work_order_id else None
        project = db.query(Project).filter(Project.id == check.project_id).first() if check.project_id else None
        checker = db.query(User).filter(User.id == check.checked_by).first() if check.checked_by else None
        confirmer = db.query(User).filter(User.id == check.confirmed_by).first() if check.confirmed_by else None

        history.append({
            "id": check.id,
            "check_no": check.check_no,
            "check_type": check.check_type,
            "work_order_id": check.work_order_id,
            "work_order_no": work_order.work_order_no if work_order else None,
            "project_id": check.project_id,
            "project_name": project.project_name if project else None,
            "total_items": check.total_items,
            "fulfilled_items": check.fulfilled_items,
            "shortage_items": check.shortage_items,
            "in_transit_items": check.in_transit_items,
            "kit_rate": float(check.kit_rate) if check.kit_rate else 0.0,
            "kit_status": check.kit_status,
            "check_time": check.check_time.isoformat() if check.check_time else None,
            "check_method": check.check_method,
            "checked_by": check.checked_by,
            "checker_name": checker.real_name or checker.username if checker else None,
            "can_start": check.can_start,
            "start_confirmed": check.start_confirmed,
            "confirm_time": check.confirm_time.isoformat() if check.confirm_time else None,
            "confirmed_by": check.confirmed_by,
            "confirmer_name": confirmer.real_name or confirmer.username if confirmer else None,
            "confirm_remark": check.confirm_remark,
            "shortage_summary": check.shortage_summary,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "history": history,
            "pagination": {
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total": total,
                "pages": pagination.pages_for_total(total),
            }
        }
    )
