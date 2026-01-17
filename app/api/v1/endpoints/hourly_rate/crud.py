# -*- coding: utf-8 -*-
"""
时薪配置CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.hourly_rate import HourlyRateConfig
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.hourly_rate import (
    HourlyRateConfigCreate,
    HourlyRateConfigResponse,
    HourlyRateConfigUpdate,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[HourlyRateConfigResponse])
def list_hourly_rate_configs(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    config_type: Optional[str] = Query(None, description="配置类型筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    role_id: Optional[int] = Query(None, description="角色ID筛选"),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    获取时薪配置列表
    """
    query = db.query(HourlyRateConfig)

    if config_type:
        query = query.filter(HourlyRateConfig.config_type == config_type)
    if user_id:
        query = query.filter(HourlyRateConfig.user_id == user_id)
    if role_id:
        query = query.filter(HourlyRateConfig.role_id == role_id)
    if dept_id:
        query = query.filter(HourlyRateConfig.dept_id == dept_id)
    if is_active is not None:
        query = query.filter(HourlyRateConfig.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    configs = query.order_by(desc(HourlyRateConfig.created_at)).offset(offset).limit(page_size).all()

    items = []
    for config in configs:
        config_dict = {
            **{c.name: getattr(config, c.name) for c in config.__table__.columns},
            "user_name": config.user.real_name if config.user else None,
            "role_name": config.role.role_name if config.role else None,
            "dept_name": config.dept.dept_name if config.dept else None,
        }
        items.append(HourlyRateConfigResponse(**config_dict))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/", response_model=HourlyRateConfigResponse, status_code=status.HTTP_201_CREATED)
def create_hourly_rate_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: HourlyRateConfigCreate,
    current_user: User = Depends(security.require_permission("hourly_rate:create")),
) -> Any:
    """
    创建时薪配置
    """
    # 验证配置类型和关联对象
    if config_in.config_type == "USER" and not config_in.user_id:
        raise HTTPException(status_code=400, detail="用户配置必须指定user_id")
    if config_in.config_type == "ROLE" and not config_in.role_id:
        raise HTTPException(status_code=400, detail="角色配置必须指定role_id")
    if config_in.config_type == "DEPT" and not config_in.dept_id:
        raise HTTPException(status_code=400, detail="部门配置必须指定dept_id")

    # 检查是否已存在相同配置
    existing = None
    if config_in.config_type == "USER" and config_in.user_id:
        existing = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "USER",
            HourlyRateConfig.user_id == config_in.user_id,
            HourlyRateConfig.is_active == True
        ).first()
    elif config_in.config_type == "ROLE" and config_in.role_id:
        existing = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "ROLE",
            HourlyRateConfig.role_id == config_in.role_id,
            HourlyRateConfig.is_active == True
        ).first()
    elif config_in.config_type == "DEPT" and config_in.dept_id:
        existing = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "DEPT",
            HourlyRateConfig.dept_id == config_in.dept_id,
            HourlyRateConfig.is_active == True
        ).first()
    elif config_in.config_type == "DEFAULT":
        existing = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "DEFAULT",
            HourlyRateConfig.is_active == True
        ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该配置已存在，请先禁用或删除现有配置")

    config_data = config_in.model_dump()
    config_data['created_by'] = current_user.id

    config = HourlyRateConfig(**config_data)
    db.add(config)
    db.commit()
    db.refresh(config)

    config_dict = {
        **{c.name: getattr(config, c.name) for c in config.__table__.columns},
        "user_name": config.user.real_name if config.user else None,
        "role_name": config.role.role_name if config.role else None,
        "dept_name": config.dept.dept_name if config.dept else None,
    }

    return HourlyRateConfigResponse(**config_dict)


@router.get("/{config_id}", response_model=HourlyRateConfigResponse)
def get_hourly_rate_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    获取时薪配置详情
    """
    config = db.query(HourlyRateConfig).filter(HourlyRateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="时薪配置不存在")

    config_dict = {
        **{c.name: getattr(config, c.name) for c in config.__table__.columns},
        "user_name": config.user.real_name if config.user else None,
        "role_name": config.role.role_name if config.role else None,
        "dept_name": config.dept.dept_name if config.dept else None,
    }

    return HourlyRateConfigResponse(**config_dict)


@router.put("/{config_id}", response_model=HourlyRateConfigResponse)
def update_hourly_rate_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    config_in: HourlyRateConfigUpdate,
    current_user: User = Depends(security.require_permission("hourly_rate:update")),
) -> Any:
    """
    更新时薪配置
    """
    config = db.query(HourlyRateConfig).filter(HourlyRateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="时薪配置不存在")

    update_data = config_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(config, field):
            setattr(config, field, value)

    db.add(config)
    db.commit()
    db.refresh(config)

    config_dict = {
        **{c.name: getattr(config, c.name) for c in config.__table__.columns},
        "user_name": config.user.real_name if config.user else None,
        "role_name": config.role.role_name if config.role else None,
        "dept_name": config.dept.dept_name if config.dept else None,
    }

    return HourlyRateConfigResponse(**config_dict)


@router.delete("/{config_id}", status_code=status.HTTP_200_OK)
def delete_hourly_rate_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    current_user: User = Depends(security.require_permission("hourly_rate:delete")),
) -> Any:
    """
    删除时薪配置
    """
    config = db.query(HourlyRateConfig).filter(HourlyRateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="时薪配置不存在")

    db.delete(config)
    db.commit()

    return ResponseModel(code=200, message="时薪配置已删除")
