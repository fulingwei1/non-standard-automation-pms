# -*- coding: utf-8 -*-
"""
采购齐套率分析 API
- 项目物料齐套率统计
- 缺料明细及影响分析
- 预计齐套时间预测
- 齐套率趋势（按项目/产品）
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.schemas import success_response
from app.models.material import BomHeader, BomItem, Material, MaterialShortage
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
def get_kitting_analysis(
    db: Session = Depends(get_db),
    project_id: Optional[int] = Query(None, description="项目ID"),
    bom_id: Optional[int] = Query(None, description="BOM ID"),
    include_details: bool = Query(True, description="是否包含缺料明细"),
    current_user: User = Depends(get_current_active_user),
):
    """
    采购齐套率综合分析

    返回：
    - summary: 汇总统计
    - projects: 各项目/BOM齐套率
    - shortage_details: 缺料明细（可选）
    - estimated_kitting: 预计齐套时间
    - trend: 齐套率趋势
    """
    # 查询 BOM
    bom_query = db.query(BomHeader).filter(
        BomHeader.status != "DRAFT",
        BomHeader.is_latest == True,
    )
    if project_id:
        bom_query = bom_query.filter(BomHeader.project_id == project_id)
    if bom_id:
        bom_query = bom_query.filter(BomHeader.id == bom_id)

    boms = bom_query.all()

    if not boms:
        return success_response(
            data={
                "summary": {
                    "total_boms": 0,
                    "avg_kitting_rate": 0,
                    "fully_kitted": 0,
                    "partially_kitted": 0,
                    "critical_shortage": 0,
                },
                "projects": [],
                "shortage_details": [],
                "estimated_kitting": [],
                "trend": [],
            },
            message="暂无BOM数据",
        )

    # 分析每个BOM的齐套率
    project_results = []
    all_shortages = []
    all_estimates = []
    fully_kitted = 0
    partially_kitted = 0
    critical_count = 0

    for bom in boms:
        bom_items = bom.items.all()
        if not bom_items:
            continue

        total_items = len(bom_items)
        kitted_items = 0
        bom_shortages = []

        for item in bom_items:
            required = float(item.quantity or 0)
            received = float(item.received_qty or 0)
            purchased = float(item.purchased_qty or 0)

            # 也考虑库存
            current_stock = 0
            if item.material_id:
                mat = db.query(Material).filter(Material.id == item.material_id).first()
                if mat:
                    current_stock = float(mat.current_stock or 0)

            available = received + current_stock
            if available >= required:
                kitted_items += 1
            else:
                shortage_qty = required - available
                in_transit = max(0, purchased - received)  # 在途数量

                # 预计到货时间
                est_arrival = _estimate_arrival(db, item.material_id, shortage_qty, in_transit)

                shortage_info = {
                    "bom_id": bom.id,
                    "bom_no": bom.bom_no,
                    "bom_name": bom.bom_name,
                    "project_id": bom.project_id,
                    "material_id": item.material_id,
                    "material_code": item.material_code,
                    "material_name": item.material_name,
                    "specification": item.specification,
                    "required_qty": round(required, 2),
                    "received_qty": round(received, 2),
                    "current_stock": round(current_stock, 2),
                    "available_qty": round(available, 2),
                    "shortage_qty": round(shortage_qty, 2),
                    "in_transit_qty": round(in_transit, 2),
                    "is_key_item": item.is_key_item,
                    "estimated_arrival": est_arrival,
                    "impact_level": "HIGH" if item.is_key_item else (
                        "MEDIUM" if shortage_qty > required * 0.5 else "LOW"
                    ),
                }
                bom_shortages.append(shortage_info)

        kitting_rate = round(kitted_items / total_items * 100, 1) if total_items else 0

        if kitting_rate >= 100:
            fully_kitted += 1
        elif kitting_rate < 60:
            critical_count += 1
        else:
            partially_kitted += 1

        # 预计齐套时间（取所有缺料中最晚的到货时间）
        est_kitting_date = None
        if bom_shortages:
            arrival_dates = [
                s["estimated_arrival"]
                for s in bom_shortages
                if s["estimated_arrival"]
            ]
            if arrival_dates:
                est_kitting_date = max(arrival_dates)

        project_results.append(
            {
                "bom_id": bom.id,
                "bom_no": bom.bom_no,
                "bom_name": bom.bom_name,
                "project_id": bom.project_id,
                "total_items": total_items,
                "kitted_items": kitted_items,
                "shortage_items": total_items - kitted_items,
                "kitting_rate": kitting_rate,
                "estimated_kitting_date": est_kitting_date,
                "status": (
                    "FULLY_KITTED" if kitting_rate >= 100
                    else "CRITICAL" if kitting_rate < 60
                    else "PARTIAL"
                ),
            }
        )

        all_shortages.extend(bom_shortages)

        if est_kitting_date:
            all_estimates.append(
                {
                    "bom_id": bom.id,
                    "bom_no": bom.bom_no,
                    "bom_name": bom.bom_name,
                    "current_kitting_rate": kitting_rate,
                    "shortage_count": len(bom_shortages),
                    "estimated_kitting_date": est_kitting_date,
                    "days_to_kit": (
                        date.fromisoformat(est_kitting_date) - date.today()
                    ).days if est_kitting_date else None,
                }
            )

    # 汇总
    total_boms = len(project_results)
    avg_kitting = (
        round(sum(p["kitting_rate"] for p in project_results) / total_boms, 1)
        if total_boms
        else 0
    )

    # 排序
    project_results.sort(key=lambda x: x["kitting_rate"])
    all_shortages.sort(
        key=lambda x: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x["impact_level"], 3),
            -x["shortage_qty"],
        )
    )
    all_estimates.sort(key=lambda x: x.get("estimated_kitting_date") or "9999")

    # 齐套率趋势（基于现有缺料预警数据）
    trend = _get_kitting_trend(db, project_id)

    result = {
        "summary": {
            "total_boms": total_boms,
            "avg_kitting_rate": avg_kitting,
            "fully_kitted": fully_kitted,
            "partially_kitted": partially_kitted,
            "critical_shortage": critical_count,
        },
        "projects": project_results,
        "estimated_kitting": all_estimates,
        "trend": trend,
    }

    if include_details:
        result["shortage_details"] = all_shortages[:100]

    return success_response(data=result, message="获取齐套率分析成功")


def _estimate_arrival(
    db: Session,
    material_id: Optional[int],
    shortage_qty: float,
    in_transit: float,
) -> Optional[str]:
    """
    预计到货时间

    逻辑：
    1. 如果在途数量能满足缺口，查最近的订单承诺交期
    2. 否则根据物料采购周期估算
    """
    if not material_id:
        return None

    # 查询该物料未完成的采购订单行
    pending_items = (
        db.query(PurchaseOrderItem)
        .join(PurchaseOrder)
        .filter(
            PurchaseOrderItem.material_id == material_id,
            PurchaseOrder.status.in_(["APPROVED", "SUBMITTED"]),
            PurchaseOrderItem.status.in_(["PENDING", "PARTIAL"]),
        )
        .order_by(PurchaseOrderItem.promised_date)
        .all()
    )

    if pending_items:
        # 找最晚的承诺交期
        dates = [
            i.promised_date for i in pending_items if i.promised_date
        ]
        if dates:
            return max(dates).isoformat()

    # 基于物料采购周期估算
    mat = db.query(Material).filter(Material.id == material_id).first()
    if mat and mat.lead_time_days:
        est = date.today() + timedelta(days=mat.lead_time_days)
        return est.isoformat()

    # 默认 30 天
    return (date.today() + timedelta(days=30)).isoformat()


def _get_kitting_trend(
    db: Session,
    project_id: Optional[int],
) -> List[Dict[str, Any]]:
    """
    齐套率趋势

    基于缺料预警表的历史数据，按月统计缺料数量变化
    """
    query = db.query(
        func.strftime("%Y-%m", MaterialShortage.created_at).label("month"),
        func.count(MaterialShortage.id).label("total_shortages"),
        func.sum(
            func.case(
                (MaterialShortage.status == "RESOLVED", 1),
                else_=0,
            )
        ).label("resolved"),
        func.sum(
            func.case(
                (MaterialShortage.status.in_(["OPEN", "ASSIGNED"]), 1),
                else_=0,
            )
        ).label("open"),
    ).filter(MaterialShortage.created_at.isnot(None))

    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)

    rows = (
        query.group_by(func.strftime("%Y-%m", MaterialShortage.created_at))
        .order_by("month")
        .all()
    )

    trend = []
    for row in rows:
        total = row.total_shortages or 0
        resolved = int(row.resolved or 0)
        resolution_rate = round(resolved / total * 100, 1) if total else 0
        trend.append(
            {
                "month": row.month,
                "total_shortages": total,
                "resolved": resolved,
                "open": int(row.open or 0),
                "resolution_rate": resolution_rate,
            }
        )

    return trend
