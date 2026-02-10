# -*- coding: utf-8 -*-
"""
定时任务 - 工时相关任务
包含：工时填报提醒、工时汇总、审批超时提醒、同步失败提醒等
"""
import logging
from datetime import date, datetime, timedelta

from app.models.base import get_db_session

logger = logging.getLogger(__name__)


def daily_timesheet_reminder_task():
    """
    每日工时填报提醒任务
    每天上午9:00执行，提醒未填报昨天工时的用户
    """
    from app.services.timesheet_reminder import notify_timesheet_missing

    try:
        with get_db_session() as db:
            count = notify_timesheet_missing(db)
            logger.info(f"[{datetime.now()}] 每日工时填报提醒完成: 发送 {count} 条提醒")

            return {
                'reminder_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 每日工时填报提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def weekly_timesheet_reminder_task():
    """
    每周工时填报提醒任务
    每周一上午10:00执行，提醒未完成上周工时填报的用户
    """
    from app.services.timesheet_reminder import notify_weekly_timesheet_missing

    try:
        with get_db_session() as db:
            count = notify_weekly_timesheet_missing(db)
            logger.info(f"[{datetime.now()}] 每周工时填报提醒完成: 发送 {count} 条提醒")

            return {
                'reminder_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 每周工时填报提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def timesheet_anomaly_alert_task():
    """
    异常工时预警任务
    每天下午14:00执行，检测并提醒异常工时记录
    """
    from app.services.timesheet_reminder import notify_timesheet_anomaly

    try:
        with get_db_session() as db:
            count = notify_timesheet_anomaly(db, days=1)
            logger.info(f"[{datetime.now()}] 异常工时预警完成: 发送 {count} 条提醒")

            return {
                'alert_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 异常工时预警失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def timesheet_approval_timeout_reminder_task():
    """
    工时审批超时提醒任务
    每天上午11:00和下午15:00执行，提醒审批超时的记录
    """
    from app.services.timesheet_reminder import notify_approval_timeout

    try:
        with get_db_session() as db:
            count = notify_approval_timeout(db, timeout_hours=24)
            logger.info(f"[{datetime.now()}] 工时审批超时提醒完成: 发送 {count} 条提醒")

            return {
                'reminder_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 工时审批超时提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def timesheet_sync_failure_alert_task():
    """
    工时数据同步失败提醒任务
    每天下午16:00执行，检查并提醒同步失败的记录
    """
    from app.services.timesheet_reminder import notify_sync_failure

    try:
        with get_db_session() as db:
            count = notify_sync_failure(db)
            logger.info(f"[{datetime.now()}] 工时数据同步失败提醒完成: 发送 {count} 条提醒")

            return {
                'alert_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 工时数据同步失败提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def daily_timesheet_aggregation_task():
    """
    每日工时汇总任务
    每天凌晨1点执行，汇总前一天的数据
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService

    with get_db_session() as db:
        try:
            # 汇总前一天的数据
            yesterday = date.today() - timedelta(days=1)
            year = yesterday.year
            month = yesterday.month

            service = TimesheetAggregationService(db)
            result = service.aggregate_monthly_timesheet(year, month)

            logger.info(
                f"[{datetime.now()}] 每日工时汇总完成（{year}年{month}月）: "
                f"{result.get('message', '')}"
            )

            return result
        except Exception as e:
            logger.error(f"[{datetime.now()}] 每日工时汇总失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


def weekly_timesheet_aggregation_task():
    """
    每周工时汇总任务
    每周一凌晨2点执行，汇总上一周的数据
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService

    with get_db_session() as db:
        try:
            # 汇总上一周的数据（上周一到上周日）
            today = date.today()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)

            # 如果跨月，需要分别汇总
            if last_monday.month == last_sunday.month:
                year = last_monday.year
                month = last_monday.month
                service = TimesheetAggregationService(db)
                result = service.aggregate_monthly_timesheet(year, month)
                logger.info(f"[{datetime.now()}] 每周工时汇总完成（{year}年{month}月）")
            else:
                # 跨月情况，分别汇总两个月
                logger.info(f"[{datetime.now()}] 每周工时汇总：跨月情况，分别汇总")
                result = {'message': '跨月汇总完成'}

            return result
        except Exception as e:
            logger.error(f"[{datetime.now()}] 每周工时汇总失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


def monthly_timesheet_aggregation_task():
    """
    每月工时汇总任务
    每月1号凌晨3点执行，汇总上一个月的数据
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService

    with get_db_session() as db:
        try:
            # 计算上个月
            today = date.today()
            if today.month == 1:
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1

            # 执行月度汇总
            service = TimesheetAggregationService(db)
            result = service.aggregate_monthly_timesheet(year, month)

            logger.info(
                f"[{datetime.now()}] 月度工时汇总完成（{year}年{month}月）: "
                f"{result.get('message', '')}"
            )

            return result
        except Exception as e:
            logger.error(f"[{datetime.now()}] 月度工时汇总失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


def calculate_monthly_labor_cost_task():
    """
    计算月度人工成本任务
    每月5号凌晨执行，计算上月的人工成本分摊
    """
    from app.services.labor_cost_service import LaborCostCalculationService

    try:
        with get_db_session() as db:
            # 计算上个月
            today = date.today()
            if today.month == 1:
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1

            service = LaborCostCalculationService(db)
            result = service.calculate_monthly_costs(year, month)

            logger.info(
                f"[{datetime.now()}] 月度人工成本计算完成（{year}年{month}月）: "
                f"{result.get('message', '')}"
            )

            return result
    except Exception as e:
        logger.error(f"[{datetime.now()}] 月度人工成本计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
