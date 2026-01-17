# -*- coding: utf-8 -*-
"""
项目级齐套率端点
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader
from app.models.project import Machine, Project
from app.models.purchase import PurchaseOrderItem
from app.models.user import User

from .utils import calculate_kit_rate

router = APIRouter()


@router.get("/projects/{project_id}/kit-rate")
def get_project_kit_rate(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    calculate_by: str = Query("quantity", description="计算方式：quantity(数量) 或 amount(金额)"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    计算项目齐套率
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if calculate_by not in ["quantity", "amount"]:
        raise HTTPException(status_code=400, detail="calculate_by 必须是 quantity 或 amount")

    # 获取项目下所有机台的BOM
    machines = db.query(Machine).filter(Machine.project_id == project_id).all()

    all_bom_items = []
    machine_stats = []

    for machine in machines:
        # 获取机台的最新BOM
        bom = (
            db.query(BomHeader)
            .filter(BomHeader.machine_id == machine.id)
            .filter(BomHeader.is_latest == True)
            .first()
        )

        if bom:
            bom_items = bom.items.all()
            all_bom_items.extend(bom_items)

            # 计算机台齐套率
            machine_kit_rate = calculate_kit_rate(db, bom_items, calculate_by)
            machine_stats.append({
                "machine_id": machine.id,
                "machine_no": machine.machine_no,
                "machine_name": machine.machine_name,
                **machine_kit_rate,
            })

    # 计算项目整体齐套率
    project_kit_rate = calculate_kit_rate(db, all_bom_items, calculate_by)

    return {
        "project_id": project_id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        **project_kit_rate,
        "machines": machine_stats,
    }


@router.get("/projects/{project_id}/material-status")
def get_project_material_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取项目物料汇总
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取项目下所有机台的物料状态
    machines = db.query(Machine).filter(Machine.project_id == project_id).all()

    # 汇总所有物料（按物料编码汇总）
    material_summary = {}

    for machine in machines:
        bom = (
            db.query(BomHeader)
            .filter(BomHeader.machine_id == machine.id)
            .filter(BomHeader.is_latest == True)
            .first()
        )

        if bom:
            for item in bom.items.all():
                material_code = item.material_code
                if material_code not in material_summary:
                    material = item.material
                    material_summary[material_code] = {
                        "material_id": item.material_id,
                        "material_code": material_code,
                        "material_name": item.material_name,
                        "specification": item.specification,
                        "unit": item.unit,
                        "total_required_qty": Decimal(0),
                        "current_stock": float(material.current_stock or 0) if material else 0,
                        "total_received_qty": Decimal(0),
                        "total_in_transit_qty": Decimal(0),
                        "is_key_material": item.is_key_item,
                        "machines": [],
                    }

                summary = material_summary[material_code]
                summary["total_required_qty"] += item.quantity or 0
                summary["total_received_qty"] += item.received_qty or 0

                # 在途数量
                if item.material_id:
                    po_items = (
                        db.query(PurchaseOrderItem)
                        .filter(PurchaseOrderItem.material_id == item.material_id)
                        .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
                        .all()
                    )
                    for po_item in po_items:
                        summary["total_in_transit_qty"] += (po_item.quantity or 0) - (po_item.received_qty or 0)

                summary["machines"].append({
                    "machine_id": machine.id,
                    "machine_no": machine.machine_no,
                    "required_qty": float(item.quantity or 0),
                })

    # 转换为列表并计算汇总
    material_list = []
    total_required = Decimal(0)
    total_available = Decimal(0)
    total_shortage = Decimal(0)

    for material_code, summary in material_summary.items():
        total_available_qty = summary["current_stock"] + float(summary["total_received_qty"]) + float(summary["total_in_transit_qty"])
        shortage_qty = max(0, float(summary["total_required_qty"]) - total_available_qty)

        total_required += summary["total_required_qty"]
        total_available += Decimal(total_available_qty)
        total_shortage += Decimal(shortage_qty)

        material_list.append({
            **summary,
            "total_required_qty": float(summary["total_required_qty"]),
            "total_received_qty": float(summary["total_received_qty"]),
            "total_in_transit_qty": float(summary["total_in_transit_qty"]),
            "total_available_qty": total_available_qty,
            "shortage_qty": shortage_qty,
            "status": "fulfilled" if shortage_qty == 0 else ("partial" if total_available_qty > 0 else "shortage"),
        })

    return {
        "project_id": project_id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "summary": {
            "total_materials": len(material_list),
            "total_required_qty": float(total_required),
            "total_available_qty": float(total_available),
            "total_shortage_qty": float(total_shortage),
        },
        "materials": material_list,
    }


@router.get("/projects/{project_id}/shortage")
def get_project_shortage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取项目缺料清单
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取项目物料状态
    material_status = get_project_material_status(
        db=db,
        project_id=project_id,
        current_user=current_user
    )

    # 筛选缺料项
    shortage_list = [
        item for item in material_status["materials"]
        if item["shortage_qty"] > 0
    ]

    return {
        "project_id": project_id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "total_shortage_items": len(shortage_list),
        "shortage_list": shortage_list,
    }


@router.get("/projects/{project_id}/critical-shortage")
def get_project_critical_shortage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取项目关键物料缺口
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取项目物料状态
    material_status = get_project_material_status(
        db=db,
        project_id=project_id,
        current_user=current_user
    )

    # 筛选关键物料且缺料的项
    critical_shortage_list = [
        item for item in material_status["materials"]
        if item["is_key_material"] and item["shortage_qty"] > 0
    ]

    return {
        "project_id": project_id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "total_critical_shortage_items": len(critical_shortage_list),
        "critical_shortage_list": critical_shortage_list,
    }
