# -*- coding: utf-8 -*-
"""
项目节点操作 API

提供节点的启动、完成、跳过、更新等操作
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.stage_instance import ProjectNodeInstance
from app.models.user import User
from app.schemas.stage_template import (
    ProjectNodeInstanceComplete,
    ProjectNodeInstanceResponse,
    ProjectNodeInstanceUpdate,
)
from app.services.stage_instance import StageInstanceService

router = APIRouter()


@router.post("/nodes/{node_instance_id}/start", response_model=ProjectNodeInstanceResponse)
def start_node(
    node_instance_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """开始节点"""
    service = StageInstanceService(db)
    try:
        node = service.start_node(node_instance_id)
        db.commit()
        return node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/nodes/{node_instance_id}/complete", response_model=ProjectNodeInstanceResponse)
def complete_node(
    node_instance_id: int,
    complete_in: ProjectNodeInstanceComplete,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """完成节点"""
    service = StageInstanceService(db)
    try:
        node = service.complete_node(
            node_instance_id=node_instance_id,
            completed_by=current_user.id,
            attachments=complete_in.attachments,
            approval_record_id=complete_in.approval_record_id,
            remark=complete_in.remark,
        )
        db.commit()
        return node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/nodes/{node_instance_id}/skip", response_model=ProjectNodeInstanceResponse)
def skip_node(
    node_instance_id: int,
    reason: Optional[str] = Query(None, description="跳过原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """跳过节点"""
    service = StageInstanceService(db)
    try:
        node = service.skip_node(node_instance_id, reason)
        db.commit()
        return node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/nodes/{node_instance_id}", response_model=ProjectNodeInstanceResponse)
def update_node_instance(
    node_instance_id: int,
    update_in: ProjectNodeInstanceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """更新节点实例信息"""
    node = db.query(ProjectNodeInstance).filter(
        ProjectNodeInstance.id == node_instance_id
    ).first()

    if not node:
        raise HTTPException(status_code=404, detail="节点实例不存在")

    update_data = update_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(node, key, value)

    db.commit()
    db.refresh(node)
    return node


@router.put("/nodes/{node_instance_id}/planned-date", response_model=ProjectNodeInstanceResponse)
def update_node_planned_date(
    node_instance_id: int,
    planned_date: date = Query(..., description="计划完成日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """更新节点计划日期"""
    service = StageInstanceService(db)
    try:
        node = service.update_node_planned_date(node_instance_id, planned_date)
        db.commit()
        return node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
