# -*- coding: utf-8 -*-
"""
项目审批 - action (统一审批系统)

提供action相关的审批功能，使用统一审批引擎
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.approval_engine import ApprovalEngineService

logger = logging.getLogger(__name__)

router = APIRouter()

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"


@router.post(
    "/",
    response_model=ResponseModel[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/action",
    response_model=ResponseModel[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def perform_project_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    decision: str,
    comment: str = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行项目审批动作（使用统一审批引擎）

    - APPROVE: 审批通过
    - REJECT: 审批驳回
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查项目审批状态（旧系统的字段）
    if project.approval_status not in ["PENDING"]:
        raise HTTPException(
            status_code=400,
            detail=f"项目不在审批中，当前状态：{project.approval_status}",
        )

    try:
        approval_service = ApprovalEngineService(db)

        # 获取审批实例（通过实体类型和ID）
        instance = approval_service.get_approval_record(
            entity_type=ENTITY_TYPE_PROJECT, entity_id=project_id
        )

        if not instance:
            raise HTTPException(status_code=404, detail="审批记录不存在")

        if instance.status not in ["PENDING", "IN_PROGRESS"]:
            raise HTTPException(
                status_code=400,
                detail=f"审批实例不在进行中，当前状态：{instance.status}",
            )

        # 执行审批动作
        if decision.upper() == "APPROVE":
            # 审批通过
            instance = approval_service.approve_step(
                instance_id=instance.id, approver_id=current_user.id, comment=comment
            )
            message = "审批通过"
            data_status = "APPROVED"

        elif decision.upper() == "REJECT":
            # 审批驳回
            instance = approval_service.reject_step(
                instance_id=instance.id,
                approver_id=current_user.id,
                comment=comment or "审批驳回",
            )
            message = "审批已驳回"
            data_status = "REJECTED"

        else:
            raise HTTPException(status_code=400, detail=f"不支持的审批动作：{decision}")

        return ResponseModel(
            code=200,
            message=message,
            data={
                "approval_instance_id": instance.id,
                "instance_no": instance.instance_no,
                "current_status": instance.status,
                "current_node_id": instance.current_node_id,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"执行项目审批操作失败: project_id={project_id}, decision={decision}, error={str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="审批操作失败，请稍后重试")
