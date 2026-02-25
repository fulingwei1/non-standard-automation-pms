# -*- coding: utf-8 -*-
"""
ECN受影响物料/订单管理 API endpoints

包含：受影响物料CRUD、受影响订单CRUD
"""

from decimal import Decimal
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn, EcnAffectedMaterial, EcnAffectedOrder
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.ecn import (
    EcnAffectedMaterialCreate,
    EcnAffectedMaterialResponse,
    EcnAffectedMaterialUpdate,
    EcnAffectedOrderCreate,
    EcnAffectedOrderResponse,
    EcnAffectedOrderUpdate,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


# ==================== 受影响物料 ====================

@router.get("/ecns/{ecn_id}/affected-materials", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_ecn_affected_materials(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取受影响物料列表
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    affected_materials = db.query(EcnAffectedMaterial).filter(EcnAffectedMaterial.ecn_id == ecn_id).all()

    items = []
    for am in affected_materials:
        from app.models.material import Material
        material = db.query(Material).filter(Material.id == am.material_id).first()

        items.append({
            "id": am.id,
            "material_id": am.material_id,
            "material_code": material.material_code if material else None,
            "material_name": material.material_name if material else None,
            "change_type": am.change_type,
            "change_description": am.change_description,
            "impact_analysis": am.impact_analysis
        })

    return items


@router.post("/ecns/{ecn_id}/affected-materials", response_model=EcnAffectedMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_affected_material(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    material_in: EcnAffectedMaterialCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加受影响物料
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    # 验证物料是否存在（如果提供了material_id）
    if material_in.material_id:
        from app.models.material import Material
        material = db.query(Material).filter(Material.id == material_in.material_id).first()
        if not material:
            raise HTTPException(status_code=404, detail="物料不存在")

    affected_material = EcnAffectedMaterial(
        ecn_id=ecn_id,
        material_id=material_in.material_id,
        bom_item_id=material_in.bom_item_id,
        material_code=material_in.material_code,
        material_name=material_in.material_name,
        specification=material_in.specification,
        change_type=material_in.change_type,
        old_quantity=material_in.old_quantity,
        old_specification=material_in.old_specification,
        old_supplier_id=material_in.old_supplier_id,
        new_quantity=material_in.new_quantity,
        new_specification=material_in.new_specification,
        new_supplier_id=material_in.new_supplier_id,
        cost_impact=material_in.cost_impact or Decimal("0"),
        status="PENDING",
        remark=material_in.remark
    )

    db.add(affected_material)

    # 更新ECN的成本影响
    total_cost_impact = db.query(func.sum(EcnAffectedMaterial.cost_impact)).filter(
        EcnAffectedMaterial.ecn_id == ecn_id
    ).scalar() or Decimal("0")
    ecn.cost_impact = total_cost_impact
    db.add(ecn)

    db.commit()
    db.refresh(affected_material)

    return _build_affected_material_response(affected_material)


@router.put("/ecns/{ecn_id}/affected-materials/{material_id}", response_model=EcnAffectedMaterialResponse, status_code=status.HTTP_200_OK)
def update_ecn_affected_material(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    material_id: int,
    material_in: EcnAffectedMaterialUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新受影响物料
    """
    affected_material = db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.id == material_id,
        EcnAffectedMaterial.ecn_id == ecn_id
    ).first()
    if not affected_material:
        raise HTTPException(status_code=404, detail="受影响物料记录不存在")

    update_data = material_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(affected_material, field, value)

    # 如果更新了成本影响，重新计算ECN的总成本影响
    if 'cost_impact' in update_data:
        total_cost_impact = db.query(func.sum(EcnAffectedMaterial.cost_impact)).filter(
            EcnAffectedMaterial.ecn_id == ecn_id
        ).scalar() or Decimal("0")
        ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if ecn:
            ecn.cost_impact = total_cost_impact
            db.add(ecn)

    db.add(affected_material)
    db.commit()
    db.refresh(affected_material)

    return _build_affected_material_response(affected_material)


@router.delete("/ecns/{ecn_id}/affected-materials/{material_id}", status_code=status.HTTP_200_OK)
def delete_ecn_affected_material(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    material_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除受影响物料
    """
    affected_material = db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.id == material_id,
        EcnAffectedMaterial.ecn_id == ecn_id
    ).first()
    if not affected_material:
        raise HTTPException(status_code=404, detail="受影响物料记录不存在")

    db.delete(affected_material)

    # 重新计算ECN的总成本影响
    total_cost_impact = db.query(func.sum(EcnAffectedMaterial.cost_impact)).filter(
        EcnAffectedMaterial.ecn_id == ecn_id
    ).scalar() or Decimal("0")
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if ecn:
        ecn.cost_impact = total_cost_impact
        db.add(ecn)

    db.commit()

    return ResponseModel(code=200, message="受影响物料已删除")


# ==================== 受影响订单 ====================

@router.get("/ecns/{ecn_id}/affected-orders", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_ecn_affected_orders(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取受影响订单列表
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    affected_orders = db.query(EcnAffectedOrder).filter(EcnAffectedOrder.ecn_id == ecn_id).all()

    items = []
    for ao in affected_orders:
        items.append({
            "id": ao.id,
            "order_type": ao.order_type,
            "order_id": ao.order_id,
            "order_no": ao.order_no,
            "impact_type": ao.impact_type,
            "impact_description": ao.impact_description,
            "action_required": ao.action_required
        })

    return items


@router.post("/ecns/{ecn_id}/affected-orders", response_model=EcnAffectedOrderResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_affected_order(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    order_in: EcnAffectedOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加受影响订单
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    # 验证订单是否存在
    if order_in.order_type == "PURCHASE":
        from app.models.purchase import PurchaseOrder
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_in.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="采购订单不存在")
    elif order_in.order_type == "OUTSOURCING":
        from app.models.outsourcing import OutsourcingOrder
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_in.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="外协订单不存在")

    affected_order = EcnAffectedOrder(
        ecn_id=ecn_id,
        order_type=order_in.order_type,
        order_id=order_in.order_id,
        order_no=order_in.order_no,
        impact_description=order_in.impact_description,
        action_type=order_in.action_type,
        action_description=order_in.action_description,
        status="PENDING"
    )

    db.add(affected_order)
    db.commit()
    db.refresh(affected_order)

    return _build_affected_order_response(affected_order)


@router.put("/ecns/{ecn_id}/affected-orders/{order_id}", response_model=EcnAffectedOrderResponse, status_code=status.HTTP_200_OK)
def update_ecn_affected_order(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    order_id: int,
    order_in: EcnAffectedOrderUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新受影响订单
    """
    affected_order = db.query(EcnAffectedOrder).filter(
        EcnAffectedOrder.id == order_id,
        EcnAffectedOrder.ecn_id == ecn_id
    ).first()
    if not affected_order:
        raise HTTPException(status_code=404, detail="受影响订单记录不存在")

    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(affected_order, field, value)

    db.add(affected_order)
    db.commit()
    db.refresh(affected_order)

    return _build_affected_order_response(affected_order)


@router.delete("/ecns/{ecn_id}/affected-orders/{order_id}", status_code=status.HTTP_200_OK)
def delete_ecn_affected_order(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除受影响订单
    """
    affected_order = db.query(EcnAffectedOrder).filter(
        EcnAffectedOrder.id == order_id,
        EcnAffectedOrder.ecn_id == ecn_id
    ).first()
    if not affected_order:
        raise HTTPException(status_code=404, detail="受影响订单记录不存在")

    db.delete(affected_order)
    db.commit()

    return ResponseModel(code=200, message="受影响订单已删除")


def _build_affected_material_response(am: EcnAffectedMaterial) -> EcnAffectedMaterialResponse:
    """构建受影响物料响应"""
    return EcnAffectedMaterialResponse(
        id=am.id,
        ecn_id=am.ecn_id,
        material_id=am.material_id,
        bom_item_id=am.bom_item_id,
        material_code=am.material_code,
        material_name=am.material_name,
        specification=am.specification,
        change_type=am.change_type,
        old_quantity=am.old_quantity,
        old_specification=am.old_specification,
        old_supplier_id=am.old_supplier_id,
        new_quantity=am.new_quantity,
        new_specification=am.new_specification,
        new_supplier_id=am.new_supplier_id,
        cost_impact=am.cost_impact or Decimal("0"),
        status=am.status,
        processed_at=am.processed_at,
        remark=am.remark,
        created_at=am.created_at,
        updated_at=am.updated_at
    )


def _build_affected_order_response(ao: EcnAffectedOrder) -> EcnAffectedOrderResponse:
    """构建受影响订单响应"""
    return EcnAffectedOrderResponse(
        id=ao.id,
        ecn_id=ao.ecn_id,
        order_type=ao.order_type,
        order_id=ao.order_id,
        order_no=ao.order_no,
        impact_description=ao.impact_description,
        action_type=ao.action_type,
        action_description=ao.action_description,
        status=ao.status,
        processed_by=ao.processed_by,
        processed_at=ao.processed_at,
        created_at=ao.created_at,
        updated_at=ao.updated_at
    )
