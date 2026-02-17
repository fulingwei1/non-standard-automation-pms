# -*- coding: utf-8 -*-
"""
项目审批 - status (统一审批系统)

[DEPRECATED] 此端点已废弃，请使用:
GET /api/v1/approvals/instances/{instance_id}
或 GET /api/v1/approvals/instances/by-entity/PROJECT/{project_id}

重构说明：
- 从直接数据库操作改为使用 ApprovalEngineService
- 利用审批引擎的查询、权限检查、通知等功能
- 保持与原有 API 的兼容性
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
from app.services.approval_engine.engine.__init__ import ApprovalEngineService
from app.utils.db_helpers import get_or_404

logger = logging.getLogger(__name__)

router = APIRouter()

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"

# 已移除 GET "/" 路由，避免与项目CRUD的 GET /projects/ 冲突
@router.get(
    "/status",
    response_model=ResponseModel[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    deprecated=True,
    description="[已废弃] 请使用 GET /api/v1/approvals/instances/{instance_id}",
)
def get_project_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目审批状态（使用统一审批系统）
    
    重构说明：
    - 使用 ApprovalEngineService.get_approval_record() 获取审批记录
    - 通过引擎的查询能力获取审批任务和日志
    - 保持与原有响应格式的兼容性
    """
    project = get_or_404(db, Project, project_id, detail="项目不存在")
    
    try:
        # 使用统一审批引擎获取审批记录
        approval_service = ApprovalEngineService(db)
        
        # 获取最新审批记录
        instance = approval_service.get_approval_record(
            template_code="PROJECT_TEMPLATE",
            entity_type=ENTITY_TYPE_PROJECT,
            entity_id=project_id,
        )
        
        if not instance:
            # 未提交审批
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
                    "submitted_at": None,
                    "progress": 0,
                    "can_approve": False,
                    "can_reject": False,
                    "can_withdraw": False,
                    "history": [],
                },
            )
        
        # 获取审批任务（通过引擎的查询能力）
        tasks = approval_service.get_pending_tasks(instance.id)
        
        # 获取审批日志
        logs = approval_service.get_approval_logs(instance.id)
        
        # 构建响应数据（保持与原格式兼容）
        progress = 0
        total_nodes = instance.total_nodes if instance.total_nodes else 0
        
        if instance.current_node_order and total_nodes > 0:
            progress = int((instance.current_node_order / total_nodes) * 100)
        
        # 获取当前步骤和审批人信息
        current_step_name = None
        current_approver_name = None
        
        if tasks:
            current_task = tasks[0]
            if hasattr(current_task, 'node_name'):
                current_step_name = current_task.node_name
            if hasattr(current_task, 'assignee_name'):
                current_approver_name = current_task.assignee_name
        
        # 判断用户权限
        can_approve = False
        can_reject = False
        can_withdraw = False
        
        # 判断当前用户是否是审批人
        if current_user.id in [task.assignee_id for task in tasks]:
            # 当前用户是审批人之一
            can_approve = True
            can_reject = True
        
        # 判断是否可以撤回（发起人或管理员）
        if instance.initiator_id == current_user.id or current_user.is_superuser:
            if instance.status == "PENDING":
                can_withdraw = True
        
        # 构建审批历史（保持与原格式兼容）
        history = []
        for log in logs:
            if hasattr(log, 'step_order'):
                history.append({
                    "step_order": log.step_order,
                    "action": log.action,
                    "operator_name": log.operator_name,
                    "comment": log.comment,
                    "action_at": log.action_at.isoformat() if log.action_at else None,
                })
        
        submitted_at = instance.submitted_at.isoformat() if instance.submitted_at else None
        
        return ResponseModel(
            code=200,
            message="获取成功",
            data={
                "project_id": project_id,
                "instance_id": instance.id,
                "instance_no": instance.instance_no,
                "status": instance.status,
                "urgency": instance.urgency,
                "current_step": current_step_name,
                "current_approver": current_approver_name,
                "submitted_at": submitted_at,
                "progress": progress,
                "can_approve": can_approve,
                "can_reject": can_reject,
                "can_withdraw": can_withdraw,
                "history": history,
            },
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取项目审批状态失败: project_id={project_id}, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取审批状态失败，请稍后重试")


__all__ = ["router"]
