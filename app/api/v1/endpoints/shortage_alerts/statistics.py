# -*- coding: utf-8 -*-
"""
统计仪表板 - 自动生成
从 shortage_alerts.py 拆分
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import BomItem, Material, MaterialShortage
from app.models.production import WorkOrder
from app.models.project import Machine, Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.shortage import (
    ArrivalFollowUp,
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageReport,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.shortage import (
    ArrivalFollowUpCreate,
    MaterialArrivalListResponse,
    MaterialArrivalResponse,
    MaterialSubstitutionCreate,
    MaterialSubstitutionListResponse,
    MaterialSubstitutionResponse,
    MaterialTransferCreate,
    MaterialTransferListResponse,
    MaterialTransferResponse,
    ShortageReportCreate,
    ShortageReportListResponse,
    ShortageReportResponse,
)

router = APIRouter(tags=["statistics"])

# 共 5 个路由

@router.get("/statistics/overview")
def get_shortage_alerts_statistics(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    获取缺料预警统计（按级别/类型）
    """
    query = db.query(MaterialShortage)

    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)

    # 按状态统计
    status_stats = {}
    status_counts = (
        db.query(MaterialShortage.status, func.count(MaterialShortage.id))
        .filter(MaterialShortage.project_id == project_id if project_id else True)
        .group_by(MaterialShortage.status)
        .all()
    )
    for status, count in status_counts:
        status_stats[status] = count

    # 按预警级别统计
    level_stats = {}
    level_counts = (
        db.query(MaterialShortage.alert_level, func.count(MaterialShortage.id))
        .filter(MaterialShortage.project_id == project_id if project_id else True)
        .group_by(MaterialShortage.alert_level)
        .all()
    )
    for level, count in level_counts:
        level_stats[level] = count

    # 总数
    total = query.count()

    # 未解决数量
    unresolved = query.filter(MaterialShortage.status != "RESOLVED").count()

    return {
        "total": total,
        "unresolved": unresolved,
        "resolved": total - unresolved,
        "by_status": status_stats,
        "by_level": level_stats,
    }


@router.get("/dashboard")
def get_shortage_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    缺料看板
    """
    query = db.query(MaterialShortage)

    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)

    # 获取所有缺料预警
    alerts = query.filter(MaterialShortage.status != "RESOLVED").all()

    # 按项目分组统计
    project_stats = {}
    for alert in alerts:
        if alert.project_id not in project_stats:
            project = db.query(Project).filter(Project.id == alert.project_id).first()
            project_stats[alert.project_id] = {
                "project_id": alert.project_id,
                "project_name": project.project_name if project else None,
                "total_shortages": 0,
                "critical_shortages": 0,
                "high_shortages": 0,
                "warning_shortages": 0,
                "total_shortage_qty": Decimal("0"),
                "materials": []
            }

        stats = project_stats[alert.project_id]
        stats["total_shortages"] += 1
        stats["total_shortage_qty"] += alert.shortage_qty or Decimal("0")

        if alert.alert_level == "CRITICAL":
            stats["critical_shortages"] += 1
        elif alert.alert_level == "HIGH":
            stats["high_shortages"] += 1
        else:
            stats["warning_shortages"] += 1

        # 添加物料信息
        stats["materials"].append({
            "material_id": alert.material_id,
            "material_code": alert.material_code,
            "material_name": alert.material_name,
            "shortage_qty": float(alert.shortage_qty),
            "required_date": alert.required_date.isoformat() if alert.required_date else None,
            "alert_level": alert.alert_level,
            "status": alert.status
        })

    # 转换为列表
    project_list = []
    for project_id, stats in project_stats.items():
        project_list.append({
            **stats,
            "total_shortage_qty": float(stats["total_shortage_qty"])
        })

    # 全局统计
    total_projects = len(project_list)
    total_shortages = len(alerts)
    critical_count = len([a for a in alerts if a.alert_level == "CRITICAL"])
    high_count = len([a for a in alerts if a.alert_level == "HIGH"])
    warning_count = len([a for a in alerts if a.alert_level == "WARNING"])

    return {
        "summary": {
            "total_projects": total_projects,
            "total_shortages": total_shortages,
            "critical_count": critical_count,
            "high_count": high_count,
            "warning_count": warning_count
        },
        "projects": project_list
    }


@router.get("/supplier-delivery")
def get_supplier_delivery_analysis(
    *,
    db: Session = Depends(deps.get_db),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    供应商交期分析
    """
    from app.models.material import Supplier
    from app.models.purchase import PurchaseOrder, PurchaseOrderItem

    query = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED", "RECEIVED"]))

    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    if start_date:
        query = query.filter(PurchaseOrder.order_date >= start_date)

    if end_date:
        query = query.filter(PurchaseOrder.order_date <= end_date)

    orders = query.all()

    supplier_stats = {}
    for order in orders:
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        supplier_name = supplier.supplier_name if supplier else None

        if order.supplier_id not in supplier_stats:
            supplier_stats[order.supplier_id] = {
                "supplier_id": order.supplier_id,
                "supplier_name": supplier_name,
                "total_orders": 0,
                "on_time_orders": 0,
                "delayed_orders": 0,
                "total_items": 0,
                "on_time_items": 0,
                "delayed_items": 0,
                "avg_delay_days": 0
            }

        stats = supplier_stats[order.supplier_id]
        stats["total_orders"] += 1

        # 检查订单是否延迟
        if order.required_date and order.actual_receipt_date:
            if order.actual_receipt_date > order.required_date:
                stats["delayed_orders"] += 1
                delay_days = (order.actual_receipt_date - order.required_date).days
                stats["avg_delay_days"] = (stats["avg_delay_days"] * (stats["delayed_orders"] - 1) + delay_days) / stats["delayed_orders"]
            else:
                stats["on_time_orders"] += 1

        # 统计订单明细
        items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.order_id == order.id).all()
        for item in items:
            stats["total_items"] += 1
            if item.required_date and item.received_date:
                if item.received_date <= item.required_date:
                    stats["on_time_items"] += 1
                else:
                    stats["delayed_items"] += 1

    # 转换为列表
    supplier_list = []
    for supplier_id, stats in supplier_stats.items():
        on_time_rate = (stats["on_time_orders"] / stats["total_orders"] * 100) if stats["total_orders"] > 0 else 0
        supplier_list.append({
            **stats,
            "on_time_rate": round(on_time_rate, 2)
        })

    return {
        "suppliers": supplier_list,
        "total_suppliers": len(supplier_list)
    }


@router.get("/daily-report")
def get_shortage_daily_report(
    *,
    db: Session = Depends(deps.get_db),
    report_date: Optional[date] = Query(None, description="报告日期（默认今天）"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    缺料日报
    """
    if not report_date:
        report_date = datetime.now().date()

    # 获取当天的缺料预警
    alerts = db.query(MaterialShortage).filter(
        func.date(MaterialShortage.created_at) == report_date
    ).all()

    # 按项目统计
    project_stats = {}
    for alert in alerts:
        if alert.project_id not in project_stats:
            project = db.query(Project).filter(Project.id == alert.project_id).first()
            project_stats[alert.project_id] = {
                "project_id": alert.project_id,
                "project_name": project.project_name if project else None,
                "shortage_count": 0,
                "total_shortage_qty": Decimal("0"),
                "critical_count": 0,
                "materials": []
            }

        stats = project_stats[alert.project_id]
        stats["shortage_count"] += 1
        stats["total_shortage_qty"] += alert.shortage_qty or Decimal("0")

        if alert.alert_level == "CRITICAL":
            stats["critical_count"] += 1

        stats["materials"].append({
            "material_code": alert.material_code,
            "material_name": alert.material_name,
            "shortage_qty": float(alert.shortage_qty),
            "alert_level": alert.alert_level
        })

    # 转换为列表
    project_list = []
    for project_id, stats in project_stats.items():
        project_list.append({
            **stats,
            "total_shortage_qty": float(stats["total_shortage_qty"])
        })

    return {
        "report_date": report_date.isoformat(),
        "total_shortages": len(alerts),
        "total_projects": len(project_list),
        "projects": project_list
    }


@router.get("/cause-analysis")
def get_shortage_cause_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    缺料原因分析
    """
    query = db.query(MaterialShortage)

    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)

    if start_date:
        query = query.filter(func.date(MaterialShortage.created_at) >= start_date)

    if end_date:
        query = query.filter(func.date(MaterialShortage.created_at) <= end_date)

    alerts = query.all()

    # 分析缺料原因（根据解决方案字段）
    cause_stats = {
        "purchase_delay": 0,  # 采购延迟
        "supplier_delay": 0,  # 供应商延迟
        "inventory_shortage": 0,  # 库存不足
        "planning_error": 0,  # 计划错误
        "other": 0  # 其他
    }

    for alert in alerts:
        solution = alert.solution or ""
        solution_lower = solution.lower()

        if "采购" in solution or "purchase" in solution_lower:
            cause_stats["purchase_delay"] += 1
        elif "供应商" in solution or "supplier" in solution_lower:
            cause_stats["supplier_delay"] += 1
        elif "库存" in solution or "inventory" in solution_lower:
            cause_stats["inventory_shortage"] += 1
        elif "计划" in solution or "planning" in solution_lower:
            cause_stats["planning_error"] += 1
        else:
            cause_stats["other"] += 1

    total = len(alerts)

    return {
        "total_shortages": total,
        "cause_distribution": cause_stats,
        "cause_percentage": {
            "purchase_delay": round((cause_stats["purchase_delay"] / total * 100) if total > 0 else 0, 2),
            "supplier_delay": round((cause_stats["supplier_delay"] / total * 100) if total > 0 else 0, 2),
            "inventory_shortage": round((cause_stats["inventory_shortage"] / total * 100) if total > 0 else 0, 2),
            "planning_error": round((cause_stats["planning_error"] / total * 100) if total > 0 else 0, 2),
            "other": round((cause_stats["other"] / total * 100) if total > 0 else 0, 2)
        }
    }


