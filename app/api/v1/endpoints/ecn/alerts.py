# -*- coding: utf-8 -*-
"""
ECN超时提醒 API endpoints

包含：超时提醒列表、批量处理超时提醒
"""

from datetime import datetime, timedelta
from typing import Any, List

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn, EcnApproval, EcnEvaluation, EcnTask
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.ecn_notification import notify_overdue_alert

router = APIRouter()


@router.get("/ecns/overdue-alerts", response_model=List[dict], status_code=status.HTTP_200_OK)
def get_ecn_overdue_alerts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN超时提醒列表
    包括：评估超时、审批超时、执行任务超时
    """
    now = datetime.now()
    alerts = []

    # 1. 评估超时提醒
    # 查找提交超过3天但评估未完成的ECN
    eval_timeout = now - timedelta(days=3)
    pending_evals = db.query(EcnEvaluation).filter(
        EcnEvaluation.status == "PENDING",
        EcnEvaluation.created_at < eval_timeout
    ).all()

    for eval in pending_evals:
        ecn = db.query(Ecn).filter(Ecn.id == eval.ecn_id).first()
        if ecn:
            alerts.append({
                "type": "EVALUATION_OVERDUE",
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "dept": eval.eval_dept,
                "overdue_days": (now - eval.created_at).days,
                "message": f"ECN {ecn.ecn_no} 的{eval.eval_dept}评估已超时{(now - eval.created_at).days}天"
            })

    # 2. 审批超时提醒
    overdue_approvals = db.query(EcnApproval).filter(
        EcnApproval.status == "PENDING",
        EcnApproval.due_date < now
    ).all()

    for approval in overdue_approvals:
        ecn = db.query(Ecn).filter(Ecn.id == approval.ecn_id).first()
        if ecn:
            overdue_days = (now - approval.due_date).days if approval.due_date else 0
            alerts.append({
                "type": "APPROVAL_OVERDUE",
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "approval_level": approval.approval_level,
                "approval_role": approval.approval_role,
                "overdue_days": overdue_days,
                "message": f"ECN {ecn.ecn_no} 的第{approval.approval_level}级审批（{approval.approval_role}）已超时{overdue_days}天"
            })
            # 更新超时标识
            approval.is_overdue = True
            db.add(approval)

    # 3. 执行任务超时提醒
    overdue_tasks = db.query(EcnTask).filter(
        EcnTask.status.in_(["PENDING", "IN_PROGRESS"]),
        EcnTask.planned_end < now.date()
    ).all()

    for task in overdue_tasks:
        ecn = db.query(Ecn).filter(Ecn.id == task.ecn_id).first()
        if ecn:
            overdue_days = (now.date() - task.planned_end).days if task.planned_end else 0
            alerts.append({
                "type": "TASK_OVERDUE",
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "task_id": task.id,
                "task_name": task.task_name,
                "overdue_days": overdue_days,
                "message": f"ECN {ecn.ecn_no} 的任务「{task.task_name}」已超时{overdue_days}天"
            })

    db.commit()

    return alerts


@router.post("/ecns/batch-process-overdue-alerts", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_process_overdue_alerts(
    *,
    db: Session = Depends(deps.get_db),
    alerts: List[dict] = Body(..., description="超时提醒列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量处理ECN超时提醒
    发送提醒通知给相关人员
    """
    from app.models.organization import Department

    results = []
    success_count = 0
    fail_count = 0

    for alert_data in alerts:
        try:
            alert_type = alert_data.get('type')
            ecn_id = alert_data.get('ecn_id')

            if not alert_type or not ecn_id:
                results.append({
                    "alert": alert_data,
                    "status": "failed",
                    "message": "缺少必要字段"
                })
                fail_count += 1
                continue

            # 查找ECN
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                results.append({
                    "alert": alert_data,
                    "status": "failed",
                    "message": "ECN不存在"
                })
                fail_count += 1
                continue

            # 根据提醒类型找到相关人员
            user_ids = []

            if alert_type == "EVALUATION_OVERDUE":
                # 评估超时：找到评估人员
                eval_dept = alert_data.get('dept')
                if eval_dept:
                    # 查找该部门的评估记录
                    evaluation = db.query(EcnEvaluation).filter(
                        EcnEvaluation.ecn_id == ecn_id,
                        EcnEvaluation.eval_dept == eval_dept,
                        EcnEvaluation.status == "PENDING"
                    ).first()

                    if evaluation and evaluation.evaluator_id:
                        user_ids.append(evaluation.evaluator_id)
                    else:
                        # 如果没有指定评估人，尝试根据部门查找部门负责人
                        dept = db.query(Department).filter(Department.dept_name == eval_dept).first()
                        if dept and dept.manager_id:
                            user_ids.append(dept.manager_id)
                        else:
                            # 如果找不到，通知ECN申请人
                            if ecn.applicant_id:
                                user_ids.append(ecn.applicant_id)

            elif alert_type == "APPROVAL_OVERDUE":
                # 审批超时：找到审批人员
                approval_level = alert_data.get('approval_level')
                if approval_level:
                    approval = db.query(EcnApproval).filter(
                        EcnApproval.ecn_id == ecn_id,
                        EcnApproval.approval_level == approval_level,
                        EcnApproval.status == "PENDING"
                    ).first()

                    if approval and approval.approver_id:
                        user_ids.append(approval.approver_id)
                    else:
                        # 如果找不到审批人，通知ECN申请人
                        if ecn.applicant_id:
                            user_ids.append(ecn.applicant_id)

            elif alert_type == "TASK_OVERDUE":
                # 任务超时：找到执行人员
                task_id = alert_data.get('task_id')
                if task_id:
                    task = db.query(EcnTask).filter(
                        EcnTask.id == task_id,
                        EcnTask.ecn_id == ecn_id
                    ).first()

                    if task and task.assignee_id:
                        user_ids.append(task.assignee_id)
                    else:
                        # 如果找不到执行人，通知ECN申请人
                        if ecn.applicant_id:
                            user_ids.append(ecn.applicant_id)

            # 如果没有找到相关人员，通知ECN申请人
            if not user_ids and ecn.applicant_id:
                user_ids.append(ecn.applicant_id)

            # 发送通知
            if user_ids:
                notify_overdue_alert(db, alert_data, user_ids)
                results.append({
                    "alert": alert_data,
                    "status": "success",
                    "message": f"已发送提醒通知给 {len(user_ids)} 位相关人员",
                    "notified_users": user_ids
                })
                success_count += 1
            else:
                results.append({
                    "alert": alert_data,
                    "status": "failed",
                    "message": "未找到相关人员"
                })
                fail_count += 1

        except Exception as e:
            results.append({
                "alert": alert_data,
                "status": "failed",
                "message": str(e)
            })
            fail_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量处理完成：成功 {success_count} 个，失败 {fail_count} 个",
        data={
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    )
