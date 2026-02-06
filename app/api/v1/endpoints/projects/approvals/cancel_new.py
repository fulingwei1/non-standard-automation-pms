# -*- coding: utf-8 -*-
"""
项目审批 - cancel (统一审批系统)

提供cancel相关的审批功能，使用统一审批引擎
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
    "/withdraw",
    response_model=ResponseModel[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/cancel",
    response_model=ResponseModel[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def withdraw_project_approval(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    comment: str = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    撤回项目审批（使用统一审批引擎）

    仅发起人可以撤回
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

        # 获取审批实例
        instance = approval_service.get_approval_record(
            entity_type=ENTITY_TYPE_PROJECT, entity_id=project_id
        )

        if not instance:
            raise HTTPException(status_code=404, detail="审批记录不存在")

        # 验证是否为发起人
        if instance.initiator_id != current_user.id:
            raise HTTPException(status_code=403, detail="仅发起人可以撤回审批")

        # 撤回审批
        instance = approval_service.withdraw_approval(
            instance_id=instance.id,
            initiator_id=current_user.id,
            comment=comment or "发起人撤回审批",
        )

        return ResponseModel(
            code=200,
            message="审批已撤回",
            data={
                "approval_instance_id": instance.id,
                "instance_no": instance.instance_no,
                "current_status": instance.status,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"撤回项目审批失败: project_id={project_id}, error={str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="撤回审批失败，请稍后重试")
