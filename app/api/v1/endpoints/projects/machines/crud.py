# -*- coding: utf-8 -*-
"""
项目机台 CRUD （迁移至 BaseCRUDService）
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.crud import QueryParams
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import MachineCreate, MachineResponse, MachineUpdate
from app.services.project import ProjectMachineService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


def _get_service(db: Session, project_id: int) -> ProjectMachineService:
    return ProjectMachineService(db=db, project_id=project_id)


def _ensure_project_exists(db: Session, project_id: int) -> None:
    exists = db.query(Project.id).filter(Project.id == project_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="项目不存在")


@router.get("/", response_model=PaginatedResponse[MachineResponse])
def list_project_machines(
    project_id: int = Path(..., description="项目ID"),
    params: QueryParams = Depends(QueryParams),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    health: Optional[str] = Query(None, description="健康度筛选"),
    order_by: Optional[str] = Query(None, description="排序字段"),
    order_direction: Optional[str] = Query(None, description="排序方向 asc/desc"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """获取项目机台列表"""
    check_project_access_or_raise(db, current_user, project_id)

    params_updates = {}
    if keyword is not None:
        params_updates["search"] = keyword
    if order_by:
        params_updates["sort_by"] = order_by
    if order_direction:
        params_updates["sort_order"] = order_direction
    if params_updates:
        params = params.model_copy(update=params_updates)

    service = _get_service(db, project_id)

    extra_filters = {}
    if stage:
        extra_filters["stage"] = stage
    if status_filter:
        extra_filters["status"] = status_filter
    if health:
        extra_filters["health"] = health

    result = service.list(params=params, extra_filters=extra_filters or None)
    return PaginatedResponse(
        items=result.items,
        total=result.total,
        page=params.page,
        page_size=params.page_size,
        pages=result.pages,
    )


@router.post("/", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
def create_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_in: MachineCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:create")),
) -> MachineResponse:
    """创建项目机台"""
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中创建机台")
    _ensure_project_exists(db, project_id)

    service = _get_service(db, project_id)
    return service.create(machine_in)


@router.get("/{machine_id}", response_model=MachineResponse)
def get_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> MachineResponse:
    """获取项目机台详情"""
    check_project_access_or_raise(db, current_user, project_id)
    service = _get_service(db, project_id)
    return service.get(machine_id)


@router.put("/{machine_id}", response_model=MachineResponse)
def update_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    machine_in: MachineUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:update")),
) -> MachineResponse:
    """更新项目机台"""
    check_project_access_or_raise(db, current_user, project_id)
    service = _get_service(db, project_id)
    return service.update(machine_id, machine_in)


@router.delete(
    "/{machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:delete")),
) -> Response:
    """删除项目机台"""
    check_project_access_or_raise(db, current_user, project_id)
    service = _get_service(db, project_id)
    service.delete(machine_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
