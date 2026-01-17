# -*- coding: utf-8 -*-
"""
齐套检查执行与开工确认端点
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.production import WorkOrder
from app.models.shortage import KitCheck
from app.models.user import User
from app.schemas.common import ResponseModel

from .utils import calculate_work_order_kit_rate, generate_check_no

router = APIRouter()


@router.post("/kit-check/work-orders/{work_order_id}/check", response_model=ResponseModel)
def check_work_order_kit(
    *,
    db: Session = Depends(deps.get_db),
    work_order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行齐套检查
    计算工单的齐套率并返回检查结果
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 计算齐套率
    kit_data = calculate_work_order_kit_rate(db, work_order)

    # 保存检查记录到 mat_kit_check 表
    check_record = KitCheck(
        check_no=generate_check_no(db),
        check_type='work_order',
        work_order_id=work_order_id,
        project_id=work_order.project_id,
        total_items=kit_data["total_items"],
        fulfilled_items=kit_data["fulfilled_items"],
        shortage_items=kit_data["shortage_items"],
        in_transit_items=kit_data["in_transit_items"],
        kit_rate=Decimal(str(kit_data["kit_rate"])),
        kit_status=kit_data["kit_status"],
        shortage_summary=kit_data.get("shortage_details", []),
        check_time=datetime.now(),
        check_method='manual',
        checked_by=current_user.id,
        can_start=kit_data["is_kit_complete"],
    )

    db.add(check_record)
    db.commit()
    db.refresh(check_record)

    return ResponseModel(
        code=200,
        message="齐套检查完成",
        data={
            "check_id": check_record.id,
            "check_no": check_record.check_no,
            "work_order_id": work_order_id,
            "work_order_no": work_order.work_order_no,
            "kit_data": kit_data,
            "check_time": check_record.check_time.isoformat(),
            "checked_by": current_user.id,
        }
    )


@router.post("/kit-check/work-orders/{work_order_id}/confirm", response_model=ResponseModel)
def confirm_work_order_start(
    *,
    db: Session = Depends(deps.get_db),
    work_order_id: int,
    confirm_type: str = Body(..., description="确认类型: start_now/wait/partial_start"),
    confirm_note: Optional[str] = Body(None, description="确认说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认开工
    确认工单物料齐套，可以开工（支持强制开工）
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if confirm_type not in ["start_now", "wait", "partial_start"]:
        raise HTTPException(status_code=400, detail="确认类型必须是 start_now、wait 或 partial_start")

    # 计算齐套率
    kit_data = calculate_work_order_kit_rate(db, work_order)

    # 如果齐套率不足且不是强制开工，需要提示
    if kit_data["kit_rate"] < 100 and confirm_type == "start_now":
        # 允许强制开工，但记录说明
        pass

    # 更新工单状态
    if confirm_type == "start_now":
        work_order.status = "READY"  # 或 "IN_PROGRESS"，根据业务需求
    elif confirm_type == "wait":
        work_order.status = "PENDING"
    elif confirm_type == "partial_start":
        work_order.status = "READY"

    # 查找或创建最新的检查记录
    latest_check = (
        db.query(KitCheck)
        .filter(KitCheck.work_order_id == work_order_id)
        .order_by(desc(KitCheck.check_time))
        .first()
    )

    if not latest_check:
        # 如果没有检查记录，先创建一个
        latest_check = KitCheck(
            check_no=generate_check_no(db),
            check_type='work_order',
            work_order_id=work_order_id,
            project_id=work_order.project_id,
            total_items=kit_data["total_items"],
            fulfilled_items=kit_data["fulfilled_items"],
            shortage_items=kit_data["shortage_items"],
            in_transit_items=kit_data["in_transit_items"],
            kit_rate=Decimal(str(kit_data["kit_rate"])),
            kit_status=kit_data["kit_status"],
            shortage_summary=kit_data.get("shortage_details", []),
            check_time=datetime.now(),
            check_method='manual',
            checked_by=current_user.id,
        )
        db.add(latest_check)

    # 更新确认信息
    latest_check.start_confirmed = (confirm_type in ["start_now", "partial_start"])
    latest_check.confirm_time = datetime.now()
    latest_check.confirmed_by = current_user.id
    latest_check.confirm_remark = confirm_note
    latest_check.can_start = (confirm_type in ["start_now", "partial_start"])

    db.add(work_order)
    db.add(latest_check)
    db.commit()
    db.refresh(work_order)
    db.refresh(latest_check)

    return ResponseModel(
        code=200,
        message="开工确认成功",
        data={
            "work_order_id": work_order_id,
            "work_order_no": work_order.work_order_no,
            "confirm_type": confirm_type,
            "confirm_note": confirm_note,
            "kit_rate": kit_data["kit_rate"],
            "confirmed_by": current_user.id,
            "confirmed_at": datetime.now().isoformat(),
        }
    )
