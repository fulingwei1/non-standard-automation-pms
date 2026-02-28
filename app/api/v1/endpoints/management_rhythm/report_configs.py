# -*- coding: utf-8 -*-
"""
报告配置管理 - 自动生成
从 management_rhythm.py 拆分
"""

# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.management_rhythm import (
    MeetingReportConfig,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.management_rhythm import (
    MeetingReportConfigCreate,
    MeetingReportConfigResponse,
    MeetingReportConfigUpdate,
)
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()



from fastapi import APIRouter
from app.common.query_filters import apply_pagination

router = APIRouter(
    prefix="/report-configs",
    tags=["report_configs"]
)

# 共 5 个路由

# ==================== 报告配置管理 ====================

@router.get("/meeting-reports/configs", response_model=PaginatedResponse)
def read_report_configs(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    report_type: Optional[str] = Query(None, description="报告类型筛选"),
    is_default: Optional[bool] = Query(None, description="是否默认配置"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报告配置列表
    """

    query = db.query(MeetingReportConfig)

    if report_type:
        query = query.filter(MeetingReportConfig.report_type == report_type)

    if is_default is not None:
        query = query.filter(MeetingReportConfig.is_default == is_default)

    total = query.count()
    configs = apply_pagination(query.order_by(desc(MeetingReportConfig.is_default), desc(MeetingReportConfig.created_at)), pagination.offset, pagination.limit).all()

    items = []
    for config in configs:
        items.append(MeetingReportConfigResponse(
            id=config.id,
            config_name=config.config_name,
            report_type=config.report_type,
            description=config.description,
            enabled_metrics=config.enabled_metrics,
            comparison_config=config.comparison_config,
            display_config=config.display_config,
            is_default=config.is_default,
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/meeting-reports/configs", response_model=MeetingReportConfigResponse, status_code=status.HTTP_201_CREATED)
def create_report_config(
    config_data: MeetingReportConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建报告配置
    """
    # 如果设置为默认配置，先取消其他默认配置
    if config_data.is_default:
        db.query(MeetingReportConfig).filter(
            and_(
                MeetingReportConfig.report_type == config_data.report_type,
                MeetingReportConfig.is_default
            )
        ).update({"is_default": False})

    config = MeetingReportConfig(
        config_name=config_data.config_name,
        report_type=config_data.report_type,
        description=config_data.description,
        enabled_metrics=[item.dict() for item in config_data.enabled_metrics] if config_data.enabled_metrics else [],
        comparison_config=config_data.comparison_config.dict() if config_data.comparison_config else None,
        display_config=config_data.display_config.dict() if config_data.display_config else None,
        is_default=config_data.is_default,
        is_active=True,
        created_by=current_user.id,
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    return MeetingReportConfigResponse(
        id=config.id,
        config_name=config.config_name,
        report_type=config.report_type,
        description=config.description,
        enabled_metrics=config.enabled_metrics,
        comparison_config=config.comparison_config,
        display_config=config.display_config,
        is_default=config.is_default,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/meeting-reports/configs/{config_id}", response_model=MeetingReportConfigResponse)
def read_report_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报告配置详情
    """
    config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    return MeetingReportConfigResponse(
        id=config.id,
        config_name=config.config_name,
        report_type=config.report_type,
        description=config.description,
        enabled_metrics=config.enabled_metrics,
        comparison_config=config.comparison_config,
        display_config=config.display_config,
        is_default=config.is_default,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.put("/meeting-reports/configs/{config_id}", response_model=MeetingReportConfigResponse)
def update_report_config(
    config_id: int,
    config_data: MeetingReportConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新报告配置
    """
    config = db.query(MeetingReportConfig).filter(MeetingReportConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 如果设置为默认配置，先取消其他默认配置
    if config_data.is_default is True:
        db.query(MeetingReportConfig).filter(
            and_(
                MeetingReportConfig.report_type == config.report_type,
                MeetingReportConfig.is_default,
                MeetingReportConfig.id != config_id
            )
        ).update({"is_default": False})

    update_data = config_data.dict(exclude_unset=True)

    # 处理嵌套对象
    if config_data.enabled_metrics is not None:
        update_data["enabled_metrics"] = [item.dict() for item in config_data.enabled_metrics]
    if config_data.comparison_config is not None:
        update_data["comparison_config"] = config_data.comparison_config.dict()
    if config_data.display_config is not None:
        update_data["display_config"] = config_data.display_config.dict()

    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return MeetingReportConfigResponse(
        id=config.id,
        config_name=config.config_name,
        report_type=config.report_type,
        description=config.description,
        enabled_metrics=config.enabled_metrics,
        comparison_config=config.comparison_config,
        display_config=config.display_config,
        is_default=config.is_default,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/meeting-reports/configs/default/{report_type}", response_model=MeetingReportConfigResponse)
def get_default_report_config(
    report_type: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取默认报告配置
    """
    config = db.query(MeetingReportConfig).filter(
        and_(
            MeetingReportConfig.report_type == report_type,
            MeetingReportConfig.is_default,
            MeetingReportConfig.is_active
        )
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="未找到默认配置")

    return MeetingReportConfigResponse(
        id=config.id,
        config_name=config.config_name,
        report_type=config.report_type,
        description=config.description,
        enabled_metrics=config.enabled_metrics,
        comparison_config=config.comparison_config,
        display_config=config.display_config,
        is_default=config.is_default,
        is_active=config.is_active,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )



