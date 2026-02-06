# -*- coding: utf-8 -*-
"""
物料供应商关联端点

此模块仅提供物料特定的供应商关联功能。
供应商的通用CRUD操作请使用 /suppliers 端点。
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import Material, MaterialSupplier
from app.models.user import User

router = APIRouter()


@router.get("/{material_id}/suppliers", response_model=List[dict])
def get_material_suppliers(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    获取物料的供应商列表

    返回指定物料的所有关联供应商，包括价格、交期等信息。

    Args:
        material_id: 物料ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        供应商列表，包含关联信息（价格、交期、最小订货量等）

    Raises:
        HTTPException: 物料不存在时返回404

    Note:
        如需查询供应商列表，请使用 GET /suppliers 端点
    """
    # 验证物料是否存在
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 查询物料供应商关联
    material_suppliers = (
        db.query(MaterialSupplier)
        .filter(MaterialSupplier.material_id == material_id)
        .filter(MaterialSupplier.is_active == True)
        .all()
    )

    result = []
    for ms in material_suppliers:
        supplier = ms.vendor
        result.append({
            "id": supplier.id,
            "supplier_code": supplier.supplier_code,
            "supplier_name": supplier.supplier_name,
            "price": float(ms.price) if ms.price else 0,
            "currency": ms.currency,
            "lead_time_days": ms.lead_time_days,
            "min_order_qty": float(ms.min_order_qty) if ms.min_order_qty else 0,
            "is_preferred": ms.is_preferred,
            "supplier_material_code": ms.supplier_material_code,
        })

    return result
