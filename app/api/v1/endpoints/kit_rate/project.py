# -*- coding: utf-8 -*-
"""
项目级齐套率端点
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.services.kit_rate import KitRateService
from app.models.user import User

router = APIRouter()


@router.get("/projects/{project_id}/kit-rate")
def get_project_kit_rate(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    calculate_by: str = Query("quantity", description="计算方式：quantity(数量) 或 amount(金额)"),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    计算项目齐套率
    """
    service = KitRateService(db)
    return service.get_project_kit_rate(project_id, calculate_by)


@router.get("/projects/{project_id}/material-status")
def get_project_material_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    获取项目物料汇总
    """
    service = KitRateService(db)
    return service.get_project_material_status(project_id)


@router.get("/projects/{project_id}/shortage")
def get_project_shortage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    获取项目缺料清单
    """
    service = KitRateService(db)
    material_status = service.get_project_material_status(project_id)

    # 筛选缺料项
    shortage_list = [
        item for item in material_status["materials"]
        if item["shortage_qty"] > 0
    ]

    return {
        "project_id": material_status["project_id"],
        "project_code": material_status["project_code"],
        "project_name": material_status["project_name"],
        "total_shortage_items": len(shortage_list),
        "shortage_list": shortage_list,
    }


@router.get("/projects/{project_id}/critical-shortage")
def get_project_critical_shortage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    获取项目关键物料缺口
    """
    service = KitRateService(db)
    material_status = service.get_project_material_status(project_id)

    # 筛选关键物料且缺料的项
    critical_shortage_list = [
        item for item in material_status["materials"]
        if item["is_key_material"] and item["shortage_qty"] > 0
    ]

    return {
        "project_id": material_status["project_id"],
        "project_code": material_status["project_code"],
        "project_name": material_status["project_name"],
        "total_critical_shortage_items": len(critical_shortage_list),
        "critical_shortage_list": critical_shortage_list,
    }
