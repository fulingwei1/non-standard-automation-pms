# -*- coding: utf-8 -*-
"""
ECN定时任务服务
功能：超时检查、自动提醒、状态更新
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.ecn import Ecn, EcnEvaluation, EcnTask


def _approval_task_level(task: ApprovalTask) -> Optional[int]:
    return task.node.node_order if task.node else task.task_order


def _approval_task_role(task: ApprovalTask) -> str:
    return task.node.node_name if task.node else task.task_type or "ECN审批"


def check_evaluation_overdue(db: Session) -> List[Dict[str, Any]]:
    """
    检查评估超时
    返回超时的评估列表
    """
    now = datetime.now()
    timeout_threshold = now - timedelta(days=3)  # 3天超时

    overdue_evals = (
        db.query(EcnEvaluation)
        .filter(
            and_(EcnEvaluation.status == "PENDING", EcnEvaluation.created_at < timeout_threshold)
        )
        .all()
    )

    alerts = []
    for eval in overdue_evals:
        ecn = db.query(Ecn).filter(Ecn.id == eval.ecn_id).first()
        if ecn:
            overdue_days = (now - eval.created_at).days
            alerts.append(
                {
                    "type": "EVALUATION_OVERDUE",
                    "ecn_id": ecn.id,
                    "ecn_no": ecn.ecn_no,
                    "ecn_title": ecn.ecn_title,
                    "eval_id": eval.id,
                    "eval_dept": eval.eval_dept,
                    "overdue_days": overdue_days,
                    "message": f"ECN {ecn.ecn_no} 的{eval.eval_dept}评估已超时{overdue_days}天",
                }
            )

    return alerts


def check_approval_overdue(db: Session) -> List[Dict[str, Any]]:
    """
    检查审批超时
    返回超时的审批列表
    """
    now = datetime.now()

    overdue_approvals = (
        db.query(ApprovalTask)
        .join(ApprovalInstance, ApprovalTask.instance_id == ApprovalInstance.id)
        .filter(
            and_(
                ApprovalInstance.entity_type == "ECN",
                ApprovalTask.status == "PENDING",
                ApprovalTask.due_at.isnot(None),
                ApprovalTask.due_at < now,
            )
        )
        .all()
    )

    alerts = []
    for approval_task in overdue_approvals:
        ecn = db.query(Ecn).filter(Ecn.id == approval_task.instance.entity_id).first()
        if ecn:
            approval_level = _approval_task_level(approval_task)
            approval_role = _approval_task_role(approval_task)
            overdue_days = (now - approval_task.due_at).days if approval_task.due_at else 0
            alerts.append(
                {
                    "type": "APPROVAL_OVERDUE",
                    "ecn_id": ecn.id,
                    "ecn_no": ecn.ecn_no,
                    "ecn_title": ecn.ecn_title,
                    "approval_task_id": approval_task.id,
                    "approval_level": approval_level,
                    "approval_role": approval_role,
                    "overdue_days": overdue_days,
                    "message": f"ECN {ecn.ecn_no} 的第{approval_level}级审批（{approval_role}）已超时{overdue_days}天",
                }
            )

    db.commit()
    return alerts


def check_task_overdue(db: Session) -> List[Dict[str, Any]]:
    """
    检查执行任务超时
    返回超时的任务列表
    """
    now = datetime.now()

    overdue_tasks = (
        db.query(EcnTask)
        .filter(
            and_(EcnTask.status.in_(["PENDING", "IN_PROGRESS"]), EcnTask.planned_end < now.date())
        )
        .all()
    )

    alerts = []
    for task in overdue_tasks:
        ecn = db.query(Ecn).filter(Ecn.id == task.ecn_id).first()
        if ecn:
            overdue_days = (now.date() - task.planned_end).days if task.planned_end else 0
            alerts.append(
                {
                    "type": "TASK_OVERDUE",
                    "ecn_id": ecn.id,
                    "ecn_no": ecn.ecn_no,
                    "ecn_title": ecn.ecn_title,
                    "task_id": task.id,
                    "task_name": task.task_name,
                    "overdue_days": overdue_days,
                    "message": f"ECN {ecn.ecn_no} 的任务「{task.task_name}」已超时{overdue_days}天",
                }
            )

    return alerts


def check_all_overdue() -> List[Dict[str, Any]]:
    """
    检查所有超时事项
    返回所有超时提醒列表
    """
    with get_db_session() as db:
        alerts = []
        alerts.extend(check_evaluation_overdue(db))
        alerts.extend(check_approval_overdue(db))
        alerts.extend(check_task_overdue(db))
        return alerts


def send_overdue_notifications(alerts: List[Dict[str, Any]]) -> None:
    """
    发送超时提醒通知
    """
    from app.dependencies import get_db_session
    from app.models.ecn import Ecn, EcnEvaluation, EcnTask
    from app.services.ecn.notification import notify_overdue_alert

    if not alerts:
        return

    with get_db_session() as db:
        for alert in alerts:
            try:
                # 根据提醒类型确定通知对象
                user_ids = []

                if alert["type"] == "EVALUATION_OVERDUE":
                    # 评估超时：通知评估部门负责人
                    eval_id = alert.get("eval_id")
                    if eval_id:
                        eval = db.query(EcnEvaluation).filter(EcnEvaluation.id == eval_id).first()
                        if eval and eval.evaluator_id:
                            user_ids.append(eval.evaluator_id)
                        else:
                            # 如果没有评估人，通知ECN申请人
                            ecn = db.query(Ecn).filter(Ecn.id == alert.get("ecn_id")).first()
                            if ecn and ecn.applicant_id:
                                user_ids.append(ecn.applicant_id)

                elif alert["type"] == "APPROVAL_OVERDUE":
                    # 审批超时：通知审批人
                    task_id = alert.get("approval_task_id") or alert.get("task_id")
                    if task_id:
                        task = (
                            db.query(ApprovalTask)
                            .join(ApprovalInstance, ApprovalTask.instance_id == ApprovalInstance.id)
                            .filter(
                                ApprovalTask.id == task_id,
                                ApprovalTask.status == "PENDING",
                                ApprovalInstance.entity_type == "ECN",
                            )
                            .first()
                        )
                        if task and task.assignee_id:
                            user_ids.append(task.assignee_id)

                elif alert["type"] == "TASK_OVERDUE":
                    # 任务超时：通知任务负责人
                    task_id = alert.get("task_id")
                    if task_id:
                        task = db.query(EcnTask).filter(EcnTask.id == task_id).first()
                        if task and task.assignee_id:
                            user_ids.append(task.assignee_id)

                # 发送通知
                if user_ids:
                    notify_overdue_alert(db, alert, user_ids)
            except Exception as e:
                logger.error(
                    f"Failed to send overdue notification for alert {alert.get('ecn_no')}: {e}"
                )


def run_ecn_scheduler() -> None:
    """
    运行ECN定时任务
    应该在后台定时任务中调用（如APScheduler、Celery等）
    """
    try:
        alerts = check_all_overdue()
        if alerts:
            send_overdue_notifications(alerts)
            logger.info(f"ECN定时任务: 发现{len(alerts)}个超时事项")
        else:
            logger.debug("ECN定时任务: 无超时事项")
    except Exception as e:
        logger.error(f"ECN定时任务执行失败: {e}")


if __name__ == "__main__":
    # 测试运行
    run_ecn_scheduler()
