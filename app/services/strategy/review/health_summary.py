# -*- coding: utf-8 -*-
"""
健康度汇总

提供战略健康度评分汇总功能
"""

"""
战略管理服务 - 战略审视与例行管理
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.schemas.strategy import (
    DimensionHealthDetail,
    HealthScoreResponse,
)



# ============================================
# 健康度汇总
# ============================================

def get_health_score_summary(db: Session, strategy_id: int) -> HealthScoreResponse:
    """
    获取健康度汇总

    Args:
        db: 数据库会话
        strategy_id: 战略 ID

    Returns:
        HealthScoreResponse: 健康度汇总
    """
    from .health_calculator import (
        calculate_strategy_health,
        get_dimension_health_details,
        get_health_level,
        get_health_trend,
    )

    overall_score = calculate_strategy_health(db, strategy_id)
    overall_level = get_health_level(overall_score) if overall_score else None

    # 获取各维度详情
    dimension_details = get_dimension_health_details(db, strategy_id)
    dimensions = [
        DimensionHealthDetail(
            dimension=d["dimension"],
            dimension_name=d["dimension_name"],
            score=d["score"],
            health_level=d["health_level"],
            csf_count=d["csf_count"],
            kpi_count=d["kpi_count"],
            kpi_completion_rate=d["kpi_completion_rate"],
            kpi_on_track=d.get("kpi_on_track", 0),
            kpi_at_risk=d.get("kpi_at_risk", 0),
            kpi_off_track=d.get("kpi_off_track", 0),
        )
        for d in dimension_details
    ]

    # 获取趋势数据
    trend_data = get_health_trend(db, strategy_id)

    return HealthScoreResponse(
        strategy_id=strategy_id,
        overall_score=overall_score,
        overall_level=overall_level,
        dimensions=dimensions,
        trend=trend_data,
        calculated_at=datetime.now(),
    )


