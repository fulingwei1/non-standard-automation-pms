# -*- coding: utf-8 -*-
"""
定时任务 - 里程碑相关任务
包含：里程碑到期预警、里程碑状态监控与收款计划调整、里程碑风险前置识别
"""
import logging
from datetime import datetime

from app.dependencies import get_db_session

logger = logging.getLogger(__name__)


def check_milestone_alerts():
    """
    里程碑到期预警服务

    每天早上8点执行：
    - 距到期 ≤1天 → CRITICAL 预警
    - 距到期 ≤3天 → WARNING 预警
    - 已逾期 → CRITICAL 预警
    - 自动通知项目负责人 + 里程碑责任人
    """
    try:
        with get_db_session() as db:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            alert_service = MilestoneAlertService(db)
            alert_count = alert_service.check_milestone_alerts()

            db.commit()

            logger.info(
                f"[{datetime.now()}] 里程碑预警检查完成: "
                f"生成 {alert_count} 个预警"
            )

            return {"alert_count": alert_count, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑预警检查失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def check_milestone_status_and_adjust_payments():
    """
    监控项目里程碑状态变化并自动调整收款计划
    每小时执行一次，检查里程碑状态变化（延期、提前完成）并调整关联的收款计划
    """
    try:
        with get_db_session() as db:
            from app.services.payment_adjustment_service import PaymentAdjustmentService

            service = PaymentAdjustmentService(db)
            result = service.check_and_adjust_all()

            logger.info(
                f"[{datetime.now()}] 里程碑-收款计划调整检查完成: "
                f"检查 {result.get('checked', 0)} 个里程碑, "
                f"调整 {result.get('adjusted', 0)} 个收款计划"
            )

            return result
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑-收款计划调整检查失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def check_milestone_risk_alerts():
    """
    里程碑风险前置识别服务

    每天早上8:10执行：
    - 扫描未来14天内到期的里程碑
    - 基于前置里程碑逾期、阶段进度落后、未启动状态等多维指标评估风险
    - 风险评分 ≥60% 生成 MILESTONE_AT_RISK 预警
    - 风险评分 ≥80% 升级为 CRITICAL
    - 自动通知项目负责人 + 里程碑责任人
    """
    try:
        with get_db_session() as db:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            alert_service = MilestoneAlertService(db)
            risk_count = alert_service.check_milestone_risk_alerts()

            db.commit()

            logger.info(
                f"[{datetime.now()}] 里程碑风险预警检查完成: "
                f"生成 {risk_count} 个风险预警"
            )

            return {
                "risk_alerts": risk_count,
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑风险预警检查失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}
