# -*- coding: utf-8 -*-
"""
认证相关 API endpoints
"""

from datetime import timedelta
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
    # 登录失败锁定检查
    try:
        from app.utils.redis_client import get_redis_client
        redis_client = get_redis_client()
        if redis_client:
            lockout_key = f"login:lockout:{form_data.username}"
            if redis_client.exists(lockout_key):
                ttl = redis_client.ttl(lockout_key)
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail={
                        "error_code": "ACCOUNT_LOCKED",
                        "message": f"账号已被锁定，请在 {ttl // 60 + 1} 分钟后重试",
                    },
                )
    except Exception as lockout_err:
        import logging
        if "ACCOUNT_LOCKED" in str(lockout_err):
            raise
        logging.getLogger(__name__).debug(f"登录锁定检查跳过: {lockout_err}")

    try:
        # 使用原始 SQL 查询避免 ORM 的自动更新机制
        from sqlalchemy import text

        result = db.execute(
            text("SELECT * FROM users WHERE username = :username LIMIT 1"),
            {"username": form_data.username}
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "USER_NOT_FOUND",
                    "message": "该员工尚未开通系统账号，请联系管理员",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 将结果转换为字典以便访问
        user_dict = dict(result._mapping)

        # 2. 密码错误
        if not security.verify_password(form_data.password, user_dict["password_hash"]):
            # 记录登录失败并检查是否需要锁定
            try:
                from app.utils.redis_client import get_redis_client as get_redis
                redis_cli = get_redis()
                if redis_cli:
                    attempt_key = f"login:attempts:{form_data.username}"
                    attempts = redis_cli.incr(attempt_key)
                    redis_cli.expire(attempt_key, 900)  # 15分钟窗口
                    if attempts >= 5:  # 5次失败后锁定
                        lockout_key = f"login:lockout:{form_data.username}"
                        redis_cli.setex(lockout_key, 900, "1") # 锁定15分钟
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "WRONG_PASSWORD",
                    "message": "密码错误，忘记密码请联系管理员重置",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. 账号未激活或已禁用
        if not user_dict["is_active"]:
            # 检查关联的员工状态来区分是未激活还是离职
            employee_result = db.execute(
                text("SELECT employment_status FROM employees WHERE id = :employee_id LIMIT 1"),
                {"employee_id": user_dict["employee_id"]}
            ).fetchone()

            if employee_result and employee_result[0] != "active":
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

        # 更新最后登录时间（临时禁用以绕过只读数据库问题）
        # user.last_login_at = datetime.now()
        # db.add(user)
        # db.commit()

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            {"sub": str(user_dict["id"])}, expires_delta=access_token_expires
        )
        # 登录成功，清除失败计数
        try:
            from app.utils.redis_client import get_redis_client as get_redis_success
            redis_success = get_redis_success()
            if redis_success:
                redis_success.delete(f"login:attempts:{form_data.username}")
        except Exception:
            pass


        # 显式回滚任何可能的更改，确保不触发数据库写入
        db.rollback()

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    finally:
        # 确保在函数退出时回滚任何未提交的更改
        try:
            db.rollback()
        except Exception:
            pass


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
        db.query(Role.id, Role.role_name, Role.role_code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == db_user.id)
        .all()
    )
    role_ids = [row.id for row in role_rows]
    [row.role_name for row in role_rows]

    # 检查是否为系统管理员（使用已查询的角色数据，避免N+1查询）
    admin_role_codes = {"admin", "super_admin", "system_admin"}
    admin_role_names = {"系统管理员", "超级管理员", "管理员"}
    is_admin = any(
        (row.role_code or "").lower() in admin_role_codes or
        (row.role_name or "") in admin_role_names
        for row in role_rows
    )

    # 构建响应数据（避免直接修改ORM对象）
    is_superuser = db_user.is_superuser or is_admin

    # 超级管理员获得所有权限，普通用户通过角色获取权限
    if is_superuser:
        permission_rows = (
            db.query(ApiPermission.perm_code)
            .filter(ApiPermission.is_active)
            .all()
        )
    else:
        permission_rows = (
            db.query(ApiPermission.perm_code)
            .join(RoleApiPermission, RoleApiPermission.permission_id == ApiPermission.id)
            .join(UserRole, UserRole.role_id == RoleApiPermission.role_id)
            .filter(UserRole.user_id == db_user.id, ApiPermission.is_active)
            .distinct()
            .all()
        )
    permission_codes = sorted(
        {row.perm_code for row in permission_rows if row.perm_code}
    )
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
        "roles": [{"role_code": row.role_code, "role_name": row.role_name} for row in role_rows],
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


@router.get("/permissions", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_permissions(
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    获取当前用户的完整权限数据

    返回:
    - permissions: 权限编码列表
    - menus: 可访问的菜单树
    - dataScopes: 数据权限范围映射
    """
    from app.services.permission_service import PermissionService

    permission_data = PermissionService.get_full_permission_data(
        db=db,
        user_id=current_user.id,
        user=current_user
    )

    return ResponseModel(
        code=200,
        message="获取成功",
        data=permission_data
    )
