# -*- coding: utf-8 -*-
"""
齐套率与物料保障 API endpoints
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import BomHeader, BomItem, Material, MaterialShortage
from app.models.project import Machine, Project
from app.models.purchase import GoodsReceiptItem, PurchaseOrderItem
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


def calculate_kit_rate(
    db: Session,
    bom_items: List[BomItem],
    calculate_by: str = "quantity"  # "quantity" or "amount"
) -> Dict[str, Any]:
    """
    计算齐套率

    Args:
        bom_items: BOM明细列表
        calculate_by: 计算方式，"quantity"按数量，"amount"按金额

    Returns:
        包含齐套率统计信息的字典
    """
    total_items = len(bom_items)
    if total_items == 0:
        return {
            "total_items": 0,
            "fulfilled_items": 0,
            "shortage_items": 0,
            "in_transit_items": 0,
            "kit_rate": 0.0,
            "kit_status": "complete",
        }

    fulfilled_items = 0
    shortage_items = 0
    in_transit_items = 0
    total_quantity = Decimal(0)
    total_amount = Decimal(0)
    fulfilled_quantity = Decimal(0)
    fulfilled_amount = Decimal(0)

    for item in bom_items:
        # 计算可用数量 = 当前库存 + 已到货数量
        material = item.material
        available_qty = (material.current_stock or 0) + (item.received_qty or 0)

        # 计算在途数量 = 已采购但未到货的数量
        # 查询该物料的采购订单明细
        in_transit_qty = Decimal(0)
        if item.material_id:
            po_items = (
                db.query(PurchaseOrderItem)
                .filter(PurchaseOrderItem.material_id == item.material_id)
                .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
                .all()
            )
            for po_item in po_items:
                in_transit_qty += (po_item.quantity or 0) - (po_item.received_qty or 0)

        # 总可用数量 = 可用数量 + 在途数量
        total_available = available_qty + in_transit_qty

        # 需求数量
        required_qty = item.quantity or 0

        # 计算金额
        item_amount = required_qty * (item.unit_price or 0)
        total_amount += item_amount

        if calculate_by == "quantity":
            total_quantity += required_qty
            if total_available >= required_qty:
                fulfilled_items += 1
                fulfilled_quantity += required_qty
            elif total_available > 0:
                in_transit_items += 1
            else:
                shortage_items += 1
        else:  # by amount
            total_quantity += required_qty
            if total_available >= required_qty:
                fulfilled_items += 1
                fulfilled_quantity += required_qty
                fulfilled_amount += item_amount
            elif total_available > 0:
                in_transit_items += 1
            else:
                shortage_items += 1

    # 计算齐套率
    if calculate_by == "quantity":
        if total_quantity > 0:
            kit_rate = float((fulfilled_quantity / total_quantity) * 100)
        else:
            kit_rate = 0.0
    else:  # by amount
        if total_amount > 0:
            kit_rate = float((fulfilled_amount / total_amount) * 100)
        else:
            kit_rate = 0.0

    # 确定齐套状态
    if kit_rate >= 100:
        kit_status = "complete"
    elif kit_rate >= 80:
        kit_status = "partial"
    else:
        kit_status = "shortage"

    return {
        "total_items": total_items,
        "fulfilled_items": fulfilled_items,
        "shortage_items": shortage_items,
        "in_transit_items": in_transit_items,
        "kit_rate": round(kit_rate, 2),
        "kit_status": kit_status,
        "total_quantity": float(total_quantity),
        "fulfilled_quantity": float(fulfilled_quantity),
        "total_amount": float(total_amount),
        "fulfilled_amount": float(fulfilled_amount),
        "calculate_by": calculate_by,
    }


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


@router.get("/machines/{machine_id}/kit-rate")
def get_machine_kit_rate(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    calculate_by: str = Query("quantity", description="计算方式：quantity(数量) 或 amount(金额)"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    计算机台齐套率
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    if calculate_by not in ["quantity", "amount"]:
        raise HTTPException(status_code=400, detail="calculate_by 必须是 quantity 或 amount")

    # 获取机台的最新BOM
    bom = (
        db.query(BomHeader)
        .filter(BomHeader.machine_id == machine_id)
        .filter(BomHeader.is_latest == True)
        .first()
    )

    if not bom:
        raise HTTPException(status_code=404, detail="机台没有BOM")

    bom_items = bom.items.all()
    kit_rate = calculate_kit_rate(db, bom_items, calculate_by)

    return {
        "machine_id": machine_id,
        "machine_no": machine.machine_no,
        "machine_name": machine.machine_name,
        "bom_id": bom.id,
        "bom_no": bom.bom_no,
        "bom_name": bom.bom_name,
        **kit_rate,
    }


@router.get("/machines/{machine_id}/material-status")
def get_machine_material_status(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取机台物料状态
    """"""
    获取机台物料状态（详细到货状态）
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 获取机台的最新BOM
    bom = (
        db.query(BomHeader)
        .filter(BomHeader.machine_id == machine_id)
        .filter(BomHeader.is_latest == True)
        .first()
    )

    if not bom:
        raise HTTPException(status_code=404, detail="机台没有BOM")

    bom_items = bom.items.all()
    material_status_list = []

    for item in bom_items:
        material = item.material
        required_qty = item.quantity or 0

        # 当前库存
        current_stock = material.current_stock or 0 if material else 0

        # 已到货数量
        received_qty = item.received_qty or 0

        # 可用数量
        available_qty = current_stock + received_qty

        # 在途数量
        in_transit_qty = Decimal(0)
        if item.material_id:
            po_items = (
                db.query(PurchaseOrderItem)
                .filter(PurchaseOrderItem.material_id == item.material_id)
                .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
                .all()
            )
            for po_item in po_items:
                in_transit_qty += (po_item.quantity or 0) - (po_item.received_qty or 0)

        # 总可用数量
        total_available = available_qty + in_transit_qty

        # 短缺数量
        shortage_qty = max(0, required_qty - total_available)

        # 状态
        if total_available >= required_qty:
            status = "fulfilled"
        elif total_available > 0:
            status = "partial"
        else:
            status = "shortage"

        material_status_list.append({
            "bom_item_id": item.id,
            "item_no": item.item_no,
            "material_id": item.material_id,
            "material_code": item.material_code,
            "material_name": item.material_name,
            "specification": item.specification,
            "unit": item.unit,
            "required_qty": float(required_qty),
            "current_stock": float(current_stock),
            "received_qty": float(received_qty),
            "available_qty": float(available_qty),
            "in_transit_qty": float(in_transit_qty),
            "total_available": float(total_available),
            "shortage_qty": float(shortage_qty),
            "status": status,
            "is_key_item": item.is_key_item,
            "required_date": item.required_date.isoformat() if item.required_date else None,
        })

    return {
        "machine_id": machine_id,
        "machine_no": machine.machine_no,
        "machine_name": machine.machine_name,
        "bom_id": bom.id,
        "bom_no": bom.bom_no,
        "items": material_status_list,
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


@router.get("/kit-rate/dashboard")
def get_kit_rate_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取齐套看板数据（全局看板）
    """
    # 如果指定了项目ID，只查询这些项目
    if project_ids:
        project_id_list = [int(id.strip()) for id in project_ids.split(",") if id.strip()]
        projects = db.query(Project).filter(Project.id.in_(project_id_list)).all()
    else:
        # 查询所有活跃项目
        projects = db.query(Project).filter(Project.is_active == True).all()

    dashboard_data = []
    total_projects = 0
    complete_projects = 0
    partial_projects = 0
    shortage_projects = 0

    for project in projects:
        kit_rate_data = get_project_kit_rate(
            db=db,
            project_id=project.id,
            calculate_by="quantity",
            current_user=current_user
        )

        dashboard_data.append({
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "kit_rate": kit_rate_data["kit_rate"],
            "kit_status": kit_rate_data["kit_status"],
            "total_items": kit_rate_data["total_items"],
            "fulfilled_items": kit_rate_data["fulfilled_items"],
            "shortage_items": kit_rate_data["shortage_items"],
        })

        total_projects += 1
        if kit_rate_data["kit_status"] == "complete":
            complete_projects += 1
        elif kit_rate_data["kit_status"] == "partial":
            partial_projects += 1
        else:
            shortage_projects += 1

    return {
        "summary": {
            "total_projects": total_projects,
            "complete_projects": complete_projects,
            "partial_projects": partial_projects,
            "shortage_projects": shortage_projects,
        },
        "projects": dashboard_data,
    }


@router.get("/kit-rate/trend")
def get_kit_rate_trend(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID（可选，不提供则查询所有项目）"),
    start_date: Optional[date] = Query(None, description="开始日期（可选，默认30天前）"),
    end_date: Optional[date] = Query(None, description="结束日期（可选，默认今天）"),
    group_by: str = Query("day", description="分组方式：day/week/month"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取齐套趋势分析
    按时间分组统计齐套率变化趋势
    """
    # 设置默认日期范围
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    if group_by not in ["day", "week", "month"]:
        raise HTTPException(status_code=400, detail="group_by 必须是 day、week 或 month")

    # 确定要查询的项目
    if project_id:
        projects = db.query(Project).filter(Project.id == project_id).all()
    else:
        projects = db.query(Project).filter(Project.is_active == True).all()

    # 生成日期范围
    date_list = []
    current = start_date
    while current <= end_date:
        date_list.append(current)
        if group_by == "day":
            current += timedelta(days=1)
        elif group_by == "week":
            current += timedelta(days=7)
        else:  # month
            # 计算下个月的同一天
            if current.month == 12:
                current = date(current.year + 1, 1, current.day)
            else:
                current = date(current.year, current.month + 1, current.day)

    # 查询历史数据（这里简化处理，实际应该从历史记录表查询）
    # 由于没有历史记录表，我们使用当前数据模拟趋势
    trend_data = []

    for date_item in date_list:
        # 计算该日期的齐套率（简化：使用当前数据）
        # 实际应该从历史记录表查询该日期的快照数据
        total_kit_rate = 0.0
        project_count = 0

        for project in projects:
            try:
                kit_rate_data = get_project_kit_rate(
                    db=db,
                    project_id=project.id,
                    calculate_by="quantity",
                    current_user=current_user
                )
                total_kit_rate += kit_rate_data["kit_rate"]
                project_count += 1
            except (ValueError, TypeError, KeyError) as e:
                pass

        avg_kit_rate = total_kit_rate / project_count if project_count > 0 else 0.0

        trend_data.append({
            "date": date_item.isoformat(),
            "kit_rate": round(avg_kit_rate, 2),
            "project_count": project_count,
        })

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "group_by": group_by,
        "trend_data": trend_data,
        "summary": {
            "avg_kit_rate": round(sum(d["kit_rate"] for d in trend_data) / len(trend_data) if trend_data else 0, 2),
            "max_kit_rate": round(max((d["kit_rate"] for d in trend_data), default=0), 2),
            "min_kit_rate": round(min((d["kit_rate"] for d in trend_data), default=0), 2),
        }
    }

