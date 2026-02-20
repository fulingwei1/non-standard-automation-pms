# -*- coding: utf-8 -*-
"""
项目成员 CRUD 操作（重构版本 - 薄控制器）

使用服务层处理业务逻辑，endpoint 仅负责请求处理和响应
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Path, Body, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import (
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse
)
from app.utils.permission_helpers import check_project_access_or_raise
from app.common.pagination import PaginationParams, get_pagination_query
from app.services.project_members import ProjectMembersService


router = APIRouter()


# ==================== CRUD 操作 ====================


@router.get("/", response_model=PaginatedResponse[ProjectMemberResponse])
def list_project_members(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: str = Query(None, description="关键词搜索"),
    order_by: str = Query(None, description="排序字段"),
    order_direction: str = Query("desc", description="排序方向 (asc/desc)"),
    role: str = Query(None, description="角色筛选"),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员列表（支持分页、搜索、排序、筛选）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectMembersService(db)
    members, total = service.list_members(
        project_id=project_id,
        offset=pagination.offset,
        limit=pagination.limit,
        keyword=keyword,
        order_by=order_by,
        order_direction=order_direction,
        role=role
    )
    
    return PaginatedResponse(
        items=members,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/", response_model=ProjectMemberResponse, status_code=201)
def add_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_in: ProjectMemberCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """为项目添加成员"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限在该项目中添加成员"
    )
    
    service = ProjectMembersService(db)
    member = service.create_member(
        project_id=project_id,
        user_id=member_in.user_id,
        role_code=member_in.role_code,
        allocation_pct=member_in.allocation_pct,
        start_date=member_in.start_date,
        end_date=member_in.end_date,
        commitment_level=member_in.commitment_level,
        reporting_to_pm=member_in.reporting_to_pm,
        remark=member_in.remark,
        created_by=current_user.id
    )
    
    return member


@router.get("/{member_id}", response_model=ProjectMemberResponse)
def get_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员详情"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectMembersService(db)
    return service.get_member_by_id(project_id, member_id)


@router.put("/{member_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    member_in: ProjectMemberUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """更新项目成员信息"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectMembersService(db)
    update_data = member_in.model_dump(exclude_unset=True)
    return service.update_member(project_id, member_id, update_data)


@router.delete("/{member_id}", status_code=204)
def remove_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
):
    """移除项目成员"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectMembersService(db)
    service.delete_member(project_id, member_id)


# ==================== 冲突检查 ====================


@router.get("/conflicts", response_model=dict)
def check_member_conflicts(
    project_id: int = Path(..., description="项目ID"),
    user_id: int = Query(..., description="用户ID"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """检查成员分配冲突"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectMembersService(db)
    return service.check_member_conflicts(
        user_id, start_date, end_date, project_id
    )


# ==================== 批量添加 ====================


class BatchAddMembersRequest(BaseModel):
    """批量添加成员请求"""
    user_ids: List[int]
    role_code: str
    allocation_pct: float = 100
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    commitment_level: Optional[str] = None
    reporting_to_pm: bool = True


@router.post("/batch", response_model=dict)
def batch_add_project_members(
    project_id: int = Path(..., description="项目ID"),
    request: BatchAddMembersRequest = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """批量添加项目成员"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限在该项目中添加成员"
    )
    
    service = ProjectMembersService(db)
    return service.batch_add_members(
        project_id=project_id,
        user_ids=request.user_ids,
        role_code=request.role_code,
        allocation_pct=request.allocation_pct,
        start_date=request.start_date,
        end_date=request.end_date,
        commitment_level=request.commitment_level,
        reporting_to_pm=request.reporting_to_pm,
        created_by=current_user.id
    )


# ==================== 扩展功能 ====================


@router.post("/{member_id}/notify-dept-manager", response_model=ResponseModel)
def notify_dept_manager(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """通知部门经理（成员加入项目）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectMembersService(db)
    result = service.notify_dept_manager(project_id, member_id)
    
    return ResponseModel(code=200, message=result['message'])


@router.get("/from-dept/{dept_id}", response_model=dict)
def get_dept_users_for_project(
    project_id: int = Path(..., description="项目ID"),
    dept_id: int = Path(..., description="部门ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取部门用户列表（用于批量添加成员）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = ProjectMembersService(db)
    return service.get_dept_users_for_project(project_id, dept_id)
