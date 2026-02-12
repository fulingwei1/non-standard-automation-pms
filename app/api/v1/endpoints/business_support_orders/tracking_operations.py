# -*- coding: utf-8 -*-
"""
验收单跟踪 - 操作功能

包含验收条件检查、催签等操作
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.acceptance import AcceptanceOrder
from app.models.business_support import AcceptanceTracking, AcceptanceTrackingRecord
from app.models.project import Project
from app.models.user import User
from app.schemas.business_support import (
    AcceptanceTrackingResponse,
    ConditionCheckRequest,
    ReminderRequest,
)
from app.schemas.common import ResponseModel

from .tracking_helpers import build_tracking_response
from .utils import _send_department_notification

router = APIRouter()


@router.post("/acceptance-tracking/{tracking_id}/check-condition", response_model=ResponseModel[AcceptanceTrackingResponse], summary="验收条件检查")
async def check_acceptance_condition(
    tracking_id: int,
    check_data: ConditionCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """验收条件检查"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")

        # 更新验收条件检查状态
        tracking.condition_check_status = check_data.condition_check_status
        tracking.condition_check_result = check_data.condition_check_result
        tracking.condition_check_date = datetime.now()
        tracking.condition_checker_id = current_user.id

        # 创建跟踪记录
        record = AcceptanceTrackingRecord(
            tracking_id=tracking_id,
            record_type="condition_check",
            record_content=f"验收条件检查：{check_data.condition_check_status} - {check_data.condition_check_result}",
            record_date=datetime.now(),
            operator_id=current_user.id,
            operator_name=current_user.username,
            result="success" if check_data.condition_check_status == "met" else "pending",
            remark=check_data.remark
        )
        db.add(record)

        db.commit()
        db.refresh(tracking)

        return ResponseModel(
            code=200,
            message="验收条件检查成功",
            data=build_tracking_response(tracking)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"验收条件检查失败: {str(e)}")


@router.post("/acceptance-tracking/{tracking_id}/remind", response_model=ResponseModel[AcceptanceTrackingResponse], summary="催签验收单")
async def remind_acceptance_signature(
    tracking_id: int,
    reminder_data: ReminderRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """催签验收单"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")

        # 更新催签信息
        tracking.reminder_count = (tracking.reminder_count or 0) + 1
        tracking.last_reminder_date = datetime.now()
        tracking.last_reminder_by = current_user.id
        tracking.tracking_status = "reminded"

        # 创建跟踪记录
        record = AcceptanceTrackingRecord(
            tracking_id=tracking_id,
            record_type="reminder",
            record_content=reminder_data.reminder_content or f"第{tracking.reminder_count}次催签验收单",
            record_date=datetime.now(),
            operator_id=current_user.id,
            operator_name=current_user.username,
            result="success",
            remark=reminder_data.remark
        )
        db.add(record)

        db.commit()
        db.refresh(tracking)

        # 实际发送催签通知（邮件、短信、系统消息等）
        # 获取验收单信息
        acceptance_order = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.id == tracking.acceptance_order_id
        ).first()

        if acceptance_order:
            # 获取项目信息
            project = None
            if acceptance_order.project_id:
                project = db.query(Project).filter(
                    Project.id == acceptance_order.project_id
                ).first()

            # 通知项目经理和销售人员
            notified_users = set()

            # 通知项目经理
            if project and project.pm_id:
                title = f"验收单催签提醒：{acceptance_order.order_no}"
                content = f"验收单 {acceptance_order.order_no} 需要催签。\n\n项目名称：{project.project_name if project else ''}\n验收类型：{acceptance_order.acceptance_type}\n客户名称：{acceptance_order.customer_name}\n计划验收日期：{acceptance_order.plan_accept_date.strftime('%Y-%m-%d') if acceptance_order.plan_accept_date else '未设置'}\n已催签{tracking.reminder_count or 0}次\n\n请及时跟进。"

                _send_department_notification(
                    db=db,
                    user_id=project.pm_id,
                    notification_type="ACCEPTANCE_REMINDER",
                    title=title,
                    content=content,
                    source_type="ACCEPTANCE_TRACKING",
                    source_id=tracking.id,
                    priority="HIGH",
                    extra_data={
                        "order_no": acceptance_order.order_no,
                        "reminder_count": tracking.reminder_count
                    }
                )
                notified_users.add(project.pm_id)

            # 通知销售人员
            if acceptance_order.sales_id and acceptance_order.sales_id not in notified_users:
                _send_department_notification(
                    db=db,
                    user_id=acceptance_order.sales_id,
                    notification_type="ACCEPTANCE_REMINDER",
                    title=f"验收单催签提醒：{acceptance_order.order_no}",
                    content=f"验收单 {acceptance_order.order_no} 需要催签，已催签{tracking.reminder_count or 0}次。",
                    source_type="ACCEPTANCE_TRACKING",
                    source_id=tracking.id,
                    priority="HIGH"
                )
                notified_users.add(acceptance_order.sales_id)

        return ResponseModel(
            code=200,
            message="催签成功",
            data=build_tracking_response(tracking)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"催签失败: {str(e)}")
