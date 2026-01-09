# -*- coding: utf-8 -*-
"""
用户管理 API endpoints
"""
from typing import Any, List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.organization import Employee
from app.models.user import User, UserRole, Role
from app.models.timesheet import Timesheet
from app.models.project import Project
from app.models.rd_project import RdProject
from app.schemas.auth import UserCreate, UserUpdate, UserResponse, UserRoleAssign
from app.schemas.common import ResponseModel, PaginatedResponse
from app.services.permission_audit_service import PermissionAuditService
from app.services.user_sync_service import UserSyncService
from fastapi import Request


# 请求体模型
class SyncEmployeesRequest(BaseModel):
    """同步员工请求"""
    only_active: bool = True  # 只同步在职员工
    auto_activate: bool = False  # 是否自动激活
    department_filter: Optional[str] = None  # 部门筛选


class BatchToggleActiveRequest(BaseModel):
    """批量激活/禁用请求"""
    user_ids: List[int]
    is_active: bool


class ToggleActiveRequest(BaseModel):
    """激活/禁用请求"""
    is_active: bool

router = APIRouter()


class UserListResponse(PaginatedResponse):
    """用户列表响应"""
    items: List[UserResponse]


def _get_role_names(user: User) -> List[str]:
    """提取用户角色名称"""
    roles = user.roles
    if hasattr(roles, "all"):
        roles = roles.all()
    return [ur.role.role_name for ur in roles] if roles else []


def _get_role_ids(user: User) -> List[int]:
    """提取用户角色ID列表"""
    roles = user.roles
    if hasattr(roles, "all"):
        roles = roles.all()
    return [ur.role_id for ur in roles] if roles else []


def _build_user_response(user: User) -> UserResponse:
    """构建用户响应"""
    return UserResponse(
        id=user.id,
        username=user.username,
        employee_id=getattr(user, "employee_id", None),
        email=user.email,
        phone=user.phone,
        real_name=user.real_name,
        employee_no=user.employee_no,
        department=user.department,
        position=user.position,
        avatar=user.avatar,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        last_login_at=user.last_login_at,
        roles=_get_role_names(user),
        role_ids=_get_role_ids(user),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _generate_employee_code(db: Session) -> str:
    """生成新的员工编码"""
    latest = db.query(Employee).order_by(Employee.id.desc()).first()
    next_no = (latest.id + 1) if latest else 1
    return f"E{next_no:04d}"


def _ensure_employee_unbound(db: Session, employee_id: int, current_user_id: Optional[int] = None) -> None:
    """确保员工尚未绑定其他账号"""
    existing = db.query(User).filter(User.employee_id == employee_id).first()
    if existing and existing.id != current_user_id:
        raise HTTPException(status_code=400, detail="该员工已绑定其他账号")


def _prepare_employee_for_new_user(db: Session, user_in: UserCreate) -> Employee:
    """根据请求绑定或创建员工记录"""
    if user_in.employee_id:
        employee = db.query(Employee).filter(Employee.id == user_in.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="员工不存在")
        _ensure_employee_unbound(db, employee.id)
        return employee

    if user_in.employee_no:
        employee = (
            db.query(Employee)
                .filter(Employee.employee_code == user_in.employee_no)
                .first()
        )
        if employee:
            _ensure_employee_unbound(db, employee.id)
            return employee

    employee = Employee(
        employee_code=user_in.employee_no or _generate_employee_code(db),
        name=user_in.real_name or user_in.username,
        department=user_in.department,
        role=user_in.position,
        phone=user_in.phone,
    )
    db.add(employee)
    db.flush()
    return employee


def _replace_user_roles(db: Session, user_id: int, role_ids: Optional[List[int]]) -> None:
    """替换用户角色"""
    if role_ids is None:
        return

    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    if not role_ids:
        return

    unique_ids = list(dict.fromkeys(role_ids))
    roles = db.query(Role).filter(Role.id.in_(unique_ids)).all()
    if len(roles) != len(unique_ids):
        raise HTTPException(status_code=400, detail="部分角色不存在")

    for role_id in unique_ids:
        db.add(UserRole(user_id=user_id, role_id=role_id))


@router.get("/", response_model=UserListResponse, status_code=status.HTTP_200_OK)
def read_users(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（用户名/姓名/工号/邮箱）"),
    department: Optional[str] = Query(None, description="部门筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("USER_VIEW")),
) -> Any:
    """
    获取用户列表（支持分页和筛选）
    
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，默认20，最大100
    - **keyword**: 关键词搜索（用户名/姓名/工号/邮箱）
    - **department**: 部门筛选
    - **is_active**: 是否启用筛选
    """
    query = db.query(User)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                User.username.like(f"%{keyword}%"),
                User.real_name.like(f"%{keyword}%"),
                User.employee_no.like(f"%{keyword}%"),
                User.email.like(f"%{keyword}%"),
            )
        )
    
    # 部门筛选
    if department:
        query = query.filter(User.department == department)
    
    # 启用状态筛选
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    
    return UserListResponse(
        items=[_build_user_response(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    request: Request,
    current_user: User = Depends(security.require_permission("USER_CREATE")),
) -> Any:
    """
    Create new user.
    """
    exist = db.query(User).filter(User.username == user_in.username).first()
    if exist:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    employee = _prepare_employee_for_new_user(db, user_in)

    user = User(
        employee_id=employee.id,
        username=user_in.username,
        password_hash=security.get_password_hash(user_in.password),
        email=user_in.email,
        phone=user_in.phone,
        real_name=user_in.real_name or employee.name,
        employee_no=user_in.employee_no or employee.employee_code,
        department=user_in.department or employee.department,
        position=user_in.position or employee.role,
    )
    db.add(user)
    db.flush()

    _replace_user_roles(db, user.id, user_in.role_ids)
    db.commit()
    db.refresh(user)

    # 记录审计日志
    try:
        PermissionAuditService.log_user_operation(
            db=db,
            operator_id=current_user.id,
            user_id=user.id,
            action=PermissionAuditService.ACTION_USER_CREATED,
            changes={
                "username": user.username,
                "email": user.email,
                "real_name": user.real_name,
                "role_ids": user_in.role_ids
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # 审计日志记录失败不影响主流程

    return _build_user_response(user)


@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id != current_user.id and not security.check_permission(
        current_user, "USER_VIEW"
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return _build_user_response(user)


@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    request: Request,
    current_user: User = Depends(security.require_permission("USER_UPDATE")),
) -> Any:
    """
    更新用户信息
    
    - **user_id**: 用户ID
    - **user_in**: 用户更新数据
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 记录变更前的状态
    old_is_active = user.is_active
    old_data = {
        "email": user.email,
        "phone": user.phone,
        "real_name": user.real_name,
        "department": user.department,
        "position": user.position,
        "is_active": user.is_active
    }

    update_data = user_in.model_dump(exclude_unset=True)
    role_ids = update_data.pop("role_ids", None)
    new_employee_id = update_data.pop("employee_id", None)

    if new_employee_id and new_employee_id != user.employee_id:
        employee = db.query(Employee).filter(Employee.id == new_employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="员工不存在")
        _ensure_employee_unbound(db, employee.id, user.id)
        user.employee_id = employee.id
        if not update_data.get("employee_no"):
            update_data["employee_no"] = employee.employee_code

    for field, value in update_data.items():
        setattr(user, field, value)

    _replace_user_roles(db, user.id, role_ids)

    db.add(user)
    db.commit()
    db.refresh(user)

    # 记录审计日志
    try:
        changes = {k: v for k, v in update_data.items() if k in old_data and old_data[k] != v}
        if role_ids is not None:
            changes["role_ids"] = role_ids
        
        # 检查状态变更
        if old_is_active != user.is_active:
            action = PermissionAuditService.ACTION_USER_ACTIVATED if user.is_active else PermissionAuditService.ACTION_USER_DEACTIVATED
        else:
            action = PermissionAuditService.ACTION_USER_UPDATED
        
        PermissionAuditService.log_user_operation(
            db=db,
            operator_id=current_user.id,
            user_id=user.id,
            action=action,
            changes=changes,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # 审计日志记录失败不影响主流程
    
    return _build_user_response(user)


@router.put("/{user_id}/roles", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def assign_user_roles(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    role_data: UserRoleAssign,
    request: Request,
    current_user: User = Depends(security.require_permission("USER_UPDATE")),
) -> Any:
    """
    分配用户角色
    
    - **user_id**: 用户ID
    - **role_ids**: 角色ID列表
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    _replace_user_roles(db, user.id, role_data.role_ids)
    db.commit()
    
    # 记录审计日志
    try:
        PermissionAuditService.log_user_role_assignment(
            db=db,
            operator_id=current_user.id,
            user_id=user.id,
            role_ids=role_data.role_ids,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # 审计日志记录失败不影响主流程
    
    return ResponseModel(
        code=200,
        message="用户角色分配成功"
    )


@router.delete("/{user_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(security.require_permission("USER_DELETE")),
) -> Any:
    """
    删除/禁用用户（软删除）
    
    - **user_id**: 用户ID
    - 软删除：将is_active设置为False，不实际删除数据
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 防止删除超级管理员
    if user.is_superuser:
        raise HTTPException(
            status_code=400,
            detail="不能删除超级管理员"
        )
    
    # 防止删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="不能删除自己的账户"
        )
    
    # 软删除：禁用用户
    user.is_active = False
    db.add(user)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="用户已禁用"
    )


# ==================== 用户同步相关接口 ====================

@router.post("/sync-from-employees", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_users_from_employees(
    *,
    db: Session = Depends(deps.get_db),
    sync_request: SyncEmployeesRequest = Body(default=SyncEmployeesRequest()),
    current_user: User = Depends(security.require_permission("USER_CREATE")),
) -> Any:
    """
    批量同步员工到用户表

    - **only_active**: 只同步在职员工（默认 true）
    - **auto_activate**: 是否自动激活新账号（默认 false）
    - **department_filter**: 部门筛选（可选）

    同步规则：
    - 用户名：姓名拼音（重名加数字后缀）
    - 初始密码：姓名拼音 + 工号后4位
    - 初始角色：根据岗位自动映射
    """
    result = UserSyncService.sync_all_employees(
        db=db,
        only_active=sync_request.only_active,
        auto_activate=sync_request.auto_activate,
        department_filter=sync_request.department_filter,
    )

    return ResponseModel(
        code=200,
        message=f"同步完成：创建 {result['created']} 个账号，跳过 {result['skipped']} 个",
        data=result
    )


@router.post("/create-from-employee/{employee_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_user_from_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    auto_activate: bool = Query(False, description="是否自动激活"),
    current_user: User = Depends(security.require_permission("USER_CREATE")),
) -> Any:
    """
    从单个员工创建用户账号

    - **employee_id**: 员工ID
    - **auto_activate**: 是否自动激活账号
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    existing_usernames = set(u.username for u in db.query(User.username).all())

    user, password = UserSyncService.create_user_from_employee(
        db=db,
        employee=employee,
        existing_usernames=existing_usernames,
        auto_activate=auto_activate,
    )

    if not user:
        raise HTTPException(status_code=400, detail=password)  # password contains error message

    db.commit()

    return ResponseModel(
        code=200,
        message="用户创建成功",
        data={
            "user_id": user.id,
            "username": user.username,
            "initial_password": password,
            "is_active": user.is_active,
        }
    )


@router.put("/{user_id}/toggle-active", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def toggle_user_active(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    toggle_request: ToggleActiveRequest,
    request: Request,
    current_user: User = Depends(security.require_permission("USER_UPDATE")),
) -> Any:
    """
    切换用户激活状态

    - **user_id**: 用户ID
    - **is_active**: 目标状态（true=激活，false=禁用）
    """
    success, message = UserSyncService.toggle_user_active(
        db=db,
        user_id=user_id,
        is_active=toggle_request.is_active
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # 记录审计日志
    try:
        action = PermissionAuditService.ACTION_USER_ACTIVATED if toggle_request.is_active else PermissionAuditService.ACTION_USER_DEACTIVATED
        PermissionAuditService.log_user_operation(
            db=db,
            operator_id=current_user.id,
            user_id=user_id,
            action=action,
            changes={"is_active": toggle_request.is_active},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass

    return ResponseModel(
        code=200,
        message=message
    )


@router.put("/{user_id}/reset-password", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def reset_user_password(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    request: Request,
    current_user: User = Depends(security.require_permission("USER_UPDATE")),
) -> Any:
    """
    重置用户密码为初始密码

    - **user_id**: 用户ID

    初始密码规则：姓名拼音 + 工号后4位
    """
    success, result = UserSyncService.reset_user_password(db=db, user_id=user_id)

    if not success:
        raise HTTPException(status_code=400, detail=result)

    # 记录审计日志
    try:
        PermissionAuditService.log_user_operation(
            db=db,
            operator_id=current_user.id,
            user_id=user_id,
            action="PASSWORD_RESET",
            changes={"password": "重置为初始密码"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass

    return ResponseModel(
        code=200,
        message="密码重置成功",
        data={
            "new_password": result
        }
    )


@router.post("/batch-toggle-active", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_toggle_user_active(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchToggleActiveRequest,
    request: Request,
    current_user: User = Depends(security.require_permission("USER_UPDATE")),
) -> Any:
    """
    批量切换用户激活状态

    - **user_ids**: 用户ID列表
    - **is_active**: 目标状态（true=激活，false=禁用）
    """
    result = UserSyncService.batch_toggle_active(
        db=db,
        user_ids=batch_request.user_ids,
        is_active=batch_request.is_active
    )

    # 记录审计日志
    try:
        action = PermissionAuditService.ACTION_USER_ACTIVATED if batch_request.is_active else PermissionAuditService.ACTION_USER_DEACTIVATED
        for user_id in batch_request.user_ids:
            PermissionAuditService.log_user_operation(
                db=db,
                operator_id=current_user.id,
                user_id=user_id,
                action=action,
                changes={"is_active": batch_request.is_active, "batch": True},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
    except Exception:
        pass

    status_text = "激活" if batch_request.is_active else "禁用"
    return ResponseModel(
        code=200,
        message=f"批量{status_text}完成：成功 {result['success']} 个，失败 {result['failed']} 个",
        data=result
    )


# ==================== 工时分配接口 ====================

@router.get("/{user_id}/time-allocation", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_user_time_allocation(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    year: Optional[int] = Query(None, description="年份（不提供则查询全部）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取用户工时分配比例（研发/非研发）
    用于统计用户在研发项目和非研发项目上的工时分配情况
    """
    # 验证用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 权限检查：只能查看自己的或需要权限
    if user_id != current_user.id:
        if not security.check_permission(current_user, "USER_VIEW"):
            raise HTTPException(status_code=403, detail="无权查看其他用户的工时分配")
    
    # 查询工时记录
    query = db.query(Timesheet).filter(
        Timesheet.user_id == user_id,
        Timesheet.status == 'APPROVED'
    )
    
    if year:
        query = query.filter(func.extract('year', Timesheet.work_date) == year)
    
    timesheets = query.all()
    
    # 获取所有研发项目关联的非标项目ID
    rd_projects = db.query(RdProject).filter(
        RdProject.status.in_(['APPROVED', 'IN_PROGRESS', 'COMPLETED']),
        RdProject.linked_project_id.isnot(None)
    ).all()
    
    rd_linked_project_ids = {p.linked_project_id for p in rd_projects if p.linked_project_id}
    
    # 统计研发和非研发工时
    rd_hours = Decimal(0)
    non_rd_hours = Decimal(0)
    total_hours = Decimal(0)
    
    rd_projects_detail = {}
    non_rd_projects_detail = {}
    
    for ts in timesheets:
        hours = Decimal(str(ts.hours or 0))
        total_hours += hours
        
        # 判断是否为研发项目
        is_rd = ts.project_id in rd_linked_project_ids if ts.project_id else False
        
        if is_rd:
            rd_hours += hours
            # 获取研发项目信息
            rd_project = None
            for rp in rd_projects:
                if rp.linked_project_id == ts.project_id:
                    rd_project = rp
                    break
            
            project_key = f"RD-{rd_project.id}" if rd_project else f"P-{ts.project_id}"
            if project_key not in rd_projects_detail:
                project = db.query(Project).filter(Project.id == ts.project_id).first()
                rd_projects_detail[project_key] = {
                    "project_id": ts.project_id,
                    "project_name": project.project_name if project else "未知项目",
                    "rd_project_id": rd_project.id if rd_project else None,
                    "rd_project_name": rd_project.project_name if rd_project else None,
                    "total_hours": Decimal(0),
                    "days": 0
                }
            rd_projects_detail[project_key]["total_hours"] += hours
            rd_projects_detail[project_key]["days"] += 1
        else:
            non_rd_hours += hours
            # 获取非研发项目信息
            project_key = f"P-{ts.project_id}" if ts.project_id else "未分配"
            if project_key not in non_rd_projects_detail:
                project = db.query(Project).filter(Project.id == ts.project_id).first() if ts.project_id else None
                non_rd_projects_detail[project_key] = {
                    "project_id": ts.project_id,
                    "project_name": project.project_name if project else "未分配项目",
                    "total_hours": Decimal(0),
                    "days": 0
                }
            non_rd_projects_detail[project_key]["total_hours"] += hours
            non_rd_projects_detail[project_key]["days"] += 1
    
    # 计算比例
    rd_ratio = 0.0
    non_rd_ratio = 0.0
    if total_hours > 0:
        rd_ratio = float(rd_hours / total_hours * 100)
        non_rd_ratio = float(non_rd_hours / total_hours * 100)
    
    # 转换Decimal为float
    for key, data in rd_projects_detail.items():
        data["total_hours"] = float(data["total_hours"])
    for key, data in non_rd_projects_detail.items():
        data["total_hours"] = float(data["total_hours"])
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "user_id": user_id,
            "user_name": user.real_name or user.username,
            "year": year,
            "total_hours": float(total_hours),
            "rd_hours": float(rd_hours),
            "non_rd_hours": float(non_rd_hours),
            "rd_ratio": rd_ratio,
            "non_rd_ratio": non_rd_ratio,
            "rd_ratio_percent": f"{rd_ratio:.2f}%",
            "non_rd_ratio_percent": f"{non_rd_ratio:.2f}%",
            "rd_projects": list(rd_projects_detail.values()),
            "non_rd_projects": list(non_rd_projects_detail.values()),
        }
    )
