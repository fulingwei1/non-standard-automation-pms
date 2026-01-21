# -*- coding: utf-8 -*-
"""
战略管理服务 - KPI 关键绩效指标
"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.strategy import CSF, KPI, KPIDataSource, KPIHistory
from app.schemas.strategy import (
    KPICreate,
    KPIDataSourceCreate,
    KPIDataSourceResponse,
    KPIDetailResponse,
    KPIHistoryResponse,
    KPIUpdate,
    KPIWithHistoryResponse,
)


def create_kpi(db: Session, data: KPICreate) -> KPI:
    """
    创建 KPI

    Args:
        db: 数据库会话
        data: 创建数据

    Returns:
        KPI: 创建的 KPI 对象
    """
    kpi = KPI(
        csf_id=data.csf_id,
        code=data.code,
        name=data.name,
        description=data.description,
        ipooc_type=data.ipooc_type,
        unit=data.unit,
        direction=data.direction,
        target_value=data.target_value,
        baseline_value=data.baseline_value,
        excellent_threshold=data.excellent_threshold,
        good_threshold=data.good_threshold,
        warning_threshold=data.warning_threshold,
        data_source_type=data.data_source_type,
        data_source_config=json.dumps(data.data_source_config) if data.data_source_config else None,
        frequency=data.frequency,
        weight=data.weight,
        owner_user_id=data.owner_user_id,
    )
    db.add(kpi)
    db.commit()
    db.refresh(kpi)
    return kpi


def get_kpi(db: Session, kpi_id: int) -> Optional[KPI]:
    """
    获取 KPI

    Args:
        db: 数据库会话
        kpi_id: KPI ID

    Returns:
        Optional[KPI]: KPI 对象
    """
    return db.query(KPI).filter(
        KPI.id == kpi_id,
        KPI.is_active == True
    ).first()


def list_kpis(
    db: Session,
    csf_id: Optional[int] = None,
    strategy_id: Optional[int] = None,
    ipooc_type: Optional[str] = None,
    data_source_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[KPI], int]:
    """
    获取 KPI 列表

    Args:
        db: 数据库会话
        csf_id: CSF ID 筛选
        strategy_id: 战略 ID 筛选
        ipooc_type: IPOOC 类型筛选
        data_source_type: 数据源类型筛选
        skip: 跳过数量
        limit: 限制数量

    Returns:
        tuple: (KPI 列表, 总数)
    """
    query = db.query(KPI).filter(KPI.is_active == True)

    if csf_id:
        query = query.filter(KPI.csf_id == csf_id)

    if strategy_id:
        query = query.join(CSF).filter(
            CSF.strategy_id == strategy_id,
            CSF.is_active == True
        )

    if ipooc_type:
        query = query.filter(KPI.ipooc_type == ipooc_type)

    if data_source_type:
        query = query.filter(KPI.data_source_type == data_source_type)

    total = query.count()
    items = query.order_by(KPI.csf_id, KPI.code).offset(skip).limit(limit).all()

    return items, total


def update_kpi(db: Session, kpi_id: int, data: KPIUpdate) -> Optional[KPI]:
    """
    更新 KPI

    Args:
        db: 数据库会话
        kpi_id: KPI ID
        data: 更新数据

    Returns:
        Optional[KPI]: 更新后的 KPI 对象
    """
    kpi = get_kpi(db, kpi_id)
    if not kpi:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # 处理 JSON 字段
    if "data_source_config" in update_data and update_data["data_source_config"]:
        update_data["data_source_config"] = json.dumps(update_data["data_source_config"])

    for key, value in update_data.items():
        setattr(kpi, key, value)

    db.commit()
    db.refresh(kpi)
    return kpi


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


def delete_kpi(db: Session, kpi_id: int) -> bool:
    """
    删除 KPI（软删除）

    Args:
        db: 数据库会话
        kpi_id: KPI ID

    Returns:
        bool: 是否删除成功
    """
    kpi = get_kpi(db, kpi_id)
    if not kpi:
        return False

    kpi.is_active = False
    db.commit()
    return True


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


# ============================================
# KPI Data Source 管理
# ============================================

def create_kpi_data_source(db: Session, data: KPIDataSourceCreate) -> KPIDataSource:
    """
    创建 KPI 数据源配置

    Args:
        db: 数据库会话
        data: 创建数据

    Returns:
        KPIDataSource: 创建的数据源配置
    """
    data_source = KPIDataSource(
        kpi_id=data.kpi_id,
        source_type=data.source_type,
        source_module=data.source_module,
        query_type=data.query_type,
        metric=data.metric,
        filters=json.dumps(data.filters) if data.filters else None,
        aggregation=data.aggregation,
        formula=data.formula,
        formula_params=json.dumps(data.formula_params) if data.formula_params else None,
        is_primary=data.is_primary,
    )
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


def get_kpi_data_sources(db: Session, kpi_id: int) -> List[KPIDataSourceResponse]:
    """
    获取 KPI 数据源配置列表

    Args:
        db: 数据库会话
        kpi_id: KPI ID

    Returns:
        List[KPIDataSourceResponse]: 数据源配置列表
    """
    sources = db.query(KPIDataSource).filter(
        KPIDataSource.kpi_id == kpi_id,
        KPIDataSource.is_active == True
    ).all()

    return [
        KPIDataSourceResponse(
            id=s.id,
            kpi_id=s.kpi_id,
            source_type=s.source_type,
            source_module=s.source_module,
            query_type=s.query_type,
            metric=s.metric,
            aggregation=s.aggregation,
            formula=s.formula,
            is_primary=s.is_primary,
            is_active=s.is_active,
            last_executed_at=s.last_executed_at,
            last_result=s.last_result,
            last_error=s.last_error,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sources
    ]
