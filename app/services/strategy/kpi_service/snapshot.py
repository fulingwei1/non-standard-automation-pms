# -*- coding: utf-8 -*-
"""
KPI服务 - 快照和趋势
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.strategy import KPI, KPIHistory

from .crud import get_kpi


def _get_current_period(frequency: str) -> str:
    """获取当前周期标识"""
    today = date.today()
    if frequency == "DAILY":
        return today.strftime("%Y-%m-%d")
    elif frequency == "WEEKLY":
        return f"{today.year}-W{today.isocalendar()[1]:02d}"
    elif frequency == "MONTHLY":
        return today.strftime("%Y-%m")
    elif frequency == "QUARTERLY":
        quarter = (today.month - 1) // 3 + 1
        return f"{today.year}-Q{quarter}"
    else:
        return str(today.year)


def _calculate_trend(db: Session, kpi_id: int) -> Optional[str]:
    """计算 KPI 趋势"""
    # 获取最近两条历史记录
    history = db.query(KPIHistory).filter(
        KPIHistory.kpi_id == kpi_id
    ).order_by(desc(KPIHistory.snapshot_date)).limit(2).all()

    if len(history) < 2:
        return None

    current = history[0].value
    previous = history[1].value

    if current is None or previous is None:
        return None

    if current > previous:
        return "UP"
    elif current < previous:
        return "DOWN"
    else:
        return "STABLE"


def create_kpi_snapshot(
    db: Session,
    kpi_id: int,
    source_type: str,
    recorded_by: Optional[int] = None,
    remark: Optional[str] = None
) -> KPIHistory:
    """
    创建 KPI 快照

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        source_type: 来源类型
        recorded_by: 记录人
        remark: 备注

    Returns:
        KPIHistory: 创建的历史记录
    """
    kpi = get_kpi(db, kpi_id)
    if not kpi:
        return None

    # 计算完成率和健康度
    from .health_calculator import calculate_kpi_completion_rate, get_health_level
    completion_rate = calculate_kpi_completion_rate(kpi)
    health_level = None
    if completion_rate is not None:
        score = int(min(completion_rate, 100))
        health_level = get_health_level(score)

    history = KPIHistory(
        kpi_id=kpi_id,
        snapshot_date=date.today(),
        snapshot_period=_get_current_period(kpi.frequency),
        value=kpi.current_value,
        target_value=kpi.target_value,
        completion_rate=Decimal(str(completion_rate)) if completion_rate else None,
        health_level=health_level,
        source_type=source_type,
        remark=remark,
        recorded_by=recorded_by,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
