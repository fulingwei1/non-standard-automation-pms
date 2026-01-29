# -*- coding: utf-8 -*-
"""
仓储统计、物料替代、物料搜索端点
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import Material, MaterialCategory
from app.models.vendor import Vendor
from app.models.shortage import MaterialSubstitution
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import MaterialSearchResponse, WarehouseStatistics

router = APIRouter()


@router.get("/{material_id}/alternatives", response_model=dict)
def get_material_alternatives(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int,
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    获取物料的替代关系
    返回该物料可以作为替代物料的所有原物料，以及该物料的所有替代物料
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 查询该物料作为替代物料的所有替代记录（即哪些物料可以用该物料替代）
    as_substitute = (
        db.query(MaterialSubstitution)
        .filter(MaterialSubstitution.substitute_material_id == material_id)
        .filter(MaterialSubstitution.status.in_(['APPROVED', 'EXECUTED']))
        .all()
    )

    # 查询该物料作为原物料的所有替代记录（即该物料可以用哪些物料替代）
    as_original = (
        db.query(MaterialSubstitution)
        .filter(MaterialSubstitution.original_material_id == material_id)
        .filter(MaterialSubstitution.status.in_(['APPROVED', 'EXECUTED']))
        .all()
    )

    # 构建替代物料列表（该物料可以替代的物料）
    can_substitute_for = []
    for sub in as_substitute:
        original_material = db.query(Material).filter(Material.id == sub.original_material_id).first()
        if original_material:
            can_substitute_for.append({
                "material_id": original_material.id,
                "material_code": original_material.material_code,
                "material_name": original_material.material_name,
                "specification": original_material.specification,
                "substitution_ratio": float(sub.substitute_qty / sub.original_qty) if sub.original_qty > 0 else 1.0,
                "substitution_reason": sub.substitution_reason,
                "status": sub.status,
                "substitution_no": sub.substitution_no,
            })

    # 构建可替代该物料的物料列表
    can_be_substituted_by = []
    for sub in as_original:
        substitute_material = db.query(Material).filter(Material.id == sub.substitute_material_id).first()
        if substitute_material:
            can_be_substituted_by.append({
                "material_id": substitute_material.id,
                "material_code": substitute_material.material_code,
                "material_name": substitute_material.material_name,
                "specification": substitute_material.specification,
                "substitution_ratio": float(sub.substitute_qty / sub.original_qty) if sub.original_qty > 0 else 1.0,
                "substitution_reason": sub.substitution_reason,
                "status": sub.status,
                "substitution_no": sub.substitution_no,
            })

    return {
        "material_id": material.id,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "can_substitute_for": can_substitute_for,  # 该物料可以替代的物料
        "can_be_substituted_by": can_be_substituted_by,  # 可以替代该物料的物料
    }


@router.get("/warehouse/statistics", response_model=WarehouseStatistics)
def get_warehouse_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """仓储统计（给生产总监看）"""
    from app.models.production import WorkOrder
    from app.models.purchase import GoodsReceiptItem, PurchaseOrder

    # 库存SKU统计
    total_items = db.query(Material).count()
    in_stock_items = db.query(Material).filter(
        Material.current_stock > 0
    ).count()

    # 低库存预警（当前库存 < 安全库存）
    low_stock_items = db.query(Material).filter(
        Material.current_stock < Material.safety_stock,
        Material.current_stock > 0
    ).count()

    # 缺货
    out_of_stock_items = db.query(Material).filter(
        Material.current_stock <= 0
    ).count()

    # 库存周转率（简化计算：本月入库金额 / 平均库存金额）
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # 本月入库金额（从入库单计算）
    inbound_amount = db.query(func.sum(GoodsReceiptItem.amount)).filter(
        GoodsReceiptItem.created_at >= datetime.combine(month_start, datetime.min.time())
    ).scalar() or 0

    # 平均库存金额（简化：当前库存金额）
    avg_inventory_amount = db.query(func.sum(
        Material.current_stock * Material.standard_price
    )).scalar() or 0

    inventory_turnover = 0.0
    if avg_inventory_amount and avg_inventory_amount > 0:
        inventory_turnover = float(inbound_amount) / float(avg_inventory_amount)

    # 仓储利用率计算
    # 基于物料的体积和数量估算占用的仓储空间
    total_volume = 0
    materials = db.query(Material).filter(Material.is_active == True).all()
    for material in materials:
        stock = float(material.current_stock or 0)
        # 假设每个物料单位占用基础体积，可以根据物料规格调整
        unit_volume = 1.0
        # 大件物料占用更多空间
        if material.material_type in ["大型设备", "机架", "机柜"]:
            unit_volume = 10.0
        elif material.material_type in ["板材", "型材"]:
            unit_volume = 3.0
        elif material.material_type in ["电子元件", "标准件"]:
            unit_volume = 0.1
        total_volume += stock * unit_volume

    # 假设仓库总容量为 10000 单位体积（可根据实际仓库配置调整）
    total_warehouse_capacity = 10000.0
    warehouse_utilization = min(100.0, (total_volume / total_warehouse_capacity) * 100) if total_warehouse_capacity > 0 else 0

    # 待入库（已采购但未完全到货的订单）
    pending_inbound = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"])
    ).count()

    # 待出库（从工单领料需求计算）
    pending_outbound = db.query(WorkOrder).filter(
        WorkOrder.status.in_(["ASSIGNED", "STARTED"]),
        # 假设有领料状态字段
    ).count()

    return WarehouseStatistics(
        total_items=total_items,
        in_stock_items=in_stock_items,
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        inventory_turnover=inventory_turnover,
        warehouse_utilization=warehouse_utilization,
        pending_inbound=pending_inbound,
        pending_outbound=pending_outbound,
    )


@router.get("/search", response_model=PaginatedResponse[MaterialSearchResponse])
def search_materials(
    db: Session = Depends(deps.get_db),
    keyword: str = Query(..., description="搜索关键词（物料编码/名称/规格）"),
    has_stock: Optional[bool] = Query(None, description="是否有库存"),
    category: Optional[str] = Query(None, description="物料类别"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """物料查找（支持编码/名称/规格搜索）"""
    from app.models.purchase import PurchaseOrder, PurchaseOrderItem

    query = db.query(Material)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Material.material_code.like(f"%{keyword}%"),
                Material.material_name.like(f"%{keyword}%"),
                Material.specification.like(f"%{keyword}%")
            )
        )

    # 库存筛选
    if has_stock is not None:
        if has_stock:
            query = query.filter(Material.current_stock > 0)
        else:
            query = query.filter(Material.current_stock <= 0)

    # 类别筛选
    if category:
        query = query.join(MaterialCategory).filter(
            MaterialCategory.category_name == category
        )

    # 分页
    total = query.count()
    materials = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for material in materials:
        # 计算在途数量
        in_transit_qty = db.query(func.sum(
            PurchaseOrderItem.quantity - PurchaseOrderItem.received_qty
        )).join(
            PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id
        ).filter(
            PurchaseOrderItem.material_id == material.id,
            PurchaseOrder.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"])
        ).scalar() or 0

        # 可用数量 = 当前库存 + 在途数量
        available_qty = (material.current_stock or 0) + in_transit_qty

        # 获取供应商名称
        supplier_name = None
        if material.default_supplier_id:
            supplier = db.query(Vendor).filter(Vendor.id == material.default_supplier_id, Vendor.vendor_type == 'MATERIAL').first()
            supplier_name = supplier.supplier_name if supplier else None

        items.append(MaterialSearchResponse(
            material_id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            specification=material.specification,
            category=material.category.category_name if material.category else None,
            current_stock=float(material.current_stock or 0),
            safety_stock=float(material.safety_stock or 0),
            in_transit_qty=float(in_transit_qty),
            available_qty=float(available_qty),
            unit=material.unit or "件",
            unit_price=float(material.standard_price or 0),
            supplier_name=supplier_name,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )
