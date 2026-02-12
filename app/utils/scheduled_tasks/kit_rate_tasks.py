# -*- coding: utf-8 -*-
"""
定时任务 - 齐套率快照
每日凌晨生成所有活跃项目的齐套率快照，支持历史趋势分析
"""
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.assembly_kit import KitRateSnapshot
from app.models.base import get_db_session
from app.models.material import BomHeader
from app.models.project import Machine, Project

logger = logging.getLogger(__name__)


def _calculate_kit_rate_for_bom_items(db: Session, bom_items: list, calculate_by: str = "quantity") -> dict:
    """
    计算 BOM 物料的齐套率

    Args:
        db: 数据库会话
        bom_items: BOM 明细列表
        calculate_by: 计算方式 quantity(数量) 或 amount(金额)

    Returns:
        齐套率计算结果
    """
    if not bom_items:
        return {
            "kit_rate": 0.0,
            "kit_status": "shortage",
            "total_items": 0,
            "fulfilled_items": 0,
            "shortage_items": 0,
            "in_transit_items": 0,
            "total_amount": 0.0,
            "shortage_amount": 0.0,
        }

    total_items = len(bom_items)
    fulfilled_items = 0
    shortage_items = 0
    in_transit_items = 0
    total_amount = Decimal(0)
    shortage_amount = Decimal(0)

    for item in bom_items:
        required_qty = item.quantity or 0
        received_qty = item.received_qty or 0
        unit_price = item.unit_price or 0

        item_amount = required_qty * unit_price
        total_amount += item_amount

        # 获取库存数量
        stock_qty = 0
        if item.material:
            stock_qty = item.material.current_stock or 0

        # 在途数量
        transit_qty = 0
        if item.material_id:
            from app.models.purchase import PurchaseOrderItem
            po_items = (
                db.query(PurchaseOrderItem)
                .filter(PurchaseOrderItem.material_id == item.material_id)
                .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
                .all()
            )
            for po_item in po_items:
                transit_qty += (po_item.quantity or 0) - (po_item.received_qty or 0)

        available_qty = received_qty + stock_qty + transit_qty

        if available_qty >= required_qty:
            fulfilled_items += 1
        else:
            shortage_items += 1
            shortage_amount += (required_qty - available_qty) * unit_price

        if transit_qty > 0:
            in_transit_items += 1

    # 计算齐套率
    if calculate_by == "amount":
        if total_amount > 0:
            kit_rate = float((total_amount - shortage_amount) / total_amount * 100)
        else:
            kit_rate = 0.0
    else:
        if total_items > 0:
            kit_rate = float(fulfilled_items / total_items * 100)
        else:
            kit_rate = 0.0

    # 确定状态
    if kit_rate >= 100:
        kit_status = "complete"
    elif kit_rate >= 80:
        kit_status = "partial"
    else:
        kit_status = "shortage"

    return {
        "kit_rate": round(kit_rate, 2),
        "kit_status": kit_status,
        "total_items": total_items,
        "fulfilled_items": fulfilled_items,
        "shortage_items": shortage_items,
        "in_transit_items": in_transit_items,
        "total_amount": float(total_amount),
        "shortage_amount": float(shortage_amount),
    }


def create_kit_rate_snapshot(
    db: Session,
    project_id: int,
    snapshot_type: str = "DAILY",
    trigger_event: Optional[str] = None,
    machine_id: Optional[int] = None,
) -> Optional[KitRateSnapshot]:
    """
    为项目创建齐套率快照

    Args:
        db: 数据库会话
        project_id: 项目 ID
        snapshot_type: 快照类型 (DAILY/STAGE_CHANGE/MANUAL)
        trigger_event: 触发事件描述
        machine_id: 机台 ID（可选，不填则为项目级快照）

    Returns:
        创建的快照对象
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"项目 {project_id} 不存在，跳过快照")
            return None

        # 如果是 DAILY 快照，检查今天是否已存在
        today = date.today()
        if snapshot_type == "DAILY":
            existing = (
                db.query(KitRateSnapshot)
                .filter(
                    KitRateSnapshot.project_id == project_id,
                    KitRateSnapshot.snapshot_date == today,
                    KitRateSnapshot.snapshot_type == "DAILY",
                )
                .first()
            )
            if existing:
                logger.debug(f"项目 {project_id} 今日已有快照，跳过")
                return existing

        # 获取项目下所有机台的 BOM
        if machine_id:
            machines = db.query(Machine).filter(Machine.id == machine_id).all()
        else:
            machines = db.query(Machine).filter(Machine.project_id == project_id).all()

        all_bom_items = []
        stage_kit_rates = {}

        for machine in machines:
            bom = (
                db.query(BomHeader)
                .filter(BomHeader.machine_id == machine.id)
                .filter(BomHeader.is_latest)
                .first()
            )

            if bom:
                bom_items = bom.items.all()
                all_bom_items.extend(bom_items)

        # 计算项目整体齐套率
        kit_rate_data = _calculate_kit_rate_for_bom_items(db, all_bom_items, "quantity")

        # 创建快照记录
        snapshot = KitRateSnapshot(
            project_id=project_id,
            machine_id=machine_id,
            snapshot_date=today,
            snapshot_time=datetime.now(),
            snapshot_type=snapshot_type,
            trigger_event=trigger_event,
            kit_rate=kit_rate_data["kit_rate"],
            kit_status=kit_rate_data["kit_status"],
            total_items=kit_rate_data["total_items"],
            fulfilled_items=kit_rate_data["fulfilled_items"],
            shortage_items=kit_rate_data["shortage_items"],
            in_transit_items=kit_rate_data["in_transit_items"],
            total_amount=kit_rate_data["total_amount"],
            shortage_amount=kit_rate_data["shortage_amount"],
            project_stage=project.stage,  # 使用stage字段
            project_health=project.health,  # 使用health字段
            stage_kit_rates=json.dumps(stage_kit_rates) if stage_kit_rates else None,
        )

        db.add(snapshot)
        db.flush()

        logger.info(
            f"项目 {project.project_code} 创建 {snapshot_type} 快照: "
            f"齐套率 {kit_rate_data['kit_rate']}%"
        )

        return snapshot

    except Exception as e:
        logger.error(f"创建项目 {project_id} 齐套率快照失败: {e}")
        return None


def daily_kit_rate_snapshot():
    """
    每日齐套率快照定时任务

    在每天凌晨执行，为所有活跃项目生成齐套率快照。
    建议调度时间: 00:30 或 01:00
    """
    logger.info("开始执行每日齐套率快照任务...")

    created_count = 0
    skipped_count = 0
    error_count = 0

    try:
        with get_db_session() as db:
            # 查询所有活跃项目（排除已完结项目，使用stage字段）
            active_projects = (
                db.query(Project)
                .filter(
                    Project.is_active,
                    Project.stage.notin_(["S9", "COMPLETED", "CLOSED"]),
                )
                .all()
            )

            logger.info(f"找到 {len(active_projects)} 个活跃项目需要生成快照")

            for project in active_projects:
                try:
                    snapshot = create_kit_rate_snapshot(
                        db=db,
                        project_id=project.id,
                        snapshot_type="DAILY",
                    )

                    if snapshot:
                        if snapshot.id:  # 新创建的快照
                            created_count += 1
                        else:  # 已存在的快照
                            skipped_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    logger.error(f"项目 {project.project_code} 快照失败: {e}")
                    error_count += 1

            db.commit()

    except Exception as e:
        logger.error(f"每日齐套率快照任务执行失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }

    result = {
        "success": True,
        "created": created_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total_projects": created_count + skipped_count + error_count,
    }

    logger.info(f"每日齐套率快照任务完成: {result}")
    return result


def create_stage_change_snapshot(
    db: Session,
    project_id: int,
    from_stage: str,
    to_stage: str,
) -> Optional[KitRateSnapshot]:
    """
    在项目阶段切换时创建快照

    此函数应在阶段切换逻辑中调用，记录阶段切换时刻的齐套率状态。

    Args:
        db: 数据库会话
        project_id: 项目 ID
        from_stage: 原阶段
        to_stage: 目标阶段

    Returns:
        创建的快照对象
    """
    trigger_event = f"{from_stage} -> {to_stage}"
    return create_kit_rate_snapshot(
        db=db,
        project_id=project_id,
        snapshot_type="STAGE_CHANGE",
        trigger_event=trigger_event,
    )
