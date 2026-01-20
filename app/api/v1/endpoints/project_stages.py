# -*- coding: utf-8 -*-
"""
项目阶段实例 API
提供项目阶段/节点的初始化、状态流转、进度查询等接口
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.stage_template import (
    AddCustomNodeRequest,
    InitializeProjectStagesRequest,
    ProjectNodeInstanceComplete,
    ProjectNodeInstanceResponse,
    ProjectNodeInstanceUpdate,
    ProjectProgressResponse,
    ProjectStageInstanceDetail,
    ProjectStageInstanceResponse,
    ProjectStageInstanceUpdate,
)
from app.services.stage_instance_service import StageInstanceService

router = APIRouter()


# ==================== 项目阶段初始化 ====================


@router.post("/{project_id}/stages/initialize", response_model=MessageResponse)
def initialize_project_stages(
    project_id: int,
    init_in: InitializeProjectStagesRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    初始化项目阶段

    根据模板为项目创建阶段和节点实例，支持调整配置：
    - skip_stages: 跳过某些阶段
    - skip_nodes: 跳过某些节点
    - stage_overrides: 调整阶段配置（工期、名称等）
    - node_overrides: 调整节点配置
    """
    service = StageInstanceService(db)
    try:
        # 构建调整配置
        adjustments = {}
        if init_in.skip_stages:
            adjustments["skip_stages"] = init_in.skip_stages
        if init_in.skip_nodes:
            adjustments["skip_nodes"] = init_in.skip_nodes
        if init_in.stage_overrides:
            adjustments["stage_overrides"] = {
                k: v.model_dump(exclude_unset=True)
                for k, v in init_in.stage_overrides.items()
            }
        if init_in.node_overrides:
            adjustments["node_overrides"] = {
                k: v.model_dump(exclude_unset=True)
                for k, v in init_in.node_overrides.items()
            }

        stages = service.initialize_project_stages(
            project_id=project_id,
            template_id=init_in.template_id,
            start_date=init_in.start_date,
            adjustments=adjustments if adjustments else None,
        )
        db.commit()
        return {"message": f"成功创建 {len(stages)} 个阶段"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/stages/clear", response_model=MessageResponse)
def clear_project_stages(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """清除项目的所有阶段实例"""
    service = StageInstanceService(db)
    count = service.clear_project_stages(project_id)
    db.commit()
    return {"message": f"已清除 {count} 个阶段"}


# ==================== 进度查询 ====================


@router.get("/{project_id}/progress", response_model=ProjectProgressResponse)
def get_project_progress(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """获取项目阶段进度概览"""
    service = StageInstanceService(db)
    return service.get_project_progress(project_id)


@router.get("/stages/{stage_instance_id}", response_model=ProjectStageInstanceDetail)
def get_stage_detail(
    stage_instance_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """获取阶段详情（包含所有节点）"""
    service = StageInstanceService(db)
    detail = service.get_stage_detail(stage_instance_id)
    if not detail:
        raise HTTPException(status_code=404, detail="阶段实例不存在")
    return detail


# ==================== 阶段状态流转 ====================


@router.post("/stages/{stage_instance_id}/start", response_model=ProjectStageInstanceResponse)
def start_stage(
    stage_instance_id: int,
    actual_start_date: Optional[date] = Query(None, description="实际开始日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """开始阶段"""
    service = StageInstanceService(db)
    try:
        stage = service.start_stage(stage_instance_id, actual_start_date)
        db.commit()
        return stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stages/{stage_instance_id}/complete", response_model=ProjectStageInstanceResponse)
def complete_stage(
    stage_instance_id: int,
    actual_end_date: Optional[date] = Query(None, description="实际结束日期"),
    auto_start_next: bool = Query(True, description="是否自动开始下一阶段"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """完成阶段"""
    service = StageInstanceService(db)
    try:
        stage, next_stage = service.complete_stage(
            stage_instance_id,
            actual_end_date,
            auto_start_next,
        )
        db.commit()
        return stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stages/{stage_instance_id}/skip", response_model=ProjectStageInstanceResponse)
def skip_stage(
    stage_instance_id: int,
    reason: Optional[str] = Query(None, description="跳过原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """跳过阶段"""
    service = StageInstanceService(db)
    try:
        stage = service.skip_stage(stage_instance_id, reason)
        db.commit()
        return stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/stages/{stage_instance_id}", response_model=ProjectStageInstanceResponse)
def update_stage_instance(
    stage_instance_id: int,
    update_in: ProjectStageInstanceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """更新阶段实例信息"""
    from app.models.stage_instance import ProjectStageInstance

    stage = db.query(ProjectStageInstance).filter(
        ProjectStageInstance.id == stage_instance_id
    ).first()

    if not stage:
        raise HTTPException(status_code=404, detail="阶段实例不存在")

    update_data = update_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stage, key, value)

    db.commit()
    db.refresh(stage)
    return stage


# ==================== 节点状态流转 ====================


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
    from app.models.stage_instance import ProjectNodeInstance

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


# ==================== 自定义节点 ====================


@router.post("/stages/{stage_instance_id}/nodes/custom", response_model=ProjectNodeInstanceResponse, status_code=status.HTTP_201_CREATED)
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
