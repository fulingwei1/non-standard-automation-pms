# -*- coding: utf-8 -*-
"""
KPI服务 - 数据源管理
"""
import json
from typing import List

from sqlalchemy.orm import Session

from app.models.strategy import KPIDataSource
from app.schemas.strategy import (
    KPIDataSourceCreate,
    KPIDataSourceResponse,
)


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
