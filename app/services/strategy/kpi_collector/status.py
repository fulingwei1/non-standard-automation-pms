# -*- coding: utf-8 -*-
"""
KPI数据采集器 - 状态查询
"""
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.strategy import CSF, KPI


def get_collection_status(db: Session, strategy_id: int) -> Dict[str, Any]:
    """
    获取采集状态概览

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        Dict: 采集状态统计
    """
    kpis = db.query(KPI).join(CSF).filter(
        CSF.strategy_id == strategy_id,
        CSF.is_active == True,
        KPI.is_active == True
    ).all()

    auto_kpis = [k for k in kpis if k.data_source_type == "AUTO"]
    manual_kpis = [k for k in kpis if k.data_source_type == "MANUAL"]

    # 统计各频率的 KPI
    frequency_stats: Dict[str, Dict[str, int]] = {}
    for kpi in kpis:
        freq = kpi.frequency or "UNKNOWN"
        if freq not in frequency_stats:
            frequency_stats[freq] = {"total": 0, "collected": 0}
        frequency_stats[freq]["total"] += 1
        if kpi.current_value is not None:
            frequency_stats[freq]["collected"] += 1

    # 最近采集时间
    collected_times = [k.last_collected_at for k in kpis if k.last_collected_at]
    last_collected = max(collected_times) if collected_times else None

    return {
        "total_kpis": len(kpis),
        "auto_kpis": len(auto_kpis),
        "manual_kpis": len(manual_kpis),
        "collected_kpis": sum(1 for k in kpis if k.current_value is not None),
        "pending_kpis": sum(1 for k in kpis if k.current_value is None),
        "frequency_stats": frequency_stats,
        "last_collected_at": last_collected,
    }
