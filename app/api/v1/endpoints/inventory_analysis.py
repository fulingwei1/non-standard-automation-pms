# -*- coding: utf-8 -*-
"""
库存分析兼容路由。

前端 InventoryAnalysis 页面使用 /inventory-analysis/* 这组旧路径；这里基于
当前物料主数据返回稳定的分析 shape，避免占位路由导致页面 404。
"""

from datetime import datetime
from typing import Any, Dict, Iterable, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import Material
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


def _num(value: Any) -> float:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return number if number == number and number not in (float("inf"), float("-inf")) else 0.0


def _round(value: Any, digits: int = 2) -> float:
    return round(_num(value), digits)


def _material_price(material: Material) -> float:
    last_price = _num(material.last_price)
    return last_price if last_price > 0 else _num(material.standard_price)


def _inventory_value(material: Material) -> float:
    return _num(material.current_stock) * _material_price(material)


def _category_name(material: Material) -> str:
    category = getattr(material, "category", None)
    return getattr(category, "category_name", None) or "未分类"


def _load_materials(db: Session) -> List[Material]:
    return (
        db.query(Material)
        .filter(Material.is_active.is_(True))
        .order_by(Material.material_code)
        .all()
    )


def _material_row(material: Material) -> Dict[str, Any]:
    stock = _num(material.current_stock)
    safety_stock = _num(material.safety_stock)
    unit = material.unit or "件"
    value = _inventory_value(material)
    return {
        "material_id": material.id,
        "material_code": material.material_code or "",
        "material_name": material.material_name or "",
        "category_name": _category_name(material),
        "current_stock": _round(stock),
        "safety_stock": _round(safety_stock),
        "shortage_qty": _round(max(safety_stock - stock, 0)),
        "unit": unit,
        "unit_price": _round(_material_price(material), 4),
        "inventory_value": _round(value),
    }


def _category_breakdown(materials: Iterable[Material]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    total_value = 0.0
    for material in materials:
        category_name = _category_name(material)
        value = _inventory_value(material)
        total_value += value
        bucket = grouped.setdefault(
            category_name,
            {"category_name": category_name, "inventory_value": 0.0, "material_count": 0},
        )
        bucket["inventory_value"] += value
        bucket["material_count"] += 1

    rows = sorted(grouped.values(), key=lambda item: item["inventory_value"], reverse=True)
    for row in rows:
        row["inventory_value"] = _round(row["inventory_value"])
        row["value_percentage"] = (
            _round(row["inventory_value"] / total_value * 100)
            if total_value > 0
            else 0
        )
    return rows


def _last_activity(material: Material) -> datetime | None:
    return material.updated_at or material.created_at


def _stale_days(material: Material, now: datetime) -> int:
    last_activity = _last_activity(material)
    if not last_activity:
        return 0
    return max((now - last_activity.replace(tzinfo=None)).days, 0)


@router.get("/")
def read_root(
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Dict[str, str]:
    return {"message": "inventory_analysis module ready"}


@router.get("/turnover-rate", response_model=ResponseModel)
def get_turnover_rate(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> ResponseModel:
    materials = _load_materials(db)
    total_value = sum(_inventory_value(material) for material in materials)

    return ResponseModel(
        data={
            "summary": {
                "total_inventory_value": _round(total_value),
                "turnover_rate": 0,
                "turnover_days": 0,
                "total_materials": len(materials),
            },
            "category_breakdown": _category_breakdown(materials),
        }
    )


@router.get("/stale-materials", response_model=ResponseModel)
def get_stale_materials(
    threshold_days: int = Query(90, ge=1, le=3650),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> ResponseModel:
    materials = _load_materials(db)
    now = datetime.utcnow()
    stocked_materials = [material for material in materials if _num(material.current_stock) > 0]
    stale_rows = []
    age_buckets = [
        {"age_range": "0-30天", "min": 0, "max": 30, "value": 0.0},
        {"age_range": "31-90天", "min": 31, "max": 90, "value": 0.0},
        {"age_range": "91-180天", "min": 91, "max": 180, "value": 0.0},
        {"age_range": "180天以上", "min": 181, "max": None, "value": 0.0},
    ]

    for material in stocked_materials:
        days = _stale_days(material, now)
        value = _inventory_value(material)
        for bucket in age_buckets:
            if days >= bucket["min"] and (bucket["max"] is None or days <= bucket["max"]):
                bucket["value"] += value
                break
        if days >= threshold_days:
            row = _material_row(material)
            row["stale_days"] = days
            last_activity = _last_activity(material)
            row["last_activity"] = last_activity.isoformat() if last_activity else None
            stale_rows.append(row)

    stale_rows.sort(key=lambda item: item["inventory_value"], reverse=True)
    total_value_with_stock = sum(_inventory_value(material) for material in stocked_materials)
    stale_value = sum(row["inventory_value"] for row in stale_rows)

    return ResponseModel(
        data={
            "summary": {
                "stale_count": len(stale_rows),
                "stale_value": _round(stale_value),
                "total_value_with_stock": _round(total_value_with_stock),
            },
            "age_distribution": [
                {"age_range": bucket["age_range"], "value": _round(bucket["value"])}
                for bucket in age_buckets
            ],
            "stale_materials": stale_rows[:50],
        }
    )


@router.get("/safety-stock-compliance", response_model=ResponseModel)
def get_safety_stock_compliance(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> ResponseModel:
    materials = _load_materials(db)
    out_of_stock = [
        _material_row(material)
        for material in materials
        if _num(material.current_stock) <= 0
    ]
    warning = [
        _material_row(material)
        for material in materials
        if 0 < _num(material.current_stock) < _num(material.safety_stock)
    ]
    compliant_count = max(len(materials) - len(out_of_stock) - len(warning), 0)
    compliant_rate = compliant_count / len(materials) * 100 if materials else 100

    return ResponseModel(
        data={
            "summary": {
                "total_materials": len(materials),
                "compliant_rate": _round(compliant_rate),
                "warning": len(warning),
                "out_of_stock": len(out_of_stock),
            },
            "warning_materials": warning[:50],
            "out_of_stock_materials": out_of_stock[:50],
        }
    )


@router.get("/abc-analysis", response_model=ResponseModel)
def get_abc_analysis(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> ResponseModel:
    materials = _load_materials(db)
    rows = sorted(
        [_material_row(material) for material in materials],
        key=lambda item: item["inventory_value"],
        reverse=True,
    )
    total_value = sum(row["inventory_value"] for row in rows)
    total_count = len(rows)
    summary = {
        "A": {"count": 0, "amount": 0.0, "amount_percent": 0, "count_percent": 0},
        "B": {"count": 0, "amount": 0.0, "amount_percent": 0, "count_percent": 0},
        "C": {"count": 0, "amount": 0.0, "amount_percent": 0, "count_percent": 0},
    }

    cumulative = 0.0
    classified_rows = []
    for row in rows:
        cumulative += row["inventory_value"]
        cumulative_percent = cumulative / total_value * 100 if total_value > 0 else 100
        if cumulative_percent <= 70:
            abc_class = "A"
        elif cumulative_percent <= 90:
            abc_class = "B"
        else:
            abc_class = "C"
        row["abc_class"] = abc_class
        classified_rows.append(row)
        summary[abc_class]["count"] += 1
        summary[abc_class]["amount"] += row["inventory_value"]

    for item in summary.values():
        item["amount"] = _round(item["amount"])
        item["amount_percent"] = _round(item["amount"] / total_value * 100) if total_value > 0 else 0
        item["count_percent"] = _round(item["count"] / total_count * 100) if total_count else 0

    return ResponseModel(
        data={
            "total_materials": total_count,
            "abc_summary": summary,
            "materials": classified_rows[:100],
        }
    )


@router.get("/cost-occupancy", response_model=ResponseModel)
def get_cost_occupancy(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> ResponseModel:
    materials = _load_materials(db)
    category_occupancy = _category_breakdown(materials)
    top_materials = sorted(
        [_material_row(material) for material in materials],
        key=lambda item: item["inventory_value"],
        reverse=True,
    )[:20]
    total_value = sum(_inventory_value(material) for material in materials)

    return ResponseModel(
        data={
            "summary": {
                "total_inventory_value": _round(total_value),
                "total_categories": len(category_occupancy),
            },
            "category_occupancy": category_occupancy,
            "top_materials": top_materials,
        }
    )


__all__ = ["router"]
