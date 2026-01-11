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
from app.models.user import User, UserRole, Role


def find_users_by_role(db: Session, role_name: str) -> List[User]:
    """
    根据角色名称查找用户
    支持模糊匹配角色名称
    """
    if not role_name:
        return []

    # 查找匹配的角色
    roles = db.query(Role).filter(
        Role.is_active == True,
        or_(
            Role.role_name == role_name,
            Role.role_name.like(f"%{role_name}%"),
            Role.role_code.like(f"%{role_name}%")
        )
    ).all()

    if not roles:
        return []

    role_ids = [r.id for r in roles]

    # 查找拥有这些角色的用户
    user_roles = db.query(UserRole).filter(
        UserRole.role_id.in_(role_ids)
    ).all()

    user_ids = list(set([ur.user_id for ur in user_roles]))

    if not user_ids:
        return []

    users = db.query(User).filter(
        User.id.in_(user_ids),
        User.is_active == True
    ).all()

    return users


def find_users_by_department(db: Session, dept_name: str) -> List[User]:
    """
    根据部门名称查找用户
    支持模糊匹配部门名称
    """
    if not dept_name:
        return []

    users = db.query(User).filter(
        User.is_active == True,
        or_(
            User.department == dept_name,
            User.department.like(f"%{dept_name}%")
        )
    ).all()
    return users


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
    Issue 3.5: 收款逾期提醒（增强版）
    提醒已逾期的收款，按逾期天数分级提醒（7天、15天、30天、60天）
    逾期必须选择原因并生成 receivable_disputes 记录（待实现）
    """
    from app.core.config import settings
    
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
    from app.core.config import settings
    
    stats = {
        "milestone_upcoming_7d": 0,
        "milestone_upcoming_3d": 0,
        "milestone_overdue": 0,
        "payment_upcoming_7d": 0,
        "payment_upcoming_3d": 0,
        "payment_overdue": 0,
        # Sprint 3: 销售模块提醒
        "gate_timeout": 0,
        "quote_expiring": 0,
        "quote_expired": 0,
        "contract_expiring": 0,
        "approval_pending": 0
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
    
    # Sprint 3: 销售模块提醒
    # 阶段门超时提醒
    stats["gate_timeout"] = notify_gate_timeout(db, settings.SALES_GATE_TIMEOUT_DAYS)
    
    # 报价过期提醒
    quote_stats = notify_quote_expiring(db)
    stats["quote_expiring"] = quote_stats.get("expiring", 0)
    stats["quote_expired"] = quote_stats.get("expired", 0)
    
    # 合同到期提醒
    stats["contract_expiring"] = notify_contract_expiring(db)
    
    # 审批待处理提醒
    stats["approval_pending"] = notify_approval_pending(db, settings.SALES_APPROVAL_TIMEOUT_HOURS)
    
    db.commit()
    
    return stats


# ==================== Sprint 3: 销售模块提醒功能 ====================


def notify_gate_timeout(db: Session, timeout_days: int = 3) -> int:
    """
    Issue 3.2: 阶段门到期提醒
    检查阶段门提交后超过指定天数未处理的情况
    """
    from app.models.sales import Opportunity, Lead
    from app.models.enums import GateStatusEnum
    from app.core.config import settings
    
    timeout_days = timeout_days or settings.SALES_GATE_TIMEOUT_DAYS
    today = date.today()
    threshold_date = today - timedelta(days=timeout_days)
    
    count = 0
    
    # 检查 G1 阶段门（Lead -> Opportunity）
    leads = db.query(Lead).filter(
        and_(
            Lead.status == "QUALIFYING",  # 资格评估中
            Lead.updated_at <= datetime.combine(threshold_date, datetime.min.time())
        )
    ).all()
    
    for lead in leads:
        if lead.owner_id:
            # 检查今天是否已发送过提醒
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == lead.owner_id,
                    Notification.source_type == "lead",
                    Notification.source_id == lead.id,
                    Notification.notification_type == "GATE_TIMEOUT",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                )
            ).first()
            
            if not existing:
                days_pending = (today - lead.updated_at.date()).days if lead.updated_at else 0
                create_notification(
                    db=db,
                    user_id=lead.owner_id,
                    notification_type="GATE_TIMEOUT",
                    title=f"阶段门超时提醒：G1（线索转商机）",
                    content=f"线索 {lead.lead_code} 的 G1 阶段门已提交 {days_pending} 天未处理，请及时处理。",
                    source_type="lead",
                    source_id=lead.id,
                    link_url=f"/sales/leads/{lead.id}",
                    priority="HIGH",
                    extra_data={
                        "gate_type": "G1",
                        "lead_code": lead.lead_code,
                        "days_pending": days_pending
                    }
                )
                count += 1
    
    # 检查 G2/G3/G4 阶段门（Opportunity）
    opportunities = db.query(Opportunity).filter(
        and_(
            Opportunity.gate_status.in_([GateStatusEnum.G2_PENDING, GateStatusEnum.G3_PENDING, GateStatusEnum.G4_PENDING]),
            Opportunity.updated_at <= datetime.combine(threshold_date, datetime.min.time())
        )
    ).all()
    
    for opp in opportunities:
        if opp.owner_id:
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == opp.owner_id,
                    Notification.source_type == "opportunity",
                    Notification.source_id == opp.id,
                    Notification.notification_type == "GATE_TIMEOUT",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                )
            ).first()
            
            if not existing:
                days_pending = (today - opp.updated_at.date()).days if opp.updated_at else 0
                gate_name = {
                    GateStatusEnum.G2_PENDING: "G2（商机转报价）",
                    GateStatusEnum.G3_PENDING: "G3（报价转合同）",
                    GateStatusEnum.G4_PENDING: "G4（合同转项目）"
                }.get(opp.gate_status, "阶段门")
                
                create_notification(
                    db=db,
                    user_id=opp.owner_id,
                    notification_type="GATE_TIMEOUT",
                    title=f"阶段门超时提醒：{gate_name}",
                    content=f"商机 {opp.opp_code} 的 {gate_name} 已提交 {days_pending} 天未处理，请及时处理。",
                    source_type="opportunity",
                    source_id=opp.id,
                    link_url=f"/sales/opportunities/{opp.id}",
                    priority="HIGH",
                    extra_data={
                        "gate_type": opp.gate_status,
                        "opp_code": opp.opp_code,
                        "days_pending": days_pending
                    }
                )
                count += 1
    
    return count


def notify_quote_expiring(db: Session) -> dict:
    """
    Issue 3.3: 报价过期提醒
    检查报价有效期，在到期前7天、3天、1天发送提醒，过期后发送过期通知
    
    Returns:
        dict: {"expiring": count, "expired": count}
    """
    from app.models.sales import Quote, QuoteVersion
    from app.models.enums import QuoteStatusEnum
    from app.core.config import settings
    
    today = date.today()
    expiring_count = 0
    expired_count = 0
    
    # 查询所有有效的报价
    quotes = db.query(Quote).join(QuoteVersion).filter(
        Quote.status.in_([QuoteStatusEnum.SENT, QuoteStatusEnum.IN_REVIEW])
    ).all()
    
    for quote in quotes:
        version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
        if not version or not version.valid_until:
            continue
        
        valid_until = version.valid_until
        days_left = (valid_until - today).days
        
        # 已过期
        if days_left < 0:
            if quote.owner_id:
                existing = db.query(Notification).filter(
                    and_(
                        Notification.user_id == quote.owner_id,
                        Notification.source_type == "quote",
                        Notification.source_id == quote.id,
                        Notification.notification_type == "QUOTE_EXPIRED",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    )
                ).first()
                
                if not existing:
                    create_notification(
                        db=db,
                        user_id=quote.owner_id,
                        notification_type="QUOTE_EXPIRED",
                        title=f"报价已过期：{quote.quote_code}",
                        content=f"报价 {quote.quote_code} 已于 {valid_until} 过期，已过期 {abs(days_left)} 天，请及时处理。",
                        source_type="quote",
                        source_id=quote.id,
                        link_url=f"/sales/quotes/{quote.id}",
                        priority="HIGH",
                        extra_data={
                            "quote_code": quote.quote_code,
                            "valid_until": valid_until.isoformat(),
                            "days_overdue": abs(days_left)
                        }
                    )
                    expired_count += 1
        
        # 即将过期（7天、3天、1天前）
        elif days_left in settings.SALES_QUOTE_EXPIRE_REMINDER_DAYS:
            if quote.owner_id:
                # 使用 JSON 字段查询需要特殊处理
                from sqlalchemy import func
                existing = db.query(Notification).filter(
                    and_(
                        Notification.user_id == quote.owner_id,
                        Notification.source_type == "quote",
                        Notification.source_id == quote.id,
                        Notification.notification_type == "QUOTE_EXPIRING",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    )
                ).first()
                
                # 检查是否已发送过相同天数的提醒
                if existing and existing.extra_data:
                    existing_days_left = existing.extra_data.get('days_left')
                    if existing_days_left == days_left:
                        continue
                
                if not existing:
                    priority = "URGENT" if days_left == 1 else ("HIGH" if days_left == 3 else "NORMAL")
                    create_notification(
                        db=db,
                        user_id=quote.owner_id,
                        notification_type="QUOTE_EXPIRING",
                        title=f"报价即将过期：{quote.quote_code}（{days_left}天后）",
                        content=f"报价 {quote.quote_code} 将在 {days_left} 天后（{valid_until}）过期，请及时跟进。",
                        source_type="quote",
                        source_id=quote.id,
                        link_url=f"/sales/quotes/{quote.id}",
                        priority=priority,
                        extra_data={
                            "quote_code": quote.quote_code,
                            "valid_until": valid_until.isoformat(),
                            "days_left": days_left
                        }
                    )
                    count += 1
    
    return count


def notify_contract_expiring(db: Session) -> int:
    """
    Issue 3.4: 合同到期提醒
    检查合同到期时间，在到期前30天、15天、7天发送提醒
    """
    from app.models.sales import Contract
    from app.models.enums import ContractStatusEnum
    from app.core.config import settings
    
    today = date.today()
    count = 0
    
    # 查询所有有效的合同
    contracts = db.query(Contract).filter(
        Contract.status.in_([ContractStatusEnum.SIGNED, ContractStatusEnum.IN_EXECUTION])
    ).all()
    
    for contract in contracts:
        if not contract.delivery_deadline:
            continue
        
        deadline = contract.delivery_deadline
        days_left = (deadline - today).days
        
        # 即将到期（30天、15天、7天前）
        if days_left in settings.SALES_CONTRACT_EXPIRE_REMINDER_DAYS and days_left > 0:
            # 获取需要通知的用户：合同负责人、项目经理、财务
            user_ids = set()
            if contract.owner_id:
                user_ids.add(contract.owner_id)
            if contract.project_id:
                project = contract.project
                if project and project.pm_id:
                    user_ids.add(project.pm_id)
            
            for user_id in user_ids:
                existing = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user_id,
                        Notification.source_type == "contract",
                        Notification.source_id == contract.id,
                        Notification.notification_type == "CONTRACT_EXPIRING",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    )
                ).first()
                
                # 检查是否已发送过相同天数的提醒
                if existing and existing.extra_data:
                    existing_days_left = existing.extra_data.get('days_left')
                    if existing_days_left == days_left:
                        continue
                
                if not existing:
                    priority = "URGENT" if days_left == 7 else ("HIGH" if days_left == 15 else "NORMAL")
                    create_notification(
                        db=db,
                        user_id=user_id,
                        notification_type="CONTRACT_EXPIRING",
                        title=f"合同即将到期：{contract.contract_code}（{days_left}天后）",
                        content=f"合同 {contract.contract_code} 的交期将在 {days_left} 天后（{deadline}）到期，请及时跟进。",
                        source_type="contract",
                        source_id=contract.id,
                        link_url=f"/sales/contracts/{contract.id}",
                        priority=priority,
                        extra_data={
                            "contract_code": contract.contract_code,
                            "delivery_deadline": deadline.isoformat(),
                            "days_left": days_left
                        }
                    )
                    count += 1
    
    return count


def notify_approval_pending(db: Session, timeout_hours: int = 24) -> int:
    """
    Issue 3.6: 审批待处理提醒
    检查审批待处理超过指定小时数的情况
    """
    from app.models.sales import ApprovalRecord, ApprovalWorkflowStep
    from app.models.enums import ApprovalRecordStatusEnum
    from app.core.config import settings
    
    timeout_hours = timeout_hours or settings.SALES_APPROVAL_TIMEOUT_HOURS
    now = datetime.now()
    threshold_time = now - timedelta(hours=timeout_hours)
    
    count = 0
    
    # 查询所有待审批的记录
    records = db.query(ApprovalRecord).filter(
        ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING,
        ApprovalRecord.created_at <= threshold_time
    ).all()
    
    for record in records:
        # 获取当前审批步骤
        step = db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step
            )
        ).first()
        
        if not step:
            continue
        
        # 获取审批人（优先使用指定审批人，否则根据角色查找）
        approver_ids = []
        if step.approver_id:
            approver_ids = [step.approver_id]
        elif step.approver_role:
            # 根据角色查找审批人
            role_users = find_users_by_role(db, step.approver_role)
            approver_ids = [u.id for u in role_users]

        if not approver_ids:
            continue

        hours_pending = (now - record.created_at).total_seconds() / 3600
        entity_name = {
            "QUOTE": "报价",
            "CONTRACT": "合同",
            "INVOICE": "发票"
        }.get(record.entity_type, "事项")

        for approver_id in approver_ids:
            # 检查今天是否已发送过提醒
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == approver_id,
                    Notification.source_type == record.entity_type.lower(),
                    Notification.source_id == record.entity_id,
                    Notification.notification_type == "APPROVAL_PENDING",
                    Notification.created_at >= datetime.combine(now.date(), datetime.min.time())
                )
            ).first()

            if not existing:
                create_notification(
                    db=db,
                    user_id=approver_id,
                    notification_type="APPROVAL_PENDING",
                    title=f"审批待处理：{entity_name}审批",
                    content=f"{entity_name}审批已待处理 {int(hours_pending)} 小时，请及时处理。",
                    source_type=record.entity_type.lower(),
                    source_id=record.entity_id,
                    link_url=f"/sales/{record.entity_type.lower()}s/{record.entity_id}/approval-status",
                    priority="HIGH" if hours_pending >= 48 else "NORMAL",
                    extra_data={
                        "entity_type": record.entity_type,
                        "entity_id": record.entity_id,
                        "approval_record_id": record.id,
                        "hours_pending": int(hours_pending),
                        "step_name": step.step_name
                    }
                )
                count += 1
    
    return count


def scan_sales_reminders(db: Session) -> dict:
    """
    扫描所有销售模块需要提醒的事项并发送通知
    返回统计信息
    """
    from app.core.config import settings
    
    stats = {
        "gate_timeout": 0,
        "quote_expiring": 0,
        "quote_expired": 0,
        "contract_expiring": 0,
        "approval_pending": 0
    }
    
    # 阶段门超时提醒
    stats["gate_timeout"] = notify_gate_timeout(db, settings.SALES_GATE_TIMEOUT_DAYS)
    
    # 报价过期提醒
    stats["quote_expiring"] = notify_quote_expiring(db)
    
    # 合同到期提醒
    stats["contract_expiring"] = notify_contract_expiring(db)
    
    # 审批待处理提醒
    stats["approval_pending"] = notify_approval_pending(db, settings.SALES_APPROVAL_TIMEOUT_HOURS)
    
    db.commit()
    
    return stats



