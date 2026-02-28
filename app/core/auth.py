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

from ..dependencies import get_db  # Moved to break circular import
from ..common.context import set_audit_context
from ..models.user import User
from ..utils.redis_client import get_redis_client
from .config import settings

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    "create_refresh_token",
    "create_token_pair",
    "verify_refresh_token",
    "verify_token_and_get_user",
    "get_current_user",
    "get_current_active_user",
    "get_current_active_superuser",
    "is_system_admin",
    "is_superuser",
    "validate_user_tenant_consistency",
    "check_permission",
    "require_permission",
    "revoke_token",
    "is_token_revoked",
    "extract_jti_from_token",
]


def is_superuser(user: User) -> bool:
    """
    判断用户是否为超级管理员
    
    超级管理员必须同时满足：
    1. is_superuser = True
    2. tenant_id IS NULL
    
    这是统一的超级管理员判断标准，避免使用 tenant_id is None 单独判断。
    
    Args:
        user: 用户对象
        
    Returns:
        bool: 是否为超级管理员
        
    Example:
        >>> if is_superuser(current_user):
        >>>     # 超级管理员可以访问所有资源
        >>>     pass
    """
    return getattr(user, "is_superuser", False) and getattr(user, "tenant_id", 0) is None


def validate_user_tenant_consistency(user: User) -> None:
    """
    验证用户租户数据一致性
    
    确保用户数据符合以下规则：
    1. 超级管理员：is_superuser=True 且 tenant_id IS NULL
    2. 租户用户：is_superuser=False 且 tenant_id IS NOT NULL
    
    Args:
        user: 用户对象
        
    Raises:
        ValueError: 当用户数据不一致时抛出异常
        
    Example:
        >>> validate_user_tenant_consistency(user)  # 验证通过
        >>> # 或抛出 ValueError
    """
    user_is_superuser = getattr(user, "is_superuser", False)
    user_tenant_id = getattr(user, "tenant_id", 0)
    user_id = getattr(user, "id", "unknown")
    
    # 超级管理员必须 tenant_id 为 None
    if user_is_superuser and user_tenant_id is not None:
        raise ValueError(
            f"Invalid superuser data: user_id={user_id} has is_superuser=True "
            f"but tenant_id={user_tenant_id} (should be NULL)"
        )
    
    # 非超级管理员必须有 tenant_id
    if not user_is_superuser and user_tenant_id is None:
        raise ValueError(
            f"Invalid tenant user data: user_id={user_id} has is_superuser=False "
            f"but tenant_id is NULL (should have a valid tenant_id)"
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 (直接使用 bcrypt，绕过 passlib 兼容性问题)"""
    import bcrypt
    password_bytes = plain_password.encode('utf-8')[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """生成密码哈希 (直接使用 bcrypt，绕过 passlib 兼容性问题)"""
    import bcrypt
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None,
) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        jti: JWT ID（可选，用于会话管理）
    
    Returns:
        JWT token字符串
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    if not jti:
        jti = secrets.token_hex(16)
    
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": jti,
            "token_type": "access",
        }
    )
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None,
) -> str:
    """
    创建刷新令牌
    
    Refresh Token有效期更长，用于获取新的Access Token
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量（默认7天）
        jti: JWT ID（可选，用于会话管理）
    
    Returns:
        JWT refresh token字符串
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        # 默认7天有效期
        expire = now + timedelta(days=7)
    
    if not jti:
        jti = secrets.token_hex(16)
    
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": jti,
            "token_type": "refresh",
        }
    )
    
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_token_pair(
    data: dict,
    access_expires: Optional[timedelta] = None,
    refresh_expires: Optional[timedelta] = None,
) -> tuple[str, str, str, str]:
    """
    创建Access Token和Refresh Token对
    
    Args:
        data: 要编码的数据（通常包含用户ID）
        access_expires: Access Token过期时间
        refresh_expires: Refresh Token过期时间
    
    Returns:
        (access_token, refresh_token, access_jti, refresh_jti)
    """
    # 生成唯一的JTI
    access_jti = secrets.token_hex(16)
    refresh_jti = secrets.token_hex(16)
    
    # 创建tokens
    access_token = create_access_token(
        data=data,
        expires_delta=access_expires,
        jti=access_jti,
    )
    
    refresh_token = create_refresh_token(
        data=data,
        expires_delta=refresh_expires,
        jti=refresh_jti,
    )
    
    return access_token, refresh_token, access_jti, refresh_jti


def verify_refresh_token(refresh_token: str) -> Optional[dict]:
    """
    验证Refresh Token
    
    Args:
        refresh_token: 要验证的refresh token
    
    Returns:
        解码后的payload，验证失败返回None
    """
    try:
        # 检查是否在黑名单中
        if is_token_revoked(refresh_token):
            logger.warning("Refresh token已被撤销")
            return None
        
        # 解码token
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # 验证token类型
        if payload.get("token_type") != "refresh":
            logger.warning("Token类型错误，期望refresh token")
            return None
        
        return payload
    
    except JWTError as e:
        logger.warning(f"Refresh token验证失败: {e}")
        return None


def extract_jti_from_token(token: str) -> Optional[str]:
    """
    从token中提取JTI（不验证token有效性）
    
    Args:
        token: JWT token字符串
    
    Returns:
        JTI字符串或None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        return payload.get("jti")
    except JWTError:
        return None


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


async def verify_token_and_get_user(token: str, db: Session) -> User:
    """
    验证Token并获取用户（供中间件使用，不使用Depends）
    
    Args:
        token: JWT token字符串
        db: 数据库会话
    
    Returns:
        User对象
    
    Raises:
        HTTPException: 认证失败时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    logger.debug(f"中间件验证token，长度: {len(token) if token else 0}")
    
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
        
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT解析失败: {e}")
        raise credentials_exception

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning(f"用户不存在: user_id={user_id}")
            raise credentials_exception

        # 设置审计上下文
        set_audit_context(operator_id=user.id, tenant_id=user.tenant_id)
        
        logger.debug(f"中间件认证成功: user_id={user.id}, username={user.username}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询用户失败: {e}", exc_info=True)
        raise credentials_exception


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
        # 查询用户（User.roles 是 lazy="dynamic"，不需要预加载）
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception

        # 将操作人ID和租户ID设置到上下文中，用于审计日志和数据隔离
        set_audit_context(operator_id=user.id, tenant_id=user.tenant_id)

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
    if not (current_user.is_superuser or is_system_admin(current_user)):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def _load_user_permissions_from_db(
    user_id: int, db: Session, tenant_id: Optional[int] = None
) -> set:
    """从数据库加载用户权限（含角色继承 + 多租户隔离）

    多租户权限规则：
    - 系统级权限（tenant_id=NULL）：所有租户可用
    - 租户级权限（tenant_id=N）：仅该租户可用

    Args:
        user_id: 用户ID
        db: 数据库会话
        tenant_id: 租户ID（用于过滤租户专属权限）

    Returns:
        权限编码集合
    """
    from sqlalchemy import text

    # 查询用户直接拥有的权限 + 通过角色继承链获得的权限
    # 权限过滤：系统级权限(tenant_id IS NULL) + 当前租户权限
    # 根据 tenant_id 是否为 None 使用不同的 SQL 条件
    # 避免 SQL 中 column = NULL 的问题（NULL 比较需要用 IS NULL）
    if tenant_id is not None:
        tenant_filter = "AND (ap.tenant_id IS NULL OR ap.tenant_id = :tenant_id)"
        params = {"user_id": user_id, "tenant_id": tenant_id}
    else:
        tenant_filter = "AND ap.tenant_id IS NULL"
        params = {"user_id": user_id}

    sql = f"""
        WITH RECURSIVE role_tree AS (
            -- 用户直接拥有的角色
            SELECT r.id, r.parent_id, r.inherit_permissions
            FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = :user_id

            UNION ALL

            -- 递归获取父角色（仅当 inherit_permissions=1 时）
            SELECT r.id, r.parent_id, r.inherit_permissions
            FROM roles r
            JOIN role_tree rt ON r.id = rt.parent_id
            WHERE rt.inherit_permissions = 1
        )
        SELECT DISTINCT ap.perm_code
        FROM role_tree rt
        JOIN role_api_permissions rap ON rt.id = rap.role_id
        JOIN api_permissions ap ON rap.permission_id = ap.id
        WHERE ap.is_active = 1
        {tenant_filter}
    """
    result = db.execute(text(sql), params)
    return {row[0] for row in result.fetchall()}


def is_system_admin(user: User) -> bool:
    """
    判断用户是否为系统管理员角色

    仅通过数据库标志位判断，不使用硬编码角色名，防止通过创建特定角色名提权。
    检查条件：
    1. is_superuser(user) = True (统一判断：is_superuser=True AND tenant_id IS NULL)
    2. User.is_tenant_admin = True
    3. 用户拥有 is_system=True 且 role_code='ADMIN' 的系统预置角色
    """
    # 优先检查超级管理员标志位（使用统一判断函数）
    if is_superuser(user):
        return True
    
    # 检查租户管理员
    if getattr(user, "is_tenant_admin", False):
        return True

    # 仅检查系统预置的 ADMIN 角色（is_system=True），防止用户自建同名角色提权
    roles = getattr(user, "roles", None)
    if not roles:
        return False

    if hasattr(roles, "all"):
        roles = roles.all()

    for user_role in roles or []:
        role = getattr(user_role, "role", user_role)
        role_code = getattr(role, "role_code", "")
        is_system = getattr(role, "is_system", False)
        # 只有系统预置角色（is_system=True）的 ADMIN 才被认可
        if is_system and role_code == "ADMIN":
            return True

    return False


def check_permission(user: User, permission_code: str, db: Session = None) -> bool:
    """
    检查用户权限（带缓存，支持多租户隔离）

    优先从缓存获取用户权限列表，缓存不存在时从数据库加载并缓存。
    缓存使用 tenant_id 进行隔离，防止跨租户数据泄露。
    """
    logger.info(
        f"Checking permission: user_id={user.id}, username={user.username}, code={permission_code}, is_superuser={user.is_superuser}"
    )
    if user.is_superuser or is_system_admin(user):
        logger.info(f"Permission GRANTED (superuser/admin): user_id={user.id}")
        return True

    # 获取租户ID用于缓存隔离
    tenant_id = getattr(user, "tenant_id", None)

    # 尝试使用缓存
    try:
        from ..services.permission_cache_service import get_permission_cache_service

        cache_service = get_permission_cache_service()

        # 从缓存获取用户权限（包含租户隔离）
        cached_permissions = cache_service.get_user_permissions(user.id, tenant_id)

        if cached_permissions is not None:
            # 缓存命中
            logger.debug(f"Permission cache hit for user {user.id} (tenant={tenant_id})")
            return permission_code in cached_permissions

        # 缓存未命中，从数据库加载
        if db is not None:
            permissions = _load_user_permissions_from_db(user.id, db, tenant_id)
            # 写入缓存（包含租户隔离）
            cache_service.set_user_permissions(user.id, permissions, tenant_id)
            logger.debug(
                f"Permission cache miss for user {user.id} (tenant={tenant_id}), loaded {len(permissions)} permissions"
            )
            return permission_code in permissions
    except Exception as e:
        logger.warning(f"Permission cache failed, fallback to DB: {e}")

    # 降级：直接查询数据库（使用新的 api_permissions 表）
    try:
        from sqlalchemy import text

        if db is None:
            # 如果没有提供db，尝试使用ORM（可能失败）
            for user_role in user.roles:
                role = user_role.role
                if hasattr(role, "api_permissions"):
                    for rap in role.api_permissions:
                        if (
                            rap.permission
                            and rap.permission.perm_code == permission_code
                        ):
                            return True
            return False
        else:
            # 使用SQL查询（已迁移到新表）
            sql = """
                SELECT COUNT(*)
                FROM user_roles ur
                JOIN role_api_permissions rap ON ur.role_id = rap.role_id
                JOIN api_permissions ap ON rap.permission_id = ap.id
                WHERE ur.user_id = :user_id
                AND ap.perm_code = :permission_code
                AND ap.is_active = 1
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
                role = user_role.role
                if hasattr(role, "api_permissions"):
                    for rap in role.api_permissions:
                        if (
                            rap.permission
                            and rap.permission.perm_code == permission_code
                        ):
                            return True
        except Exception:
            logger.debug("权限检查 ORM 降级查询失败", exc_info=True)
        return False


def require_permission(permission_code: str):
    """
    权限检查 - 兼容两种用法:
    1. 作为装饰器: @require_permission("some:permission")
    2. 作为依赖:   Depends(require_permission("some:permission"))

    Note: 兼容性实现，暂不做真正的权限校验，仅校验登录状态
    TODO: 实现真正的权限检查逻辑
    """
    import functools
    from fastapi import Depends as _Depends

    # When called as Depends(), FastAPI will introspect this function's signature.
    # We return a dependency function that accepts the same args as get_current_active_user.
    def permission_dependency(
        current_user: "User" = _Depends(get_current_active_user),
    ) -> "User":
        # TODO: check current_user has permission_code
        return current_user

    # Support use as a plain decorator too: @require_permission("x")
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    # Make the returned object work as both a Depends-callable AND a decorator.
    # FastAPI calls it with keyword arguments; decorator usage calls it with a function.
    class _PermissionGuard:
        """Callable that works as Depends-dependency and as decorator."""

        def __call__(self, *args, **kwargs):
            # If called with a single callable argument (decorator use): return wrapped func
            if len(args) == 1 and callable(args[0]) and not kwargs:
                return decorator(args[0])
            # Otherwise behave as the dependency (should not be called directly)
            return permission_dependency(*args, **kwargs)

        # FastAPI inspects __call__'s signature for Depends resolution;
        # copy signature from permission_dependency so it sees (current_user) not (*args, **kwargs).
        __wrapped__ = permission_dependency
        __signature__ = permission_dependency.__code__

    guard = _PermissionGuard()
    # Copy the signature so FastAPI can resolve the dependency correctly
    import inspect
    guard.__signature__ = inspect.signature(permission_dependency)
    return guard
