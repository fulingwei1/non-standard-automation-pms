# -*- coding: utf-8 -*-
"""
项目状态批量操作端点

包含批量更新状态、阶段、分配项目经理等

已迁移到通用批量操作框架
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectStatusLog
from app.models.user import User
from app.schemas.common import BatchOperationResponse
from app.schemas.project import (
    BatchAssignPMRequest,
    BatchUpdateStageRequest,
    BatchUpdateStatusRequest,
)
from app.services.data_scope import DataScopeService
from app.utils.batch_operations import BatchOperationExecutor, create_scope_filter
from app.utils.db_helpers import get_or_404

router = APIRouter()

# 创建数据范围过滤函数
scope_filter = create_scope_filter(
    model=Project,
    scope_service=DataScopeService,
    filter_method="filter_projects_by_scope"
)


@router.post("/batch/update-status", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_update_project_status(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchUpdateStatusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> BatchOperationResponse:
    """
    批量更新项目状态
    """
    valid_statuses = [f"ST{i:02d}" for i in range(1, 31)]
    if batch_request.new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="无效的状态编码。有效值：ST01-ST30"
        )

    executor = BatchOperationExecutor(
        model=Project,
        db=db,
        current_user=current_user,
        scope_filter_func=scope_filter
    )
    
    def log_operation(project: Project, op_type: str):
        """记录操作日志"""
        old_status = getattr(project, '_old_status', project.status)
        status_log = ProjectStatusLog(
            project_id=project.id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status=batch_request.new_status,
            old_health=project.health,
            new_health=project.health,
            change_type="STATUS_CHANGE",
            change_reason=batch_request.reason or f"批量状态变更：{old_status} → {batch_request.new_status}",
            changed_by=current_user.id,
            changed_at=datetime.now()
        )
        db.add(status_log)
    
    result = executor.batch_status_update(
        entity_ids=batch_request.project_ids,
        new_status=batch_request.new_status,
        validator_func=lambda project: project.status != batch_request.new_status,
        error_message="状态未变更",
        log_func=log_operation
    )
    
    return BatchOperationResponse(**result.to_dict(id_field="project_id"))


@router.post("/batch/update-stage", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_update_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchUpdateStageRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> BatchOperationResponse:
    """
    批量更新项目阶段
    """
    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if batch_request.new_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段编码。有效值：{', '.join(valid_stages)}"
        )

    executor = BatchOperationExecutor(
        model=Project,
        db=db,
        current_user=current_user,
        scope_filter_func=scope_filter
    )
    
    def update_stage(project: Project):
        """更新阶段的操作函数"""
        project.stage = batch_request.new_stage
    
    def log_operation(project: Project, op_type: str):
        """记录操作日志"""
        old_stage = getattr(project, '_old_stage', project.stage or "S1")
        status_log = ProjectStatusLog(
            project_id=project.id,
            old_stage=old_stage,
            new_stage=batch_request.new_stage,
            old_status=project.status,
            new_status=project.status,
            old_health=project.health,
            new_health=project.health,
            change_type="STAGE_CHANGE",
            change_reason=batch_request.reason or f"批量阶段变更：{old_stage} → {batch_request.new_stage}",
            changed_by=current_user.id,
            changed_at=datetime.now()
        )
        db.add(status_log)
    
    result = executor.execute(
        entity_ids=batch_request.project_ids,
        operation_func=update_stage,
        validator_func=lambda project: (project.stage or "S1") != batch_request.new_stage,
        error_message="阶段未变更",
        log_func=log_operation,
        operation_type="BATCH_UPDATE_STAGE"
    )
    
    return BatchOperationResponse(**result.to_dict(id_field="project_id"))


@router.post("/batch/assign-pm", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_assign_project_manager(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchAssignPMRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> BatchOperationResponse:
    """
    批量分配项目经理
    """
    pm = get_or_404(db, User, batch_request.pm_id, detail="项目经理不存在")

    pm_name = pm.real_name or pm.username

    executor = BatchOperationExecutor(
        model=Project,
        db=db,
        current_user=current_user,
        scope_filter_func=scope_filter
    )
    
    def assign_pm(project: Project):
        """分配项目经理的操作函数"""
        project.pm_id = batch_request.pm_id
        project.pm_name = pm_name
    
    def log_operation(project: Project, op_type: str):
        """记录操作日志"""
        old_pm_id = getattr(project, '_old_pm_id', project.pm_id)
        old_pm_name = getattr(project, '_old_pm_name', project.pm_name)
        
        if old_pm_id != batch_request.pm_id:
            status_log = ProjectStatusLog(
                project_id=project.id,
                old_stage=project.stage,
                new_stage=project.stage,
                old_status=project.status,
                new_status=project.status,
                old_health=project.health,
                new_health=project.health,
                change_type="PM_CHANGE",
                change_reason=f"批量分配项目经理：{old_pm_name or '未分配'} → {pm_name}",
                changed_by=current_user.id,
                changed_at=datetime.now()
            )
            db.add(status_log)
    
    result = executor.execute(
        entity_ids=batch_request.project_ids,
        operation_func=assign_pm,
        log_func=log_operation,
        operation_type="BATCH_ASSIGN_PM"
    )
    
    return BatchOperationResponse(**result.to_dict(id_field="project_id"))
