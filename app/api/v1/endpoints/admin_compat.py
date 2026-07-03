# -*- coding: utf-8 -*-
"""Administrative compatibility routes used by legacy admin pages."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import ApiPermission, Role, RoleApiPermission, User

router = APIRouter()


def _supplies() -> List[Dict[str, Any]]:
    return [
        {
            "id": 1,
            "name": "A4 复印纸",
            "category": "办公耗材",
            "specification": "80g 500张/包",
            "unit": "包",
            "quantity": 48,
            "currentStock": 48,
            "minStock": 20,
            "unitPrice": 28,
            "totalValue": 1344,
            "status": "normal",
            "supplier": "综合办公供应商",
            "lastPurchaseDate": "2026-06-05",
            "lastPurchase": "2026-06-05",
        },
        {
            "id": 2,
            "name": "签字笔",
            "category": "办公文具",
            "specification": "0.5mm 黑色",
            "unit": "盒",
            "quantity": 9,
            "currentStock": 9,
            "minStock": 12,
            "unitPrice": 36,
            "totalValue": 324,
            "status": "low",
            "supplier": "文具集采",
            "lastPurchaseDate": "2026-06-10",
            "lastPurchase": "2026-06-10",
        },
        {
            "id": 3,
            "name": "打印机硒鼓",
            "category": "办公耗材",
            "specification": "HP 兼容",
            "unit": "个",
            "quantity": 7,
            "currentStock": 7,
            "minStock": 5,
            "unitPrice": 260,
            "totalValue": 1820,
            "status": "normal",
            "supplier": "IT 备件供应商",
            "lastPurchaseDate": "2026-05-28",
            "lastPurchase": "2026-05-28",
        },
    ]


def _vehicles() -> List[Dict[str, Any]]:
    today = date.today()
    return [
        {
            "id": 1,
            "plateNumber": "粤B KJB01",
            "brand": "比亚迪",
            "model": "宋PLUS",
            "status": "in_use",
            "mileage": 42680,
            "purchaseDate": "2024-03-18",
            "driver": "张工",
            "purpose": "客户现场联调",
            "destination": "深圳宝安",
            "startTime": "08:30",
            "endTime": "18:00",
        },
        {
            "id": 2,
            "plateNumber": "粤B KJB02",
            "brand": "广汽传祺",
            "model": "M8",
            "status": "available",
            "mileage": 31820,
            "purchaseDate": "2023-11-06",
            "driver": "",
            "nextMaintenance": (today + timedelta(days=24)).isoformat(),
            "nextMaintenanceMileage": 35000,
        },
        {
            "id": 3,
            "plateNumber": "粤B KJB03",
            "brand": "丰田",
            "model": "海狮",
            "status": "maintenance",
            "mileage": 68120,
            "purchaseDate": "2022-08-21",
            "maintenanceReason": "常规保养",
            "returnDate": (today + timedelta(days=2)).isoformat(),
        },
    ]


def _assets() -> List[Dict[str, Any]]:
    return [
        {
            "id": 1,
            "assetNo": "FA-ATE-001",
            "name": "研发测试服务器",
            "category": "办公设备",
            "department": "电气软件部",
            "owner": "软件组",
            "purchaseDate": "2024-09-12",
            "originalValue": 86000,
            "currentValue": 64500,
            "depreciation": 21500,
            "status": "in_use",
            "location": "研发区机柜",
        },
        {
            "id": 2,
            "assetNo": "FA-OFF-018",
            "name": "会议室投影系统",
            "category": "办公设备",
            "department": "综合管理部",
            "owner": "行政",
            "purchaseDate": "2023-04-20",
            "originalValue": 32000,
            "currentValue": 18800,
            "depreciation": 13200,
            "status": "maintenance",
            "location": "三楼会议室",
        },
        {
            "id": 3,
            "assetNo": "FA-FUR-026",
            "name": "工程师工位桌椅",
            "category": "办公家具",
            "department": "机械设计部",
            "owner": "机械组",
            "purchaseDate": "2025-01-08",
            "originalValue": 14800,
            "currentValue": 12600,
            "depreciation": 2200,
            "status": "in_use",
            "location": "二楼设计区",
        },
    ]


def _expense_statistics(period: str = "month") -> Dict[str, Any]:
    scale = {"month": 1, "quarter": 3, "year": 12}.get(period, 1)
    monthly_budget = 80000 * scale
    monthly_spent = 52600 * scale
    remaining_budget = max(monthly_budget - monthly_spent, 0)
    budget_utilization = round(monthly_spent / monthly_budget * 100, 1) if monthly_budget else 0
    return {
        "monthlyBudget": monthly_budget,
        "monthlySpent": monthly_spent,
        "remainingBudget": remaining_budget,
        "budgetUtilization": budget_utilization,
        "trend": -4.8,
        "lastMonthSpent": 55240 * scale,
        "categories": [
            {"category": "办公用品", "amount": 13800 * scale},
            {"category": "车辆费用", "amount": 16400 * scale},
            {"category": "物业及能耗", "amount": 18800 * scale},
            {"category": "差旅接待", "amount": 3600 * scale},
        ],
        "monthlyTrend": [
            {"month": "2026-03", "amount": 51200},
            {"month": "2026-04", "amount": 54800},
            {"month": "2026-05", "amount": 55240},
            {"month": "2026-06", "amount": 52600},
        ],
    }


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    total_roles = db.query(Role).count()
    active_roles = db.query(Role).filter(Role.is_active.is_(True)).count()
    total_permissions = db.query(ApiPermission).count()
    assigned_permissions = db.query(RoleApiPermission.permission_id).distinct().count()
    data = {
        "totalUsers": total_users,
        "activeUsers": active_users,
        "inactiveUsers": max(total_users - active_users, 0),
        "newUsersThisMonth": 0,
        "usersWithRoles": 0,
        "usersWithoutRoles": total_users,
        "totalRoles": total_roles,
        "systemRoles": db.query(Role).filter(Role.is_system.is_(True)).count(),
        "customRoles": db.query(Role).filter(Role.is_system.is_(False)).count(),
        "activeRoles": active_roles,
        "inactiveRoles": max(total_roles - active_roles, 0),
        "totalPermissions": total_permissions,
        "assignedPermissions": assigned_permissions,
        "unassignedPermissions": max(total_permissions - assigned_permissions, 0),
        "systemUptime": 99.9,
        "databaseSize": 0,
        "storageUsed": 0,
        "apiResponseTime": 0,
        "errorRate": 0,
        "loginCountToday": 0,
        "loginCountThisWeek": 0,
        "lastBackup": None,
        "auditLogsToday": 0,
        "auditLogsThisWeek": 0,
    }
    return {"code": 200, "message": "success", "data": data}


@router.get("/supplies")
def list_supplies(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = _supplies()
    return {"items": items, "total": len(items)}


@router.get("/supplies/inventory")
def get_supplies_inventory(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = _supplies()
    return {
        "items": items,
        "totalValue": sum(item["totalValue"] for item in items),
        "lowStockItems": [item for item in items if item["status"] == "low"],
    }


@router.get("/supplies/{supply_id}")
def get_supply(
    supply_id: int,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    item = next((item for item in _supplies() if item["id"] == supply_id), _supplies()[0])
    return item


@router.get("/expenses/statistics")
def get_expense_statistics(
    period: str = "month",
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    return {"code": 200, "message": "success", "data": _expense_statistics(period)}


@router.get("/vehicles")
def list_vehicles(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = _vehicles()
    return {"items": items, "total": len(items)}


@router.get("/vehicles/available")
def list_available_vehicles(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = [item for item in _vehicles() if item["status"] == "available"]
    return {"items": items, "total": len(items)}


@router.get("/vehicles/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    item = next((item for item in _vehicles() if item["id"] == vehicle_id), _vehicles()[0])
    return item


@router.get("/assets")
def list_assets(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = _assets()
    return {"items": items, "total": len(items)}


@router.get("/assets/statistics")
def get_asset_statistics(
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    items = _assets()
    return {
        "total": len(items),
        "totalValue": sum(item["currentValue"] for item in items),
        "totalDepreciation": sum(item["depreciation"] for item in items),
        "maintenance": len([item for item in items if item["status"] == "maintenance"]),
    }


@router.get("/assets/{asset_id}")
def get_asset(
    asset_id: int,
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    item = next((item for item in _assets() if item["id"] == asset_id), _assets()[0])
    return item
