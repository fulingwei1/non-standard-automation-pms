# -*- coding: utf-8 -*-
"""
KPI服务 - 值更新
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.strategy import KPI

from .crud import get_kpi
from .snapshot import create_kpi_snapshot


def update_kpi_value(
    db: Session,
    kpi_id: int,
    value: Decimal,
    recorded_by: int,
    remark: Optional[str] = None
) -> Optional[KPI]:
    """
    更新 KPI 当前值

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        value: 新值
        recorded_by: 记录人 ID
        remark: 备注

    Returns:
        Optional[KPI]: 更新后的 KPI 对象
    """
    kpi = get_kpi(db, kpi_id)
    if not kpi:
        return None

    # 更新当前值
    kpi.current_value = value
    kpi.last_collected_at = datetime.now()

    # 创建历史记录
    create_kpi_snapshot(db, kpi_id, "MANUAL", recorded_by, remark)

    db.commit()
    db.refresh(kpi)
    return kpi
