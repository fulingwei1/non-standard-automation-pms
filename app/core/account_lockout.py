# -*- coding: utf-8 -*-
"""
账号锁定机制 - 内存实现（无需 Redis / 数据库）

连续登录失败 5 次后锁定 30 分钟，服务重启后自动解锁。
生产环境建议使用 app/services/account_lockout_service.py（Redis 持久化版）。

使用示例（在 auth endpoint 中）：
    from app.core.account_lockout import account_lockout

    locked, remain = account_lockout.is_locked(username)
    if locked:
        raise HTTPException(403, f"账号已锁定，请 {remain:.0f} 秒后重试")

    if not verify_password(password, hash):
        account_lockout.record_failure(username)
        raise HTTPException(401, "密码错误")

    account_lockout.reset(username)
"""
import time
from collections import defaultdict
from threading import Lock


class AccountLockout:
    """基于内存的账号锁定机制（线程安全）"""

    MAX_FAILURES: int = 5          # 允许的最大失败次数
    LOCKOUT_DURATION: int = 30 * 60  # 锁定时长（秒），默认 30 分钟

    def __init__(self):
        self._failures: dict = defaultdict(list)
        self._locked_until: dict = {}
        self._lock = Lock()

    def record_failure(self, username: str) -> bool:
        """
        记录一次登录失败。

        Args:
            username: 用户名

        Returns:
            True 表示本次失败触发了账号锁定，False 表示尚未达到阈值
        """
        now = time.time()
        with self._lock:
            # 清理超出统计窗口的旧记录
            self._failures[username] = [
                t for t in self._failures[username] if now - t < self.LOCKOUT_DURATION
            ]
            self._failures[username].append(now)

            if len(self._failures[username]) >= self.MAX_FAILURES:
                self._locked_until[username] = now + self.LOCKOUT_DURATION
                return True
            return False

    def is_locked(self, username: str) -> tuple[bool, float]:
        """
        检查账号是否处于锁定状态。

        Returns:
            (is_locked, remaining_seconds)
            is_locked=True 时 remaining_seconds 为剩余锁定秒数
        """
        now = time.time()
        with self._lock:
            locked_until = self._locked_until.get(username, 0)
            if locked_until > now:
                return True, locked_until - now
            if locked_until > 0:
                # 锁定已自然过期，清理状态
                del self._locked_until[username]
                self._failures[username] = []
            return False, 0.0

    def reset(self, username: str) -> None:
        """登录成功后重置失败计数和锁定状态。"""
        with self._lock:
            self._failures.pop(username, None)
            self._locked_until.pop(username, None)

    def remaining_attempts(self, username: str) -> int:
        """返回当前账号剩余允许失败次数（仅供前端提示用）。"""
        now = time.time()
        with self._lock:
            recent = [t for t in self._failures[username] if now - t < self.LOCKOUT_DURATION]
            return max(0, self.MAX_FAILURES - len(recent))


# 全局单例（in-memory 简化版）
account_lockout = AccountLockout()

__all__ = ["AccountLockout", "account_lockout"]
