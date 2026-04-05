# -*- coding: utf-8 -*-
"""
物料进度可视化服务
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.material import BomHeader, BomItem, MaterialShortage
from app.models.material_progress_subscription import MaterialProgressSubscription
from app.models.project import Project
from app.models.project.team import ProjectMember
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.user import User
from app.models.vendor import Vendor


def _check_project_access(db: Session, project_id: int, user: User) -> Project:
    """校验项目存在且用户有权限访问"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在: {project_id}",
        )
    # 超级管理员跳过成员检查
    if user.is_superuser:
        return project
    # 项目经理可直接访问
    if project.pm_id == user.id:
        return project
    # 检查是否为项目成员
    is_member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
            ProjectMember.is_active == True,
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该项目成员，无权查看物料进度",
        )
    return project


def get_material_progress_overview(
    db: Session, project_id: int, user: User
) -> Dict[str, Any]:
    """获取项目物料进度总览"""
    project = _check_project_access(db, project_id, user)

    # 获取该项目所有已发布 BOM 的物料行
    bom_items = (
        db.query(BomItem)
        .join(BomHeader, BomItem.bom_id == BomHeader.id)
        .filter(
            BomHeader.project_id == project_id,
            BomHeader.status.in_(["RELEASED", "APPROVED"]),
        )
        .all()
    )

    total = len(bom_items)
    kitted = sum(1 for i in bom_items if i.kitting_status == "COMPLETE")
    in_progress = sum(1 for i in bom_items if i.kitting_status == "IN_PROGRESS")
    shortage = sum(1 for i in bom_items if i.kitting_status == "SHORTAGE")
    kitting_rate = Decimal(str(round(kitted / total * 100, 2))) if total > 0 else Decimal("0")

    # 关键物料
    key_items = [i for i in bom_items if i.is_key_item]
    key_materials = []
    for item in key_items:
        qty = float(item.quantity or 0)
        recv = float(item.received_qty or 0)
        short = max(0, qty - recv)
        key_materials.append({
            "material_id": item.material_id,
            "material_code": item.material_code,
            "material_name": item.material_name,
            "specification": item.specification,
            "required_qty": item.quantity,
            "received_qty": item.received_qty or Decimal("0"),
            "shortage_qty": Decimal(str(short)),
            "kitting_status": item.kitting_status or "PENDING",
            "expected_arrival_date": item.expected_arrival_date,
            "impact_description": f"关键物料，缺料{short:.0f}{item.unit or '件'}" if short > 0 else None,
        })

    # 近 30 天齐套率趋势（基于 BomItem 实际到货日期回推）
    today = date.today()
    trend = []
    for day_offset in range(29, -1, -1):
        d = today - timedelta(days=day_offset)
        # 截至该日已齐套的行数
        kitted_by_date = sum(
            1 for i in bom_items
            if i.actual_arrival_date and i.actual_arrival_date <= d
        )
        rate = Decimal(str(round(kitted_by_date / total * 100, 2))) if total > 0 else Decimal("0")
        trend.append({"date": d, "kitting_rate": rate})

    # 预计齐套日期：取所有未齐套物料中最晚的 expected_arrival_date
    pending_dates = [
        i.expected_arrival_date
        for i in bom_items
        if i.kitting_status != "COMPLETE" and i.expected_arrival_date
    ]
    estimated_kitting_date = max(pending_dates) if pending_dates else None

    return {
        "project_id": project.id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "total_bom_items": total,
        "kitted_items": kitted,
        "in_progress_items": in_progress,
        "shortage_items": shortage,
        "kitting_rate": kitting_rate,
        "material_status": project.material_status,
        "key_materials": key_materials,
        "kitting_trend": trend,
        "estimated_kitting_date": estimated_kitting_date,
    }


def get_bom_progress(db: Session, project_id: int, user: User) -> Dict[str, Any]:
    """获取 BOM 物料明细进度"""
    _check_project_access(db, project_id, user)

    bom_headers = (
        db.query(BomHeader)
        .filter(
            BomHeader.project_id == project_id,
            BomHeader.status.in_(["RELEASED", "APPROVED", "DRAFT"]),
        )
        .all()
    )

    boms = []
    for bom in bom_headers:
        items = db.query(BomItem).filter(BomItem.bom_id == bom.id).all()
        total = len(items)
        kitted = sum(1 for i in items if i.kitting_status == "COMPLETE")
        rate = Decimal(str(round(kitted / total * 100, 2))) if total > 0 else Decimal("0")

        # 获取机台名称
        machine_name = None
        if bom.machine:
            machine_name = getattr(bom.machine, "machine_name", None) or getattr(bom.machine, "name", None)

        item_list = []
        for item in items:
            qty = float(item.quantity or 0)
            purchased = float(item.purchased_qty or 0)
            received = float(item.received_qty or 0)
            in_transit = max(0, purchased - received)
            short = max(0, qty - received)

            # 查询供应商名称和承诺交期
            supplier_name = None
            promised_date = None
            if item.supplier_id:
                vendor = db.query(Vendor).filter(Vendor.id == item.supplier_id).first()
                if vendor:
                    supplier_name = vendor.supplier_name

                # 查找对应 PO item 的承诺交期
                po_item = (
                    db.query(PurchaseOrderItem)
                    .filter(PurchaseOrderItem.bom_item_id == item.id)
                    .order_by(PurchaseOrderItem.id.desc())
                    .first()
                )
                if po_item:
                    promised_date = po_item.promised_date

            item_list.append({
                "bom_item_id": item.id,
                "item_no": item.item_no,
                "material_id": item.material_id,
                "material_code": item.material_code,
                "material_name": item.material_name,
                "specification": item.specification,
                "unit": item.unit or "件",
                "required_qty": item.quantity,
                "purchased_qty": item.purchased_qty or Decimal("0"),
                "in_transit_qty": Decimal(str(in_transit)),
                "received_qty": item.received_qty or Decimal("0"),
                "shortage_qty": Decimal(str(short)),
                "kitting_status": item.kitting_status or "PENDING",
                "is_key_item": item.is_key_item or False,
                "supplier_name": supplier_name,
                "promised_date": promised_date,
                "expected_arrival_date": item.expected_arrival_date,
                "actual_arrival_date": item.actual_arrival_date,
            })

        boms.append({
            "bom_id": bom.id,
            "bom_no": bom.bom_no,
            "bom_name": bom.bom_name,
            "machine_name": machine_name,
            "status": bom.status,
            "total_items": total,
            "kitted_items": kitted,
            "kitting_rate": rate,
            "items": item_list,
        })

    return {
        "project_id": project_id,
        "boms": boms,
        "total_boms": len(boms),
    }


def get_shortage_tracker(db: Session, project_id: int, user: User) -> Dict[str, Any]:
    """获取缺料跟踪看板"""
    _check_project_access(db, project_id, user)

    shortages = (
        db.query(MaterialShortage)
        .filter(MaterialShortage.project_id == project_id)
        .all()
    )

    items = []
    for s in shortages:
        # 处理人/指派人名称
        handler_name = None
        if s.handler_id:
            handler = db.query(User).filter(User.id == s.handler_id).first()
            if handler:
                handler_name = handler.display_name or handler.username

        assigned_to_name = None
        if s.assigned_to_id:
            assignee = db.query(User).filter(User.id == s.assigned_to_id).first()
            if assignee:
                assigned_to_name = assignee.display_name or assignee.username

        # 机台名称
        machine_name = None
        if s.machine:
            machine_name = getattr(s.machine, "machine_name", None) or getattr(s.machine, "name", None)

        # 供应商信息（从关联的 PO 获取）
        supplier_name = None
        supplier_promised_date = None
        if s.bom_item_id:
            po_item = (
                db.query(PurchaseOrderItem)
                .join(PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id)
                .filter(PurchaseOrderItem.bom_item_id == s.bom_item_id)
                .order_by(PurchaseOrderItem.id.desc())
                .first()
            )
            if po_item and po_item.order:
                if po_item.order.vendor:
                    supplier_name = po_item.order.vendor.supplier_name
                supplier_promised_date = po_item.promised_date

        # 影响天数
        impact_days = None
        if s.required_date and s.status != "RESOLVED":
            if s.actual_arrival_date:
                delta = (s.actual_arrival_date - s.required_date).days
                impact_days = max(0, delta)
            elif s.expected_arrival_date:
                delta = (s.expected_arrival_date - s.required_date).days
                impact_days = max(0, delta)

        items.append({
            "shortage_id": s.id,
            "material_id": s.material_id,
            "material_code": s.material_code,
            "material_name": s.material_name,
            "specification": None,
            "shortage_qty": s.shortage_qty,
            "required_date": s.required_date,
            "alert_level": s.alert_level or "WARNING",
            "status": s.status or "OPEN",
            "handler_name": handler_name,
            "assigned_to_name": assigned_to_name,
            "solution": s.solution,
            "resolution_method": s.resolution_method,
            "supplier_name": supplier_name,
            "supplier_promised_date": supplier_promised_date,
            "expected_arrival_date": s.actual_arrival_date if s.status == "RESOLVED" else None,
            "impact_days": impact_days,
            "machine_name": machine_name,
        })

    open_count = sum(1 for i in items if i["status"] == "OPEN")
    in_progress_count = sum(1 for i in items if i["status"] in ("IN_PROGRESS", "ACKNOWLEDGED"))
    resolved_count = sum(1 for i in items if i["status"] == "RESOLVED")
    critical_count = sum(1 for i in items if i["alert_level"] == "CRITICAL")
    total_impact = sum(i["impact_days"] or 0 for i in items)

    return {
        "project_id": project_id,
        "total_shortages": len(items),
        "open_count": open_count,
        "in_progress_count": in_progress_count,
        "resolved_count": resolved_count,
        "critical_count": critical_count,
        "total_impact_days": total_impact,
        "items": items,
    }


def subscribe_material_progress(
    db: Session, project_id: int, user: User, data: Dict[str, Any]
) -> MaterialProgressSubscription:
    """订阅/更新物料进度通知"""
    _check_project_access(db, project_id, user)

    # 查找已有订阅
    sub = (
        db.query(MaterialProgressSubscription)
        .filter(
            MaterialProgressSubscription.project_id == project_id,
            MaterialProgressSubscription.user_id == user.id,
        )
        .first()
    )

    if sub:
        # 更新
        sub.notify_kitting_change = data.get("notify_kitting_change", sub.notify_kitting_change)
        sub.notify_key_material_arrival = data.get("notify_key_material_arrival", sub.notify_key_material_arrival)
        sub.notify_shortage_alert = data.get("notify_shortage_alert", sub.notify_shortage_alert)
        sub.kitting_change_threshold = data.get("kitting_change_threshold", sub.kitting_change_threshold)
        sub.is_active = True
    else:
        # 新建
        sub = MaterialProgressSubscription(
            project_id=project_id,
            user_id=user.id,
            notify_kitting_change=data.get("notify_kitting_change", True),
            notify_key_material_arrival=data.get("notify_key_material_arrival", True),
            notify_shortage_alert=data.get("notify_shortage_alert", True),
            kitting_change_threshold=data.get("kitting_change_threshold", Decimal("5")),
        )
        db.add(sub)

    db.commit()
    db.refresh(sub)
    return sub


def unsubscribe_material_progress(
    db: Session, project_id: int, user: User
) -> bool:
    """取消订阅"""
    sub = (
        db.query(MaterialProgressSubscription)
        .filter(
            MaterialProgressSubscription.project_id == project_id,
            MaterialProgressSubscription.user_id == user.id,
        )
        .first()
    )
    if sub:
        sub.is_active = False
        db.commit()
        return True
    return False


def get_subscription(
    db: Session, project_id: int, user: User
) -> Optional[MaterialProgressSubscription]:
    """获取当前订阅状态"""
    return (
        db.query(MaterialProgressSubscription)
        .filter(
            MaterialProgressSubscription.project_id == project_id,
            MaterialProgressSubscription.user_id == user.id,
            MaterialProgressSubscription.is_active == True,
        )
        .first()
    )
