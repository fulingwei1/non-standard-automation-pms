# -*- coding: utf-8 -*-
"""
KPI服务 - 详情和历史
"""
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.strategy import CSF, KPI, KPIHistory
from app.schemas.strategy import (
    KPIDetailResponse,
    KPIHistoryResponse,
    KPIWithHistoryResponse,
)

from .crud import get_kpi
from .snapshot import _calculate_trend


def get_kpi_detail(db: Session, kpi_id: int) -> Optional[KPIDetailResponse]:
    """
    获取 KPI 详情

    Args:
        db: 数据库会话
        kpi_id: KPI ID

    Returns:
        Optional[KPIDetailResponse]: KPI 详情
    """
    kpi = get_kpi(db, kpi_id)
    if not kpi:
        return None

    # 获取健康度
    from .health_calculator import calculate_kpi_health, calculate_kpi_completion_rate
    health_data = calculate_kpi_health(db, kpi_id)
    completion_rate = calculate_kpi_completion_rate(kpi)

    # 获取责任人名称
    owner_name = None
    if kpi.owner_user_id:
        from app.models.user import User
        user = db.query(User).filter(User.id == kpi.owner_user_id).first()
        if user:
            owner_name = user.name

    # 获取 CSF 信息
    csf = db.query(CSF).filter(CSF.id == kpi.csf_id).first()
    csf_name = csf.name if csf else None
    csf_dimension = csf.dimension if csf else None

    # 计算趋势
    trend = _calculate_trend(db, kpi_id)

    return KPIDetailResponse(
        id=kpi.id,
        csf_id=kpi.csf_id,
        code=kpi.code,
        name=kpi.name,
        description=kpi.description,
        ipooc_type=kpi.ipooc_type,
        unit=kpi.unit,
        direction=kpi.direction,
        target_value=kpi.target_value,
        baseline_value=kpi.baseline_value,
        current_value=kpi.current_value,
        excellent_threshold=kpi.excellent_threshold,
        good_threshold=kpi.good_threshold,
        warning_threshold=kpi.warning_threshold,
        data_source_type=kpi.data_source_type,
        frequency=kpi.frequency,
        last_collected_at=kpi.last_collected_at,
        weight=kpi.weight,
        owner_user_id=kpi.owner_user_id,
        is_active=kpi.is_active,
        created_at=kpi.created_at,
        updated_at=kpi.updated_at,
        owner_name=owner_name,
        csf_name=csf_name,
        csf_dimension=csf_dimension,
        completion_rate=completion_rate,
        health_level=health_data.get("level"),
        trend=trend,
    )


def get_kpi_history(
    db: Session,
    kpi_id: int,
    limit: int = 12
) -> List[KPIHistoryResponse]:
    """
    获取 KPI 历史记录

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        limit: 限制数量

    Returns:
        List[KPIHistoryResponse]: 历史记录列表
    """
    history = db.query(KPIHistory).filter(
        KPIHistory.kpi_id == kpi_id
    ).order_by(desc(KPIHistory.snapshot_date)).limit(limit).all()

    return [
        KPIHistoryResponse(
            id=h.id,
            kpi_id=h.kpi_id,
            snapshot_date=h.snapshot_date,
            snapshot_period=h.snapshot_period,
            value=h.value,
            target_value=h.target_value,
            completion_rate=h.completion_rate,
            health_level=h.health_level,
            source_type=h.source_type,
            remark=h.remark,
            recorded_by=h.recorded_by,
            created_at=h.created_at,
            updated_at=h.updated_at,
        )
        for h in reversed(history)
    ]


def get_kpi_with_history(db: Session, kpi_id: int) -> Optional[KPIWithHistoryResponse]:
    """
    获取 KPI 详情及历史

    Args:
        db: 数据库会话
        kpi_id: KPI ID

    Returns:
        Optional[KPIWithHistoryResponse]: KPI 详情及历史
    """
    detail = get_kpi_detail(db, kpi_id)
    if not detail:
        return None

    history = get_kpi_history(db, kpi_id)

    return KPIWithHistoryResponse(
        **detail.model_dump(),
        history=history,
    )
