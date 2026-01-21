# -*- coding: utf-8 -*-
"""
预警统计 - 趋势分析
"""
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.alert import AlertRecord
from app.models.user import User

router = APIRouter()


@router.get("/alerts/statistics/trends", response_model=dict, status_code=status.HTTP_200_OK)
def get_alert_trends(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    period: str = Query("DAILY", description="统计周期: DAILY/WEEKLY/MONTHLY"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    预警趋势分析数据

    返回多维度趋势数据：
    - 按日期统计（日/周/月）
    - 按级别统计趋势
    - 按类型统计趋势
    - 按状态统计趋势
    """
    from app.services.alert_trend_service import (
        build_summary_statistics,
        build_trend_statistics,
        generate_date_range,
    )

    # 默认时间范围：最近30天
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    query = db.query(AlertRecord).filter(
        AlertRecord.triggered_at.isnot(None)
    )

    if project_id:
        query = query.filter(AlertRecord.project_id == project_id)

    query = query.filter(
        AlertRecord.triggered_at >= datetime.combine(start_date, datetime.min.time()),
        AlertRecord.triggered_at <= datetime.combine(end_date, datetime.max.time())
    )

    alerts = query.all()

    # 构建趋势统计
    trend_stats = build_trend_statistics(alerts, period)
    date_trends = trend_stats['date_trends']
    level_trends = trend_stats['level_trends']
    type_trends = trend_stats['type_trends']
    status_trends = trend_stats['status_trends']

    # 生成完整的时间序列
    date_range = generate_date_range(start_date, end_date, period)

    # 构建趋势数据数组
    trends_data = []
    for date_key in date_range:
        trends_data.append({
            "date": date_key,
            "total": date_trends.get(date_key, 0),
            "by_level": level_trends.get(date_key, {}),
            "by_type": type_trends.get(date_key, {}),
            "by_status": status_trends.get(date_key, {}),
        })

    # 汇总统计
    summary_stats = build_summary_statistics(alerts)

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "trends": trends_data,
        "summary": {
            "total": len(alerts),
            "by_level": summary_stats['by_level'],
            "by_type": summary_stats['by_type'],
            "by_status": summary_stats['by_status'],
        }
    }
