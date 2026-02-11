# -*- coding: utf-8 -*-
"""
物料需求列表与库存对比
"""

from datetime import date
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.material import BomHeader, BomItem, Material
from app.models.project import Machine
from app.models.purchase import PurchaseOrderItem
from app.models.user import User
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/material-demands", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_material_demands(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    material_id: Optional[int] = Query(None, description="物料ID筛选"),
    material_code: Optional[str] = Query(None, description="物料编码筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="需求开始日期"),
    end_date: Optional[date] = Query(None, description="需求结束日期"),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    获取物料需求列表
    """"""
    物料需求汇总（多项目汇总）
    """
    # 从BOM明细汇总物料需求
    query = (
        db.query(
            BomItem.material_id,
            BomItem.material_code,
            BomItem.material_name,
            func.sum(BomItem.quantity).label('total_demand'),
            func.min(BomItem.required_date).label('earliest_date'),
            func.max(BomItem.required_date).label('latest_date'),
            func.count(BomItem.id).label('demand_count')
        )
        .join(BomHeader, BomItem.bom_id == BomHeader.id)
        .join(Machine, BomHeader.machine_id == Machine.id)
        .group_by(BomItem.material_id, BomItem.material_code, BomItem.material_name)
    )

    if material_id:
        query = query.filter(BomItem.material_id == material_id)

    query = apply_keyword_filter(query, BomItem, material_code, "material_code", use_ilike=False)

    if project_id:
        query = query.filter(Machine.project_id == project_id)

    if start_date:
        query = query.filter(BomItem.required_date >= start_date)

    if end_date:
        query = query.filter(BomItem.required_date <= end_date)

    # 获取物料信息
    results = query.all()

    items = []
    for result in results:
        material = db.query(Material).filter(Material.id == result.material_id).first()

        # 计算可用库存
        available_stock = material.current_stock or Decimal("0")

        # 计算在途数量（已采购但未到货）
        in_transit_qty = Decimal("0")
        if result.material_id:
            po_items = (
                db.query(PurchaseOrderItem)
                .filter(PurchaseOrderItem.material_id == result.material_id)
                .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
                .all()
            )
            for po_item in po_items:
                in_transit_qty += (po_item.quantity or Decimal("0")) - (po_item.received_qty or Decimal("0"))

        total_available = available_stock + in_transit_qty
        shortage_qty = max(Decimal("0"), result.total_demand - total_available)

        items.append({
            "material_id": result.material_id,
            "material_code": result.material_code,
            "material_name": result.material_name,
            "specification": material.specification if material else None,
            "unit": material.unit if material else "件",
            "total_demand": float(result.total_demand),
            "available_stock": float(available_stock),
            "in_transit_qty": float(in_transit_qty),
            "total_available": float(total_available),
            "shortage_qty": float(shortage_qty),
            "earliest_date": result.earliest_date.isoformat() if result.earliest_date else None,
            "latest_date": result.latest_date.isoformat() if result.latest_date else None,
            "demand_count": result.demand_count,
            "is_key_material": material.is_key_material if material else False
        })

    # 按短缺数量排序
    items.sort(key=lambda x: x['shortage_qty'], reverse=True)

    total = len(items)
    paginated_items = items[pagination.offset:pagination.offset + pagination.limit]

    return PaginatedResponse(
        items=paginated_items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/material-demands/vs-stock", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_material_demands_vs_stock(
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表（逗号分隔）"),
    material_ids: Optional[str] = Query(None, description="物料ID列表（逗号分隔）"),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    需求与库存对比（需求-库存）
    """
    # 解析项目ID列表
    project_id_list = None
    if project_ids:
        project_id_list = [int(p.strip()) for p in project_ids.split(",") if p.strip()]

    # 解析物料ID列表
    material_id_list = None
    if material_ids:
        material_id_list = [int(m.strip()) for m in material_ids.split(",") if m.strip()]

    # 从BOM明细汇总物料需求
    query = (
        db.query(
            BomItem.material_id,
            BomItem.material_code,
            BomItem.material_name,
            func.sum(BomItem.quantity).label('total_demand')
        )
        .join(BomHeader, BomItem.bom_id == BomHeader.id)
        .join(Machine, BomHeader.machine_id == Machine.id)
        .group_by(BomItem.material_id, BomItem.material_code, BomItem.material_name)
    )

    if project_id_list:
        query = query.filter(Machine.project_id.in_(project_id_list))

    if material_id_list:
        query = query.filter(BomItem.material_id.in_(material_id_list))

    results = query.all()

    items = []
    for result in results:
        material = db.query(Material).filter(Material.id == result.material_id).first()
        if not material:
            continue

        # 当前库存
        current_stock = material.current_stock or Decimal("0")

        # 安全库存
        safety_stock = material.safety_stock or Decimal("0")

        # 在途数量
        in_transit_qty = Decimal("0")
        po_items = (
            db.query(PurchaseOrderItem)
            .filter(PurchaseOrderItem.material_id == result.material_id)
            .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
            .all()
        )
        for po_item in po_items:
            in_transit_qty += (po_item.quantity or Decimal("0")) - (po_item.received_qty or Decimal("0"))

        # 可用库存 = 当前库存 + 在途数量 - 安全库存
        available_stock = current_stock + in_transit_qty - safety_stock

        # 短缺数量
        shortage_qty = max(Decimal("0"), result.total_demand - available_stock)

        # 库存状态
        stock_status = "SUFFICIENT"
        if shortage_qty > 0:
            if shortage_qty > result.total_demand * Decimal("0.5"):
                stock_status = "CRITICAL"
            else:
                stock_status = "INSUFFICIENT"

        items.append({
            "material_id": result.material_id,
            "material_code": result.material_code,
            "material_name": result.material_name,
            "specification": material.specification,
            "unit": material.unit,
            "total_demand": float(result.total_demand),
            "current_stock": float(current_stock),
            "safety_stock": float(safety_stock),
            "in_transit_qty": float(in_transit_qty),
            "available_stock": float(available_stock),
            "shortage_qty": float(shortage_qty),
            "stock_status": stock_status,
            "is_key_material": material.is_key_material,
            "lead_time_days": material.lead_time_days or 0
        })

    # 按短缺数量排序
    items.sort(key=lambda x: (x['is_key_material'], x['shortage_qty']), reverse=True)

    return items
