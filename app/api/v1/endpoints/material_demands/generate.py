# -*- coding: utf-8 -*-
"""
自动生成采购需求
"""

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader, BomItem, Material
from app.models.project import Machine
from app.models.purchase import PurchaseOrderItem
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/material-demands/generate-pr", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def generate_purchase_requisition(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表（逗号分隔）"),
    material_ids: Optional[str] = Query(None, description="物料ID列表（逗号分隔），为空则生成所有短缺物料"),
    supplier_id: Optional[int] = Query(None, description="默认供应商ID"),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    自动生成采购需求（从缺口生成PR）
    """
    # 解析项目ID列表
    project_id_list = None
    if project_ids:
        project_id_list = [int(p.strip()) for p in project_ids.split(",") if p.strip()]

    # 解析物料ID列表
    material_id_list = None
    if material_ids:
        material_id_list = [int(m.strip()) for m in material_ids.split(",") if m.strip()]

    # 获取物料需求与库存对比
    query = (
        db.query(
            BomItem.material_id,
            BomItem.material_code,
            BomItem.material_name,
            func.sum(BomItem.quantity).label('total_demand'),
            func.min(BomItem.required_date).label('earliest_date')
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

    generated_count = 0
    pr_items = []

    for result in results:
        material = db.query(Material).filter(Material.id == result.material_id).first()
        if not material:
            continue

        # 计算可用库存
        current_stock = material.current_stock or Decimal("0")

        # 计算在途数量
        in_transit_qty = Decimal("0")
        po_items = (
            db.query(PurchaseOrderItem)
            .filter(PurchaseOrderItem.material_id == result.material_id)
            .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
            .all()
        )
        for po_item in po_items:
            in_transit_qty += (po_item.quantity or Decimal("0")) - (po_item.received_qty or Decimal("0"))

        total_available = current_stock + in_transit_qty
        shortage_qty = max(Decimal("0"), result.total_demand - total_available)

        # 如果有短缺，生成采购需求
        if shortage_qty > 0:
            # 考虑最小订购量
            min_order_qty = material.min_order_qty or Decimal("1")
            purchase_qty = max(shortage_qty, min_order_qty)

            # 确定供应商
            target_supplier_id = supplier_id or material.default_supplier_id
            if not target_supplier_id:
                continue  # 跳过没有供应商的物料

            pr_items.append({
                "material_id": result.material_id,
                "material_code": result.material_code,
                "material_name": result.material_name,
                "quantity": purchase_qty,
                "unit": material.unit,
                "unit_price": material.last_price or material.standard_price or Decimal("0"),
                "required_date": result.earliest_date,
                "supplier_id": target_supplier_id
            })
            generated_count += 1

    if generated_count == 0:
        return ResponseModel(message="没有需要生成采购需求的物料")

    return ResponseModel(
        message=f"成功生成 {generated_count} 条采购需求",
        data={
            "count": generated_count,
            "items": pr_items
        }
    )
