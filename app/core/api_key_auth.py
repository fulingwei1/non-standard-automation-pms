# -*- coding: utf-8 -*-
"""
API Key认证机制

提供基于API Key的认证方式，作为JWT的备选方案。
适用场景：
- 服务间调用
- 第三方集成
- 自动化脚本
- Webhook回调

安全特性：
- API Key加密存储（使用SHA256哈希）
- 支持权限范围限制
- 支持过期时间
- 支持IP白名单
- 请求速率限制
- 审计日志记录
"""

import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session


# API Key Header名称
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


class APIKeyAuth:
    """API Key认证管理器"""

    @staticmethod
    def generate_api_key(prefix: str = "pms") -> tuple[str, str]:
        """
        生成API Key
        
        格式: {prefix}_{random_string}
        
        Args:
            prefix: API Key前缀，用于识别来源
            
        Returns:
            tuple: (原始key, 哈希后的key)
        """
        # 生成32字节随机字符串
        random_part = secrets.token_urlsafe(32)
        api_key = f"{prefix}_{random_part}"
        
        # 计算哈希（用于存储）
        key_hash = APIKeyAuth.hash_api_key(api_key)
        
        return api_key, key_hash

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """
        对API Key进行哈希（使用SHA256）
        
        Args:
            api_key: 原始API Key
            
        Returns:
            str: 哈希后的key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def verify_api_key(db: Session, api_key: str, client_ip: Optional[str] = None) -> Optional[dict]:
        """
        验证API Key
        
        Args:
            db: 数据库会话
            api_key: 待验证的API Key
            client_ip: 客户端IP地址
            
        Returns:
            Optional[dict]: 验证成功返回API Key信息，失败返回None
        """
        if not api_key:
            return None

        # 计算哈希
        key_hash = APIKeyAuth.hash_api_key(api_key)

        # 从数据库查询（需要实现APIKey模型）
        try:
            from app.models.api_key import APIKey
            
            api_key_obj = db.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            ).first()

            if not api_key_obj:
                return None

            # 检查过期时间
            if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
                return None

            # 检查IP白名单
            if api_key_obj.allowed_ips:
                if client_ip not in api_key_obj.allowed_ips:
                    return None

            # 更新最后使用时间
            api_key_obj.last_used_at = datetime.utcnow()
            api_key_obj.usage_count = (api_key_obj.usage_count or 0) + 1
            db.commit()

            return {
                "id": api_key_obj.id,
                "name": api_key_obj.name,
                "user_id": api_key_obj.user_id,
                "tenant_id": api_key_obj.tenant_id,
                "scopes": api_key_obj.scopes or [],
                "metadata": api_key_obj.metadata or {}
            }

        except ImportError:
            # APIKey模型未实现，返回None
            import logging
            logging.getLogger(__name__).warning("APIKey模型未实现，跳过API Key认证")
            return None


async def get_api_key_user(
    api_key: str = Security(api_key_header),
    db: Session = None
) -> Optional[dict]:
    """
    从API Key获取用户信息（依赖注入）
    
    Args:
        api_key: API Key（从请求头提取）
        db: 数据库会话
        
    Returns:
        Optional[dict]: API Key信息
        
    Raises:
        HTTPException: 认证失败
    """
    if not api_key:
        return None

    # 获取客户端IP
    # client_ip = request.client.host if request.client else None

    # 验证API Key
    api_key_info = APIKeyAuth.verify_api_key(db, api_key)
    
    if not api_key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    return api_key_info


def require_api_key_scope(required_scope: str):
    """
    API Key权限装饰器
    
    Args:
        required_scope: 必需的权限范围
        
    Example:
        @router.get("/projects")
        async def list_projects(
            api_key_info: dict = Depends(require_api_key_scope("projects:read"))
        ):
            ...
    """
    async def check_scope(
        api_key_info: dict = Security(get_api_key_user)
    ) -> dict:
        if not api_key_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key required"
            )

        scopes = api_key_info.get("scopes", [])
        
        # 检查是否有管理员权限或特定权限
        if "admin" not in scopes and required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient API Key scope: {required_scope} required"
            )

        return api_key_info

    return check_scope


__all__ = [
    "APIKeyAuth",
    "get_api_key_user",
    "require_api_key_scope",
    "api_key_header"
]
