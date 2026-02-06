# -*- coding: utf-8 -*-
"""
定时任务 - 销售相关任务
包含：销售提醒、收款提醒、逾期应收预警、商机阶段超时等
"""
import logging
from datetime import date, datetime
from decimal import Decimal

from app.models.alert import AlertRecord, AlertRule
from app.models.base import get_db_session
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum

logger = logging.getLogger(__name__)


def sales_reminder_scan():
    """
    销售模块提醒扫描任务
    扫描里程碑、收款计划等需要提醒的事项
    """
    from app.services.sales_reminder import scan_and_notify_all

    with get_db_session() as db:
        try:
            stats = scan_and_notify_all(db)
            logger.info(f"销售提醒扫描完成: {stats}")
        except Exception as e:
            logger.error(f"销售提醒扫描失败: {str(e)}")
            import traceback
            traceback.print_exc()


def check_payment_reminder():
    """
    S.8: 收款提醒服务
    每天上午9:30执行，提醒即将到期的收款计划
    """
    try:
        with get_db_session() as db:
            from app.services.sales_reminder import notify_payment_plan_upcoming

            # 提醒7天内到期的收款计划
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
            from app.models.sales import Contract, Invoice

            today = date.today()

            # 获取或创建预警规则
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

            # 查询逾期发票
            overdue_invoices = db.query(Invoice).join(Contract).filter(
                Invoice.status == "ISSUED",
                Invoice.payment_status.in_(["PENDING", "PARTIAL"]),
                Invoice.due_date.isnot(None),
                Invoice.due_date < today
            ).all()

            alert_count = 0

            for invoice in overdue_invoices:
                # 计算未收金额
                total_amount = invoice.total_amount or invoice.amount or Decimal("0")
                paid_amount = invoice.paid_amount or Decimal("0")
                unpaid_amount = total_amount - paid_amount

                if unpaid_amount <= 0:
                    continue

                overdue_days = (today - invoice.due_date).days

                # 检查是否已有待处理预警
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'INVOICE',
                    AlertRecord.target_id == invoice.id,
                    AlertRecord.rule_id == overdue_rule.id,
                    AlertRecord.status == 'PENDING'
                ).first()

                if existing_alert:
                    continue

                # 根据逾期天数确定预警级别
                if overdue_days >= 90:
                    alert_level = AlertLevelEnum.URGENT.value
                elif overdue_days >= 60:
                    alert_level = AlertLevelEnum.CRITICAL.value
                elif overdue_days >= 30:
                    alert_level = AlertLevelEnum.WARNING.value
                else:
                    alert_level = AlertLevelEnum.INFO.value

                # 生成预警编号
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
                    alert_content=f'发票 {invoice.invoice_code}（客户：{customer_name}）已逾期 {overdue_days} 天，'
                                  f'未收金额：{float(unpaid_amount):,.2f} 元，请及时跟进。',
                    status=AlertStatusEnum.PENDING.value,
                    triggered_at=datetime.now(),
                    trigger_value=str(overdue_days)
                )
                db.add(alert)
                alert_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 逾期应收预警检查完成: "
                f"检查 {len(overdue_invoices)} 张发票, 生成 {alert_count} 个预警"
            )

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
            from app.models.notification import Notification
            from app.models.sales import Opportunity

            today = date.today()

            # 查询活跃的商机（使用stage字段）
            opportunities = db.query(Opportunity).filter(
                Opportunity.stage.in_([
                    "DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"
                ])
            ).all()

            reminder_count = 0

            # 各阶段的标准停留时间（天）
            stage_timeout_days = {
                "QUALIFICATION": 7,     # 资格确认：7天
                "NEEDS_ANALYSIS": 14,   # 需求分析：14天
                "PROPOSAL": 10,         # 方案设计：10天
                "NEGOTIATION": 14,      # 商务谈判：14天
                "CLOSING": 7            # 成交阶段：7天
            }

            for opp in opportunities:
                if not opp.stage or not opp.updated_at:
                    continue

                # 计算在当前阶段停留的天数
                days_in_stage = (today - opp.updated_at.date()).days
                timeout_days = stage_timeout_days.get(opp.stage, 14)

                # 如果超过标准时间，发送提醒
                if days_in_stage > timeout_days:
                    # 检查今天是否已发送过提醒
                    existing = db.query(Notification).filter(
                        Notification.source_type == "opportunity",
                        Notification.source_id == opp.id,
                        Notification.notification_type == "OPPORTUNITY_STAGE_TIMEOUT",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    ).first()

                    if not existing:
                        from app.services.sales_reminder import create_notification

                        create_notification(
                            db=db,
                            user_id=opp.owner_id,
                            notification_type="OPPORTUNITY_STAGE_TIMEOUT",
                            title=f"商机阶段停留超时：{opp.opportunity_name}",
                            content=f"商机 {opp.opportunity_name} 在 {opp.stage} 阶段已停留 {days_in_stage} 天，"
                                    f"超过标准时间 {timeout_days} 天，请及时推进。",
                            source_type="opportunity",
                            source_id=opp.id,
                            link_url=f"/sales/opportunities/{opp.id}",
                            priority="HIGH" if days_in_stage > timeout_days * 1.5 else "NORMAL",
                            extra_data={
                                "opportunity_name": opp.opportunity_name,
                                "stage": opp.stage,
                                "days_in_stage": days_in_stage,
                                "timeout_days": timeout_days
                            }
                        )
                        reminder_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 商机阶段超时提醒完成: "
                f"检查 {len(opportunities)} 个商机, 发送 {reminder_count} 条提醒"
            )

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
