# -*- coding: utf-8 -*-
"""
供应商和物料供应商关联端点
"""

from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import Material, MaterialSupplier, Supplier
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import SupplierResponse

router = APIRouter()


@router.get("/suppliers", response_model=PaginatedResponse[SupplierResponse])
def get_suppliers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（供应商名称/编码）"),
    supplier_type: Optional[str] = Query(None, description="供应商类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    supplier_level: Optional[str] = Query(None, description="供应商等级筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取供应商列表（支持分页、搜索、筛选）
    此路由作为 /suppliers 的快捷方式，用于物料管理模块中获取供应商列表
    """
    query = db.query(Supplier)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Supplier.supplier_name.contains(keyword),
                Supplier.supplier_code.contains(keyword),
                Supplier.supplier_short_name.contains(keyword),
            )
        )

    # 供应商类型筛选
    if supplier_type:
        query = query.filter(Supplier.supplier_type == supplier_type)

    # 状态筛选
    if status:
        query = query.filter(Supplier.status == status)

    # 等级筛选
    if supplier_level:
        query = query.filter(Supplier.supplier_level == supplier_level)

    # 总数 - 使用独立的查询避免连接问题
    total = query.count()

    # 分页 - 确保 offset 和 limit 都是有效的整数
    offset = max(0, (page - 1) * page_size)
    page_size_int = max(1, int(page_size))

    # 重新构建查询对象以避免 SQLite 连接问题
    suppliers_query = db.query(Supplier)

    # 重新应用所有筛选条件
    if keyword:
        suppliers_query = suppliers_query.filter(
            or_(
                Supplier.supplier_name.contains(keyword),
                Supplier.supplier_code.contains(keyword),
                Supplier.supplier_short_name.contains(keyword),
            )
        )
    if supplier_type:
        suppliers_query = suppliers_query.filter(Supplier.supplier_type == supplier_type)
    if status:
        suppliers_query = suppliers_query.filter(Supplier.status == status)
    if supplier_level:
        suppliers_query = suppliers_query.filter(Supplier.supplier_level == supplier_level)

    # 应用排序和分页
    suppliers_query = suppliers_query.order_by(desc(Supplier.created_at))
    if offset > 0:
        suppliers_query = suppliers_query.offset(offset)
    suppliers = suppliers_query.limit(page_size_int).all()

    # 手动构建响应对象，确保 Decimal 类型正确处理
    items = []
    for supplier in suppliers:
        items.append(SupplierResponse(
            id=supplier.id,
            supplier_code=supplier.supplier_code,
            supplier_name=supplier.supplier_name,
            supplier_short_name=supplier.supplier_short_name,
            supplier_type=supplier.supplier_type,
            contact_person=supplier.contact_person,
            contact_phone=supplier.contact_phone,
            contact_email=supplier.contact_email,
            address=supplier.address,
            quality_rating=supplier.quality_rating or Decimal("0"),
            delivery_rating=supplier.delivery_rating or Decimal("0"),
            service_rating=supplier.service_rating or Decimal("0"),
            overall_rating=supplier.overall_rating or Decimal("0"),
            supplier_level=supplier.supplier_level or "B",
            status=supplier.status or "ACTIVE",
            cooperation_start=supplier.cooperation_start,
            last_order_date=supplier.last_order_date,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{material_id}/suppliers", response_model=List)
def get_material_suppliers(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """获取物料的供应商列表"""
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
        supplier = ms.supplier
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
