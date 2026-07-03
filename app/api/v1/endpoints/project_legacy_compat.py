# -*- coding: utf-8 -*-
"""Compatibility routes for legacy project detail APIs.

The frontend project detail service still calls the old top-level stage/member
paths. Keep these thin aliases backed by the current project modules.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.stage_instance import ProjectStageInstance
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectMemberResponse
from app.schemas.stage_template import ProjectStageInstanceResponse
from app.services.project_members import ProjectMembersService
from app.utils.permission_helpers import check_project_read_access_or_raise

members_router = APIRouter()
stages_router = APIRouter()


@members_router.get(
    "/projects/{project_id}/members",
    response_model=PaginatedResponse[ProjectMemberResponse],
)
def list_project_members_legacy(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: str = Query(None, description="关键词搜索"),
    order_by: str = Query(None, description="排序字段"),
    order_direction: str = Query("desc", description="排序方向 (asc/desc)"),
    role: str = Query(None, description="角色筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """Legacy alias for GET /projects/{project_id}/members/."""
    check_project_read_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    members, total = service.list_members(
        project_id=project_id,
        offset=pagination.offset,
        limit=pagination.limit,
        keyword=keyword,
        order_by=order_by,
        order_direction=order_direction,
        role=role,
    )

    return PaginatedResponse(
        items=members,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@stages_router.get(
    "/projects/{project_id}/stages",
    response_model=List[ProjectStageInstanceResponse],
)
def list_project_stages_legacy(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """Legacy alias for GET /projects/{project_id}/stages/."""
    check_project_read_access_or_raise(db, current_user, project_id)

    return (
        db.query(ProjectStageInstance)
        .filter(ProjectStageInstance.project_id == project_id)
        .order_by(ProjectStageInstance.sequence)
        .all()
    )
