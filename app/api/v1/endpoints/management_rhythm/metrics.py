# -*- coding: utf-8 -*-
"""
指标定义管理 - 自动生成
从 management_rhythm.py 拆分
"""

# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.management_rhythm import (
    ReportMetricDefinition,
)
from app.models.user import User
from app.schemas.management_rhythm import (
    AvailableMetricsResponse,
    ReportMetricDefinitionCreate,
    ReportMetricDefinitionResponse,
    ReportMetricDefinitionUpdate,
)

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/management-rhythm/metrics",
    tags=["metrics"]
)

# 共 3 个路由

# ==================== 指标定义管理 ====================

@router.get("/meeting-reports/metrics/available", response_model=AvailableMetricsResponse)
def get_available_metrics(
    db: Session = Depends(deps.get_db),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_active: Optional[bool] = Query(True, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取可用指标列表
    """
    query = db.query(ReportMetricDefinition)

    if category:
        query = query.filter(ReportMetricDefinition.category == category)

    if is_active is not None:
        query = query.filter(ReportMetricDefinition.is_active == is_active)

    metrics = query.order_by(ReportMetricDefinition.category, ReportMetricDefinition.metric_name).all()

    # 获取所有分类
    categories = db.query(ReportMetricDefinition.category).distinct().all()
    category_list = sorted([cat[0] for cat in categories])

    items = []
    for metric in metrics:
        items.append(ReportMetricDefinitionResponse(
            id=metric.id,
            metric_code=metric.metric_code,
            metric_name=metric.metric_name,
            category=metric.category,
            description=metric.description,
            data_source=metric.data_source,
            data_field=metric.data_field,
            filter_conditions=metric.filter_conditions,
            calculation_type=metric.calculation_type,
            calculation_formula=metric.calculation_formula,
            support_mom=metric.support_mom,
            support_yoy=metric.support_yoy,
            unit=metric.unit,
            format_type=metric.format_type,
            decimal_places=metric.decimal_places,
            is_active=metric.is_active,
            is_system=metric.is_system,
            created_by=metric.created_by,
            created_at=metric.created_at,
            updated_at=metric.updated_at,
        ))

    return AvailableMetricsResponse(
        metrics=items,
        categories=category_list,
        total_count=len(items)
    )


@router.post("/meeting-reports/metrics", response_model=ReportMetricDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_metric_definition(
    metric_data: ReportMetricDefinitionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建指标定义
    """
    # 检查指标编码是否已存在
    existing = db.query(ReportMetricDefinition).filter(
        ReportMetricDefinition.metric_code == metric_data.metric_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="指标编码已存在")

    metric = ReportMetricDefinition(
        metric_code=metric_data.metric_code,
        metric_name=metric_data.metric_name,
        category=metric_data.category,
        description=metric_data.description,
        data_source=metric_data.data_source,
        data_field=metric_data.data_field,
        filter_conditions=metric_data.filter_conditions,
        calculation_type=metric_data.calculation_type,
        calculation_formula=metric_data.calculation_formula,
        support_mom=metric_data.support_mom,
        support_yoy=metric_data.support_yoy,
        unit=metric_data.unit,
        format_type=metric_data.format_type,
        decimal_places=metric_data.decimal_places,
        is_active=True,
        is_system=False,
        created_by=current_user.id,
    )

    db.add(metric)
    db.commit()
    db.refresh(metric)

    return ReportMetricDefinitionResponse(
        id=metric.id,
        metric_code=metric.metric_code,
        metric_name=metric.metric_name,
        category=metric.category,
        description=metric.description,
        data_source=metric.data_source,
        data_field=metric.data_field,
        filter_conditions=metric.filter_conditions,
        calculation_type=metric.calculation_type,
        calculation_formula=metric.calculation_formula,
        support_mom=metric.support_mom,
        support_yoy=metric.support_yoy,
        unit=metric.unit,
        format_type=metric.format_type,
        decimal_places=metric.decimal_places,
        is_active=metric.is_active,
        is_system=metric.is_system,
        created_by=metric.created_by,
        created_at=metric.created_at,
        updated_at=metric.updated_at,
    )


@router.put("/meeting-reports/metrics/{metric_id}", response_model=ReportMetricDefinitionResponse)
def update_metric_definition(
    metric_id: int,
    metric_data: ReportMetricDefinitionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新指标定义
    """
    metric = db.query(ReportMetricDefinition).filter(ReportMetricDefinition.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="指标定义不存在")

    # 系统预置指标不能修改某些字段
    if metric.is_system:
        if metric_data.data_source or metric_data.calculation_type or metric_data.calculation_formula:
            raise HTTPException(status_code=403, detail="系统预置指标不能修改数据源和计算方式")

    update_data = metric_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(metric, field, value)

    db.commit()
    db.refresh(metric)

    return ReportMetricDefinitionResponse(
        id=metric.id,
        metric_code=metric.metric_code,
        metric_name=metric.metric_name,
        category=metric.category,
        description=metric.description,
        data_source=metric.data_source,
        data_field=metric.data_field,
        filter_conditions=metric.filter_conditions,
        calculation_type=metric.calculation_type,
        calculation_formula=metric.calculation_formula,
        support_mom=metric.support_mom,
        support_yoy=metric.support_yoy,
        unit=metric.unit,
        format_type=metric.format_type,
        decimal_places=metric.decimal_places,
        is_active=metric.is_active,
        is_system=metric.is_system,
        created_by=metric.created_by,
        created_at=metric.created_at,
        updated_at=metric.updated_at,
    )



