# -*- coding: utf-8 -*-
"""
采购价格分析 API
- 物料价格趋势（按时间）
- 不同供应商价格对比
- 价格异常检测（涨幅过大）
- 采购成本优化建议
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.schemas import success_response
from app.models.material import Material, MaterialSupplier
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.user import User
from app.models.vendor import Vendor

router = APIRouter()
logger = logging.getLogger(__name__)

# 价格异常阈值
PRICE_ANOMALY_THRESHOLD = 0.20  # 涨幅超过 20% 视为异常


@router.get("/")
def get_price_analysis(
    db: Session = Depends(get_db),
    material_id: Optional[int] = Query(None, description="物料ID"),
    material_code: Optional[str] = Query(None, description="物料编码"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    top_n: int = Query(20, ge=1, le=100, description="分析物料数量"),
    current_user: User = Depends(get_current_active_user),
):
    """
    采购价格综合分析

    返回：
    - price_trends: 物料价格趋势
    - supplier_comparison: 供应商价格对比
    - anomalies: 价格异常检测
    - optimization_suggestions: 成本优化建议
    """
    dt_start = date.fromisoformat(start_date) if start_date else date.today() - timedelta(days=365)
    dt_end = date.fromisoformat(end_date) if end_date else date.today()

    # 1. 物料价格趋势
    price_trends = _get_price_trends(db, dt_start, dt_end, material_id, material_code, top_n)

    # 2. 供应商价格对比
    supplier_comparison = _get_supplier_price_comparison(
        db, dt_start, dt_end, material_id, material_code, supplier_id
    )

    # 3. 价格异常检测
    anomalies = _detect_price_anomalies(db, dt_start, dt_end, material_id)

    # 4. 采购成本优化建议
    suggestions = _generate_optimization_suggestions(db, dt_start, dt_end, top_n)

    return success_response(
        data={
            "period": {
                "start_date": dt_start.isoformat(),
                "end_date": dt_end.isoformat(),
            },
            "price_trends": price_trends,
            "supplier_comparison": supplier_comparison,
            "anomalies": anomalies,
            "optimization_suggestions": suggestions,
        },
        message="获取价格分析成功",
    )


def _get_price_trends(
    db: Session,
    start_date: date,
    end_date: date,
    material_id: Optional[int],
    material_code: Optional[str],
    top_n: int,
) -> List[Dict[str, Any]]:
    """
    物料价格趋势分析

    按月聚合采购单价，展示价格变化趋势
    """
    query = (
        db.query(
            PurchaseOrderItem.material_id,
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            func.strftime("%Y-%m", PurchaseOrder.order_date).label("month"),
            func.avg(PurchaseOrderItem.unit_price).label("avg_price"),
            func.min(PurchaseOrderItem.unit_price).label("min_price"),
            func.max(PurchaseOrderItem.unit_price).label("max_price"),
            func.sum(PurchaseOrderItem.quantity).label("total_qty"),
            func.sum(PurchaseOrderItem.amount).label("total_amount"),
        )
        .join(PurchaseOrder)
        .filter(
            PurchaseOrder.order_date.isnot(None),
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date,
            PurchaseOrder.status.notin_(["DRAFT", "CANCELLED"]),
            PurchaseOrderItem.unit_price > 0,
        )
    )

    if material_id:
        query = query.filter(PurchaseOrderItem.material_id == material_id)
    if material_code:
        query = query.filter(PurchaseOrderItem.material_code == material_code)

    rows = (
        query.group_by(
            PurchaseOrderItem.material_id,
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            func.strftime("%Y-%m", PurchaseOrder.order_date),
        )
        .order_by(PurchaseOrderItem.material_code, "month")
        .all()
    )

    # 按物料分组
    material_map: Dict[str, Dict] = {}
    for row in rows:
        key = row.material_code
        if key not in material_map:
            material_map[key] = {
                "material_id": row.material_id,
                "material_code": row.material_code,
                "material_name": row.material_name,
                "trend": [],
                "total_amount": 0,
            }
        material_map[key]["trend"].append(
            {
                "month": row.month,
                "avg_price": round(float(row.avg_price or 0), 4),
                "min_price": round(float(row.min_price or 0), 4),
                "max_price": round(float(row.max_price or 0), 4),
                "total_qty": round(float(row.total_qty or 0), 2),
                "total_amount": round(float(row.total_amount or 0), 2),
            }
        )
        material_map[key]["total_amount"] += float(row.total_amount or 0)

    # 计算价格变化率
    results = list(material_map.values())
    for item in results:
        trend = item["trend"]
        if len(trend) >= 2:
            first_price = trend[0]["avg_price"]
            last_price = trend[-1]["avg_price"]
            if first_price > 0:
                item["price_change_rate"] = round((last_price - first_price) / first_price * 100, 2)
            else:
                item["price_change_rate"] = 0
        else:
            item["price_change_rate"] = 0
        item["total_amount"] = round(item["total_amount"], 2)

    # 按采购金额排序，取 top_n
    results.sort(key=lambda x: x["total_amount"], reverse=True)
    return results[:top_n]


def _get_supplier_price_comparison(
    db: Session,
    start_date: date,
    end_date: date,
    material_id: Optional[int],
    material_code: Optional[str],
    supplier_id: Optional[int],
) -> List[Dict[str, Any]]:
    """
    同一物料不同供应商的价格对比
    """
    query = (
        db.query(
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            PurchaseOrder.supplier_id,
            Vendor.supplier_name,
            func.avg(PurchaseOrderItem.unit_price).label("avg_price"),
            func.min(PurchaseOrderItem.unit_price).label("min_price"),
            func.max(PurchaseOrderItem.unit_price).label("max_price"),
            func.sum(PurchaseOrderItem.quantity).label("total_qty"),
            func.count(PurchaseOrderItem.id).label("order_lines"),
        )
        .join(PurchaseOrder)
        .join(Vendor, Vendor.id == PurchaseOrder.supplier_id)
        .filter(
            PurchaseOrder.order_date.isnot(None),
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date,
            PurchaseOrder.status.notin_(["DRAFT", "CANCELLED"]),
            PurchaseOrderItem.unit_price > 0,
        )
    )

    if material_id:
        query = query.filter(PurchaseOrderItem.material_id == material_id)
    if material_code:
        query = query.filter(PurchaseOrderItem.material_code == material_code)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    rows = (
        query.group_by(
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            PurchaseOrder.supplier_id,
            Vendor.supplier_name,
        )
        .order_by(PurchaseOrderItem.material_code, "avg_price")
        .all()
    )

    # 按物料分组
    material_map: Dict[str, Dict] = {}
    for row in rows:
        key = row.material_code
        if key not in material_map:
            material_map[key] = {
                "material_code": row.material_code,
                "material_name": row.material_name,
                "suppliers": [],
            }
        material_map[key]["suppliers"].append(
            {
                "supplier_id": row.supplier_id,
                "supplier_name": row.supplier_name,
                "avg_price": round(float(row.avg_price or 0), 4),
                "min_price": round(float(row.min_price or 0), 4),
                "max_price": round(float(row.max_price or 0), 4),
                "total_qty": round(float(row.total_qty or 0), 2),
                "order_lines": row.order_lines,
            }
        )

    # 计算价差
    results = list(material_map.values())
    for item in results:
        suppliers = item["suppliers"]
        if len(suppliers) >= 2:
            prices = [s["avg_price"] for s in suppliers]
            item["price_spread"] = round(max(prices) - min(prices), 4)
            min_price = min(prices)
            if min_price > 0:
                item["price_spread_pct"] = round(
                    (max(prices) - min_price) / min_price * 100, 2
                )
            else:
                item["price_spread_pct"] = 0
            item["lowest_supplier"] = suppliers[0]["supplier_name"]
        else:
            item["price_spread"] = 0
            item["price_spread_pct"] = 0
            item["lowest_supplier"] = suppliers[0]["supplier_name"] if suppliers else None

    # 按价差百分比排序
    results.sort(key=lambda x: x.get("price_spread_pct", 0), reverse=True)
    return results[:30]


def _detect_price_anomalies(
    db: Session,
    start_date: date,
    end_date: date,
    material_id: Optional[int],
) -> List[Dict[str, Any]]:
    """
    价格异常检测

    检测相邻两次采购中单价涨幅超过阈值的记录
    """
    query = (
        db.query(
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            PurchaseOrderItem.unit_price,
            PurchaseOrder.order_date,
            PurchaseOrder.order_no,
            Vendor.supplier_name,
        )
        .join(PurchaseOrder)
        .join(Vendor, Vendor.id == PurchaseOrder.supplier_id)
        .filter(
            PurchaseOrder.order_date.isnot(None),
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date,
            PurchaseOrder.status.notin_(["DRAFT", "CANCELLED"]),
            PurchaseOrderItem.unit_price > 0,
        )
    )

    if material_id:
        query = query.filter(PurchaseOrderItem.material_id == material_id)

    rows = query.order_by(PurchaseOrderItem.material_code, PurchaseOrder.order_date).all()

    anomalies = []
    prev_by_material: Dict[str, Dict] = {}

    for row in rows:
        code = row.material_code
        price = float(row.unit_price)

        if code in prev_by_material:
            prev = prev_by_material[code]
            prev_price = prev["price"]
            if prev_price > 0:
                change_rate = (price - prev_price) / prev_price
                if change_rate > PRICE_ANOMALY_THRESHOLD:
                    anomalies.append(
                        {
                            "material_code": code,
                            "material_name": row.material_name,
                            "prev_price": round(prev_price, 4),
                            "prev_date": prev["date"].isoformat() if prev["date"] else None,
                            "prev_order": prev["order_no"],
                            "current_price": round(price, 4),
                            "current_date": row.order_date.isoformat() if row.order_date else None,
                            "current_order": row.order_no,
                            "supplier_name": row.supplier_name,
                            "change_rate": round(change_rate * 100, 2),
                            "alert_level": "HIGH" if change_rate > 0.5 else "MEDIUM",
                        }
                    )

        prev_by_material[code] = {
            "price": price,
            "date": row.order_date,
            "order_no": row.order_no,
        }

    anomalies.sort(key=lambda x: x["change_rate"], reverse=True)
    return anomalies[:50]


def _generate_optimization_suggestions(
    db: Session, start_date: date, end_date: date, top_n: int
) -> List[Dict[str, Any]]:
    """
    采购成本优化建议

    基于数据分析生成可操作的建议：
    1. 可切换到更低价供应商的物料
    2. 价格持续上涨的物料（需关注）
    3. 单一供应商依赖的高价值物料
    """
    suggestions = []

    # 1. 检测可切换低价供应商的物料
    # 找到当前（最近一次采购）价格高于最低供应商报价的物料
    recent_purchases = (
        db.query(
            PurchaseOrderItem.material_id,
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            PurchaseOrderItem.unit_price,
            Vendor.supplier_name.label("current_supplier"),
        )
        .join(PurchaseOrder)
        .join(Vendor, Vendor.id == PurchaseOrder.supplier_id)
        .filter(
            PurchaseOrder.order_date.isnot(None),
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.status.notin_(["DRAFT", "CANCELLED"]),
            PurchaseOrderItem.unit_price > 0,
            PurchaseOrderItem.material_id.isnot(None),
        )
        .order_by(PurchaseOrderItem.material_code, desc(PurchaseOrder.order_date))
        .all()
    )

    # 取每个物料最近一次采购价
    seen_materials = set()
    recent_price_map: Dict[int, Dict] = {}
    for row in recent_purchases:
        if row.material_id not in seen_materials and row.material_id:
            seen_materials.add(row.material_id)
            recent_price_map[row.material_id] = {
                "material_code": row.material_code,
                "material_name": row.material_name,
                "current_price": float(row.unit_price),
                "current_supplier": row.current_supplier,
            }

    # 对比 MaterialSupplier 中的最低报价
    for mid, info in list(recent_price_map.items())[:top_n]:
        lowest = (
            db.query(MaterialSupplier.price, Vendor.supplier_name)
            .join(Vendor, Vendor.id == MaterialSupplier.supplier_id)
            .filter(
                MaterialSupplier.material_id == mid,
                MaterialSupplier.is_active == True,
                MaterialSupplier.price > 0,
            )
            .order_by(MaterialSupplier.price)
            .first()
        )
        if lowest and float(lowest.price) < info["current_price"] * 0.95:
            saving_pct = round(
                (info["current_price"] - float(lowest.price)) / info["current_price"] * 100, 1
            )
            suggestions.append(
                {
                    "type": "SWITCH_SUPPLIER",
                    "priority": "HIGH" if saving_pct > 10 else "MEDIUM",
                    "material_code": info["material_code"],
                    "material_name": info["material_name"],
                    "current_price": round(info["current_price"], 4),
                    "current_supplier": info["current_supplier"],
                    "suggested_price": round(float(lowest.price), 4),
                    "suggested_supplier": lowest.supplier_name,
                    "saving_pct": saving_pct,
                    "message": f"物料 {info['material_code']} 可切换至 {lowest.supplier_name}，预计节省 {saving_pct}%",
                }
            )

    # 2. 单一供应商高价值物料
    single_source = (
        db.query(
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            func.sum(PurchaseOrderItem.amount).label("total_amount"),
            func.count(func.distinct(PurchaseOrder.supplier_id)).label("supplier_count"),
        )
        .join(PurchaseOrder)
        .filter(
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date,
            PurchaseOrder.status.notin_(["DRAFT", "CANCELLED"]),
        )
        .group_by(PurchaseOrderItem.material_code, PurchaseOrderItem.material_name)
        .having(func.count(func.distinct(PurchaseOrder.supplier_id)) == 1)
        .having(func.sum(PurchaseOrderItem.amount) > 10000)
        .order_by(desc("total_amount"))
        .limit(10)
        .all()
    )

    for row in single_source:
        suggestions.append(
            {
                "type": "SINGLE_SOURCE_RISK",
                "priority": "MEDIUM",
                "material_code": row.material_code,
                "material_name": row.material_name,
                "total_amount": round(float(row.total_amount or 0), 2),
                "message": f"物料 {row.material_code} 仅有1家供应商，采购金额 {round(float(row.total_amount or 0), 2)} 元，建议开发备选供应商",
            }
        )

    suggestions.sort(key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x["priority"], 3))
    return suggestions
