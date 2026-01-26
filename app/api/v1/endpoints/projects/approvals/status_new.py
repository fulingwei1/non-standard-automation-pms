# -*- coding: utf-8 -*-
"""
项目审批 - status (统一审批系统)
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.approval import ApprovalInstance, ApprovalTask, ApprovalActionLog
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"


@router.get(
    "/approval/status",
    response_model=ResponseModel[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_project_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目审批状态（使用统一审批系统）

    返回：
    - 审批实例信息
    - 当前步骤
    - 审批进度
    - 可执行的操作
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    try:
        instance = (
            db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == ENTITY_TYPE_PROJECT,
                ApprovalInstance.entity_id == project_id,
            )
            .order_by(ApprovalInstance.submitted_at.desc())
            .first()
        )

        if not instance:
            return ResponseModel(
                code=200,
                message="项目未提交审批",
                data={
                    "project_id": project_id,
                    "instance_id": None,
                    "instance_no": None,
                    "status": "NOT_SUBMITTED",
                    "current_step": None,
                    "current_approver": None,
                    "progress": 0,
                    "can_approve": False,
                    "can_reject": False,
                    "can_withdraw": False,
                },
            )

        tasks = (
            db.query(ApprovalTask)
            .filter(
                ApprovalTask.instance_id == instance.id,
                ApprovalTask.status == "PENDING",
            )
            .all()
        )

        first_task = tasks[0] if tasks else None

        # 获取审批历史
        logs = (
            db.query(ApprovalActionLog)
            .filter(ApprovalActionLog.instance_id == instance.id)
            .order_by(ApprovalActionLog.action_at.desc())
            .all()
        )

        # 判断当前用户的操作权限
        can_approve = False
        can_reject = False
        can_withdraw = False

        status_value = instance.status
        if status_value in ["PENDING", "IN_PROGRESS"]:
            if first_task:
                if first_task.assignee_id == current_user.id:
                    can_approve = True
                    can_reject = True

            if instance.initiator_id == current_user.id:
                can_withdraw = True

        # 计算进度
        progress = 0
        total_nodes_value = instance.total_nodes
        if total_nodes_value:
            current_level = instance.current_node_order or 0
            total_levels = total_nodes_value or 0
            if status_value == "APPROVED":
                progress = 100
            elif status_value == "REJECTED":
                progress = 0
            else:
                progress = (
                    int((current_level / total_levels) * 100) if total_levels > 0 else 0
                )

        current_step_name = None
        current_approver_name = None
        if first_task:
            current_step_name = first_task.node_name
            current_approver_name = first_task.assignee_name

        submitted_at = instance.submitted_at
        return ResponseModel(
            code=200,
            message="获取成功",
            data={
                "project_id": project_id,
                "instance_id": instance.id,
                "instance_no": instance.instance_no,
                "status": status_value,
                "urgency": instance.urgency,
                "current_step": current_step_name,
                "current_approver": current_approver_name,
                "submitted_at": submitted_at.isoformat() if submitted_at else None,
                "progress": progress,
                "can_approve": can_approve,
                "can_reject": can_reject,
                "can_withdraw": can_withdraw,
                "history": [
                    {
                        "step_order": log.step_order,
                        "action": log.action,
                        "operator_name": log.operator_name,
                        "comment": log.comment,
                        "action_at": log.action_at.isoformat()
                        if log.action_at
                        else None,
                    }
                    for log in logs
                ],
            },
        )

    except Exception as e:
        logger.error(
            f"获取项目审批状态失败: project_id={project_id}, error={str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="获取审批状态失败")
