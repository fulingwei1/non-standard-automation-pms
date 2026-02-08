# -*- coding: utf-8 -*-
"""
项目里程碑工作流操作（基于统一状态机框架）

路由: /projects/{project_id}/milestones/{milestone_id}/complete
"""

import logging
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.state_machine.milestone import MilestoneStateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    StateMachineValidationError,
)
from app.models.project import ProjectMilestone
from app.models.user import User
from app.schemas.project import MilestoneResponse
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()
logger = logging.getLogger(__name__)


@router.put("/{milestone_id}/complete", response_model=MilestoneResponse)
def complete_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    actual_date: Optional[date] = Query(None, description="实际完成日期"),
    auto_trigger_invoice: bool = Query(True, description="自动触发开票"),
    comment: Optional[str] = Query(None, description="备注"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
) -> Any:
    """
    完成项目里程碑（自动触发收款计划开票）

    状态转换: PENDING → COMPLETED
    自动触发: 收款计划开票
    """
    # 检查项目访问权限
    check_project_access_or_raise(db, current_user, project_id)

    # 获取里程碑
    milestone = (
        db.query(ProjectMilestone)
        .filter(
            ProjectMilestone.id == milestone_id,
            ProjectMilestone.project_id == project_id,
        )
        .first()
    )

    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    # 检查当前状态
    if milestone.status == "COMPLETED":
        # 已完成，直接返回
        logger.info(f"里程碑 {milestone.milestone_code} 已完成，无需重复操作")
        return milestone

    # 初始化状态机
    state_machine = MilestoneStateMachine(milestone, db)

    # 执行状态转换
    try:
        state_machine.transition_to(
            "COMPLETED",
            current_user=current_user,
            comment=comment or f"完成里程碑：{milestone.milestone_name}",
            actual_date=actual_date,
            auto_trigger_invoice=auto_trigger_invoice,
        )

        db.commit()
        db.refresh(milestone)

        return milestone

    except InvalidStateTransitionError as e:
        logger.error(f"里程碑状态转换失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        logger.error(f"权限拒绝: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        logger.error(f"状态机验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTPException (from _ensure_can_complete check)
        raise
    except Exception as e:
        logger.error(f"完成里程碑失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"完成里程碑失败: {str(e)}")
