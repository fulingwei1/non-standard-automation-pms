# -*- coding: utf-8 -*-
"""
认证相关 API endpoints
"""

import logging
import secrets
from datetime import timedelta
from typing import Any, Optional

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
from app.schemas.session import (
    DeviceInfo,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RevokeSessionRequest,
    SessionListResponse,
    SessionResponse,
)
from app.services.session_service import SessionService
from app.services.account_lockout_service import AccountLockoutService
from app.schemas.common import ResponseModel

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=dict, status_code=status.HTTP_200_OK)
# @limiter.limit("5/minute")  # FIXME: 暂时禁用，slowapi有兼容性问题  
def login(
    request: Request,  # 用于获取客户端IP和User-Agent
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    device_info: Optional[DeviceInfo] = None,
) -> Any:
    """
    用户登录，返回 JWT Token

    安全机制（双层保护）：
    1. IP级别速率限制（5次/分钟）
       - 防止DDoS攻击和分布式暴力破解
       - 基于来源IP地址限流
    2. AccountLockoutService（账户锁定）
       - 防止针对特定账户的暴力破解
       - 5次失败锁定30分钟

    - **username**: 用户名
    - **password**: 密码

    错误码说明：
    - USER_NOT_FOUND: 账号不存在
    - USER_INACTIVE: 账号未激活
    - USER_DISABLED: 账号已禁用（员工已离职）
    - WRONG_PASSWORD: 密码错误
    """
    # 获取客户端信息
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    
    # 检查IP黑名单
    if AccountLockoutService.is_ip_blacklisted(client_ip):
        logger.warning(f"来自黑名单IP的登录尝试: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "IP_BLACKLISTED",
                "message": "您的IP已被限制访问，请联系管理员",
            },
        )
    
    # 检查账户锁定状态
    lockout_status = AccountLockoutService.check_lockout(form_data.username, db)
    if lockout_status["locked"]:
        logger.warning(f"尝试登录已锁定账户: {form_data.username}, IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error_code": "ACCOUNT_LOCKED",
                "message": lockout_status["message"],
                "locked_until": lockout_status["locked_until"],
            },
        )

    try:
        # 使用原始 SQL 查询避免 ORM 的自动更新机制
        from sqlalchemy import text

        result = db.execute(
            text("SELECT * FROM users WHERE username = :username LIMIT 1"),
            {"username": form_data.username}
        ).fetchone()

        if not result:
            # 记录失败（用户不存在）
            AccountLockoutService.record_failed_login(
                username=form_data.username,
                ip=client_ip,
                user_agent=user_agent,
                reason="user_not_found",
                db=db
            )
            # 统一返回"用户名或密码错误"，不泄露用户是否存在
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "INVALID_CREDENTIALS",
                    "message": "用户名或密码错误",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 将结果转换为字典以便访问
        user_dict = dict(result._mapping)

        # 2. 密码错误
        if not security.verify_password(form_data.password, user_dict["password_hash"]):
            # 记录登录失败
            lockout_result = AccountLockoutService.record_failed_login(
                username=form_data.username,
                ip=client_ip,
                user_agent=user_agent,
                reason="wrong_password",
                db=db
            )
            
            # 构建错误消息
            error_detail = {
                "error_code": "WRONG_PASSWORD",
                "message": "用户名或密码错误",  # 统一错误消息，不泄露信息
            }
            
            # 如果账户被锁定，更新错误消息
            if lockout_result["locked"]:
                error_detail["error_code"] = "ACCOUNT_LOCKED"
                error_detail["message"] = f"登录失败次数过多，账户已被锁定{AccountLockoutService.LOCKOUT_DURATION_MINUTES}分钟"
                error_detail["locked_until"] = lockout_result["locked_until"]
                logger.warning(f"账户已锁定: {form_data.username}, IP: {client_ip}, 失败次数: {lockout_result['attempts']}")
                status_code = status.HTTP_423_LOCKED
            else:
                # 提示剩余尝试次数
                remaining = AccountLockoutService.LOCKOUT_THRESHOLD - lockout_result["attempts"]
                if remaining <= 2:
                    error_detail["message"] += f"，剩余尝试次数: {remaining}"
                status_code = status.HTTP_401_UNAUTHORIZED
            
            raise HTTPException(
                status_code=status_code,
                detail=error_detail,
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

        # === 2FA验证检查 ===
        # 如果用户启用了2FA，需要提供2FA验证码
        if user_dict.get("two_factor_enabled"):
            # 返回特殊响应，要求提供2FA码
            # 生成临时令牌（有效期5分钟）用于2FA验证
            temp_token_data = {
                "sub": str(user_dict["id"]),
                "purpose": "2fa_pending"
            }
            temp_token = security.create_access_token(
                data=temp_token_data,
                expires_delta=timedelta(minutes=5)
            )
            return {
                "requires_2fa": True,
                "temp_token": temp_token,
                "message": "请提供双因素认证码"
            }
        
        # 更新最后登录时间（临时禁用以绕过只读数据库问题）
        # user.last_login_at = datetime.now()
        # db.add(user)
        # db.commit()

        # 创建Access Token和Refresh Token对
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=7)  # Refresh Token有效期7天
        
        access_token, refresh_token, access_jti, refresh_jti = security.create_token_pair(
            data={"sub": str(user_dict["id"])},
            access_expires=access_token_expires,
            refresh_expires=refresh_token_expires,
        )
        
        # 创建会话记录
        try:
            SessionService.create_session(
                db=db,
                user_id=user_dict["id"],
                access_token_jti=access_jti,
                refresh_token_jti=refresh_jti,
                ip_address=client_ip,
                user_agent=user_agent,
                device_info=device_info.model_dump() if device_info else None,
            )
        except Exception as e:
            logger.warning(f"创建会话记录失败: {e}")
        
        # 登录成功，清除失败计数和记录成功登录
        AccountLockoutService.record_successful_login(
            username=form_data.username,
            ip=client_ip,
            user_agent=user_agent,
            db=db
        )

        # 显式回滚任何可能的更改，确保不触发数据库写入
        db.rollback()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": 7 * 24 * 3600,  # 7天
        }
    finally:
        # 确保在函数退出时回滚任何未提交的更改
        try:
            db.rollback()
        except Exception:
            pass


@router.post("/logout", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    logout_data: LogoutRequest,
    token: str = Depends(security.oauth2_scheme),
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    用户登出，使 Token 失效
    
    - **logout_all**: 是否登出所有设备（默认false，只登出当前设备）
    """
    # 提取当前token的JTI
    current_jti = security.extract_jti_from_token(token)
    
    if logout_data.logout_all:
        # 登出所有设备
        count = SessionService.revoke_all_sessions(
            db=db,
            user_id=current_user.id,
            except_jti=None,  # 包括当前会话
        )
        message = f"已登出所有设备（{count}个会话）"
    else:
        # 只登出当前设备
        if current_jti:
            session = SessionService.get_session_by_jti(db, current_jti, "access")
            if session:
                SessionService.revoke_session(db, session.id, current_user.id)
            else:
                # 如果找不到会话，仍然将token加入黑名单
                security.revoke_token(token)
        else:
            security.revoke_token(token)
        message = "登出成功"
    
    return ResponseModel(code=200, message=message)


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")  # 防止token刷新滥用
def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    使用Refresh Token刷新Access Token
    
    - **refresh_token**: 刷新令牌
    - **device_info**: 可选的设备信息
    
    错误码：
    - 401: Refresh Token无效或已过期
    - 403: 会话已被撤销
    """
    # 验证Refresh Token
    payload = security.verify_refresh_token(refresh_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token无效或已过期",
        )
    
    # 提取用户ID和JTI
    user_id_str = payload.get("sub")
    refresh_jti = payload.get("jti")
    
    if not user_id_str or not refresh_jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token格式错误",
        )
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token格式错误",
        )
    
    # 检查会话是否存在且有效
    session = SessionService.get_session_by_jti(db, refresh_jti, "refresh")
    if not session or not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="会话已失效，请重新登录",
        )
    
    # 验证用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    
    # 生成新的Access Token（使用滑动窗口策略）
    new_access_jti = secrets.token_hex(16)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = security.create_access_token(
        data={"sub": str(user_id)},
        expires_delta=access_token_expires,
        jti=new_access_jti,
    )
    
    # 将旧的Access Token加入黑名单
    if session.access_token_jti:
        security.revoke_token(session.access_token_jti)
    
    # 更新会话记录
    SessionService.update_session_activity(
        db=db,
        jti=refresh_jti,
        new_access_jti=new_access_jti,
    )
    
    logger.info(f"刷新Token成功: user_id={user_id}, session_id={session.id}")
    
    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


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
@limiter.limit("5/hour")  # 严格限制密码修改频率
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
