# -*- coding: utf-8 -*-
"""
销售提醒服务 - 收款提醒
"""

from datetime import date, datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.enums import DisputeReasonCodeEnum, DisputeStatusEnum
from app.models.notification import Notification
from app.models.project import ProjectPaymentPlan
from app.models.sales.invoices import ReceivableDispute
from app.services.sales_reminder.base import create_notification, find_users_by_role


def notify_payment_plan_upcoming(db: Session, days_before: int = 7) -> int:
    """
    提醒即将到期的收款计划
    """
    today = date.today()
    target_date = today + timedelta(days=days_before)

    # 查找即将到期的收款计划
    payment_plans = db.query(ProjectPaymentPlan).filter(
        and_(
            ProjectPaymentPlan.status.in_(["PENDING", "INVOICED"]),
            ProjectPaymentPlan.planned_date.isnot(None),
            ProjectPaymentPlan.planned_date <= target_date,
            ProjectPaymentPlan.planned_date >= today
        )
    ).all()

    count = 0
    for plan in payment_plans:
        # 获取项目负责人或合同负责人
        project = plan.project
        contract = plan.contract

        user_id = None
        if contract and contract.owner_id:
            user_id = contract.owner_id
        elif project and project.pm_id:
            user_id = project.pm_id

        if user_id:
            # 检查是否已发送过提醒
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.source_type == "payment_plan",
                    Notification.source_id == plan.id,
                    Notification.notification_type == "PAYMENT_PLAN_UPCOMING",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                )
            ).first()

            if not existing:
                create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="PAYMENT_PLAN_UPCOMING",
                    title=f"收款计划即将到期：{plan.payment_name}",
                    content=f"收款计划 {plan.payment_name}（金额：{plan.planned_amount}）将在 {plan.planned_date} 到期，请及时跟进。",
                    source_type="payment_plan",
                    source_id=plan.id,
                    link_url=f"/projects/{plan.project_id}/payment-plans" if plan.project_id else None,
                    priority="HIGH" if days_before <= 3 else "NORMAL",
                    extra_data={
                        "payment_name": plan.payment_name,
                        "payment_type": plan.payment_type,
                        "planned_amount": float(plan.planned_amount),
                        "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
                        "days_left": (plan.planned_date - today).days if plan.planned_date else None
                    }
                )
                count += 1

    return count


def _create_overdue_dispute_record(
    db: Session,
    payment_id: int,
    overdue_days: int,
    description: str = None
) -> ReceivableDispute:
    """
    为逾期收款创建争议记录

    Args:
        db: 数据库会话
        payment_id: 付款计划ID
        overdue_days: 逾期天数
        description: 描述信息

    Returns:
        创建的 ReceivableDispute 记录
    """
    # 检查是否已存在该付款计划的争议记录
    existing_dispute = db.query(ReceivableDispute).filter(
        and_(
            ReceivableDispute.payment_id == payment_id,
            ReceivableDispute.reason_code == DisputeReasonCodeEnum.OVERDUE.value,
            ReceivableDispute.status.in_([
                DisputeStatusEnum.OPEN.value,
                DisputeStatusEnum.IN_PROGRESS.value
            ])
        )
    ).first()

    if existing_dispute:
        # 已存在未解决的争议记录，更新描述
        existing_dispute.description = description or f"收款已逾期 {overdue_days} 天"
        return existing_dispute

    # 创建新的争议记录
    dispute = ReceivableDispute(
        payment_id=payment_id,
        reason_code=DisputeReasonCodeEnum.OVERDUE.value,
        description=description or f"收款已逾期 {overdue_days} 天，系统自动生成争议记录",
        status=DisputeStatusEnum.OPEN.value,
        responsible_dept="财务部",
        expect_resolve_date=date.today() + timedelta(days=30)  # 默认30天内解决
    )
    db.add(dispute)
    return dispute


def notify_payment_overdue(db: Session) -> int:
    """
    Issue 3.5: 收款逾期提醒（增强版）
    提醒已逾期的收款，按逾期天数分级提醒（7天、15天、30天、60天）
    逾期时自动生成 receivable_disputes 记录以跟踪争议
    """
    today = date.today()

    # 查找已逾期的收款计划（状态为PENDING或INVOICED，且计划日期已过）
    payment_plans = db.query(ProjectPaymentPlan).filter(
        and_(
            ProjectPaymentPlan.status.in_(["PENDING", "INVOICED"]),
            ProjectPaymentPlan.planned_date.isnot(None),
            ProjectPaymentPlan.planned_date < today,
            ProjectPaymentPlan.actual_amount < ProjectPaymentPlan.planned_amount
        )
    ).all()

    count = 0
    reminder_days = [7, 15, 30, 60]  # 分级提醒时间点

    for plan in payment_plans:
        overdue_days = (today - plan.planned_date).days if plan.planned_date else 0

        # 只在特定天数发送提醒（避免每天重复发送）
        if overdue_days not in reminder_days and overdue_days < 7:
            continue

        # 为逾期收款创建/更新争议记录
        _create_overdue_dispute_record(
            db=db,
            payment_id=plan.id,
            overdue_days=overdue_days,
            description=f"收款计划 {plan.payment_name} 已逾期 {overdue_days} 天，" +
                       f"未收金额：{plan.planned_amount - (plan.actual_amount or 0)}"
        )

        # 获取需要通知的用户：收款责任人、销售、财务、销售经理
        user_ids = set()

        # 合同负责人
        if plan.contract and plan.contract.owner_id:
            user_ids.add(plan.contract.owner_id)

        # 项目经理
        if plan.project and plan.project.pm_id:
            user_ids.add(plan.project.pm_id)

        # 添加财务人员
        finance_users = find_users_by_role(db, "财务")
        for user in finance_users:
            user_ids.add(user.id)

        # 添加销售经理
        sales_managers = find_users_by_role(db, "销售经理")
        for user in sales_managers:
            user_ids.add(user.id)

        for user_id in user_ids:
            # 检查今天是否已发送过提醒
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.source_type == "payment_plan",
                    Notification.source_id == plan.id,
                    Notification.notification_type == "PAYMENT_OVERDUE",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                )
            ).first()

            if not existing:
                unpaid_amount = plan.planned_amount - (plan.actual_amount or 0)

                # 根据逾期天数确定优先级
                if overdue_days >= 60:
                    priority = "URGENT"
                elif overdue_days >= 30:
                    priority = "HIGH"
                elif overdue_days >= 15:
                    priority = "HIGH"
                else:
                    priority = "NORMAL"

                create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="PAYMENT_OVERDUE",
                    title=f"收款已逾期：{plan.payment_name}（{overdue_days}天）",
                    content=f"收款计划 {plan.payment_name} 已逾期 {overdue_days} 天，未收金额：{unpaid_amount}，请尽快跟进。",
                    source_type="payment_plan",
                    source_id=plan.id,
                    link_url=f"/projects/{plan.project_id}/payment-plans" if plan.project_id else None,
                    priority=priority,
                    extra_data={
                        "payment_name": plan.payment_name,
                        "payment_type": plan.payment_type,
                        "planned_amount": float(plan.planned_amount),
                        "actual_amount": float(plan.actual_amount or 0),
                        "unpaid_amount": float(unpaid_amount),
                        "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
                        "overdue_days": overdue_days
                    }
                )
                count += 1

    return count
