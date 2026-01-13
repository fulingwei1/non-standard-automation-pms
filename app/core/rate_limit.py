# -*- coding: utf-8 -*-
"""
API 速率限制配置

用于防止暴力破解和 DDoS 攻击
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# 使用客户端 IP 作为限制键
limiter = Limiter(key_func=get_remote_address)
