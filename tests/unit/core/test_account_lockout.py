# -*- coding: utf-8 -*-
"""
账号锁定机制测试
"""

import time
import pytest
from unittest.mock import patch

from app.core.account_lockout import AccountLockout, account_lockout


class TestAccountLockoutInit:
    """测试账号锁定初始化"""
    
    def test_init(self):
        """测试初始化"""
        lockout = AccountLockout()
        assert lockout.MAX_FAILURES == 5
        assert lockout.LOCKOUT_DURATION == 30 * 60
        assert isinstance(lockout._failures, dict)
        assert isinstance(lockout._locked_until, dict)
    
    def test_constants(self):
        """测试常量配置"""
        lockout = AccountLockout()
        assert lockout.MAX_FAILURES > 0
        assert lockout.LOCKOUT_DURATION > 0


class TestRecordFailure:
    """测试记录登录失败"""
    
    def test_record_first_failure(self):
        """测试记录第一次失败"""
        lockout = AccountLockout()
        result = lockout.record_failure("testuser")
        assert result is False  # 未达到锁定阈值
    
    def test_record_multiple_failures(self):
        """测试记录多次失败"""
        lockout = AccountLockout()
        
        for i in range(4):
            result = lockout.record_failure("testuser")
            assert result is False
        
        # 第5次失败应触发锁定
        result = lockout.record_failure("testuser")
        assert result is True
    
    def test_record_failures_different_users(self):
        """测试不同用户的失败记录独立"""
        lockout = AccountLockout()
        
        lockout.record_failure("user1")
        lockout.record_failure("user2")
        
        assert len(lockout._failures["user1"]) == 1
        assert len(lockout._failures["user2"]) == 1
    
    def test_record_failure_cleans_old_records(self):
        """测试记录失败时清理旧记录"""
        lockout = AccountLockout()
        
        # 模拟旧的失败记录
        old_time = time.time() - lockout.LOCKOUT_DURATION - 100
        lockout._failures["testuser"] = [old_time]
        
        # 记录新失败
        lockout.record_failure("testuser")
        
        # 旧记录应被清理
        assert len(lockout._failures["testuser"]) == 1
        assert lockout._failures["testuser"][0] > old_time


class TestIsLocked:
    """测试账号锁定状态检查"""
    
    def test_is_locked_not_locked(self):
        """测试未锁定的账号"""
        lockout = AccountLockout()
        
        is_locked, remaining = lockout.is_locked("testuser")
        
        assert is_locked is False
        assert remaining == 0.0
    
    def test_is_locked_after_max_failures(self):
        """测试达到最大失败次数后锁定"""
        lockout = AccountLockout()
        
        # 触发锁定
        for i in range(5):
            lockout.record_failure("testuser")
        
        is_locked, remaining = lockout.is_locked("testuser")
        
        assert is_locked is True
        assert remaining > 0
        assert remaining <= lockout.LOCKOUT_DURATION
    
    def test_is_locked_clears_expired_lock(self):
        """测试过期的锁定自动清理"""
        lockout = AccountLockout()
        
        # 设置已过期的锁定
        lockout._locked_until["testuser"] = time.time() - 100
        lockout._failures["testuser"] = [time.time() - 200]
        
        is_locked, remaining = lockout.is_locked("testuser")
        
        assert is_locked is False
        assert remaining == 0.0
        assert "testuser" not in lockout._locked_until
        assert lockout._failures["testuser"] == []
    
    def test_is_locked_remaining_time(self):
        """测试剩余锁定时间计算"""
        lockout = AccountLockout()
        
        # 设置锁定时间
        future_time = time.time() + 600  # 10分钟后
        lockout._locked_until["testuser"] = future_time
        
        is_locked, remaining = lockout.is_locked("testuser")
        
        assert is_locked is True
        assert 595 < remaining < 605  # 允许一定误差


class TestReset:
    """测试重置账号状态"""
    
    def test_reset_clears_failures(self):
        """测试重置清除失败记录"""
        lockout = AccountLockout()
        
        lockout.record_failure("testuser")
        lockout.record_failure("testuser")
        
        lockout.reset("testuser")
        
        assert "testuser" not in lockout._failures or lockout._failures["testuser"] == []
    
    def test_reset_clears_lockout(self):
        """测试重置清除锁定状态"""
        lockout = AccountLockout()
        
        # 触发锁定
        for i in range(5):
            lockout.record_failure("testuser")
        
        lockout.reset("testuser")
        
        is_locked, _ = lockout.is_locked("testuser")
        assert is_locked is False
        assert "testuser" not in lockout._locked_until
    
    def test_reset_nonexistent_user(self):
        """测试重置不存在的用户"""
        lockout = AccountLockout()
        
        # 不应抛出异常
        lockout.reset("nonexistent")
        
        assert True  # 如果到这里，说明没有抛出异常


class TestRemainingAttempts:
    """测试剩余尝试次数"""
    
    def test_remaining_attempts_initial(self):
        """测试初始剩余次数"""
        lockout = AccountLockout()
        
        remaining = lockout.remaining_attempts("testuser")
        
        assert remaining == lockout.MAX_FAILURES
    
    def test_remaining_attempts_after_failures(self):
        """测试失败后的剩余次数"""
        lockout = AccountLockout()
        
        lockout.record_failure("testuser")
        lockout.record_failure("testuser")
        
        remaining = lockout.remaining_attempts("testuser")
        
        assert remaining == lockout.MAX_FAILURES - 2
    
    def test_remaining_attempts_zero(self):
        """测试剩余次数为0"""
        lockout = AccountLockout()
        
        # 触发锁定
        for i in range(5):
            lockout.record_failure("testuser")
        
        remaining = lockout.remaining_attempts("testuser")
        
        assert remaining == 0
    
    def test_remaining_attempts_cleans_old_records(self):
        """测试计算剩余次数时清理旧记录"""
        lockout = AccountLockout()
        
        # 添加旧的失败记录
        old_time = time.time() - lockout.LOCKOUT_DURATION - 100
        lockout._failures["testuser"] = [old_time, old_time, old_time]
        
        # 添加新的失败记录
        lockout.record_failure("testuser")
        
        remaining = lockout.remaining_attempts("testuser")
        
        # 应该只计算新记录
        assert remaining == lockout.MAX_FAILURES - 1


class TestThreadSafety:
    """测试线程安全性"""
    
    def test_lock_exists(self):
        """测试锁对象存在"""
        lockout = AccountLockout()
        assert lockout._lock is not None
    
    def test_concurrent_access(self):
        """测试并发访问（基本测试）"""
        import threading
        
        lockout = AccountLockout()
        errors = []
        
        def record_failures():
            try:
                for i in range(10):
                    lockout.record_failure("concurrent_user")
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=record_failures) for _ in range(3)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0  # 不应有异常


class TestGlobalInstance:
    """测试全局单例"""
    
    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert account_lockout is not None
        assert isinstance(account_lockout, AccountLockout)
    
    def test_global_instance_is_singleton(self):
        """测试全局实例是单例"""
        from app.core.account_lockout import account_lockout as lockout2
        
        assert account_lockout is lockout2


class TestRealWorldScenario:
    """测试真实场景"""
    
    def test_login_flow(self):
        """测试登录流程"""
        lockout = AccountLockout()
        username = "testuser"
        
        # 1. 初始状态
        is_locked, _ = lockout.is_locked(username)
        assert is_locked is False
        
        # 2. 失败4次
        for i in range(4):
            lockout.record_failure(username)
            is_locked, _ = lockout.is_locked(username)
            assert is_locked is False
        
        # 3. 第5次失败，触发锁定
        lockout.record_failure(username)
        is_locked, remaining = lockout.is_locked(username)
        assert is_locked is True
        assert remaining > 0
        
        # 4. 重置后可以再次登录
        lockout.reset(username)
        is_locked, _ = lockout.is_locked(username)
        assert is_locked is False
    
    def test_lockout_expiration(self):
        """测试锁定过期"""
        lockout = AccountLockout()
        username = "testuser"
        
        # 设置一个很快就过期的锁定
        lockout._locked_until[username] = time.time() + 0.1
        
        # 立即检查应该是锁定的
        is_locked, _ = lockout.is_locked(username)
        assert is_locked is True
        
        # 等待过期
        time.sleep(0.2)
        
        # 应该自动解锁
        is_locked, _ = lockout.is_locked(username)
        assert is_locked is False
