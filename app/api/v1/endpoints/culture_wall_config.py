# -*- coding: utf-8 -*-
"""
文化墙配置管理
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.culture_wall_config import CultureWallConfig
from app.models.user import User
from app.schemas.culture_wall_config import (
    CultureWallConfigCreate,
    CultureWallConfigResponse,
    CultureWallConfigUpdate,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _dump_schema(schema: Any, *, exclude_unset: bool = False) -> dict:
    if hasattr(schema, "model_dump"):
        return schema.model_dump(exclude_unset=exclude_unset)
    return schema.dict(exclude_unset=exclude_unset)


def _default_config_payload() -> dict:
    return _dump_schema(CultureWallConfigCreate(config_name="默认文化墙配置"))


def _to_config_response(config: CultureWallConfig) -> CultureWallConfigResponse:
    defaults = _default_config_payload()
    return CultureWallConfigResponse(
        id=config.id,
        config_name=config.config_name,
        description=config.description,
        is_enabled=bool(config.is_enabled),
        is_default=bool(config.is_default),
        content_types=config.content_types or defaults["content_types"],
        visible_roles=config.visible_roles or [],
        play_settings=config.play_settings or defaults["play_settings"],
        created_by=config.created_by,
        created_at=config.created_at.isoformat() if config.created_at else None,
        updated_at=config.updated_at.isoformat() if config.updated_at else None,
    )


def _ensure_unique_config_name(
    db: Session,
    config_name: str,
    *,
    exclude_config_id: Optional[int] = None,
) -> None:
    query = db.query(CultureWallConfig).filter(
        CultureWallConfig.config_name == config_name
    )
    if exclude_config_id is not None:
        query = query.filter(CultureWallConfig.id != exclude_config_id)
    if query.first():
        raise HTTPException(status_code=400, detail="配置名称已存在")


def _clear_default_configs(db: Session, *, exclude_config_id: Optional[int] = None) -> None:
    query = db.query(CultureWallConfig).filter(CultureWallConfig.is_default.is_(True))
    if exclude_config_id is not None:
        query = query.filter(CultureWallConfig.id != exclude_config_id)
    for config in query.all():
        config.is_default = False


@router.get("/", response_model=List[CultureWallConfigResponse])
def read_culture_wall_configs(
    include_disabled: bool = Query(False, description="是否包含已停用配置"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙配置列表
    """
    query = db.query(CultureWallConfig)
    if not include_disabled:
        query = query.filter(CultureWallConfig.is_enabled.is_(True))

    configs = query.order_by(
        desc(CultureWallConfig.is_default),
        desc(CultureWallConfig.created_at),
    ).all()
    return [_to_config_response(config) for config in configs]


@router.post("/", response_model=CultureWallConfigResponse)
def create_culture_wall_config(
    config_data: CultureWallConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建文化墙配置
    """
    payload = _dump_schema(config_data)
    _ensure_unique_config_name(db, payload["config_name"])
    if payload["is_default"]:
        _clear_default_configs(db)

    config = CultureWallConfig(
        config_name=payload["config_name"],
        description=payload["description"],
        is_enabled=payload["is_enabled"],
        is_default=payload["is_default"],
        content_types=payload["content_types"],
        visible_roles=payload["visible_roles"],
        play_settings=payload["play_settings"],
        created_by=current_user.id,
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    return _to_config_response(config)


@router.get("/{config_id}", response_model=CultureWallConfigResponse)
def read_culture_wall_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙配置详情
    """
    config = get_or_404(db, CultureWallConfig, config_id, "配置不存在")
    return _to_config_response(config)


@router.put("/{config_id}", response_model=CultureWallConfigResponse)
def update_culture_wall_config(
    config_id: int,
    config_data: CultureWallConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新文化墙配置
    """
    config = get_or_404(db, CultureWallConfig, config_id, "配置不存在")
    payload = _dump_schema(config_data, exclude_unset=True)

    if "config_name" in payload:
        _ensure_unique_config_name(
            db,
            payload["config_name"],
            exclude_config_id=config_id,
        )
    if payload.get("is_default") is True:
        _clear_default_configs(db, exclude_config_id=config_id)

    for field, value in payload.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return _to_config_response(config)


@router.delete("/{config_id}", status_code=status.HTTP_200_OK)
def delete_culture_wall_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除文化墙配置
    """
    config = get_or_404(db, CultureWallConfig, config_id, "配置不存在")
    db.delete(config)
    db.commit()
    return {"message": "删除成功"}


__all__ = ["router"]
