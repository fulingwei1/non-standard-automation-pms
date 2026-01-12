# -*- coding: utf-8 -*-
"""
销售和财务定时任务

包含收款提醒、逾期应收预警、商机阶段超时、售前工单超时、合同到期提醒等
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.base import get_db_session
from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum

logger = logging.getLogger(__name__)


def sales_reminder_scan():
    """
    销售模块提醒扫描任务
    扫描里程碑、收款计划等需要提醒的事项
    """
    from app.services.sales_reminder_service import scan_and_notify_all

    try:
        with get_db_session() as db:
            result = scan_and_notify_all(db)
            logger.info(f"[{datetime.now()}] 销售提醒扫描完成: {result}")
            return result
    except Exception as e:
        logger.error(f"[{datetime.now()}] 销售提醒扫描失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_payment_reminder():
    """
    S.8: 收款提醒服务
    每天上午9:30执行，提醒即将到期的收款计划
    """
    try:
        with get_db_session() as db:
            from app.services.sales_reminder_service import notify_payment_plan_upcoming

            count = notify_payment_plan_upcoming(db, days_before=7)

            logger.info(f"[{datetime.now()}] 收款提醒服务完成: 发送 {count} 条提醒")

            return {
                'reminder_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 收款提醒服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_overdue_receivable_alerts():
    """
    S.9: 逾期应收预警服务
    每天上午10:30执行，检查逾期应收款项并生成预警
    """
    try:
        with get_db_session() as db:
            from app.models.sales import Invoice, Contract

            today = date.today()

            overdue_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'OVERDUE_RECEIVABLE',
                AlertRule.is_enabled == True
            ).first()

            if not overdue_rule:
                overdue_rule = AlertRule(
                    rule_code='OVERDUE_RECEIVABLE',
                    rule_name='逾期应收预警',
                    rule_type=AlertRuleTypeEnum.FINANCIAL.value,
                    target_type='INVOICE',
                    condition_type='THRESHOLD',
                    condition_operator='GT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当发票已逾期且未完全收款时触发预警'
                )
                db.add(overdue_rule)
                db.flush()

            overdue_invoices = db.query(Invoice).join(Contract).filter(
                Invoice.status == "ISSUED",
                Invoice.payment_status.in_(["PENDING", "PARTIAL"]),
                Invoice.due_date.isnot(None),
                Invoice.due_date < today
            ).all()

            alert_count = 0

            for invoice in overdue_invoices:
                total_amount = invoice.total_amount or invoice.amount or Decimal("0")
                paid_amount = invoice.paid_amount or Decimal("0")
                unpaid_amount = total_amount - paid_amount

                if unpaid_amount <= 0:
                    continue

                overdue_days = (today - invoice.due_date).days

                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'INVOICE',
                    AlertRecord.target_id == invoice.id,
                    AlertRecord.rule_id == overdue_rule.id,
                    AlertRecord.status == 'PENDING'
                ).first()

                if existing_alert:
                    continue

                if overdue_days >= 90:
                    alert_level = AlertLevelEnum.URGENT.value
                elif overdue_days >= 60:
                    alert_level = AlertLevelEnum.CRITICAL.value
                elif overdue_days >= 30:
                    alert_level = AlertLevelEnum.WARNING.value
                else:
                    alert_level = AlertLevelEnum.INFO.value

                alert_no = f'AR{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                contract = invoice.contract
                customer_name = contract.customer.customer_name if contract and contract.customer else "未知客户"

                alert = AlertRecord(
                    alert_no=alert_no,
                    rule_id=overdue_rule.id,
                    target_type='INVOICE',
                    target_id=invoice.id,
                    target_no=invoice.invoice_code,
                    target_name=f"发票 {invoice.invoice_code}",
                    project_id=contract.project_id if contract else None,
                    alert_level=alert_level,
                    alert_title=f'逾期应收预警：{invoice.invoice_code}',
                    alert_content=f'发票 {invoice.invoice_code}（客户：{customer_name}）已逾期 {overdue_days} 天，未收金额：{float(unpaid_amount):,.2f} 元，请及时跟进。',
                    status=AlertStatusEnum.PENDING.value,
                    triggered_at=datetime.now(),
                    trigger_value=str(overdue_days)
                )
                db.add(alert)
                alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 逾期应收预警检查完成: 检查 {len(overdue_invoices)} 张发票, 生成 {alert_count} 个预警")

            return {
                'checked_count': len(overdue_invoices),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 逾期应收预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_opportunity_stage_timeout():
    """
    S.13: 商机阶段超时提醒
    每天下午3:30执行，检查商机在某个阶段停留时间过长
    """
    try:
        with get_db_session() as db:
            from app.models.sales import Opportunity
            from app.models.notification import Notification
            from app.services.sales_reminder_service import create_notification

            today = date.today()

            opportunities = db.query(Opportunity).filter(
                Opportunity.status.in_(["ACTIVE", "NEGOTIATING", "PROPOSAL"])
            ).all()

            reminder_count = 0

            stage_timeout_days = {
                "QUALIFICATION": 7,
                "NEEDS_ANALYSIS": 14,
                "PROPOSAL": 10,
                "NEGOTIATION": 14,
                "CLOSING": 7
            }

            for opp in opportunities:
                if not opp.stage or not opp.updated_at:
                    continue

                days_in_stage = (today - opp.updated_at.date()).days
                timeout_days = stage_timeout_days.get(opp.stage, 14)

                if days_in_stage > timeout_days:
                    existing = db.query(Notification).filter(
                        Notification.source_type == "opportunity",
                        Notification.source_id == opp.id,
                        Notification.notification_type == "OPPORTUNITY_STAGE_TIMEOUT",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    ).first()

                    if not existing:
                        create_notification(
                            db=db,
                            user_id=opp.owner_id,
                            notification_type="OPPORTUNITY_STAGE_TIMEOUT",
                            title=f"商机阶段停留超时：{opp.opportunity_name}",
                            content=f"商机 {opp.opportunity_name} 在 {opp.stage} 阶段已停留 {days_in_stage} 天，超过标准时间 {timeout_days} 天，请及时推进。",
                            source_type="opportunity",
                            source_id=opp.id,
                            link_url=f"/sales/opportunities/{opp.id}",
                            priority="HIGH" if days_in_stage > timeout_days * 1.5 else "NORMAL"
                        )
                        reminder_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 商机阶段超时提醒完成: 检查 {len(opportunities)} 个商机, 发送 {reminder_count} 条提醒")

            return {
                'checked_count': len(opportunities),
                'reminder_count': reminder_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 商机阶段超时提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_presale_workorder_timeout():
    """
    S.22: 售前工单超时提醒
    每天下午4:00执行，检查售前工单处理超时
    """
    try:
        with get_db_session() as db:
            from app.models.presale import PresaleSupportTicket
            from app.models.notification import Notification
            from app.services.sales_reminder_service import create_notification

            today = date.today()

            tickets = db.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.status.in_(["PENDING", "ACCEPTED", "PROCESSING"])
            ).all()

            reminder_count = 0

            timeout_days = {
                "CONSULT": 3,
                "QUOTATION": 5,
                "SOLUTION": 7,
                "TENDER": 10,
                "OTHER": 5
            }

            for ticket in tickets:
                if not ticket.created_at:
                    continue

                days_since_created = (today - ticket.created_at.date()).days
                ticket_type = ticket.ticket_type or "OTHER"
                threshold = timeout_days.get(ticket_type, 5)

                if days_since_created > threshold:
                    existing = db.query(Notification).filter(
                        Notification.source_type == "presale_ticket",
                        Notification.source_id == ticket.id,
                        Notification.notification_type == "PRESALE_TICKET_TIMEOUT",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    ).first()

                    if not existing:
                        assignee_id = ticket.assignee_id or ticket.applicant_id
                        if not assignee_id:
                            continue

                        create_notification(
                            db=db,
                            user_id=assignee_id,
                            notification_type="PRESALE_TICKET_TIMEOUT",
                            title=f"售前工单处理超时：{ticket.ticket_no}",
                            content=f"售前工单 {ticket.ticket_no}（{ticket.title}）已创建 {days_since_created} 天，超过标准处理时间 {threshold} 天，请及时处理。",
                            source_type="presale_ticket",
                            source_id=ticket.id,
                            link_url=f"/presale/tickets/{ticket.id}",
                            priority="HIGH" if days_since_created > threshold * 1.5 else "NORMAL"
                        )
                        reminder_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 售前工单超时提醒完成: 检查 {len(tickets)} 个工单, 发送 {reminder_count} 条提醒")

            return {
                'checked_count': len(tickets),
                'reminder_count': reminder_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 售前工单超时提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_contract_expiry_reminder():
    """
    合同到期提醒服务
    每天执行，检查即将到期的合同
    """
    try:
        with get_db_session() as db:
            from app.models.sales import Contract
            from app.models.notification import Notification
            from app.services.sales_reminder_service import create_notification

            today = date.today()
            warning_date = today + timedelta(days=30)

            contracts = db.query(Contract).filter(
                Contract.status == "ACTIVE",
                Contract.end_date.isnot(None),
                Contract.end_date <= warning_date,
                Contract.end_date >= today
            ).all()

            reminder_count = 0

            for contract in contracts:
                days_to_expire = (contract.end_date - today).days

                existing = db.query(Notification).filter(
                    Notification.source_type == "contract",
                    Notification.source_id == contract.id,
                    Notification.notification_type == "CONTRACT_EXPIRY_REMINDER",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                ).first()

                if not existing and contract.owner_id:
                    create_notification(
                        db=db,
                        user_id=contract.owner_id,
                        notification_type="CONTRACT_EXPIRY_REMINDER",
                        title=f"合同即将到期：{contract.contract_no}",
                        content=f"合同 {contract.contract_no} 将在 {days_to_expire} 天后到期（{contract.end_date}），请及时跟进续签事宜。",
                        source_type="contract",
                        source_id=contract.id,
                        link_url=f"/sales/contracts/{contract.id}",
                        priority="HIGH" if days_to_expire <= 7 else "NORMAL"
                    )
                    reminder_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 合同到期提醒完成: 检查 {len(contracts)} 个合同, 发送 {reminder_count} 条提醒")

            return {
                'checked_count': len(contracts),
                'reminder_count': reminder_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 合同到期提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
