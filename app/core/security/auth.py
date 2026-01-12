# -*- coding: utf-8 -*-
"""
基础认证模块

包含密码验证、JWT令牌创建、Token黑名单管理等功能
"""

from datetime import datetime, timedelta
from threading import Lock
from typing import Optional
import secrets
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from ..config import settings
from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

# Token 黑名单（优先使用Redis，不可用时降级到内存存储）
_token_blacklist = set()  # 内存黑名单（降级方案）
_token_blacklist_lock = Lock()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
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
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}
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
                    now = datetime.utcnow().timestamp()
                    ttl = max(int(exp - now), 60)  # 至少保留60秒
                else:
                    # 如果没有过期时间，使用默认过期时间
                    ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

                # 存储到Redis，key格式: jwt:blacklist:{jti}
                redis_key = f"jwt:blacklist:{jti}"
                redis_client.setex(redis_key, ttl, "1")
                logger.debug(f"Token已加入Redis黑名单: {jti[:16]}...")
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
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}
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
