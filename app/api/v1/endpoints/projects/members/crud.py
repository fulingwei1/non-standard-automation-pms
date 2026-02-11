# -*- coding: utf-8 -*-
"""
项目成员 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
包含批量添加、冲突检查、部门经理通知等扩展功能
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.core import security
from app.models.organization import Department, Employee
from app.models.project import ProjectMember, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import (
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse
)
from app.utils.permission_helpers import check_project_access_or_raise
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter


def filter_by_role(query, role: str):
    """自定义角色筛选器"""
    return query.filter(ProjectMember.role_code == role)


def enrich_member_response(member: ProjectMember) -> ProjectMember:
    """填充成员的username和real_name"""
    if member.user:
        member.username = member.user.username
        member.real_name = member.user.real_name
    else:
        member.username = "Unknown"
        member.real_name = "Unknown"
    return member


# 使用项目中心CRUD路由基类创建路由（用于获取基础路由结构）
base_router = create_project_crud_router(
    model=ProjectMember,
    create_schema=ProjectMemberCreate,
    update_schema=ProjectMemberUpdate,
    response_schema=ProjectMemberResponse,
    permission_prefix="project",
    project_id_field="project_id",
    keyword_fields=["remark"],
    default_order_by="created_at",
    default_order_direction="desc",
    custom_filters={
        "role": filter_by_role,
    },
)

# 创建新的router，覆盖所有端点以添加填充用户信息的逻辑
router = APIRouter()


# 覆盖列表端点，添加填充用户信息逻辑
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
    
    # 构建查询
    query = db.query(ProjectMember).filter(ProjectMember.project_id == project_id)
    
    # 角色筛选
    if role:
        query = query.filter(ProjectMember.role_code == role)
    
    # 关键词搜索
    query = apply_keyword_filter(query, ProjectMember, keyword, "remark")
    
    # 排序
    order_field = getattr(ProjectMember, order_by or "created_at", None)
    if order_field:
        if order_direction == "asc":
            query = query.order_by(order_field.asc())
        else:
            query = query.order_by(order_field.desc())
    
    # 分页
    total = query.count()
    members = query.offset(pagination.offset).limit(pagination.limit).all()
    
    # 填充用户信息
    for member in members:
        enrich_member_response(member)
    
    return PaginatedResponse(
        items=members,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


# 覆盖创建端点，添加重复检查和填充用户信息逻辑
@router.post("/", response_model=ProjectMemberResponse, status_code=201)
def add_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_in: ProjectMemberCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """为项目添加成员（覆盖基类端点，添加重复检查逻辑）"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限在该项目中添加成员"
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否已是项目成员
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_in.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该用户已是项目成员")
    
    # 准备成员数据，强制使用路径中的 project_id
    member_data = member_in.model_dump(exclude_unset=True)
    member_data["project_id"] = project_id
    
    member = ProjectMember(**member_data)
    db.add(member)
    db.commit()
    db.refresh(member)
    
    # 填充用户信息
    return enrich_member_response(member)


# 覆盖详情端点，添加填充用户信息逻辑
@router.get("/{member_id}", response_model=ProjectMemberResponse)
def get_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员详情（覆盖基类端点，填充用户信息）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")
    
    # 填充用户信息
    return enrich_member_response(member)


# 覆盖更新端点，添加填充用户信息逻辑
@router.put("/{member_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    member_in: ProjectMemberUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """更新项目成员信息（覆盖基类端点，填充用户信息）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")
    
    update_data = member_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(member, field):
            setattr(member, field, value)
    
    db.add(member)
    db.commit()
    db.refresh(member)
    
    # 填充用户信息
    return enrich_member_response(member)


# 覆盖删除端点
@router.delete("/{member_id}", status_code=204)
def remove_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
):
    """移除项目成员（覆盖基类端点）"""
    check_project_access_or_raise(db, current_user, project_id)

    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id,
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    db.delete(member)
    db.commit()


# ==================== 冲突检查 ====================


def check_member_conflicts_internal(
    db: Session,
    user_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    exclude_project_id: Optional[int] = None
) -> dict:
    """检查成员分配冲突（内部函数）"""
    if not start_date or not end_date:
        return {'has_conflict': False}

    query = db.query(ProjectMember).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.is_active == True,
        or_(
            and_(ProjectMember.start_date <= start_date, ProjectMember.end_date >= start_date),
            and_(ProjectMember.start_date <= end_date, ProjectMember.end_date >= end_date),
            and_(ProjectMember.start_date >= start_date, ProjectMember.end_date <= end_date)
        )
    )

    if exclude_project_id:
        query = query.filter(ProjectMember.project_id != exclude_project_id)

    conflicting_members = query.all()

    if not conflicting_members:
        return {'has_conflict': False}

    conflicting_projects = []
    for member in conflicting_members:
        project = db.query(Project).filter(Project.id == member.project_id).first()
        if project:
            conflicting_projects.append({
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'allocation_pct': float(member.allocation_pct or 100),
                'start_date': member.start_date.isoformat() if member.start_date else None,
                'end_date': member.end_date.isoformat() if member.end_date else None,
            })

    user = db.query(User).filter(User.id == user_id).first()
    user_name = user.real_name or user.username if user else f'User {user_id}'

    return {
        'has_conflict': True,
        'user_id': user_id,
        'user_name': user_name,
        'conflicting_projects': conflicting_projects,
        'conflict_count': len(conflicting_projects)
    }


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
    return check_member_conflicts_internal(db, user_id, start_date, end_date, project_id)


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
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中添加成员")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    added_count = 0
    skipped_count = 0
    conflicts = []

    for user_id in request.user_ids:
        existing = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ).first()

        if existing:
            skipped_count += 1
            continue

        conflict_info = check_member_conflicts_internal(
            db, user_id, request.start_date, request.end_date, project_id
        )
        if conflict_info['has_conflict']:
            conflicts.append({
                'user_id': user_id,
                'user_name': conflict_info.get('user_name', f'User {user_id}'),
                'conflicting_projects': conflict_info.get('conflicting_projects', [])
            })
            continue

        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role_code=request.role_code,
            allocation_pct=request.allocation_pct,
            start_date=request.start_date,
            end_date=request.end_date,
            commitment_level=request.commitment_level,
            reporting_to_pm=request.reporting_to_pm,
            dept_manager_notified=False,
            created_by=current_user.id
        )

        db.add(member)
        added_count += 1

    db.commit()

    return {
        'added_count': added_count,
        'skipped_count': skipped_count,
        'conflicts': conflicts,
        'message': f'成功添加 {added_count} 位成员，跳过 {skipped_count} 位，发现 {len(conflicts)} 个时间冲突'
    }


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

    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    if member.dept_manager_notified:
        return ResponseModel(code=200, message="部门经理已通知")

    member.dept_manager_notified = True
    db.commit()

    return ResponseModel(code=200, message="部门经理通知已发送")


@router.get("/from-dept/{dept_id}", response_model=dict)
def get_dept_users_for_project(
    project_id: int = Path(..., description="项目ID"),
    dept_id: int = Path(..., description="部门ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取部门用户列表（用于批量添加成员）"""
    check_project_access_or_raise(db, current_user, project_id)

    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    employees = db.query(Employee).filter(
        Employee.department == dept.dept_name,
        Employee.is_active == True
    ).all()

    employee_ids = [e.id for e in employees]
    users = db.query(User).filter(
        User.employee_id.in_(employee_ids),
        User.is_active == True
    ).all()

    existing_member_ids = db.query(ProjectMember.user_id).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.is_active == True
    ).all()
    existing_user_ids = {m[0] for m in existing_member_ids}

    available_users = []
    for user in users:
        available_users.append({
            'user_id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'is_member': user.id in existing_user_ids
        })

    return {
        'dept_id': dept_id,
        'dept_name': dept.dept_name,
        'users': available_users
    }
