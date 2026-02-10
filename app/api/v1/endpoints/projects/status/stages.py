# -*- coding: utf-8 -*-
"""
项目阶段管理端点

包含阶段初始化、阶段推进、阶段门校验、状态历史等
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import ProjectStage, ProjectStatusLog
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import StageAdvanceRequest

from ..utils import _serialize_project_status_log, check_gate_detailed
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.post("/{project_id}/stages/init", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def init_project_stages(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    初始化项目阶段
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    existing_stages = db.query(ProjectStage).filter(
        ProjectStage.project_id == project_id
    ).count()

    if existing_stages > 0:
        return ResponseModel(
            code=200,
            message="项目阶段已存在，无需重复初始化",
            data={"project_id": project_id, "stage_count": existing_stages}
        )

    from app.utils.project_utils import init_project_stages as do_init_stages
    do_init_stages(db, project_id)

    stage_count = db.query(ProjectStage).filter(
        ProjectStage.project_id == project_id
    ).count()

    return ResponseModel(
        code=200,
        message="项目阶段初始化成功",
        data={"project_id": project_id, "stage_count": stage_count}
    )


@router.get("/{project_id}/status-history", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_status_history(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    change_type: Optional[str] = Query(None, description="变更类型筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目状态变更历史
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectStatusLog).filter(
        ProjectStatusLog.project_id == project_id
    )

    if change_type:
        query = query.filter(ProjectStatusLog.change_type == change_type)

    total = query.count()
    logs = query.order_by(desc(ProjectStatusLog.changed_at)).offset(pagination.offset).limit(pagination.limit).all()

    items = [_serialize_project_status_log(log) for log in logs]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/{project_id}/stage-advance", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def advance_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    advance_request: StageAdvanceRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目阶段推进（含阶段门校验）
    """
    from app.services.stage_advance_service import (
        create_installation_dispatch_orders,
        create_status_log,
        generate_cost_review_report,
        perform_gate_check,
        update_project_stage_and_status,
        validate_stage_advancement,
        validate_target_stage,
    )
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    validate_target_stage(advance_request.target_stage)

    current_stage = project.stage or "S1"
    validate_stage_advancement(current_stage, advance_request.target_stage)

    gate_passed, missing_items, gate_check_result = perform_gate_check(
        db, project, advance_request.target_stage,
        advance_request.skip_gate_check, current_user.is_superuser
    )

    if not gate_passed:
        return ResponseModel(
            code=400,
            message="阶段门校验未通过",
            data={
                "project_id": project_id,
                "target_stage": advance_request.target_stage,
                "gate_passed": False,
                "missing_items": missing_items,
                "gate_check_result": gate_check_result,
            }
        )

    old_stage = current_stage
    old_status = project.status

    new_status = update_project_stage_and_status(
        db, project, advance_request.target_stage, old_stage, old_status
    )

    create_status_log(
        db, project_id, old_stage, advance_request.target_stage,
        old_status, new_status, project.health,
        advance_request.reason, current_user.id
    )

    create_installation_dispatch_orders(
        db, project, advance_request.target_stage, old_stage
    )

    generate_cost_review_report(
        db, project_id, advance_request.target_stage, new_status, current_user.id
    )

    # 创建阶段切换时的齐套率快照
    try:
        from app.utils.scheduled_tasks import create_stage_change_snapshot
        create_stage_change_snapshot(
            db=db,
            project_id=project_id,
            from_stage=old_stage,
            to_stage=advance_request.target_stage,
        )
    except Exception as e:
        # 快照失败不影响阶段推进
        import logging
        logging.getLogger(__name__).warning(f"创建阶段切换快照失败: {e}")

    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=200,
        message="阶段推进成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "old_stage": old_stage,
            "new_stage": advance_request.target_stage,
            "new_status": new_status,
            "gate_passed": gate_passed,
            "gate_check_result": check_gate_detailed(db, project, advance_request.target_stage) if not advance_request.skip_gate_check else None,
        }
    )


@router.post("/{project_id}/check-auto-transition", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def check_auto_stage_transition(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    auto_advance: bool = Query(False, description="是否自动推进"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查阶段自动流转条件
    """
    from app.services.status_transition_service import StatusTransitionService
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    transition_service = StatusTransitionService(db)
    result = transition_service.check_auto_stage_transition(project_id, auto_advance=auto_advance)

    return ResponseModel(
        code=200,
        message=result.get("message", "检查完成"),
        data=result
    )


@router.get("/{project_id}/gate-check/{target_stage}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_gate_check_result(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    target_stage: str = Path(..., description="目标阶段（S2-S9）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取阶段门校验详细结果
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    valid_stages = ['S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if target_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的目标阶段。有效值：{', '.join(valid_stages)}"
        )

    gate_check_result = check_gate_detailed(db, project, target_stage)

    return ResponseModel(
        code=200,
        message="获取阶段门校验结果成功",
        data=gate_check_result
    )
