# -*- coding: utf-8 -*-
"""
销售模块提醒服务
包含：关键节点提醒、逾期提醒
"""

from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.notification import Notification
from app.models.project import ProjectMilestone, ProjectPaymentPlan
from app.models.sales import Contract, Invoice, ReceivableDispute
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    content: str,
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
    link_url: Optional[str] = None,
    priority: str = "NORMAL",
    extra_data: Optional[dict] = None
) -> Notification:
    """
    创建系统通知
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type=source_type,
        source_id=source_id,
        link_url=link_url,
        priority=priority,
        extra_data=extra_data or {}
    )
    db.add(notification)
    return notification


def notify_milestone_upcoming(db: Session, days_before: int = 7) -> int:
    """
    提醒即将到期的里程碑
    """
    today = date.today()
    target_date = today + timedelta(days=days_before)
    
    # 查找即将到期的里程碑
    milestones = db.query(ProjectMilestone).filter(
        and_(
            ProjectMilestone.status == "PENDING",
            ProjectMilestone.planned_date <= target_date,
            ProjectMilestone.planned_date >= today
        )
    ).all()
    
    count = 0
    for milestone in milestones:
        if milestone.owner_id:
            # 检查是否已发送过提醒
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == milestone.owner_id,
                    Notification.source_type == "milestone",
                    Notification.source_id == milestone.id,
                    Notification.notification_type == "MILESTONE_UPCOMING",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                )
            ).first()
            
            if not existing:
                create_notification(
                    db=db,
                    user_id=milestone.owner_id,
                    notification_type="MILESTONE_UPCOMING",
                    title=f"里程碑即将到期：{milestone.milestone_name}",
                    content=f"里程碑 {milestone.milestone_code} 将在 {milestone.planned_date} 到期，请及时处理。",
                    source_type="milestone",
                    source_id=milestone.id,
                    link_url=f"/projects/{milestone.project_id}/milestones/{milestone.id}",
                    priority="HIGH" if days_before <= 3 else "NORMAL",
                    extra_data={
                        "milestone_code": milestone.milestone_code,
                        "planned_date": milestone.planned_date.isoformat(),
                        "days_left": (milestone.planned_date - today).days
                    }
                )
                count += 1
    
    return count


def notify_milestone_overdue(db: Session) -> int:
    """
    提醒已逾期的里程碑
    """
    today = date.today()
    
    # 查找已逾期的里程碑
    milestones = db.query(ProjectMilestone).filter(
        and_(
            ProjectMilestone.status == "PENDING",
            ProjectMilestone.planned_date < today
        )
    ).all()
    
    count = 0
    for milestone in milestones:
        if milestone.owner_id:
            # 检查今天是否已发送过提醒
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == milestone.owner_id,
                    Notification.source_type == "milestone",
                    Notification.source_id == milestone.id,
                    Notification.notification_type == "MILESTONE_OVERDUE",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                )
            ).first()
            
            if not existing:
                overdue_days = (today - milestone.planned_date).days
                create_notification(
                    db=db,
                    user_id=milestone.owner_id,
                    notification_type="MILESTONE_OVERDUE",
                    title=f"里程碑已逾期：{milestone.milestone_name}",
                    content=f"里程碑 {milestone.milestone_code} 已逾期 {overdue_days} 天，请尽快处理。",
                    source_type="milestone",
                    source_id=milestone.id,
                    link_url=f"/projects/{milestone.project_id}/milestones/{milestone.id}",
                    priority="URGENT",
                    extra_data={
                        "milestone_code": milestone.milestone_code,
                        "planned_date": milestone.planned_date.isoformat(),
                        "overdue_days": overdue_days
                    }
                )
                count += 1
    
    return count


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


def notify_payment_overdue(db: Session) -> int:
    """
    提醒已逾期的收款
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
                overdue_days = (today - plan.planned_date).days if plan.planned_date else 0
                unpaid_amount = plan.planned_amount - (plan.actual_amount or 0)
                
                # 根据逾期天数确定优先级
                if overdue_days >= 60:
                    priority = "URGENT"
                elif overdue_days >= 30:
                    priority = "HIGH"
                else:
                    priority = "NORMAL"
                
                create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="PAYMENT_OVERDUE",
                    title=f"收款已逾期：{plan.payment_name}",
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


def notify_contract_signed(db: Session, contract_id: int) -> Optional[Notification]:
    """
    合同签订提醒
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or not contract.owner_id:
        return None
    
    return create_notification(
        db=db,
        user_id=contract.owner_id,
        notification_type="CONTRACT_SIGNED",
        title=f"合同已签订：{contract.contract_code}",
        content=f"合同 {contract.contract_code} 已签订，金额：{contract.contract_amount}，请及时跟进后续流程。",
        source_type="contract",
        source_id=contract.id,
        link_url=f"/sales/contracts/{contract.id}",
        priority="HIGH",
        extra_data={
            "contract_code": contract.contract_code,
            "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
            "signed_date": contract.signed_date.isoformat() if contract.signed_date else None
        }
    )


def notify_invoice_issued(db: Session, invoice_id: int) -> Optional[Notification]:
    """
    发票开具提醒
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return None
    
    contract = invoice.contract
    if not contract or not contract.owner_id:
        return None
    
    return create_notification(
        db=db,
        user_id=contract.owner_id,
        notification_type="INVOICE_ISSUED",
        title=f"发票已开具：{invoice.invoice_code}",
        content=f"发票 {invoice.invoice_code} 已开具，金额：{invoice.total_amount}，请及时跟进收款。",
        source_type="invoice",
        source_id=invoice.id,
        link_url=f"/sales/invoices/{invoice.id}",
        priority="NORMAL",
        extra_data={
            "invoice_code": invoice.invoice_code,
            "invoice_amount": float(invoice.total_amount) if invoice.total_amount else 0,
            "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None
        }
    )


def scan_and_notify_all(db: Session) -> dict:
    """
    扫描所有需要提醒的事项并发送通知
    返回统计信息
    """
    stats = {
        "milestone_upcoming_7d": 0,
        "milestone_upcoming_3d": 0,
        "milestone_overdue": 0,
        "payment_upcoming_7d": 0,
        "payment_upcoming_3d": 0,
        "payment_overdue": 0
    }
    
    # 里程碑提醒（7天前）
    stats["milestone_upcoming_7d"] = notify_milestone_upcoming(db, days_before=7)
    
    # 里程碑提醒（3天前）
    stats["milestone_upcoming_3d"] = notify_milestone_upcoming(db, days_before=3)
    
    # 里程碑逾期
    stats["milestone_overdue"] = notify_milestone_overdue(db)
    
    # 收款计划提醒（7天前）
    stats["payment_upcoming_7d"] = notify_payment_plan_upcoming(db, days_before=7)
    
    # 收款计划提醒（3天前）
    stats["payment_upcoming_3d"] = notify_payment_plan_upcoming(db, days_before=3)
    
    # 收款逾期
    stats["payment_overdue"] = notify_payment_overdue(db)
    
    db.commit()
    
    return stats



