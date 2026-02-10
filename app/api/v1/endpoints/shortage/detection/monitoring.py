# -*- coding: utf-8 -*-
"""
监控检查 - monitoring.py

说明:
齐套检查功能已独立为 kit_check 模块，本文件提供：
1. 齐套检查入口（委托给 kit_check 模块）
2. 库存预警功能

路由:
- GET    /inventory-warnings        库存预警列表
- POST   /inventory-warnings/check  执行库存检查
"""
import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.material import Material
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 库存预警
# ============================================================

@router.get("/inventory-warnings", response_model=PaginatedResponse)
def list_inventory_warnings(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    category_id: Optional[int] = Query(None, description="物料分类ID筛选"),
    warning_type: Optional[str] = Query(None, description="预警类型: LOW_STOCK/OVERSTOCK/EXPIRING"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取库存预警列表
    检测库存低于安全库存或高于最大库存的物料
    """
    query = db.query(Material).filter(Material.is_active == True)

    # 分类筛选
    if category_id:
        query = query.filter(Material.category_id == category_id)

    # 获取所有物料
    materials = query.all()

    # 筛选出有预警的物料
    warnings = []
    for material in materials:
        # 获取当前库存（如果有库存字段）
        current_stock = getattr(material, 'current_stock', None) or Decimal("0")
        safety_stock = getattr(material, 'safety_stock', None) or Decimal("0")
        max_stock = getattr(material, 'max_stock', None)

        warning_item = None

        # 低库存预警
        if safety_stock > 0 and current_stock < safety_stock:
            if warning_type is None or warning_type == "LOW_STOCK":
                warning_item = {
                    "material_id": material.id,
                    "material_code": material.material_code,
                    "material_name": material.material_name,
                    "category_id": material.category_id,
                    "warning_type": "LOW_STOCK",
                    "current_stock": float(current_stock),
                    "safety_stock": float(safety_stock),
                    "shortage_qty": float(safety_stock - current_stock),
                    "max_stock": float(max_stock) if max_stock else None,
                }

        # 超库存预警
        elif max_stock and current_stock > max_stock:
            if warning_type is None or warning_type == "OVERSTOCK":
                warning_item = {
                    "material_id": material.id,
                    "material_code": material.material_code,
                    "material_name": material.material_name,
                    "category_id": material.category_id,
                    "warning_type": "OVERSTOCK",
                    "current_stock": float(current_stock),
                    "safety_stock": float(safety_stock),
                    "max_stock": float(max_stock),
                    "excess_qty": float(current_stock - max_stock),
                }

        if warning_item:
            warnings.append(warning_item)

    # 分页
    total = len(warnings)
    items = warnings[pagination.offset:pagination.offset + pagination.limit]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/inventory-warnings/check", response_model=ResponseModel)
def run_inventory_check(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行库存检查
    检查所有物料的库存状态，返回预警汇总
    """
    query = db.query(Material).filter(Material.is_active == True)
    materials = query.all()

    low_stock_count = 0
    overstock_count = 0
    total_checked = len(materials)

    for material in materials:
        current_stock = getattr(material, 'current_stock', None) or Decimal("0")
        safety_stock = getattr(material, 'safety_stock', None) or Decimal("0")
        max_stock = getattr(material, 'max_stock', None)

        if safety_stock > 0 and current_stock < safety_stock:
            low_stock_count += 1
        elif max_stock and current_stock > max_stock:
            overstock_count += 1

    return ResponseModel(
        code=200,
        message="库存检查完成",
        data={
            "total_checked": total_checked,
            "low_stock_count": low_stock_count,
            "overstock_count": overstock_count,
            "warning_count": low_stock_count + overstock_count,
            "check_time": __import__("datetime").datetime.now().isoformat()
        }
    )


# ============================================================
# 齐套检查入口（委托给 kit_check 模块）
# ============================================================

# 注意：齐套检查的完整功能在 kit_check 模块中实现
# 路由: /api/v1/kit-check/
# - GET  /work-orders           工单齐套列表
# - GET  /work-orders/{id}      工单齐套详情
# - POST /check                 执行齐套检查
# - POST /confirm-start         开工确认
# - GET  /history               检查历史
