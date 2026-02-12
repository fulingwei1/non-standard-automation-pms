# -*- coding: utf-8 -*-
"""
齐套分析服务
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.assembly_kit import AssemblyStage, BomItemAssemblyAttrs
from app.models.material import BomHeader, BomItem, Material
from app.models.project import Machine, Project

logger = logging.getLogger(__name__)


def validate_analysis_inputs(
    db: Session,
    project_id: int,
    bom_id: int,
    machine_id: Optional[int] = None
) -> Tuple[Project, BomHeader, Optional[Machine]]:
    """
    验证齐套分析输入参数

    Returns:
        Tuple[Project, BomHeader, Optional[Machine]]: 验证后的项目、BOM和机台对象
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证BOM
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 验证机台(可选)
    machine = None
    if machine_id:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="机台不存在")

    return project, bom, machine


def initialize_stage_results(
    stages: List[AssemblyStage]
) -> Dict[str, Dict[str, Any]]:
    """
    初始化阶段统计结果

    Returns:
        dict: 阶段代码到统计数据的映射
    """
    stage_results = {}
    for stage in stages:
        stage_results[stage.stage_code] = {
            "total": 0,
            "fulfilled": 0,
            "blocking_total": 0,
            "blocking_fulfilled": 0,
            "stage": stage
        }
    return stage_results


def analyze_bom_item(
    db: Session,
    bom_item: BomItem,
    check_date: date,
    stage_map: Dict[str, AssemblyStage],
    stage_results: Dict[str, Dict[str, Any]],
    calculate_available_qty_func
) -> Optional[Dict[str, Any]]:
    """
    分析单个BOM物料项

    Returns:
        Optional[Dict]: 缺料明细（如果有缺料），否则返回None
    """
    material = db.query(Material).filter(Material.id == bom_item.material_id).first()
    if not material:
        return None

    # 获取装配属性
    attr = db.query(BomItemAssemblyAttrs).filter(
        BomItemAssemblyAttrs.bom_item_id == bom_item.id
    ).first()

    if attr:
        stage_code = attr.assembly_stage
        is_blocking = attr.is_blocking
    else:
        # 默认分配到机械模组阶段
        stage_code = "MECH"
        is_blocking = True

    if stage_code not in stage_results:
        stage_code = "MECH"

    # 计算可用数量
    required_qty = bom_item.quantity or Decimal(1)
    stock_qty, allocated_qty, in_transit_qty, available_qty = calculate_available_qty_func(
        db, material.id, check_date
    )

    shortage_qty = max(Decimal(0), required_qty - available_qty)
    is_fulfilled = shortage_qty == 0
    shortage_rate = (shortage_qty / required_qty * 100) if required_qty > 0 else Decimal(0)

    # 更新阶段统计
    stage_results[stage_code]["total"] += 1
    if is_fulfilled:
        stage_results[stage_code]["fulfilled"] += 1

    if is_blocking:
        stage_results[stage_code]["blocking_total"] += 1
        if is_fulfilled:
            stage_results[stage_code]["blocking_fulfilled"] += 1

    # 记录缺料明细
    if shortage_qty > 0:
        # 计算距需求日期的天数
        days_to_required = 7  # 默认7天
        if bom_item.required_date:
            days_to_required = (bom_item.required_date - check_date).days

        # 导入 determine_alert_level 函数
        from app.api.v1.endpoints.assembly_kit.kit_analysis.utils import determine_alert_level
        alert_level = determine_alert_level(db, is_blocking, shortage_rate, days_to_required)

        # 获取预计到货日期（从采购订单）
        expected_arrival = get_expected_arrival_date(db, material.id)

        return {
            "bom_item_id": bom_item.id,
            "material_id": material.id,
            "material_code": material.material_code,
            "material_name": material.material_name,
            "assembly_stage": stage_code,
            "is_blocking": is_blocking,
            "required_qty": required_qty,
            "stock_qty": stock_qty,
            "allocated_qty": allocated_qty,
            "in_transit_qty": in_transit_qty,
            "available_qty": available_qty,
            "shortage_qty": shortage_qty,
            "shortage_rate": shortage_rate,
            "alert_level": alert_level,
            "expected_arrival": expected_arrival,
            "required_date": bom_item.required_date
        }

    return None


def get_expected_arrival_date(
    db: Session,
    material_id: int
) -> Optional[date]:
    """
    获取物料的预计到货日期（从采购订单）

    Returns:
        Optional[date]: 预计到货日期
    """
    try:
        from app.models import PurchaseOrder, PurchaseOrderItem
        po_item = db.query(PurchaseOrderItem).join(
            PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id
        ).filter(
            PurchaseOrderItem.material_id == material_id,
            PurchaseOrder.status.in_(['approved', 'partial_received']),
            PurchaseOrder.promised_date.isnot(None)
        ).order_by(PurchaseOrder.promised_date.asc()).first()

        if po_item and po_item.order and po_item.order.promised_date:
            return po_item.order.promised_date
    except Exception:
        logger.debug("获取物料预计到货日期失败，已忽略", exc_info=True)

    return None


def calculate_stage_kit_rates(
    stages: List[AssemblyStage],
    stage_results: Dict[str, Dict[str, Any]],
    shortage_details: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], bool, Optional[str], Optional[str], Dict[str, int], List[Dict[str, Any]]]:
    """
    计算各阶段齐套率和是否可开始

    Returns:
        Tuple: (阶段齐套率列表, 是否可开始, 第一个阻塞阶段, 当前可工作阶段, 整体统计, 所有阻塞物料)
    """
    stage_kit_rates = []
    can_proceed = True
    first_blocked_stage = None
    current_workable_stage = None
    overall_total = 0
    overall_fulfilled = 0
    blocking_total = 0
    blocking_fulfilled = 0
    all_blocking_items = []

    for stage in stages:
        stats = stage_results.get(stage.stage_code, {
            "total": 0,
            "fulfilled": 0,
            "blocking_total": 0,
            "blocking_fulfilled": 0
        })

        total = stats["total"]
        fulfilled = stats["fulfilled"]
        b_total = stats["blocking_total"]
        b_fulfilled = stats["blocking_fulfilled"]

        overall_total += total
        overall_fulfilled += fulfilled
        blocking_total += b_total
        blocking_fulfilled += b_fulfilled

        kit_rate = Decimal(fulfilled / total * 100) if total > 0 else Decimal(100)
        blocking_rate = Decimal(b_fulfilled / b_total * 100) if b_total > 0 else Decimal(100)

        # 判断是否可开始: 前序阶段都可开始 && 当前阶段阻塞齐套率100%
        stage_can_start = can_proceed and (blocking_rate == 100)

        if stage_can_start:
            current_workable_stage = stage.stage_code

        if not stage_can_start and can_proceed:
            first_blocked_stage = stage.stage_code
            can_proceed = False
            # 收集该阶段的阻塞物料
            for detail in shortage_details:
                if detail.get("assembly_stage") == stage.stage_code and detail.get("is_blocking"):
                    all_blocking_items.append(detail)

        stage_kit_rates.append({
            "stage_code": stage.stage_code,
            "stage_name": stage.stage_name,
            "stage_order": stage.stage_order,
            "total_items": total,
            "fulfilled_items": fulfilled,
            "kit_rate": round(kit_rate, 2),
            "blocking_total": b_total,
            "blocking_fulfilled": b_fulfilled,
            "blocking_rate": round(blocking_rate, 2),
            "can_start": stage_can_start,
            "color_code": stage.color_code
        })

    overall_stats = {
        "total": overall_total,
        "fulfilled": overall_fulfilled,
        "blocking_total": blocking_total,
        "blocking_fulfilled": blocking_fulfilled
    }

    return stage_kit_rates, can_proceed, first_blocked_stage, current_workable_stage, overall_stats, all_blocking_items
