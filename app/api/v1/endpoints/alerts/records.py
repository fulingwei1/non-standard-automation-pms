# -*- coding: utf-8 -*-
"""
RECORDS - 自动生成
从 alerts.py 拆分
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.alert import (
    AlertRecord,
)
from app.models.user import User
from app.schemas.alert import (
    AlertRecordHandle,
    AlertRecordResponse,
)
from app.schemas.common import PaginatedResponse
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404

router = APIRouter(tags=["records"])

# ==================== 路由定义 ====================
# 共 6 个路由

@router.get("/alerts", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_alert_records(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    alert_level: Optional[str] = Query(None, description="预警级别筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    target_type: Optional[str] = Query(None, description="对象类型筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    date_from: Optional[date] = Query(None, description="开始日期（别名）"),
    date_to: Optional[date] = Query(None, description="结束日期（别名）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取预警记录列表
    """
    query = db.query(AlertRecord)

    # 项目筛选
    if project_id:
        query = query.filter(AlertRecord.project_id == project_id)

    # 机台筛选
    if machine_id:
        query = query.filter(AlertRecord.machine_id == machine_id)

    # 预警级别筛选
    if alert_level:
        query = query.filter(AlertRecord.alert_level == alert_level)

    # 状态筛选
    if status:
        query = query.filter(AlertRecord.status == status)

    # 对象类型筛选
    if target_type:
        query = query.filter(AlertRecord.target_type == target_type)

    # 日期范围筛选（支持 start_date/end_date 和 date_from/date_to）
    date_from_value = date_from or start_date
    date_to_value = date_to or end_date
    if date_from_value:
        query = query.filter(AlertRecord.triggered_at >= datetime.combine(date_from_value, datetime.min.time()))
    if date_to_value:
        query = query.filter(AlertRecord.triggered_at <= datetime.combine(date_to_value, datetime.max.time()))

    # 计算总数
    total = query.count()

    # 分页 - 使用 eager loading 避免 N+1 查询
    alerts_query = query.options(
        joinedload(AlertRecord.rule),
        joinedload(AlertRecord.project),
        joinedload(AlertRecord.machine)
    ).order_by(AlertRecord.triggered_at.desc())
    alerts = apply_pagination(alerts_query, pagination.offset, pagination.limit).all()

    # 批量获取处理人信息（避免循环查询）
    handler_ids = [alert.handler_id for alert in alerts if alert.handler_id]
    handlers_map = {}
    if handler_ids:
        handlers = db.query(User).filter(User.id.in_(handler_ids)).all()
        handlers_map = {h.id: h for h in handlers}

    # 补充关联信息
    items = []
    for alert in alerts:
        project_name = alert.project.project_name if alert.project else None

        handler_name = None
        if alert.handler_id and alert.handler_id in handlers_map:
            handler = handlers_map[alert.handler_id]
            handler_name = handler.real_name or handler.username

        items.append({
            "id": alert.id,
            "alert_no": alert.alert_no,
            "alert_level": alert.alert_level,
            "alert_title": alert.alert_title,
            "target_type": alert.target_type,
            "target_name": alert.target_name,
            "project_name": project_name,
            "triggered_at": alert.triggered_at,
            "status": alert.status,
            "handler_name": handler_name
        })

    return pagination.to_response(items, total)


@router.get("/alerts/{alert_id}", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def read_alert_record(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取预警详情
    """
    alert = db.query(AlertRecord).options(
        joinedload(AlertRecord.rule),
        joinedload(AlertRecord.project),
        joinedload(AlertRecord.machine)
    ).filter(AlertRecord.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    # 补充关联信息（已通过 eager loading 加载）
    rule_name = alert.rule.rule_name if alert.rule else None
    project_name = alert.project.project_name if alert.project else None

    handler_name = None
    if alert.handler_id:
        handler = db.query(User).filter(User.id == alert.handler_id).first()
        handler_name = handler.real_name or handler.username if handler else None

    return {
        "id": alert.id,
        "alert_no": alert.alert_no,
        "rule_id": alert.rule_id,
        "rule_name": rule_name,
        "target_type": alert.target_type,
        "target_id": alert.target_id,
        "target_no": alert.target_no,
        "target_name": alert.target_name,
        "project_id": alert.project_id,
        "project_name": project_name,
        "alert_level": alert.alert_level,
        "alert_title": alert.alert_title,
        "alert_content": alert.alert_content,
        "triggered_at": alert.triggered_at,
        "trigger_value": alert.trigger_value,
        "threshold_value": alert.threshold_value,
        "status": alert.status,
        "acknowledged_by": alert.acknowledged_by,
        "acknowledged_at": alert.acknowledged_at,
        "handler_id": alert.handler_id,
        "handler_name": handler_name,
        "handle_start_at": alert.handle_start_at,
        "handle_end_at": alert.handle_end_at,
        "handle_result": alert.handle_result,
        "created_at": alert.created_at,
        "updated_at": alert.updated_at
    }


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def acknowledge_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认预警
    """
    alert = get_or_404(db, AlertRecord, alert_id, "预警记录不存在")

    if alert.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能确认待处理状态的预警")

    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now()

    db.add(alert)
    db.commit()
    db.refresh(alert)

    # 返回详情（需要重新查询以获取关联信息）
    return read_alert_record(alert_id, db, current_user)


@router.put("/alerts/{alert_id}/resolve", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def resolve_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    handle_in: AlertRecordHandle,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    处理预警
    """
    alert = get_or_404(db, AlertRecord, alert_id, "预警记录不存在")

    if alert.status == "RESOLVED":
        raise HTTPException(status_code=400, detail="预警已处理")

    # 如果还未开始处理，设置开始时间
    if not alert.handle_start_at:
        alert.handle_start_at = datetime.now()
        alert.handler_id = current_user.id

    alert.status = "RESOLVED"
    alert.handle_end_at = datetime.now()
    alert.handle_result = handle_in.handle_result
    alert.handle_note = handle_in.handle_note

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return read_alert_record(alert_id, db, current_user)


@router.put("/alerts/{alert_id}/close", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def close_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    handle_in: AlertRecordHandle,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭预警
    """
    alert = get_or_404(db, AlertRecord, alert_id, "预警记录不存在")

    if alert.status == "CLOSED":
        raise HTTPException(status_code=400, detail="预警已关闭")

    alert.status = "CLOSED"
    alert.handler_id = current_user.id
    alert.handle_end_at = datetime.now()
    if handle_in.handle_result:
        alert.handle_result = handle_in.handle_result

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return read_alert_record(alert_id, db, current_user)


@router.put("/alerts/{alert_id}/ignore", response_model=AlertRecordResponse, status_code=status.HTTP_200_OK)
def ignore_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    忽略预警
    """
    alert = get_or_404(db, AlertRecord, alert_id, "预警记录不存在")

    if alert.status == "RESOLVED":
        raise HTTPException(status_code=400, detail="已处理的预警不能忽略")

    alert.status = "IGNORED"
    alert.handler_id = current_user.id
    alert.handle_end_at = datetime.now()
    alert.handle_result = "已忽略"

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return read_alert_record(alert_id, db, current_user)
