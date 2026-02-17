# -*- coding: utf-8 -*-
"""
用户 CRUD 端点（重构版）
使用统一响应格式
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.schemas import paginated_response, success_response
from app.models.organization import Employee
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, UserRoleAssign, UserUpdate
from app.services.permission_audit_service import PermissionAuditService
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

from .utils import build_user_response, ensure_employee_unbound, prepare_employee_for_new_user, replace_user_roles

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
def read_users(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（用户名/姓名/工号/邮箱）"),
    department: Optional[str] = Query(None, description="部门筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Any:
    """获取用户列表（支持分页和筛选）"""
    try:
        from app.models.user import UserRole, Role

        query = db.query(User)

        query = apply_keyword_filter(query, User, keyword, ["username", "real_name", "employee_no", "email"])

        if department:
            query = query.filter(User.department == department)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        total = query.count()
        users = apply_pagination(query.order_by(User.created_at.desc()), pagination.offset, pagination.limit).all()

        # 批量查询所有用户的角色（避免N+1查询）
        user_ids = [u.id for u in users]
        user_roles_data = (
            db.query(UserRole.user_id, UserRole.role_id, Role.role_name)
            .join(Role, UserRole.role_id == Role.id)
            .filter(UserRole.user_id.in_(user_ids))
            .all()
        )

        # 构建用户角色映射
        user_roles_map = {}
        for user_id, role_id, role_name in user_roles_data:
            if user_id not in user_roles_map:
                user_roles_map[user_id] = {"role_ids": [], "role_names": []}
            user_roles_map[user_id]["role_ids"].append(role_id)
            user_roles_map[user_id]["role_names"].append(role_name)

        user_responses = []
        for u in users:
            try:
                # 使用预加载的角色数据（避免N+1查询）
                roles_data = user_roles_map.get(u.id, {"role_ids": [], "role_names": []})
                user_responses.append(UserResponse(
                    id=u.id,
                    username=u.username,
                    employee_id=getattr(u, "employee_id", None),
                    email=u.email or "",
                    phone=u.phone or "",
                    real_name=u.real_name or "",
                    employee_no=u.employee_no or "",
                    department=u.department or "",
                    position=u.position or "",
                    avatar=u.avatar,
                    is_active=u.is_active,
                    is_superuser=u.is_superuser,
                    last_login_at=u.last_login_at,
                    roles=roles_data["role_names"],
                    role_ids=roles_data["role_ids"],
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                ))
            except Exception as e:
                logger.error(f"构建用户 {u.username} 响应失败: {e}", exc_info=True)
                # 构建失败时使用空角色列表
                user_responses.append(UserResponse(
                    id=u.id, username=u.username, employee_id=getattr(u, "employee_id", None),
                    email=u.email or "", phone=u.phone or "", real_name=u.real_name or "",
                    employee_no=u.employee_no or "", department=u.department or "",
                    position=u.position or "", avatar=u.avatar, is_active=u.is_active,
                    is_superuser=u.is_superuser, last_login_at=u.last_login_at,
                    roles=[], role_ids=[], created_at=u.created_at, updated_at=u.updated_at,
                ))

        # 使用统一分页响应格式
        return paginated_response(
            items=user_responses,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    request: Request,
    current_user: User = Depends(security.require_permission("user:create")),
) -> Any:
    """创建新用户"""
    exist = db.query(User).filter(User.username == user_in.username).first()
    if exist:
        raise HTTPException(status_code=400, detail="该用户名已存在")

    employee = prepare_employee_for_new_user(db, user_in)

    # 创建用户时确保租户数据一致性
    # 普通用户必须属于当前用户的租户
    # 只有超级管理员可以创建跨租户用户（但这需要专门的接口，这里不支持）
    user_tenant_id = getattr(current_user, "tenant_id", None)
    
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
        # 确保数据一致性：新用户不是超级管理员，必须有租户ID
        is_superuser=False,
        tenant_id=user_tenant_id,
    )
    db.add(user)
    db.flush()
    
    # 验证用户数据一致性
    try:
        from app.core.auth import validate_user_tenant_consistency
        validate_user_tenant_consistency(user)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    replace_user_roles(db, user.id, user_in.role_ids)
    db.commit()
    db.refresh(user)

    try:
        PermissionAuditService.log_user_operation(
            db=db, operator_id=current_user.id, user_id=user.id,
            action=PermissionAuditService.ACTION_USER_CREATED,
            changes={"username": user.username, "email": user.email, "real_name": user.real_name, "role_ids": user_in.role_ids},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        logger.warning("审计日志记录失败，不影响主流程", exc_info=True)

    # 使用统一响应格式
    return success_response(
        data=build_user_response(user),
        message="用户创建成功",
        code=status.HTTP_201_CREATED
    )


@router.get("/{user_id}")
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """获取指定用户"""
    user = get_or_404(db, User, user_id, "用户不存在")
    if user.id != current_user.id and not security.check_permission(current_user, "user:read"):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 使用统一响应格式
    return success_response(
        data=build_user_response(user),
        message="获取用户信息成功"
    )


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    request: Request,
    current_user: User = Depends(security.require_permission("user:update")),
) -> Any:
    """更新用户信息"""
    user = get_or_404(db, User, user_id, "用户不存在")

    old_is_active = user.is_active
    old_data = {"email": user.email, "phone": user.phone, "real_name": user.real_name,
                "department": user.department, "position": user.position, "is_active": user.is_active}

    update_data = user_in.model_dump(exclude_unset=True)
    role_ids = update_data.pop("role_ids", None)
    new_employee_id = update_data.pop("employee_id", None)

    if new_employee_id and new_employee_id != user.employee_id:
        employee = get_or_404(db, Employee, new_employee_id, "员工不存在")
        ensure_employee_unbound(db, employee.id, user.id)
        user.employee_id = employee.id
        if not update_data.get("employee_no"):
            update_data["employee_no"] = employee.employee_code

    for field, value in update_data.items():
        # 防止通过普通更新接口修改敏感字段
        if field in ("is_superuser", "tenant_id"):
            raise HTTPException(
                status_code=400, 
                detail=f"不允许通过此接口修改 {field} 字段，请使用专门的管理接口"
            )
        setattr(user, field, value)

    replace_user_roles(db, user.id, role_ids)
    
    # 验证用户数据一致性
    try:
        from app.core.auth import validate_user_tenant_consistency
        validate_user_tenant_consistency(user)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        changes = {k: v for k, v in update_data.items() if k in old_data and old_data[k] != v}
        if role_ids is not None:
            changes["role_ids"] = role_ids
        action = (PermissionAuditService.ACTION_USER_ACTIVATED if user.is_active else PermissionAuditService.ACTION_USER_DEACTIVATED) if old_is_active != user.is_active else PermissionAuditService.ACTION_USER_UPDATED
        PermissionAuditService.log_user_operation(
            db=db, operator_id=current_user.id, user_id=user.id, action=action, changes=changes,
            ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")
        )
    except Exception:
        logger.warning("审计日志记录失败，不影响主流程", exc_info=True)

    # 使用统一响应格式
    return success_response(
        data=build_user_response(user),
        message="用户更新成功"
    )


@router.put("/{user_id}/roles", status_code=status.HTTP_200_OK)
def assign_user_roles(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    role_data: UserRoleAssign,
    request: Request,
    current_user: User = Depends(security.require_permission("user:update")),
) -> Any:
    """分配用户角色"""
    user = get_or_404(db, User, user_id, "用户不存在")

    replace_user_roles(db, user.id, role_data.role_ids)
    db.commit()

    try:
        PermissionAuditService.log_user_role_assignment(
            db=db, operator_id=current_user.id, user_id=user.id, role_ids=role_data.role_ids,
            ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")
        )
    except Exception:
        logger.warning("审计日志记录失败，不影响主流程", exc_info=True)

    # 使用统一响应格式
    return success_response(
        data=None,
        message="用户角色分配成功"
    )


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(security.require_permission("user:delete")),
) -> Any:
    """删除/禁用用户（软删除）"""
    user = get_or_404(db, User, user_id, "用户不存在")

    if user.is_superuser:
        raise HTTPException(status_code=400, detail="不能删除超级管理员")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")

    user.is_active = False
    db.add(user)
    db.commit()

    # 使用统一响应格式
    return success_response(
        data=None,
        message="用户已禁用"
    )
