# -*- coding: utf-8 -*-
"""
OTD 阈值配置管理端点

- GET  /otd/thresholds  查看当前生效配置（任意登录用户）
- PUT  /otd/thresholds  更新默认配置（PMO/管理员）

权限检查复用 otd.py 的 _require_pmo_or_admin。
"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.otd import _require_pmo_or_admin
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.otd_threshold import (
    OtdThresholdConfigResponse,
    OtdThresholdConfigUpdate,
)

router = APIRouter(prefix="/otd/thresholds", tags=["OTD阈值配置"])


@router.get("", response_model=ResponseModel, summary="查看 OTD 阈值配置")
def get_thresholds(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查看当前生效的 OTD 11 维风险检测阈值配置。

    返回 DB 中 is_default=True 的配置；DB 无配置则返回代码默认值。
    """
    from app.services.otd.threshold_service import get_active_config

    config = get_active_config(db)
    resp = OtdThresholdConfigResponse.model_validate(config)
    return ResponseModel(code=200, message="OTD 阈值配置", data=resp.model_dump())


@router.put("", response_model=ResponseModel, summary="更新 OTD 阈值配置")
def update_thresholds(
    payload: OtdThresholdConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新 OTD 默认阈值配置（PMO/管理员）。

    支持部分更新：只传需要改的字段，其他保持原值。
    首次更新时若 DB 无配置行，会自动从代码默认值创建。
    改完立即生效（下次扫描即用新阈值），无需重启。
    """
    _require_pmo_or_admin(current_user)
    from app.services.otd.threshold_service import update_default_config

    config = update_default_config(db, payload, current_user.id)
    resp = OtdThresholdConfigResponse.model_validate(config)
    return ResponseModel(
        code=200,
        message="OTD 阈值配置已更新，下次扫描立即生效",
        data=resp.model_dump(),
    )
