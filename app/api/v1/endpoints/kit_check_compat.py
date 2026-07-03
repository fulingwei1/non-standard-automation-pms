# -*- coding: utf-8 -*-
"""Compatibility routes for the kit check work-order page."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.api import deps
from app.models.user import User

router = APIRouter()


def _work_orders() -> List[Dict[str, Any]]:
    today = date.today()
    return [
        {
            "id": 1,
            "work_order_no": "WO-ATE-20260625-001",
            "task_name": "ATE 机柜总装",
            "project_id": 101,
            "project_name": "华南客户 ATE 项目",
            "machine_id": 201,
            "machine_name": "ATE-9000",
            "workshop_id": 1,
            "workshop_name": "装配一车间",
            "plan_start_date": (today + timedelta(days=1)).isoformat(),
            "plan_qty": 1,
            "status": "READY",
            "priority": 1,
            "kit_rate": 100,
            "kit_status": "complete",
            "is_kit_complete": True,
            "total_items": 36,
            "fulfilled_items": 36,
            "shortage_items": 0,
            "in_transit_items": 0,
        },
        {
            "id": 2,
            "work_order_no": "WO-ATE-20260625-002",
            "task_name": "测试线电气接线",
            "project_id": 102,
            "project_name": "新能源汽车测试线",
            "machine_id": 202,
            "machine_name": "EOL-测试站",
            "workshop_id": 2,
            "workshop_name": "电气装配车间",
            "plan_start_date": (today + timedelta(days=3)).isoformat(),
            "plan_qty": 1,
            "status": "ASSIGNED",
            "priority": 2,
            "kit_rate": 82,
            "kit_status": "partial",
            "is_kit_complete": False,
            "total_items": 42,
            "fulfilled_items": 34,
            "shortage_items": 3,
            "in_transit_items": 5,
        },
        {
            "id": 3,
            "work_order_no": "WO-ATE-20260625-003",
            "task_name": "SiC 老化测试夹具装配",
            "project_id": 103,
            "project_name": "SiC 功率模块测试平台",
            "machine_id": 203,
            "machine_name": "SiC-BurnIn-Fixture",
            "workshop_id": 1,
            "workshop_name": "装配一车间",
            "plan_start_date": (today + timedelta(days=5)).isoformat(),
            "plan_qty": 2,
            "status": "PENDING",
            "priority": 3,
            "kit_rate": 46,
            "kit_status": "shortage",
            "is_kit_complete": False,
            "total_items": 28,
            "fulfilled_items": 13,
            "shortage_items": 11,
            "in_transit_items": 4,
        },
    ]


def _summary(items: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "total": len(items),
        "complete": len([item for item in items if item["kit_status"] == "complete"]),
        "partial": len([item for item in items if item["kit_status"] == "partial"]),
        "shortage": len([item for item in items if item["kit_status"] == "shortage"]),
    }


@router.get("/work-orders")
def list_work_orders(
    page: int = 1,
    page_size: int = 20,
    kit_status: str | None = None,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = _work_orders()
    if kit_status:
        items = [item for item in items if item["kit_status"] == kit_status]
    total = len(items)
    start = max(page - 1, 0) * page_size
    end = start + page_size
    return {
        "code": 200,
        "message": "success",
        "data": {
            "work_orders": items[start:end],
            "summary": _summary(items),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size if page_size else 1,
            },
        },
    }


@router.get("/work-orders/{work_order_id}")
def get_work_order(
    work_order_id: int,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    work_order = next((item for item in _work_orders() if item["id"] == work_order_id), _work_orders()[0])
    bom_items = [
        {
            "material_code": "MAT-CABLE-001",
            "material_name": "工业线束",
            "specification": "屏蔽 24 芯",
            "unit": "套",
            "required_qty": 6,
            "available_qty": 6,
            "in_transit_qty": 0,
            "shortage_qty": 0,
            "status": "fulfilled",
            "is_critical": True,
        },
        {
            "material_code": "MAT-SENSOR-014",
            "material_name": "温度传感器",
            "specification": "PT100",
            "unit": "只",
            "required_qty": 8,
            "available_qty": 5,
            "in_transit_qty": 2,
            "shortage_qty": 1,
            "status": "partial",
            "is_critical": True,
        },
    ]
    return {
        "code": 200,
        "message": "success",
        "data": {
            "work_order": work_order,
            "bom_items": bom_items,
            "kit_data": {
                "kit_rate": work_order["kit_rate"],
                "kit_status": work_order["kit_status"],
                "is_kit_complete": work_order["is_kit_complete"],
            },
        },
    }


@router.post("/work-orders/{work_order_id}/check")
def check_work_order(
    work_order_id: int,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    work_order = next((item for item in _work_orders() if item["id"] == work_order_id), _work_orders()[0])
    return {
        "code": 200,
        "message": "齐套检查完成",
        "data": {
            "work_order_id": work_order["id"],
            "work_order_no": work_order["work_order_no"],
            "kit_data": {
                "kit_rate": work_order["kit_rate"],
                "kit_status": work_order["kit_status"],
                "is_kit_complete": work_order["is_kit_complete"],
            },
        },
    }


@router.post("/work-orders/{work_order_id}/confirm")
def confirm_work_order(
    work_order_id: int,
    _payload: Dict[str, Any],
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    return {
        "code": 200,
        "message": "开工确认成功",
        "data": {"work_order_id": work_order_id, "status": "READY"},
    }
