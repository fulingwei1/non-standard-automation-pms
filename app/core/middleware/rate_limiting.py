# -*- coding: utf-8 -*-
"""
速率限制中间件 - 基于内存的简单实现（无需Redis）

作为 slowapi 装饰器模式的全局补充层，保护所有未标注路由
策略：
- 登录接口：每分钟最多 10 次（防暴力破解）
- 全局请求：每分钟最多 300 次（内网用户，防误操作/脚本刷接口）
"""
import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class InMemoryRateLimiter:
    """基于滑动窗口的内存速率限制器（线程安全）"""

    def __init__(self):
        self._requests: dict = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        检查请求是否允许通过。

        Args:
            key:    限流键（如 "login:1.2.3.4"）
            limit:  时间窗口内允许的最大请求数
            window: 时间窗口长度（秒）

        Returns:
            True 表示允许，False 表示超出限制
        """
        now = time.time()
        with self._lock:
            bucket = self._requests[key]
            # 清理滑动窗口外的旧记录
            bucket[:] = [t for t in bucket if now - t < window]
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True


# 全局单例
rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """全局速率限制中间件（in-memory，无 Redis 依赖）"""

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # ── 登录接口专项限流 ───────────────────────────
        # 每分钟最多 10 次（防账号暴力破解）
        if "/auth/login" in path or "/auth/token" in path:
            if not rate_limiter.is_allowed(f"login:{client_ip}", 10, 60):
                return Response(
                    content='{"detail":"登录请求过于频繁，请稍后再试"}',
                    status_code=429,
                    media_type="application/json",
                )

        # ── 全局限流 ───────────────────────────────────
        # 每分钟最多 300 次（内网用户正常使用不会触发）
        if not rate_limiter.is_allowed(f"global:{client_ip}", 300, 60):
            return Response(
                content='{"detail":"请求过于频繁，请稍后再试"}',
                status_code=429,
                media_type="application/json",
            )

        return await call_next(request)


__all__ = ["InMemoryRateLimiter", "RateLimitMiddleware", "rate_limiter"]
