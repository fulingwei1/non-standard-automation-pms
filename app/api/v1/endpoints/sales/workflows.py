# -*- coding: utf-8 -*-
"""
审批工作流管理 API endpoints
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.sales import ApprovalWorkflow, ApprovalWorkflowStep
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.schemas.sales import (
    ApprovalWorkflowCreate,
    ApprovalWorkflowResponse,
    ApprovalWorkflowStepResponse,
    ApprovalWorkflowUpdate,
)

router = APIRouter()


@router.get("/approval-workflows", response_model=PaginatedResponse[ApprovalWorkflowResponse])
def list_approval_workflows(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    workflow_type: Optional[str] = Query(None, description="工作流类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审批工作流列表
    """
    query = db.query(ApprovalWorkflow).options(
        joinedload(ApprovalWorkflow.steps)
    )

    if workflow_type:
        query = query.filter(ApprovalWorkflow.workflow_type == workflow_type)

    if is_active is not None:
        query = query.filter(ApprovalWorkflow.is_active == is_active)

    total = query.count()
    workflows = apply_pagination(query.order_by(ApprovalWorkflow.created_at.desc()), pagination.offset, pagination.limit).all()

    result = []
    for workflow in workflows:
        workflow_dict = {
            **{c.name: getattr(workflow, c.name) for c in workflow.__table__.columns},
            "steps": [
                ApprovalWorkflowStepResponse(
                    **{c.name: getattr(step, c.name) for c in step.__table__.columns},
                    approver_name=step.approver.real_name if step.approver else None
                )
                for step in sorted(workflow.steps, key=lambda x: x.step_order)
            ]
        }
        result.append(ApprovalWorkflowResponse(**workflow_dict))

    return PaginatedResponse(
        items=result,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/approval-workflows", response_model=ApprovalWorkflowResponse, status_code=201)
def create_approval_workflow(
    *,
    db: Session = Depends(deps.get_db),
    workflow_in: ApprovalWorkflowCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建审批工作流
    """
    workflow_data = workflow_in.model_dump(exclude={"steps"})
    workflow = ApprovalWorkflow(**workflow_data)
    db.add(workflow)
    db.flush()

    # 创建审批步骤
    for step_data in workflow_in.steps:
        step = ApprovalWorkflowStep(
            workflow_id=workflow.id,
            **step_data.model_dump()
        )
        db.add(step)

    db.commit()
    db.refresh(workflow)

    # 加载步骤
    workflow_dict = {
        **{c.name: getattr(workflow, c.name) for c in workflow.__table__.columns},
        "steps": [
            ApprovalWorkflowStepResponse(
                **{c.name: getattr(step, c.name) for c in step.__table__.columns},
                approver_name=step.approver.real_name if step.approver else None
            )
            for step in sorted(workflow.steps, key=lambda x: x.step_order)
        ]
    }

    return ApprovalWorkflowResponse(**workflow_dict)


@router.get("/approval-workflows/{workflow_id}", response_model=ApprovalWorkflowResponse)
def get_approval_workflow(
    *,
    db: Session = Depends(deps.get_db),
    workflow_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审批工作流详情
    """
    workflow = db.query(ApprovalWorkflow).options(
        joinedload(ApprovalWorkflow.steps)
    ).filter(ApprovalWorkflow.id == workflow_id).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="审批工作流不存在")

    workflow_dict = {
        **{c.name: getattr(workflow, c.name) for c in workflow.__table__.columns},
        "steps": [
            ApprovalWorkflowStepResponse(
                **{c.name: getattr(step, c.name) for c in step.__table__.columns},
                approver_name=step.approver.real_name if step.approver else None
            )
            for step in sorted(workflow.steps, key=lambda x: x.step_order)
        ]
    }

    return ApprovalWorkflowResponse(**workflow_dict)


@router.put("/approval-workflows/{workflow_id}", response_model=ApprovalWorkflowResponse)
def update_approval_workflow(
    *,
    db: Session = Depends(deps.get_db),
    workflow_id: int,
    workflow_in: ApprovalWorkflowUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新审批工作流
    """
    workflow = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="审批工作流不存在")

    update_data = workflow_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workflow, key, value)

    db.commit()
    db.refresh(workflow)

    # 加载步骤
    workflow_dict = {
        **{c.name: getattr(workflow, c.name) for c in workflow.__table__.columns},
        "steps": [
            ApprovalWorkflowStepResponse(
                **{c.name: getattr(step, c.name) for c in step.__table__.columns},
                approver_name=step.approver.real_name if step.approver else None
            )
            for step in sorted(workflow.steps, key=lambda x: x.step_order)
        ]
    }

    return ApprovalWorkflowResponse(**workflow_dict)
