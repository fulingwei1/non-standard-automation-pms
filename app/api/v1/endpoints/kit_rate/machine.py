# -*- coding: utf-8 -*-
"""
机台级齐套率端点
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.services.kit_rate import KitRateService
from app.models.user import User

router = APIRouter()


@router.get("/machines/{machine_id}/kit-rate")
def get_machine_kit_rate(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    calculate_by: str = Query("quantity", description="计算方式：quantity(数量) 或 amount(金额)"),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    计算机台齐套率
    """
    service = KitRateService(db)
    return service.get_machine_kit_rate(machine_id, calculate_by)


@router.get("/machines/{machine_id}/material-status")
def get_machine_material_status(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    获取机台物料状态（详细到货状态）
    """
    service = KitRateService(db)
    return service.get_machine_material_status(machine_id)
