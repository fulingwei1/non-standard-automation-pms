# -*- coding: utf-8 -*-
"""
项目状态批量操作端点

包含批量更新状态、阶段、分配项目经理等
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectStatusLog
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import (
    BatchAssignPMRequest,
    BatchUpdateStageRequest,
    BatchUpdateStatusRequest,
)

router = APIRouter()


def _get_accessible_project_ids(db: Session, project_ids: list, current_user: User) -> set:
    """获取用户有权限访问的项目ID集合"""
    from app.services.data_scope import DataScopeService
    query = db.query(Project).filter(Project.id.in_(project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    return {p.id for p in query.all()}


@router.post("/batch/update-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_project_status(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchUpdateStatusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新项目状态
    """
    valid_statuses = [f"ST{i:02d}" for i in range(1, 31)]
    if batch_request.new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="无效的状态编码。有效值：ST01-ST30"
        )

    success_count = 0
    failed_projects = []

    accessible_project_ids = _get_accessible_project_ids(
        db, batch_request.project_ids, current_user
    )

    for project_id in batch_request.project_ids:
        try:
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue

            old_status = project.status
            if old_status == batch_request.new_status:
                continue

            project.status = batch_request.new_status
            db.add(project)

            status_log = ProjectStatusLog(
                project_id=project_id,
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
            success_count += 1

        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量状态更新完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    )


@router.post("/batch/update-stage", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchUpdateStageRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新项目阶段
    """
    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if batch_request.new_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段编码。有效值：{', '.join(valid_stages)}"
        )

    success_count = 0
    failed_projects = []

    accessible_project_ids = _get_accessible_project_ids(
        db, batch_request.project_ids, current_user
    )

    for project_id in batch_request.project_ids:
        try:
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue

            old_stage = project.stage or "S1"
            if old_stage == batch_request.new_stage:
                continue

            project.stage = batch_request.new_stage
            db.add(project)

            status_log = ProjectStatusLog(
                project_id=project_id,
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
            success_count += 1

        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量阶段更新完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    )


@router.post("/batch/assign-pm", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_assign_project_manager(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchAssignPMRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量分配项目经理
    """
    pm = db.query(User).filter(User.id == batch_request.pm_id).first()
    if not pm:
        raise HTTPException(status_code=404, detail="项目经理不存在")

    pm_name = pm.real_name or pm.username

    success_count = 0
    failed_projects = []

    accessible_project_ids = _get_accessible_project_ids(
        db, batch_request.project_ids, current_user
    )

    for project_id in batch_request.project_ids:
        try:
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue

            old_pm_id = project.pm_id
            old_pm_name = project.pm_name

            project.pm_id = batch_request.pm_id
            project.pm_name = pm_name
            db.add(project)

            if old_pm_id != batch_request.pm_id:
                status_log = ProjectStatusLog(
                    project_id=project_id,
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

            success_count += 1

        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量分配项目经理完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects,
            "pm_id": batch_request.pm_id,
            "pm_name": pm_name
        }
    )
