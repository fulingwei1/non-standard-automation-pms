# -*- coding: utf-8 -*-
"""
请求签名验证机制

提供基于HMAC-SHA256的请求签名验证，防止请求篡改和重放攻击。

签名算法：
1. 构建签名字符串：{method}\n{path}\n{timestamp}\n{body_hash}
2. 使用HMAC-SHA256计算签名：HMAC-SHA256(secret, signature_string)
3. Base64编码签名结果

请求头：
- X-Signature: 签名值
- X-Timestamp: 时间戳（毫秒）
- X-Nonce: 随机数（可选，增强安全性）

安全特性：
- 防止请求篡改（验证body完整性）
- 防止重放攻击（时间窗口验证）
- 支持Nonce去重（可选）
"""

import base64
import hashlib
import hmac
import time
from typing import Optional

from fastapi import HTTPException, Request, status

from app.core.config import settings


class RequestSignatureVerifier:
    """请求签名验证器"""

    # 签名有效期（秒）- 防止重放攻击
    SIGNATURE_EXPIRY_SECONDS = 300  # 5分钟

    @staticmethod
    def compute_signature(
        method: str,
        path: str,
        timestamp: str,
        body: bytes,
        secret: str
    ) -> str:
        """
        计算请求签名
        
        Args:
            method: HTTP方法（GET, POST等）
            path: 请求路径（包含query参数）
            timestamp: 时间戳（毫秒）
            body: 请求体（字节）
            secret: 签名密钥
            
        Returns:
            str: Base64编码的签名
        """
        # 计算body的SHA256哈希
        body_hash = hashlib.sha256(body).hexdigest()

        # 构建签名字符串
        signature_string = f"{method}\n{path}\n{timestamp}\n{body_hash}"

        # 使用HMAC-SHA256计算签名
        signature_bytes = hmac.new(
            secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Base64编码
        return base64.b64encode(signature_bytes).decode('utf-8')

    @staticmethod
    def verify_signature(
        request: Request,
        signature: str,
        timestamp: str,
        body: bytes,
        secret: str,
        nonce: Optional[str] = None
    ) -> bool:
        """
        验证请求签名
        
        Args:
            request: FastAPI请求对象
            signature: 请求携带的签名
            timestamp: 时间戳（毫秒）
            body: 请求体
            secret: 签名密钥
            nonce: 随机数（可选）
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            HTTPException: 验证失败
        """
        # 1. 验证时间戳（防止重放攻击）
        try:
            ts = int(timestamp)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timestamp format"
            )

        current_time = int(time.time() * 1000)
        time_diff = abs(current_time - ts)

        if time_diff > RequestSignatureVerifier.SIGNATURE_EXPIRY_SECONDS * 1000:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request signature expired"
            )

        # 2. 计算期望的签名
        method = request.method
        path = str(request.url.path)
        if request.url.query:
            path += f"?{request.url.query}"

        expected_signature = RequestSignatureVerifier.compute_signature(
            method=method,
            path=path,
            timestamp=timestamp,
            body=body,
            secret=secret
        )

        # 3. 比较签名（恒定时间比较，防止时序攻击）
        import secrets
        if not secrets.compare_digest(signature, expected_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid request signature"
            )

        # 4. 验证Nonce（可选，需要Redis或数据库存储）
        if nonce:
            # TODO: 检查nonce是否已使用（需要缓存支持）
            pass

        return True

    @staticmethod
    async def verify_request(
        request: Request,
        secret: Optional[str] = None
    ) -> bool:
        """
        验证请求签名（从请求头提取信息）
        
        Args:
            request: FastAPI请求对象
            secret: 签名密钥（默认使用settings.SECRET_KEY）
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            HTTPException: 验证失败
        """
        # 提取签名相关头
        signature = request.headers.get("X-Signature")
        timestamp = request.headers.get("X-Timestamp")
        nonce = request.headers.get("X-Nonce")

        if not signature or not timestamp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature headers (X-Signature, X-Timestamp)"
            )

        # 读取请求体
        body = await request.body()

        # 使用默认密钥
        if secret is None:
            secret = settings.SECRET_KEY

        return RequestSignatureVerifier.verify_signature(
            request=request,
            signature=signature,
            timestamp=timestamp,
            body=body,
            secret=secret,
            nonce=nonce
        )


def generate_client_signature(
    method: str,
    url: str,
    body: bytes,
    secret: str
) -> tuple[str, str]:
    """
    生成客户端请求签名（工具函数）
    
    Args:
        method: HTTP方法
        url: 完整URL（包含query参数）
        body: 请求体
        secret: 签名密钥
        
    Returns:
        tuple: (signature, timestamp)
        
    Example:
        >>> signature, timestamp = generate_client_signature(
        ...     method="POST",
        ...     url="https://api.example.com/v1/projects",
        ...     body=b'{"name":"test"}',
        ...     secret="your-secret-key"
        ... )
        >>> headers = {
        ...     "X-Signature": signature,
        ...     "X-Timestamp": timestamp
        ... }
    """
    from urllib.parse import urlparse
    
    parsed_url = urlparse(url)
    path = parsed_url.path
    if parsed_url.query:
        path += f"?{parsed_url.query}"

    # 生成时间戳（毫秒）
    timestamp = str(int(time.time() * 1000))

    # 计算签名
    signature = RequestSignatureVerifier.compute_signature(
        method=method,
        path=path,
        timestamp=timestamp,
        body=body,
        secret=secret
    )

    return signature, timestamp


__all__ = [
    "RequestSignatureVerifier",
    "generate_client_signature"
]
