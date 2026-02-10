# -*- coding: utf-8 -*-
"""
项目审批 - submit (统一审批系统)

[DEPRECATED] 此端点已废弃，请使用: POST /api/v1/approvals/instances/submit
传入 entity_type="PROJECT", entity_id=project_id

提供submit相关的审批功能，使用统一审批引擎
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
    deprecated=True,
    description="[已废弃] 请使用 POST /api/v1/approvals/instances/submit",
)
@router.post(
    "/submit",
    response_model=ResponseModel[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
    deprecated=True,
)
def submit_project_approval(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    workflow_id: int = None,  # 可选，不提供时使用默认流程
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交项目审批（使用统一审批引擎）

    - 检查项目状态
    - 使用 WorkflowEngine 创建审批实例
    - 更新项目审批状态
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查项目状态
    if project.approval_status == "PENDING":
        raise HTTPException(status_code=400, detail="项目已在审批中")
    if project.approval_status == "APPROVED":
        raise HTTPException(status_code=400, detail="项目已审批通过")

    # 使用统一审批引擎提交审批
    try:
        approval_service = ApprovalEngineService(db)

        # 构建表单数据
        form_data = {
            "project_code": project.project_code,
            "project_name": project.project_name,
            "short_name": project.short_name,
            "project_type": project.project_type,
            "project_category": project.project_category,
            "priority": project.priority,
            "customer_id": project.customer_id,
            "customer_name": project.customer_name,
            "contract_amount": float(project.contract_amount)
            if project.contract_amount
            else 0,
            "budget_amount": float(project.budget_amount)
            if project.budget_amount
            else 0,
            "actual_cost": float(project.actual_cost) if project.actual_cost else 0,
            "progress_pct": float(project.progress_pct) if project.progress_pct else 0,
            "pm_id": project.pm_id,
            "pm_name": project.pm_name,
            "dept_id": project.dept_id,
            "planned_start_date": project.planned_start_date.isoformat()
            if project.planned_start_date
            else None,
            "planned_end_date": project.planned_end_date.isoformat()
            if project.planned_end_date
            else None,
        }

        # 提交审批
        instance = approval_service.submit(
            template_code="PROJECT_TEMPLATE",
            entity_type=ENTITY_TYPE_PROJECT,
            entity_id=project_id,
            form_data=form_data,
            initiator_id=current_user.id,
            title=None,  # 适配器会自动生成
            summary=None,  # 适配器会自动生成
            urgency="NORMAL",
            cc_user_ids=None,
        )

        return ResponseModel(
            code=200,
            message="项目审批已提交",
            data={
                "approval_instance_id": instance.id,
                "instance_no": instance.instance_no,
                "current_status": instance.status,
                "current_node_id": instance.current_node_id,
                "project_status": project.status,
            },
        )

    except ValueError as e:
        # 验证错误（如状态不允许提交）
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"提交项目审批失败: project_id={project_id}, error={str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="提交审批失败，请稍后重试")
