# -*- coding: utf-8 -*-
"""
认证模块 - 密码、Token、用户获取
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..models.user import User
from ..utils.redis_client import get_redis_client
from .config import settings

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

# Token 黑名单（优先使用Redis，不可用时降级到内存存储）
_token_blacklist = set()  # 内存黑名单（降级方案）
_token_blacklist_lock = Lock()

__all__ = [
    "pwd_context",
    "oauth2_scheme",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_active_superuser",
    "check_permission",
    "require_permission",
    "revoke_token",
    "is_token_revoked",
]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": secrets.token_hex(16),
        }
    )
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def revoke_token(token: Optional[str]) -> None:
    """
    将 Token 加入黑名单

    优先使用Redis存储，如果Redis不可用则使用内存存储。
    使用JTI (JWT ID) 作为黑名单键，并设置与token相同的过期时间。
    """
    if not token:
        return

    try:
        # 尝试从token中提取JTI和过期时间
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti:
            # 如果没有JTI，使用整个token的哈希值
            import hashlib

            jti = hashlib.sha256(token.encode()).hexdigest()

        # 尝试使用Redis
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 计算剩余过期时间（秒）
                if exp:
                    now = datetime.now(timezone.utc).timestamp()
                    ttl = max(int(exp - now), 60)  # 至少保留60秒
                else:
                    # 如果没有过期时间，使用默认过期时间
                    ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

                # 存储到Redis，key格式: jwt:blacklist:{jti}
                redis_key = f"jwt:blacklist:{jti}"
                redis_client.setex(redis_key, ttl, "1")
                logger.debug(f"Token已加入Redis黑名单: jti={jti[:8]}...")
                return
            except Exception as e:
                logger.warning(f"Redis操作失败，降级到内存存储: {e}")

        # 降级到内存存储
        with _token_blacklist_lock:
            _token_blacklist.add(token)
            logger.debug("Token已加入内存黑名单（降级模式）")
    except JWTError as e:
        logger.warning(f"无法解析token，直接加入内存黑名单: {e}")
        with _token_blacklist_lock:
            _token_blacklist.add(token)


def is_token_revoked(token: Optional[str]) -> bool:
    """
    判断 Token 是否已撤销

    优先检查Redis，如果Redis不可用则检查内存黑名单。
    """
    if not token:
        return False

    try:
        # 尝试从token中提取JTI
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        jti = payload.get("jti")

        if not jti:
            # 如果没有JTI，使用整个token的哈希值
            import hashlib

            jti = hashlib.sha256(token.encode()).hexdigest()

        # 尝试使用Redis
        redis_client = get_redis_client()
        if redis_client:
            try:
                redis_key = f"jwt:blacklist:{jti}"
                exists = redis_client.exists(redis_key)
                if exists:
                    return True
            except Exception as e:
                logger.warning(f"Redis查询失败，降级到内存检查: {e}")

        # 降级到内存检查
        with _token_blacklist_lock:
            return token in _token_blacklist
    except JWTError:
        # 如果无法解析token，检查内存黑名单
        with _token_blacklist_lock:
            return token in _token_blacklist


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 调试日志（生产环境建议禁用DEBUG级别）
    logger.debug(f"收到认证请求，token长度: {len(token) if token else 0}")
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        # sub字段是字符串，需要转换为整数
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        return user
    except Exception as e:
        logger.error(f"ORM查询用户失败: {e}", exc_info=True)
        # 如果是因为其他模型关系错误，尝试使用SQL查询
        try:
            from sqlalchemy import text

            result = db.execute(
                text(
                    "SELECT id, username, is_active, is_superuser FROM users WHERE id = :user_id"
                ),
                {"user_id": user_id},
            )
            user_row = result.fetchone()
            if user_row:
                # 创建一个简单的User对象
                user = User()
                user.id = user_row[0]
                user.username = user_row[1]
                user.is_active = bool(user_row[2])
                user.is_superuser = bool(user_row[3]) if len(user_row) > 3 else False
                # 设置其他必需字段的默认值
                user.employee_id = 0
                user.password_hash = None  # B105: 使用 None 而不是空字符串
                user.auth_type = "password"
                return user
            else:
                raise credentials_exception
        except Exception as sql_e:
            logger.error(f"SQL查询用户也失败: {sql_e}", exc_info=True)
            raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """获取当前超级管理员用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def _load_user_permissions_from_db(user_id: int, db: Session) -> set:
    """从数据库加载用户权限（含继承）"""
    from sqlalchemy import text

    # 查询用户直接拥有的权限 + 通过角色继承链获得的权限
    sql = """
        WITH RECURSIVE role_tree AS (
            -- 用户直接拥有的角色
            SELECT r.id, r.parent_id
            FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = :user_id

            UNION ALL

            -- 递归获取父角色
            SELECT r.id, r.parent_id
            FROM roles r
            JOIN role_tree rt ON r.id = rt.parent_id
        )
        SELECT DISTINCT p.perm_code
        FROM role_tree rt
        JOIN role_permissions rp ON rt.id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
    """
    result = db.execute(text(sql), {"user_id": user_id})
    return {row[0] for row in result.fetchall()}


def check_permission(user: User, permission_code: str, db: Session = None) -> bool:
    """
    检查用户权限（带缓存）

    优先从缓存获取用户权限列表，缓存不存在时从数据库加载并缓存。
    """
    if user.is_superuser:
        return True

    # 尝试使用缓存
    try:
        from ..services.permission_cache_service import get_permission_cache_service
        cache_service = get_permission_cache_service()

        # 从缓存获取用户权限
        cached_permissions = cache_service.get_user_permissions(user.id)

        if cached_permissions is not None:
            # 缓存命中
            logger.debug(f"Permission cache hit for user {user.id}")
            return permission_code in cached_permissions

        # 缓存未命中，从数据库加载
        if db is not None:
            permissions = _load_user_permissions_from_db(user.id, db)
            # 写入缓存
            cache_service.set_user_permissions(user.id, permissions)
            logger.debug(f"Permission cache miss for user {user.id}, loaded {len(permissions)} permissions")
            return permission_code in permissions
    except Exception as e:
        logger.warning(f"Permission cache failed, fallback to DB: {e}")

    # 降级：直接查询数据库
    try:
        from sqlalchemy import text

        if db is None:
            # 如果没有提供db，尝试使用ORM（可能失败）
            for user_role in user.roles:
                for role_permission in user_role.role.permissions:
                    if role_permission.permission.permission_code == permission_code:
                        return True
            return False
        else:
            # 使用SQL查询
            sql = """
                SELECT COUNT(*)
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = :user_id
                AND p.perm_code = :permission_code
            """
            result = db.execute(
                text(sql), {"user_id": user.id, "permission_code": permission_code}
            ).scalar()
            return result > 0
    except Exception as e:
        logger.warning(f"权限检查失败，使用ORM查询: {e}")
        # 降级到ORM查询
        try:
            for user_role in user.roles:
                for role_permission in user_role.role.permissions:
                    if role_permission.permission.permission_code == permission_code:
                        return True
        except Exception:
            logger.debug("权限检查 ORM 降级查询失败", exc_info=True)
        return False


def require_permission(permission_code: str):
    """权限装饰器依赖"""

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if not check_permission(current_user, permission_code, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有执行此操作的权限"
            )
        return current_user

    return permission_checker
