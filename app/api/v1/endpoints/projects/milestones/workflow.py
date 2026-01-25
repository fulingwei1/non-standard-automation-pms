# -*- coding: utf-8 -*-
"""
项目里程碑工作流操作

路由: /projects/{project_id}/milestones/{milestone_id}/complete
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project import MilestoneResponse
from app.services.project import ProjectMilestoneService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.put("/{milestone_id}/complete", response_model=MilestoneResponse)
def complete_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    actual_date: Optional[date] = Query(None, description="实际完成日期"),
    auto_trigger_invoice: bool = Query(True, description="自动触发开票"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
) -> Any:
    """
    完成项目里程碑（自动触发收款计划开票）
    """
    check_project_access_or_raise(db, current_user, project_id)
    service = ProjectMilestoneService(db, project_id)
    milestone = service.complete_milestone(
        milestone_id,
        actual_date=actual_date,
        auto_trigger_invoice=auto_trigger_invoice,
    )
    return milestone


# 注意：删除端点已由CRUD基类提供，此处不再重复定义
# 删除功能请使用: DELETE /projects/{project_id}/milestones/{milestone_id}
