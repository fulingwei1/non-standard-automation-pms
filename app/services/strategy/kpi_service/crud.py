# -*- coding: utf-8 -*-
"""
KPI服务 - CRUD操作
"""
import json
from typing import List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.strategy import CSF, KPI
from app.schemas.strategy import KPICreate, KPIUpdate


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
    items = apply_pagination(query.order_by(KPI.csf_id, KPI.code), skip, limit).all()

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
