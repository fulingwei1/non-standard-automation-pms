# -*- coding: utf-8 -*-
"""
自定义节点 API

提供在阶段中添加自定义节点的功能
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.stage_template import (
    AddCustomNodeRequest,
    ProjectNodeInstanceResponse,
)
from app.services.stage_instance import StageInstanceService

router = APIRouter()


@router.post(
    "/{stage_instance_id}/nodes/custom",
    response_model=ProjectNodeInstanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_custom_node(
    stage_instance_id: int,
    node_in: AddCustomNodeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """在阶段中添加自定义节点"""
    if node_in.stage_instance_id != stage_instance_id:
        raise HTTPException(status_code=400, detail="阶段ID不匹配")

    service = StageInstanceService(db)
    try:
        node = service.add_custom_node(
            stage_instance_id=stage_instance_id,
            node_code=node_in.node_code,
            node_name=node_in.node_name,
            node_type=node_in.node_type,
            completion_method=node_in.completion_method,
            is_required=node_in.is_required,
            planned_date=node_in.planned_date,
            insert_after_node_id=node_in.insert_after_node_id,
        )
        db.commit()
        return node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
