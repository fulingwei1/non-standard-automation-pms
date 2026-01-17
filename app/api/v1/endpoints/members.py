from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department, Employee
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import (
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[ProjectMemberResponse])
def read_members(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Retrieve project members.
    """
    query = db.query(ProjectMember)

    # 如果指定了project_id，检查访问权限
    if project_id:
        from app.utils.permission_helpers import check_project_access_or_raise
        check_project_access_or_raise(db, current_user, project_id)
        query = query.filter(ProjectMember.project_id == project_id)
    else:
        # 如果没有指定project_id，根据用户权限过滤项目
        from app.services.data_scope_service import DataScopeService
        user_project_ids = DataScopeService.get_user_project_ids(db, current_user.id)
        if not current_user.is_superuser:
            data_scope = DataScopeService.get_user_data_scope(db, current_user)
            if data_scope == "OWN":
                user_managed_projects = db.query(Project.id).filter(
                    (Project.created_by == current_user.id) | (Project.pm_id == current_user.id)
                ).all()
                user_project_ids = user_project_ids | {p[0] for p in user_managed_projects}
            elif data_scope == "DEPT":
                from app.models.organization import Department
                if current_user.department:
                    dept = db.query(Department).filter(Department.dept_name == current_user.department).first()
                    if dept:
                        dept_projects = db.query(Project.id).filter(Project.dept_id == dept.id).all()
                        user_project_ids = user_project_ids | {p[0] for p in dept_projects}

        if user_project_ids:
            query = query.filter(ProjectMember.project_id.in_(user_project_ids))
        elif not current_user.is_superuser:
            query = query.filter(ProjectMember.id == -1)

    members = query.offset(skip).limit(limit).all()

    # Map user info
    for m in members:
        m.username = m.user.username if m.user else "Unknown"
        m.real_name = m.user.real_name if m.user else "Unknown"

    return members


@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
def get_project_members(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目的成员列表
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()

    # 补充用户信息
    for m in members:
        m.username = m.user.username if m.user else "Unknown"
        m.real_name = m.user.real_name if m.user else "Unknown"

    return members


@router.post("/", response_model=ProjectMemberResponse)
def add_member(
    *,
    db: Session = Depends(deps.get_db),
    member_in: ProjectMemberCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加项目成员
    """
    # Check project exists
    project = db.query(Project).filter(Project.id == member_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # Check user exists
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # Check if already a member
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == member_in.project_id,
            ProjectMember.user_id == member_in.user_id,
        )
        .first()
    )
    if member:
        raise HTTPException(
            status_code=400,
            detail="该用户已是项目成员",
        )

    member = ProjectMember(**member_in.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)

    member.username = user.username
    member.real_name = user.real_name
    return member


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
def add_project_member(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    member_in: ProjectMemberCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    为项目添加成员
    """
    # 检查项目访问权限
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中添加成员")

    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已经是成员
    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_in.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="该用户已是项目成员",
        )

    member_data = member_in.model_dump()
    member_data['project_id'] = project_id

    member = ProjectMember(**member_data)
    db.add(member)
    db.commit()
    db.refresh(member)

    member.username = user.username
    member.real_name = user.real_name
    return member


@router.put("/project-members/{member_id}", response_model=ProjectMemberResponse)
def update_project_member(
    *,
    db: Session = Depends(deps.get_db),
    member_id: int,
    member_in: ProjectMemberUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目成员角色和分配信息
    """
    member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    update_data = member_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(member, field):
            setattr(member, field, value)

    db.add(member)
    db.commit()
    db.refresh(member)

    # 补充用户信息
    member.username = member.user.username if member.user else "Unknown"
    member.real_name = member.user.real_name if member.user else "Unknown"

    return member


@router.delete("/{member_id}", status_code=200)
def remove_member(
    *,
    db: Session = Depends(deps.get_db),
    member_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    移除项目成员
    """
    member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    db.delete(member)
    db.commit()

    return ResponseModel(code=200, message="项目成员已移除")


class BatchAddMembersRequest(BaseModel):
    """批量添加成员请求"""
    user_ids: List[int] = Body(..., description="用户ID列表")
    role_code: str = Body(..., description="角色编码")
    allocation_pct: float = Body(100, ge=0, le=100, description="分配比例")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    commitment_level: Optional[str] = Body(None, description="投入级别：FULL/PARTIAL/ADVISORY")
    reporting_to_pm: bool = Body(True, description="是否向项目经理汇报")


@router.post("/projects/{project_id}/members/batch", response_model=dict)
def batch_add_project_members(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    request: BatchAddMembersRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量添加项目成员
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中添加成员")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    added_count = 0
    skipped_count = 0
    conflicts = []

    for user_id in request.user_ids:
        # 检查是否已是成员
        existing = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ).first()

        if existing:
            skipped_count += 1
            continue

        # 检查时间冲突
        conflict_info = _check_member_conflicts(
            db, user_id, request.start_date, request.end_date, project_id
        )
        if conflict_info['has_conflict']:
            conflicts.append({
                'user_id': user_id,
                'user_name': conflict_info.get('user_name', f'User {user_id}'),
                'conflicting_projects': conflict_info.get('conflicting_projects', [])
            })
            continue

        # 创建成员
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role_code=request.role_code,
            allocation_pct=request.allocation_pct,
            start_date=request.start_date,
            end_date=request.end_date,
            commitment_level=request.commitment_level,
            reporting_to_pm=request.reporting_to_pm,
            dept_manager_notified=False,  # 需要通知部门经理
            created_by=current_user.id
        )

        db.add(member)
        added_count += 1

        # 通知部门经理（异步，这里只标记）
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.department:
            # 标记需要通知，实际通知可以通过后台任务处理
            member.dept_manager_notified = False

    db.commit()

    return {
        'added_count': added_count,
        'skipped_count': skipped_count,
        'conflicts': conflicts,
        'message': f'成功添加 {added_count} 位成员，跳过 {skipped_count} 位，发现 {len(conflicts)} 个时间冲突'
    }


@router.get("/projects/{project_id}/members/conflicts", response_model=dict)
def check_member_conflicts(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    user_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查成员分配冲突
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    conflict_info = _check_member_conflicts(
        db, user_id, start_date, end_date, project_id
    )

    return conflict_info


def _check_member_conflicts(
    db: Session,
    user_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    exclude_project_id: Optional[int] = None
) -> dict:
    """
    检查成员分配冲突（内部函数）

    Returns:
        冲突信息字典
    """
    if not start_date or not end_date:
        return {'has_conflict': False}

    # 查询该用户在同一时间段的其他项目分配
    query = db.query(ProjectMember).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.is_active == True,
        or_(
            # 新分配的开始日期在现有分配的时间范围内
            and_(
                ProjectMember.start_date <= start_date,
                ProjectMember.end_date >= start_date
            ),
            # 新分配的结束日期在现有分配的时间范围内
            and_(
                ProjectMember.start_date <= end_date,
                ProjectMember.end_date >= end_date
            ),
            # 新分配完全包含现有分配
            and_(
                ProjectMember.start_date >= start_date,
                ProjectMember.end_date <= end_date
            )
        )
    )

    if exclude_project_id:
        query = query.filter(ProjectMember.project_id != exclude_project_id)

    conflicting_members = query.all()

    if not conflicting_members:
        return {'has_conflict': False}

    # 获取冲突的项目信息
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


@router.post("/projects/{project_id}/members/{member_id}/notify-dept-manager", response_model=ResponseModel)
def notify_dept_manager(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    member_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    通知部门经理（成员加入项目）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    if member.dept_manager_notified:
        return ResponseModel(code=200, message="部门经理已通知")

    # 标记为已通知（实际通知可以通过消息系统发送）
    member.dept_manager_notified = True
    db.commit()

    return ResponseModel(code=200, message="部门经理通知已发送")


@router.get("/projects/{project_id}/members/from-dept/{dept_id}", response_model=dict)
def get_dept_users_for_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    dept_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取部门用户列表（用于批量添加成员）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    # 获取部门员工
    employees = db.query(Employee).filter(
        Employee.department == dept.dept_name,
        Employee.is_active == True
    ).all()

    # 获取对应的用户
    employee_ids = [e.id for e in employees]
    users = db.query(User).filter(
        User.employee_id.in_(employee_ids),
        User.is_active == True
    ).all()

    # 获取已在项目中的成员
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
