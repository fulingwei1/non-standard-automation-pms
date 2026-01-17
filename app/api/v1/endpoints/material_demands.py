# -*- coding: utf-8 -*-
"""
物料需求计划(MRP) API endpoints
包含：物料需求汇总、需求与库存对比、自动生成采购需求、需求时间表
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import BomHeader, BomItem, Material, MaterialShortage
from app.models.project import Machine, Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


@router.get("/material-demands", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_material_demands(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    material_id: Optional[int] = Query(None, description="物料ID筛选"),
    material_code: Optional[str] = Query(None, description="物料编码筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="需求开始日期"),
    end_date: Optional[date] = Query(None, description="需求结束日期"),
    current_user: User = Depends(security.require_procurement_access()),
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

    if material_code:
        query = query.filter(BomItem.material_code.like(f"%{material_code}%"))

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
    offset = (page - 1) * page_size
    paginated_items = items[offset:offset + page_size]

    return PaginatedResponse(
        items=paginated_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/material-demands/vs-stock", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_material_demands_vs_stock(
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表（逗号分隔）"),
    material_ids: Optional[str] = Query(None, description="物料ID列表（逗号分隔）"),
    current_user: User = Depends(security.require_procurement_access()),
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


@router.post("/material-demands/generate-pr", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def generate_purchase_requisition(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表（逗号分隔）"),
    material_ids: Optional[str] = Query(None, description="物料ID列表（逗号分隔），为空则生成所有短缺物料"),
    supplier_id: Optional[int] = Query(None, description="默认供应商ID"),
    current_user: User = Depends(security.require_procurement_access()),
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


@router.get("/material-demands/schedule", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_material_demand_schedule(
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表（逗号分隔）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: str = Query("day", description="分组方式：day/week/month"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    需求时间表（按日期需求）
    """
    # 解析项目ID列表
    project_id_list = None
    if project_ids:
        project_id_list = [int(p.strip()) for p in project_ids.split(",") if p.strip()]

    # 默认查询未来30天
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)

    # 从BOM明细查询需求
    query = (
        db.query(
            BomItem.required_date,
            BomItem.material_id,
            BomItem.material_code,
            BomItem.material_name,
            func.sum(BomItem.quantity).label('demand_qty')
        )
        .join(BomHeader, BomItem.bom_id == BomHeader.id)
        .join(Machine, BomHeader.machine_id == Machine.id)
        .filter(BomItem.required_date >= start_date)
        .filter(BomItem.required_date <= end_date)
    )

    if project_id_list:
        query = query.filter(Machine.project_id.in_(project_id_list))

    query = query.group_by(BomItem.required_date, BomItem.material_id, BomItem.material_code, BomItem.material_name)
    results = query.all()

    # 按日期分组
    schedule = {}
    for result in results:
        demand_date = result.required_date.isoformat() if result.required_date else None
        if not demand_date:
            continue

        # 根据分组方式调整日期
        if group_by == "week":
            # 获取该周的周一
            demand_date_obj = result.required_date
            days_since_monday = demand_date_obj.weekday()
            week_start = demand_date_obj - timedelta(days=days_since_monday)
            demand_date = week_start.isoformat()
        elif group_by == "month":
            # 使用月份的第一天
            demand_date_obj = result.required_date
            demand_date = date(demand_date_obj.year, demand_date_obj.month, 1).isoformat()

        if demand_date not in schedule:
            schedule[demand_date] = []

        schedule[demand_date].append({
            "material_id": result.material_id,
            "material_code": result.material_code,
            "material_name": result.material_name,
            "demand_qty": float(result.demand_qty)
        })

    # 转换为列表格式
    items = []
    for demand_date in sorted(schedule.keys()):
        items.append({
            "date": demand_date,
            "materials": schedule[demand_date],
            "total_materials": len(schedule[demand_date]),
            "total_demand": sum(m["demand_qty"] for m in schedule[demand_date])
        })

    return items


@router.get("/materials/{material_id}/lead-time-forecast", response_model=dict, status_code=status.HTTP_200_OK)
def get_material_lead_time_forecast(
    material_id: int,
    db: Session = Depends(deps.get_db),
    days: int = Query(90, description="统计天数（默认90天）"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    物料交期预测（基于历史）
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 查询历史采购订单的到货时间
    cutoff_date = datetime.now() - timedelta(days=days)

    po_items = (
        db.query(PurchaseOrderItem)
        .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
        .filter(PurchaseOrderItem.material_id == material_id)
        .filter(PurchaseOrder.status.in_(["APPROVED", "ORDERED", "RECEIVED", "CLOSED"]))
        .filter(PurchaseOrder.created_at >= cutoff_date)
        .all()
    )

    # 计算平均交期
    lead_times = []
    for po_item in po_items:
        if po_item.received_at and po_item.purchase_order:
            order_date = po_item.purchase_order.created_at.date()
            receive_date = po_item.received_at.date() if isinstance(po_item.received_at, datetime) else po_item.received_at
            lead_time = (receive_date - order_date).days
            if lead_time > 0:
                lead_times.append(lead_time)

    if lead_times:
        avg_lead_time = sum(lead_times) / len(lead_times)
        min_lead_time = min(lead_times)
        max_lead_time = max(lead_times)
    else:
        # 使用物料的标准交期
        avg_lead_time = material.lead_time_days or 7
        min_lead_time = avg_lead_time - 2
        max_lead_time = avg_lead_time + 5

    return {
        "material_id": material_id,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "standard_lead_time": material.lead_time_days or 0,
        "historical_count": len(lead_times),
        "forecast_avg_lead_time": round(avg_lead_time, 1),
        "forecast_min_lead_time": round(min_lead_time, 1),
        "forecast_max_lead_time": round(max_lead_time, 1),
        "recommended_lead_time": round(avg_lead_time + 2, 1)  # 建议交期 = 平均交期 + 2天缓冲
    }

