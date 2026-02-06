# -*- coding: utf-8 -*-
"""
定时任务 - 生产相关任务
包含：生产计划预警、报工超时提醒、生产日报生成
"""
import logging
from datetime import date, datetime, timedelta

from app.models.alert import AlertRecord, AlertRule
from app.models.base import get_db_session
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum

from .base import send_notification_for_alert

logger = logging.getLogger(__name__)


def check_production_plan_alerts():
    """
    P0-3: 生产计划预警服务
    每天执行一次，检查生产计划执行情况并生成预警
    """
    try:
        with get_db_session() as db:
            from app.models.production import ProductionPlan

            today = date.today()

            # 获取或创建预警规则
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

            # 查询所有执行中的生产计划
            active_plans = db.query(ProductionPlan).filter(
                ProductionPlan.status == 'EXECUTING'
            ).all()

            alert_count = 0

            for plan in active_plans:
                # 检查计划进度
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
                            alert_content=f'生产计划 {plan.plan_no} 进度仅 {plan.progress}%，'
                                          f'距离计划结束日期还有 {days_left} 天',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=str(plan.progress),
                            threshold_value='80'
                        )
                        db.add(alert)
                        db.flush()

                        # 发送通知
                        send_notification_for_alert(db, alert, logger)

                        alert_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 生产计划预警检查完成: "
                f"检查 {len(active_plans)} 个计划, 生成 {alert_count} 个预警"
            )

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

            # 获取或创建预警规则
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

            # 查询所有进行中的工单
            active_orders = db.query(WorkOrder).filter(
                WorkOrder.status.in_(['IN_PROGRESS', 'ASSIGNED'])
            ).all()

            alert_count = 0

            for order in active_orders:
                # 获取最后一次报工时间
                last_report = db.query(WorkReport).filter(
                    WorkReport.work_order_id == order.id
                ).order_by(WorkReport.report_time.desc()).first()

                hours_since_start = 0

                # 如果没有报工记录，使用实际开始时间
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

                # 检查是否已有预警记录
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

                    # 发送通知
                    send_notification_for_alert(db, alert, logger)

                    alert_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 报工超时检查完成: "
                f"检查 {len(active_orders)} 个工单, 生成 {alert_count} 个预警"
            )

            return {
                'checked_count': len(active_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 报工超时检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def generate_production_daily_reports(target_date=None):
    """
    生成生产日报
    每天凌晨执行，汇总前一天的生产数据
    """
    from typing import Optional

    try:
        with get_db_session() as db:
            from app.models.production import ProductionDailyReport

            if target_date is None:
                target_date = date.today() - timedelta(days=1)

            # 检查是否已有报告
            existing = db.query(ProductionDailyReport).filter(
                ProductionDailyReport.report_date == target_date
            ).first()

            if existing:
                logger.info(f"[{datetime.now()}] 生产日报已存在: {target_date}")
                return {'message': f'Report already exists for {target_date}'}

            # 计算统计数据
            stats = _calculate_production_daily_stats(db, target_date, None)

            # 创建日报（映射到模型实际字段）
            report = ProductionDailyReport(
                report_date=target_date,
                plan_qty=stats.get('total_work_orders', 0),
                completed_qty=stats.get('completed_work_orders', 0),
                total_qty=stats.get('total_output', 0),
                qualified_qty=stats.get('qualified_output', 0),
                pass_rate=100 - stats.get('defect_rate', 0),
                efficiency=stats.get('efficiency_rate', 0)
            )
            db.add(report)
            db.commit()

            logger.info(f"[{datetime.now()}] 生产日报生成完成: {target_date}")

            return {
                'report_date': target_date.isoformat(),
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 生产日报生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def _calculate_production_daily_stats(db, target_date, workshop_id):
    """
    计算生产日统计数据
    """
    from app.models.production import WorkOrder, WorkReport

    # 查询当天的工单
    query = db.query(WorkOrder).filter(
        WorkOrder.created_at >= datetime.combine(target_date, datetime.min.time()),
        WorkOrder.created_at < datetime.combine(target_date + timedelta(days=1), datetime.min.time())
    )

    if workshop_id:
        query = query.filter(WorkOrder.workshop_id == workshop_id)

    work_orders = query.all()

    total_work_orders = len(work_orders)
    completed_work_orders = sum(1 for wo in work_orders if wo.status == 'COMPLETED')

    # 计算产出
    total_output = sum(wo.completed_qty or 0 for wo in work_orders)
    qualified_output = sum(wo.qualified_qty or 0 for wo in work_orders)

    defect_rate = 0
    if total_output > 0:
        defect_rate = ((total_output - qualified_output) / total_output) * 100

    efficiency_rate = 0
    if total_work_orders > 0:
        efficiency_rate = (completed_work_orders / total_work_orders) * 100

    return {
        'total_work_orders': total_work_orders,
        'completed_work_orders': completed_work_orders,
        'total_output': total_output,
        'qualified_output': qualified_output,
        'defect_rate': round(defect_rate, 2),
        'efficiency_rate': round(efficiency_rate, 2)
    }
