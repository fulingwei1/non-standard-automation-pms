# -*- coding: utf-8 -*-
"""
认证相关 API endpoints
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.user import (
    ApiPermission,
    Role,
    RoleApiPermission,
    User,
    UserRole,
)
from app.schemas.auth import PasswordChange, Token, UserResponse
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")  # 每分钟最多5次登录尝试，防止暴力破解
def login(
    request: Request,  # slowapi 需要 Request 参数
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    用户登录，返回 JWT Token

    - **username**: 用户名
    - **password**: 密码

    错误码说明：
    - USER_NOT_FOUND: 账号不存在
    - USER_INACTIVE: 账号未激活
    - USER_DISABLED: 账号已禁用（员工已离职）
    - WRONG_PASSWORD: 密码错误
    """
    user = db.query(User).filter(User.username == form_data.username).first()

    # 1. 账号不存在
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "USER_NOT_FOUND",
                "message": "该员工尚未开通系统账号，请联系管理员",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. 密码错误
    if not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "WRONG_PASSWORD",
                "message": "密码错误，忘记密码请联系管理员重置",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. 账号未激活或已禁用
    if not user.is_active:
        # 检查关联的员工状态来区分是未激活还是离职
        from app.models.organization import Employee

        employee = db.query(Employee).filter(Employee.id == user.employee_id).first()

        if employee and employee.employment_status != "active":
            # 员工已离职
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "USER_DISABLED",
                    "message": "账号已被禁用，如有疑问请联系管理员",
                },
            )
        else:
            # 账号未激活
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "USER_INACTIVE",
                    "message": "账号待激活，请联系管理员开通系统访问权限",
                },
            )

    # 更新最后登录时间
    user.last_login_at = datetime.now()
    db.add(user)
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        {"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def logout(
    token: str = Depends(security.oauth2_scheme),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    用户登出，使 Token 失效

    注意：当前实现使用内存黑名单，生产环境应使用 Redis
    """
    # 将 token 加入黑名单（实际应使用 Redis 等集中存储）
    security.revoke_token(token)

    return ResponseModel(code=200, message="登出成功")


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
def refresh_token(
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    刷新访问令牌

    使用当前有效的 token 获取新的 token
    """
    # 直接使用当前用户生成新token（更简单可靠）
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token = security.create_access_token(
        {"sub": str(current_user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    获取当前用户信息，包含角色和权限
    """
    # 使用当前请求的会话重新加载用户，确保数据最新且绑定到同一session
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 直接通过 JOIN 查询角色与权限，避免懒加载触发 SQLite 旧库的字段映射问题
    role_rows = (
        db.query(Role.id, Role.role_name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == db_user.id)
        .all()
    )
    role_ids = [row.id for row in role_rows]
    role_names = [row.role_name for row in role_rows]

    permission_rows = (
        db.query(ApiPermission.perm_code)
        .join(RoleApiPermission, RoleApiPermission.permission_id == ApiPermission.id)
        .join(UserRole, UserRole.role_id == RoleApiPermission.role_id)
        .filter(UserRole.user_id == db_user.id, ApiPermission.is_active == True)
        .distinct()
        .all()
    )
    permission_codes = sorted(
        {row.perm_code for row in permission_rows if row.perm_code}
    )

    # 构建响应数据（避免直接修改ORM对象）
    is_superuser = db_user.is_superuser or security.is_system_admin(db_user)
    user_data = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "phone": db_user.phone,
        "real_name": db_user.real_name,
        "employee_no": db_user.employee_no,
        "department": db_user.department,
        "position": db_user.position,
        "avatar": db_user.avatar,
        "is_active": db_user.is_active,
        "is_superuser": is_superuser,
        "last_login_at": db_user.last_login_at,
        "roles": role_names,
        "role_ids": role_ids,
        "permissions": permission_codes,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
    }

    return UserResponse(**user_data)


@router.put("/password", response_model=ResponseModel, status_code=status.HTTP_200_OK)
@limiter.limit("5/hour")  # 每小时最多5次密码修改尝试，防止暴力破解
def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
    token: str = Depends(security.oauth2_scheme),
) -> Any:
    """
    修改当前用户密码

    - **old_password**: 原密码
    - **new_password**: 新密码
    """
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 验证原密码
    if not security.verify_password(password_data.old_password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误"
        )

    # 更新密码
    db_user.password_hash = security.get_password_hash(password_data.new_password)
    db.add(db_user)
    db.commit()

    # 密码更新后撤销当前 token，强制重新登录
    security.revoke_token(token)

    return ResponseModel(code=200, message="密码修改成功，请重新登录")
