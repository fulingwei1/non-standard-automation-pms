# -*- coding: utf-8 -*-
"""
P0 预警服务定时任务

包含缺料预警、任务延期预警、生产计划预警、报工超时提醒、
齐套检查、到货延迟检查、任务到期提醒、外协交期预警等
"""

import logging
from datetime import datetime, date, timedelta

from app.models.base import get_db_session
from app.models.project import Project, ProjectMilestone
from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum
from .base import send_notification_for_alert

logger = logging.getLogger(__name__)


def generate_shortage_alerts():
    """
    P0-1: 缺料预警生成服务
    每天执行一次，检查所有活跃项目的缺料情况并生成预警
    """
    try:
        with get_db_session() as db:
            from app.models.material import MaterialShortage

            today = date.today()

            # 获取或创建预警规则
            shortage_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'MATERIAL_SHORTAGE',
                AlertRule.is_enabled == True
            ).first()

            if not shortage_rule:
                shortage_rule = AlertRule(
                    rule_code='MATERIAL_SHORTAGE',
                    rule_name='缺料预警',
                    rule_type=AlertRuleTypeEnum.MATERIAL_SHORTAGE.value,
                    target_type='MATERIAL',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当物料短缺时触发预警'
                )
                db.add(shortage_rule)
                db.flush()

            # 查询所有未解决的缺料记录
            shortages = db.query(MaterialShortage).filter(
                MaterialShortage.status == 'OPEN'
            ).all()

            alert_count = 0

            for shortage in shortages:
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'MATERIAL_SHORTAGE',
                    AlertRecord.target_id == shortage.id,
                    AlertRecord.status == 'PENDING'
                ).first()

                if not existing_alert:
                    days_to_required = (shortage.required_date - today).days if shortage.required_date else 999

                    if days_to_required < 0:
                        level = AlertLevelEnum.CRITICAL.value
                    elif days_to_required <= 3:
                        level = AlertLevelEnum.URGENT.value
                    elif days_to_required <= 7:
                        level = AlertLevelEnum.WARNING.value
                    else:
                        level = AlertLevelEnum.INFO.value

                    alert_no = f'SA{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=shortage_rule.id,
                        target_type='MATERIAL_SHORTAGE',
                        target_id=shortage.id,
                        target_no=shortage.material_code,
                        target_name=f'{shortage.material_name} 缺料',
                        project_id=shortage.project_id,
                        alert_level=level,
                        alert_title=f'物料缺料：{shortage.material_name}',
                        alert_content=f'物料 {shortage.material_code} 缺料 {float(shortage.shortage_qty)}，需求日期：{shortage.required_date}',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(float(shortage.shortage_qty)),
                        threshold_value='0'
                    )
                    db.add(alert)
                    db.flush()
                    send_notification_for_alert(db, alert, logger)
                    alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 缺料预警生成完成: 检查 {len(shortages)} 个缺料记录, 生成 {alert_count} 个预警")

            return {
                'checked_count': len(shortages),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 缺料预警生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_task_delay_alerts():
    """
    P0-2: 任务延期预警服务
    每小时执行一次，检查所有延期任务并生成预警
    """
    try:
        with get_db_session() as db:
            from app.models.progress import Task

            today = date.today()

            delay_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'TASK_DELAY',
                AlertRule.is_enabled == True
            ).first()

            if not delay_rule:
                delay_rule = AlertRule(
                    rule_code='TASK_DELAY',
                    rule_name='任务延期预警',
                    rule_type=AlertRuleTypeEnum.SCHEDULE_DELAY.value,
                    target_type='TASK',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当任务计划结束日期已过但未完成时触发预警'
                )
                db.add(delay_rule)
                db.flush()

            overdue_tasks = db.query(Task).filter(
                Task.status.notin_(['DONE', 'CANCELLED']),
                Task.plan_end < today
            ).all()

            alert_count = 0

            for task in overdue_tasks:
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'TASK',
                    AlertRecord.target_id == task.id,
                    AlertRecord.status == 'PENDING'
                ).first()

                if not existing_alert:
                    days_overdue = (today - task.plan_end).days

                    if days_overdue >= 7:
                        level = AlertLevelEnum.CRITICAL.value
                    elif days_overdue >= 3:
                        level = AlertLevelEnum.URGENT.value
                    else:
                        level = AlertLevelEnum.WARNING.value

                    alert_no = f'TD{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=delay_rule.id,
                        target_type='TASK',
                        target_id=task.id,
                        target_no=task.task_name,
                        target_name=task.task_name,
                        project_id=task.project_id,
                        alert_level=level,
                        alert_title=f'任务延期：{task.task_name}',
                        alert_content=f'任务 {task.task_name} 已延期 {days_overdue} 天（计划完成日期：{task.plan_end}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(days_overdue),
                        threshold_value='0'
                    )
                    db.add(alert)
                    db.flush()
                    send_notification_for_alert(db, alert, logger)
                    alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 任务延期预警检查完成: 发现 {len(overdue_tasks)} 个延期任务, 生成 {alert_count} 个预警")

            return {
                'overdue_count': len(overdue_tasks),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 任务延期预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_production_plan_alerts():
    """
    P0-3: 生产计划预警服务
    每天执行一次，检查生产计划执行情况并生成预警
    """
    try:
        with get_db_session() as db:
            from app.models.production import ProductionPlan

            today = date.today()

            plan_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'PRODUCTION_PLAN',
                AlertRule.is_enabled == True
            ).first()

            if not plan_rule:
                plan_rule = AlertRule(
                    rule_code='PRODUCTION_PLAN',
                    rule_name='生产计划预警',
                    rule_type=AlertRuleTypeEnum.SCHEDULE_DELAY.value,
                    target_type='PRODUCTION_PLAN',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='80',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当生产计划进度低于80%或计划日期临近时触发预警'
                )
                db.add(plan_rule)
                db.flush()

            active_plans = db.query(ProductionPlan).filter(
                ProductionPlan.status == 'EXECUTING'
            ).all()

            alert_count = 0

            for plan in active_plans:
                if plan.progress < 80 and plan.plan_end_date <= today + timedelta(days=7):
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'PRODUCTION_PLAN',
                        AlertRecord.target_id == plan.id,
                        AlertRecord.status == 'PENDING'
                    ).first()

                    if not existing_alert:
                        days_left = (plan.plan_end_date - today).days
                        level = AlertLevelEnum.CRITICAL.value if days_left < 0 else AlertLevelEnum.WARNING.value

                        alert_no = f'PP{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=plan_rule.id,
                            target_type='PRODUCTION_PLAN',
                            target_id=plan.id,
                            target_no=plan.plan_no,
                            target_name=plan.plan_name,
                            project_id=plan.project_id,
                            alert_level=level,
                            alert_title=f'生产计划进度滞后：{plan.plan_name}',
                            alert_content=f'生产计划 {plan.plan_no} 进度仅 {plan.progress}%，距离计划结束日期还有 {days_left} 天',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=str(plan.progress),
                            threshold_value='80'
                        )
                        db.add(alert)
                        db.flush()
                        send_notification_for_alert(db, alert, logger)
                        alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 生产计划预警检查完成: 检查 {len(active_plans)} 个计划, 生成 {alert_count} 个预警")

            return {
                'checked_count': len(active_plans),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 生产计划预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_work_report_timeout():
    """
    P0-4: 报工超时提醒服务
    每小时执行一次，检查超过24小时未报工的工单
    """
    try:
        with get_db_session() as db:
            from app.models.production import WorkOrder, WorkReport

            now = datetime.now()
            today = date.today()
            timeout_threshold = now - timedelta(hours=24)

            timeout_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'WORK_REPORT_TIMEOUT',
                AlertRule.is_enabled == True
            ).first()

            if not timeout_rule:
                timeout_rule = AlertRule(
                    rule_code='WORK_REPORT_TIMEOUT',
                    rule_name='报工超时提醒',
                    rule_type=AlertRuleTypeEnum.SCHEDULE_DELAY.value,
                    target_type='WORK_ORDER',
                    condition_type='THRESHOLD',
                    condition_operator='GT',
                    threshold_value='24',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当工单超过24小时未报工时触发预警'
                )
                db.add(timeout_rule)
                db.flush()

            active_orders = db.query(WorkOrder).filter(
                WorkOrder.status.in_(['IN_PROGRESS', 'ASSIGNED'])
            ).all()

            alert_count = 0

            for order in active_orders:
                last_report = db.query(WorkReport).filter(
                    WorkReport.work_order_id == order.id
                ).order_by(WorkReport.report_time.desc()).first()

                hours_since_start = 0
                if not last_report:
                    if order.actual_start_time and order.actual_start_time < timeout_threshold:
                        hours_since_start = (now - order.actual_start_time).total_seconds() / 3600
                    else:
                        continue
                else:
                    if last_report.report_time < timeout_threshold:
                        hours_since_start = (now - last_report.report_time).total_seconds() / 3600
                    else:
                        continue

                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'WORK_ORDER',
                    AlertRecord.target_id == order.id,
                    AlertRecord.status == 'PENDING'
                ).first()

                if not existing_alert:
                    alert_no = f'WT{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=timeout_rule.id,
                        target_type='WORK_ORDER',
                        target_id=order.id,
                        target_no=order.work_order_no,
                        target_name=order.task_name,
                        project_id=order.project_id,
                        alert_level=AlertLevelEnum.WARNING.value,
                        alert_title=f'报工超时：{order.task_name}',
                        alert_content=f'工单 {order.work_order_no} 已超过 {int(hours_since_start)} 小时未报工',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(int(hours_since_start)),
                        threshold_value='24'
                    )
                    db.add(alert)
                    db.flush()
                    send_notification_for_alert(db, alert, logger)
                    alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 报工超时提醒检查完成: 检查 {len(active_orders)} 个工单, 生成 {alert_count} 个预警")

            return {
                'checked_count': len(active_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 报工超时提醒检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def calculate_progress_summary():
    """
    P0-5: 进度汇总计算服务
    每小时执行一次，自动计算项目进度汇总
    """
    try:
        with get_db_session() as db:
            from app.models.progress import Task

            active_projects = db.query(Project).filter(
                Project.is_active == True
            ).all()

            updated_count = 0

            for project in active_projects:
                tasks = db.query(Task).filter(
                    Task.project_id == project.id,
                    Task.status != 'CANCELLED'
                ).all()

                if not tasks:
                    continue

                total_weight = sum(float(task.weight) for task in tasks)
                weighted_progress = sum(float(task.progress_percent) * float(task.weight) for task in tasks)

                if total_weight > 0:
                    calculated_progress = int(weighted_progress / total_weight)

                    if hasattr(project, 'progress'):
                        project.progress = calculated_progress
                        updated_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 进度汇总计算完成: 更新 {updated_count} 个项目进度")

            return {
                'updated_count': updated_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 进度汇总计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def daily_kit_check():
    """
    P0-6: 每日齐套检查服务
    每天执行一次，检查所有工单的齐套情况
    """
    try:
        with get_db_session() as db:
            from app.models.shortage import KitCheck
            from app.models.production import WorkOrder

            today = date.today()

            kit_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'KIT_RATE_LOW',
                AlertRule.is_enabled == True
            ).first()

            if not kit_rule:
                kit_rule = AlertRule(
                    rule_code='KIT_RATE_LOW',
                    rule_name='齐套率过低预警',
                    rule_type=AlertRuleTypeEnum.MATERIAL_SHORTAGE.value,
                    target_type='WORK_ORDER',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='80',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当工单齐套率低于80%时触发预警'
                )
                db.add(kit_rule)
                db.flush()

            future_date = today + timedelta(days=7)
            upcoming_orders = db.query(WorkOrder).filter(
                WorkOrder.status.in_(['PENDING', 'ASSIGNED']),
                WorkOrder.plan_start_date.between(today, future_date)
            ).all()

            alert_count = 0

            for order in upcoming_orders:
                latest_check = db.query(KitCheck).filter(
                    KitCheck.work_order_id == order.id
                ).order_by(KitCheck.check_time.desc()).first()

                if latest_check and latest_check.kit_rate < 80:
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'WORK_ORDER',
                        AlertRecord.target_id == order.id,
                        AlertRecord.rule_id == kit_rule.id,
                        AlertRecord.status == 'PENDING'
                    ).first()

                    if not existing_alert:
                        alert_no = f'KC{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=kit_rule.id,
                            target_type='WORK_ORDER',
                            target_id=order.id,
                            target_no=order.work_order_no,
                            target_name=order.task_name,
                            project_id=order.project_id,
                            alert_level=AlertLevelEnum.WARNING.value,
                            alert_title=f'工单齐套率过低：{order.task_name}',
                            alert_content=f'工单 {order.work_order_no} 齐套率仅 {float(latest_check.kit_rate)}%，缺料 {latest_check.shortage_items} 项',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=str(float(latest_check.kit_rate)),
                            threshold_value='80'
                        )
                        db.add(alert)
                        db.flush()
                        send_notification_for_alert(db, alert, logger)
                        alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 每日齐套检查完成: 检查 {len(upcoming_orders)} 个工单, 生成 {alert_count} 个预警")

            return {
                'checked_count': len(upcoming_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 每日齐套检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_delivery_delay():
    """
    P0-7: 到货延迟检查服务
    每天执行一次，检查采购订单到货延迟情况
    """
    try:
        with get_db_session() as db:
            from app.models.purchase import PurchaseOrder

            today = date.today()

            delay_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'DELIVERY_DELAY',
                AlertRule.is_enabled == True
            ).first()

            if not delay_rule:
                delay_rule = AlertRule(
                    rule_code='DELIVERY_DELAY',
                    rule_name='到货延迟预警',
                    rule_type=AlertRuleTypeEnum.DELIVERY_DUE.value,
                    target_type='PURCHASE_ORDER',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当采购订单到货日期超过要求交期时触发预警'
                )
                db.add(delay_rule)
                db.flush()

            delayed_orders = db.query(PurchaseOrder).filter(
                PurchaseOrder.status.in_(['CONFIRMED', 'IN_PROGRESS', 'PARTIAL_RECEIVED']),
                PurchaseOrder.required_date < today
            ).all()

            alert_count = 0

            for order in delayed_orders:
                days_delayed = (today - order.required_date).days

                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'PURCHASE_ORDER',
                    AlertRecord.target_id == order.id,
                    AlertRecord.status == 'PENDING'
                ).first()

                if not existing_alert:
                    level = AlertLevelEnum.CRITICAL.value if days_delayed >= 7 else AlertLevelEnum.WARNING.value

                    alert_no = f'DD{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=delay_rule.id,
                        target_type='PURCHASE_ORDER',
                        target_id=order.id,
                        target_no=order.order_no,
                        target_name=order.order_title or order.order_no,
                        project_id=order.project_id,
                        alert_level=level,
                        alert_title=f'采购订单到货延迟：{order.order_no}',
                        alert_content=f'采购订单 {order.order_no} 已延迟 {days_delayed} 天（要求交期：{order.required_date}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(days_delayed),
                        threshold_value='0'
                    )
                    db.add(alert)
                    alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 到货延迟检查完成: 发现 {len(delayed_orders)} 个延迟订单, 生成 {alert_count} 个预警")

            return {
                'delayed_count': len(delayed_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 到货延迟检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_task_deadline_reminder():
    """
    P0-8: 任务到期提醒服务
    每小时执行一次，检查即将到期的任务并发送提醒
    """
    try:
        with get_db_session() as db:
            from app.models.task_center import TaskUnified

            now = datetime.now()
            today = date.today()
            reminder_threshold = now + timedelta(hours=24)

            reminder_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'TASK_DEADLINE_REMINDER',
                AlertRule.is_enabled == True
            ).first()

            if not reminder_rule:
                reminder_rule = AlertRule(
                    rule_code='TASK_DEADLINE_REMINDER',
                    rule_name='任务到期提醒',
                    rule_type=AlertRuleTypeEnum.SCHEDULE_DELAY.value,
                    target_type='TASK_UNIFIED',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='24',
                    alert_level=AlertLevelEnum.INFO.value,
                    is_enabled=True,
                    is_system=True,
                    description='当任务即将在24小时内到期时触发提醒'
                )
                db.add(reminder_rule)
                db.flush()

            upcoming_tasks = db.query(TaskUnified).filter(
                TaskUnified.status.notin_(['COMPLETED', 'CANCELLED']),
                TaskUnified.deadline.isnot(None),
                TaskUnified.deadline <= reminder_threshold,
                TaskUnified.deadline > now
            ).all()

            alert_count = 0

            for task in upcoming_tasks:
                hours_left = (task.deadline - now).total_seconds() / 3600

                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'TASK_UNIFIED',
                    AlertRecord.target_id == task.id,
                    AlertRecord.rule_id == reminder_rule.id,
                    AlertRecord.triggered_at >= now - timedelta(hours=24)
                ).first()

                if not existing_alert:
                    alert_no = f'TR{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=reminder_rule.id,
                        target_type='TASK_UNIFIED',
                        target_id=task.id,
                        target_no=task.task_code,
                        target_name=task.title,
                        project_id=task.project_id,
                        alert_level=AlertLevelEnum.INFO.value,
                        alert_title=f'任务即将到期：{task.title}',
                        alert_content=f'任务 {task.task_code} 将在 {int(hours_left)} 小时后到期（截止时间：{task.deadline}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(int(hours_left)),
                        threshold_value='24'
                    )
                    db.add(alert)
                    alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 任务到期提醒检查完成: 发现 {len(upcoming_tasks)} 个即将到期任务, 生成 {alert_count} 个提醒")

            return {
                'upcoming_count': len(upcoming_tasks),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 任务到期提醒检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_outsourcing_delivery_alerts():
    """
    P0-9: 外协交期预警服务
    每天执行一次，检查外协订单交期情况
    """
    try:
        with get_db_session() as db:
            from app.models.outsourcing import OutsourcingOrder

            today = date.today()
            warning_date = today + timedelta(days=3)

            delivery_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'OUTSOURCING_DELIVERY',
                AlertRule.is_enabled == True
            ).first()

            if not delivery_rule:
                delivery_rule = AlertRule(
                    rule_code='OUTSOURCING_DELIVERY',
                    rule_name='外协交期预警',
                    rule_type=AlertRuleTypeEnum.DELIVERY_DUE.value,
                    target_type='OUTSOURCING_ORDER',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='3',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当外协订单交期临近或已逾期时触发预警'
                )
                db.add(delivery_rule)
                db.flush()

            active_orders = db.query(OutsourcingOrder).filter(
                OutsourcingOrder.status.in_(['CONFIRMED', 'IN_PROGRESS'])
            ).all()

            alert_count = 0

            for order in active_orders:
                if not order.required_date:
                    continue

                days_to_delivery = (order.required_date - today).days

                if days_to_delivery <= 3:
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'OUTSOURCING_ORDER',
                        AlertRecord.target_id == order.id,
                        AlertRecord.status == 'PENDING'
                    ).first()

                    if not existing_alert:
                        if days_to_delivery < 0:
                            level = AlertLevelEnum.CRITICAL.value
                            title = f'外协订单交期逾期：{order.order_no}'
                            content = f'外协订单 {order.order_no} 已逾期 {abs(days_to_delivery)} 天（要求交期：{order.required_date}）'
                        else:
                            level = AlertLevelEnum.WARNING.value
                            title = f'外协订单交期临近：{order.order_no}'
                            content = f'外协订单 {order.order_no} 将在 {days_to_delivery} 天后到期（要求交期：{order.required_date}）'

                        alert_no = f'OD{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=delivery_rule.id,
                            target_type='OUTSOURCING_ORDER',
                            target_id=order.id,
                            target_no=order.order_no,
                            target_name=order.order_title or order.order_no,
                            project_id=order.project_id,
                            alert_level=level,
                            alert_title=title,
                            alert_content=content,
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=str(days_to_delivery),
                            threshold_value='3'
                        )
                        db.add(alert)
                        db.flush()
                        send_notification_for_alert(db, alert, logger)
                        alert_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 外协交期预警检查完成: 检查 {len(active_orders)} 个订单, 生成 {alert_count} 个预警")

            return {
                'checked_count': len(active_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 外协交期预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
