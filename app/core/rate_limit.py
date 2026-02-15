# -*- coding: utf-8 -*-
"""
API 速率限制配置

用于防止暴力破解和 DDoS 攻击

注意：这是一个兼容性模块，实际实现在 rate_limiting.py
"""
from app.core.rate_limiting import (
    limiter,
    user_limiter,
    strict_limiter,
    get_remote_address,
    get_user_or_ip,
    get_ip_and_user,
)

__all__ = [
    "limiter",
    "user_limiter",
    "strict_limiter",
    "get_remote_address",
    "get_user_or_ip",
    "get_ip_and_user",
]
