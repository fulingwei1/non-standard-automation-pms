# -*- coding: utf-8 -*-
"""
销售提醒服务 - 销售流程提醒（阶段门、报价、审批）
"""

from datetime import date, datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import ApprovalRecordStatusEnum, GateStatusEnum, QuoteStatusEnum
from app.models.notification import Notification
from app.models.sales import (
    ApprovalRecord,
    ApprovalWorkflowStep,
    Lead,
    Opportunity,
    Quote,
    QuoteVersion,
)
from app.services.sales_reminder.base import create_notification, find_users_by_role


def notify_gate_timeout(db: Session, timeout_days: int = 3) -> int:
    """
    Issue 3.2: 阶段门到期提醒
    检查阶段门提交后超过指定天数未处理的情况
    """
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
    today = date.today()
    expiring_count = 0
    expired_count = 0

    # 查询所有有效的报价（使用正确的枚举值，不需要join）
    quotes = db.query(Quote).filter(
        Quote.status.in_([QuoteStatusEnum.SUBMITTED, QuoteStatusEnum.APPROVED])
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
                    expiring_count += 1

    return {"expiring": expiring_count, "expired": expired_count}


def notify_approval_pending(db: Session, timeout_hours: int = 24) -> int:
    """
    Issue 3.6: 审批待处理提醒
    检查审批待处理超过指定小时数的情况
    """
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
