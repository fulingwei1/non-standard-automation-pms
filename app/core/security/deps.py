# -*- coding: utf-8 -*-
"""
依赖注入模块

包含数据库会话获取、当前用户获取等FastAPI依赖
"""

import logging

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import settings
from ...models.base import get_session
from ...models.user import User
from .auth import oauth2_scheme, is_token_revoked

logger = logging.getLogger(__name__)


def get_db():
    """获取数据库会话依赖"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 调试日志
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
                text("SELECT id, username, is_active, is_superuser FROM users WHERE id = :user_id"),
                {"user_id": user_id}
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
                user.password_hash = ""
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
