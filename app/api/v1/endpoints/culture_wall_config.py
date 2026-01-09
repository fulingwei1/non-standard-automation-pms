# -*- coding: utf-8 -*-
"""
文化墙配置 API endpoints
用于管理员配置文化墙的显示内容和可见角色
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.culture_wall_config import CultureWallConfig
from app.schemas.culture_wall_config import (
    CultureWallConfigCreate,
    CultureWallConfigUpdate,
    CultureWallConfigResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/culture-wall/config", response_model=CultureWallConfigResponse)
def get_culture_wall_config(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙配置（获取默认配置或当前用户角色的配置）
    """
    # 首先尝试获取默认配置
    default_config = db.query(CultureWallConfig).filter(
        CultureWallConfig.is_default == True,
        CultureWallConfig.is_enabled == True
    ).first()
    
    if default_config:
        return default_config
    
    # 如果没有默认配置，获取第一个启用的配置
    config = db.query(CultureWallConfig).filter(
        CultureWallConfig.is_enabled == True
    ).order_by(desc(CultureWallConfig.created_at)).first()
    
    if not config:
        # 如果没有配置，返回默认配置结构
        from app.schemas.culture_wall_config import ContentTypeConfig, PlaySettings
        return CultureWallConfigResponse(
            id=0,
            config_name="默认配置",
            description="系统默认配置",
            is_enabled=True,
            is_default=True,
            content_types={
                "STRATEGY": ContentTypeConfig(enabled=True, max_count=10, priority=1),
                "CULTURE": ContentTypeConfig(enabled=True, max_count=10, priority=2),
                "IMPORTANT": ContentTypeConfig(enabled=True, max_count=10, priority=3),
                "NOTICE": ContentTypeConfig(enabled=True, max_count=10, priority=4),
                "REWARD": ContentTypeConfig(enabled=True, max_count=10, priority=5),
                "PERSONAL_GOAL": ContentTypeConfig(enabled=True, max_count=5, priority=6),
                "NOTIFICATION": ContentTypeConfig(enabled=True, max_count=10, priority=7),
            },
            visible_roles=[],
            play_settings=PlaySettings(),
        )
    
    return config


@router.get("/culture-wall/config/list", response_model=PaginatedResponse)
def list_culture_wall_configs(
    db: Session = Depends(deps.get_db),
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙配置列表（管理员功能）
    """
    # 检查权限
    if not (current_user.is_superuser or current_user.role in ['admin', 'super_admin', '管理员', '系统管理员']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    configs = db.query(CultureWallConfig).order_by(desc(CultureWallConfig.created_at)).all()
    
    total = len(configs)
    start = (page - 1) * page_size
    end = start + page_size
    items = configs[start:end]
    
    return PaginatedResponse(
        items=[CultureWallConfigResponse.from_orm(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/culture-wall/config", response_model=CultureWallConfigResponse)
def create_culture_wall_config(
    config_data: CultureWallConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建文化墙配置（管理员功能）
    """
    # 检查权限
    if not (current_user.is_superuser or current_user.role in ['admin', 'super_admin', '管理员', '系统管理员']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    # 如果设置为默认配置，需要取消其他默认配置
    if config_data.is_default:
        db.query(CultureWallConfig).update({"is_default": False})
    
    # 检查配置名称是否已存在
    existing = db.query(CultureWallConfig).filter(
        CultureWallConfig.config_name == config_data.config_name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="配置名称已存在"
        )
    
    config = CultureWallConfig(
        **config_data.dict(),
        created_by=current_user.id
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return config


@router.put("/culture-wall/config/{config_id}", response_model=CultureWallConfigResponse)
def update_culture_wall_config(
    config_id: int,
    config_data: CultureWallConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新文化墙配置（管理员功能）
    """
    # 检查权限
    if not (current_user.is_superuser or current_user.role in ['admin', 'super_admin', '管理员', '系统管理员']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    config = db.query(CultureWallConfig).filter(CultureWallConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 如果设置为默认配置，需要取消其他默认配置
    if config_data.is_default:
        db.query(CultureWallConfig).filter(CultureWallConfig.id != config_id).update({"is_default": False})
    
    # 更新配置
    update_data = config_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    return config


@router.delete("/culture-wall/config/{config_id}")
def delete_culture_wall_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除文化墙配置（管理员功能）
    """
    # 检查权限
    if not (current_user.is_superuser or current_user.role in ['admin', 'super_admin', '管理员', '系统管理员']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此功能"
        )
    
    config = db.query(CultureWallConfig).filter(CultureWallConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 不能删除默认配置
    if config.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除默认配置"
        )
    
    db.delete(config)
    db.commit()
    
    return {"message": "配置已删除"}
