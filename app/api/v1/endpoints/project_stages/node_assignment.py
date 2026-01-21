# -*- coding: utf-8 -*-
"""
节点分配 API

提供节点负责人分配功能
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.stage_template import AssignNodeRequest, ProjectNodeInstanceResponse
from app.services.stage_instance import StageInstanceService

router = APIRouter()


@router.put("/nodes/{node_instance_id}/assign", response_model=ProjectNodeInstanceResponse)
def assign_node(
    node_instance_id: int,
    assign_in: AssignNodeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    分配节点负责人

    PM 将节点分配给工程师后，工程师可以创建子任务来分解工作。
    """
    service = StageInstanceService(db)
    try:
        node = service.assign_node(
            node_instance_id=node_instance_id,
            assignee_id=assign_in.assignee_id,
            auto_complete_on_tasks=assign_in.auto_complete_on_tasks,
        )
        db.commit()
        return node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
