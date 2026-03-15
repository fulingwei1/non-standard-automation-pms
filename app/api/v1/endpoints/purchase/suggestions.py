# -*- coding: utf-8 -*-
"""
采购建议 API
- 基于安全库存生成采购建议
- 基于 BOM 需求生成采购建议
"""

import logging
from datetime import date, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas import success_response
from app.models.material import Material
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/suggestions", summary="采购建议列表")
def get_purchase_suggestions(
    safety_stock: Optional[bool] = Query(False, description="是否基于安全库存生成"),
    bom_based: Optional[bool] = Query(False, description="是否基于 BOM 生成"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    获取采购建议列表
    
    - **safety_stock**: 基于安全库存生成（当前库存 < 安全库存）
    - **bom_based**: 基于 BOM 生成
    - **limit**: 返回数量限制（默认 50）
    """
    items = []
    
    if safety_stock:
        # 查询当前库存低于安全库存的物料
        materials = (
            db.query(Material)
            .filter(
                Material.safety_stock > 0,
                Material.current_stock < Material.safety_stock,
            )
            .limit(limit)
            .all()
        )
        
        for mat in materials:
            shortage_qty = float(mat.safety_stock) - float(mat.current_stock or 0)
            suggested_qty = shortage_qty * 1.2  # 补充到安全库存的 1.2 倍
            
            items.append({
                "material_id": mat.id,
                "material_code": mat.material_code,
                "material_name": mat.material_name,
                "unit": mat.unit or "个",
                "current_stock": float(mat.current_stock or 0),
                "safety_stock": float(mat.safety_stock),
                "suggested_quantity": round(suggested_qty, 2),
                "reason": f"当前库存 ({mat.current_stock}) < 安全库存 ({mat.safety_stock})",
                "source": "SAFETY_STOCK",
                "priority": "HIGH" if shortage_qty > float(mat.safety_stock) * 0.5 else "NORMAL",
                "required_date": (date.today() + timedelta(days=7)).isoformat(),
            })
    
    elif bom_based:
        # TODO: 基于 BOM 生成建议
        items = []
    
    else:
        # 默认只返回安全库存建议
        materials = (
            db.query(Material)
            .filter(
                Material.safety_stock > 0,
                Material.current_stock < Material.safety_stock,
            )
            .limit(limit)
            .all()
        )
        
        for mat in materials:
            shortage_qty = float(mat.safety_stock) - float(mat.current_stock or 0)
            suggested_qty = shortage_qty * 1.2
            
            items.append({
                "material_id": mat.id,
                "material_code": mat.material_code,
                "material_name": mat.material_name,
                "unit": mat.unit or "个",
                "current_stock": float(mat.current_stock or 0),
                "safety_stock": float(mat.safety_stock),
                "suggested_quantity": round(suggested_qty, 2),
                "reason": f"当前库存 ({mat.current_stock}) < 安全库存 ({mat.safety_stock})",
                "source": "SAFETY_STOCK",
                "priority": "HIGH" if shortage_qty > float(mat.safety_stock) * 0.5 else "NORMAL",
                "required_date": (date.today() + timedelta(days=7)).isoformat(),
            })
    
    return success_response(
        data={
            "items": items,
            "total": len(items),
            "safety_stock_based": safety_stock,
            "bom_based": bom_based,
        },
        message=f"采购建议生成成功（{len(items)} 条）"
    )


@router.get("/suggestions/{material_id}", summary="单个物料采购建议")
def get_material_suggestion(
    material_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """获取单个物料的采购建议"""
    mat = db.query(Material).filter(Material.id == material_id).first()
    if not mat:
        return success_response(
            data=None,
            message="物料不存在",
            code=404
        )
    
    if not mat.safety_stock or mat.current_stock >= mat.safety_stock:
        return success_response(
            data=None,
            message="该物料不需要采购"
        )
    
    shortage_qty = float(mat.safety_stock) - float(mat.current_stock or 0)
    suggested_qty = shortage_qty * 1.2
    
    item = {
        "material_id": mat.id,
        "material_code": mat.material_code,
        "material_name": mat.material_name,
        "unit": mat.unit or "个",
        "current_stock": float(mat.current_stock or 0),
        "safety_stock": float(mat.safety_stock),
        "suggested_quantity": round(suggested_qty, 2),
        "reason": f"当前库存 ({mat.current_stock}) < 安全库存 ({mat.safety_stock})",
        "required_date": (date.today() + timedelta(days=7)).isoformat(),
    }
    
    return success_response(
        data=item,
        message="采购建议生成成功"
    )
