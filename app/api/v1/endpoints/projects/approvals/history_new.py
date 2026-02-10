# -*- coding: utf-8 -*-
"""
项目审批 - history (统一审批系统)

[DEPRECATED] 此端点已废弃，请使用:
GET /api/v1/approvals/instances/{instance_id}
响应中包含 logs 字段，即审批历史
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.approval import (
    ApprovalInstance,
    ApprovalActionLog,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"


@router.get(
    "/",
    response_model=ResponseModel[List[Dict[str, Any]]],
    status_code=status.HTTP_200_OK,
    deprecated=True,
    description="[已废弃] 请使用 GET /api/v1/approvals/instances/{instance_id}",
)
@router.get(
    "/history",
    response_model=ResponseModel[List[Dict[str, Any]]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
    deprecated=True,
)
def get_project_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目审批历史（使用统一审批系统）
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
            return ResponseModel(code=200, message="项目未提交审批", data=[])

        logs = (
            db.query(ApprovalActionLog)
            .filter(ApprovalActionLog.instance_id == instance.id)
            .order_by(ApprovalActionLog.action_at.desc())
            .all()
        )

        result = []
        for log in logs:
            action_at = log.action_at
            result.append(
                {
                    "history_id": log.id,
                    "step_order": log.step_order,
                    "node_name": log.node_name,
                    "action": log.action,
                    "operator_id": log.operator_id,
                    "operator_name": log.operator_name,
                    "comment": log.comment,
                    "action_at": action_at.isoformat() if action_at else None,
                    "attachments": getattr(log, "attachments", []),
                }
            )

        return ResponseModel(
            code=200,
            message="获取成功",
            data={
                "project_id": project_id,
                "instance_id": instance.id,
                "instance_no": instance.instance_no,
                "status": instance.status,
                "history": result,
            },
        )

    except Exception as e:
        logger.error(
            f"获取项目审批历史失败: project_id={project_id}, error={str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="获取审批历史失败")
