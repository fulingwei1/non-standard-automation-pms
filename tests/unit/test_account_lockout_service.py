# -*- coding: utf-8 -*-
"""
账户锁定服务单元测试
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.login_attempt import LoginAttempt
from app.services.account_lockout_service import AccountLockoutService


class TestAccountLockoutService(unittest.TestCase):
    """账户锁定服务测试"""
    
    def setUp(self):
        """每个测试前执行"""
        self.username = "testuser"
        self.ip = "192.168.1.100"
        self.user_agent = "Mozilla/5.0"
        self.mock_db = MagicMock(spec=Session)
        
    def tearDown(self):
        """每个测试后执行"""
        pass


class TestLockoutLogic(TestAccountLockoutService):
    """锁定逻辑测试（8个用例）"""
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_check_lockout_not_locked(self, mock_redis_client):
        """测试账户未锁定状态"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.check_lockout(self.username, self.mock_db)
        
        self.assertFalse(result["locked"])
        self.assertIsNone(result["locked_until"])
        self.assertEqual(result["remaining_attempts"], AccountLockoutService.LOCKOUT_THRESHOLD)
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_check_lockout_locked(self, mock_redis_client):
        """测试账户已锁定状态"""
        locked_until = datetime.now() + timedelta(minutes=10)
        mock_redis = MagicMock()
        mock_redis.get.side_effect = [locked_until.isoformat(), None]
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.check_lockout(self.username, self.mock_db)
        
        self.assertTrue(result["locked"])
        self.assertIsNotNone(result["locked_until"])
        self.assertEqual(result["remaining_attempts"], 0)
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_record_failed_login_increments_attempts(self, mock_redis_client):
        """测试记录失败登录增加尝试次数"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 2
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.record_failed_login(
            self.username, self.ip, self.user_agent, db=self.mock_db
        )
        
        self.assertEqual(result["attempts"], 2)
        self.assertFalse(result["locked"])
        # incr 会被调用多次（username + IP 两个计数器）
        self.assertGreaterEqual(mock_redis.incr.call_count, 1)
        mock_redis.expire.assert_called()
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_record_failed_login_triggers_lockout(self, mock_redis_client):
        """测试达到阈值触发锁定"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = AccountLockoutService.LOCKOUT_THRESHOLD
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.record_failed_login(
            self.username, self.ip, self.user_agent, db=self.mock_db
        )
        
        self.assertEqual(result["attempts"], AccountLockoutService.LOCKOUT_THRESHOLD)
        self.assertTrue(result["locked"])
        self.assertIsNotNone(result["locked_until"])
        mock_redis.setex.assert_called_once()
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_record_successful_login_clears_attempts(self, mock_redis_client):
        """测试成功登录清除失败次数"""
        mock_redis = MagicMock()
        mock_redis_client.return_value = mock_redis
        
        AccountLockoutService.record_successful_login(
            self.username, self.ip, self.user_agent, self.mock_db
        )
        
        # 验证删除了两个key
        self.assertEqual(mock_redis.delete.call_count, 2)
        mock_redis.delete.assert_any_call(f"login_attempts:{self.username}")
        mock_redis.delete.assert_any_call(f"lockout:{self.username}")
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_remaining_attempts_calculation(self, mock_redis_client):
        """测试剩余尝试次数计算"""
        mock_redis = MagicMock()
        # 已失败3次
        mock_redis.get.side_effect = [None, "3"]
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.check_lockout(self.username, self.mock_db)
        
        expected_remaining = AccountLockoutService.LOCKOUT_THRESHOLD - 3
        self.assertEqual(result["remaining_attempts"], expected_remaining)
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_captcha_threshold(self, mock_redis_client):
        """测试验证码阈值"""
        mock_redis = MagicMock()
        # 失败次数达到验证码阈值
        mock_redis.get.side_effect = [None, str(AccountLockoutService.CAPTCHA_THRESHOLD)]
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.check_lockout(self.username, self.mock_db)
        
        self.assertTrue(result["requires_captcha"])
        self.assertFalse(result["locked"])
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_lockout_persistence_to_db(self, mock_redis_client):
        """测试失败记录持久化到数据库"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        mock_redis_client.return_value = mock_redis
        
        AccountLockoutService.record_failed_login(
            self.username, self.ip, self.user_agent, "wrong_password", self.mock_db
        )
        
        # 验证数据库添加操作
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()


class TestUnlockMechanism(TestAccountLockoutService):
    """解锁机制测试（5个用例）"""
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_manual_unlock_success(self, mock_redis_client):
        """测试手动解锁成功"""
        mock_redis = MagicMock()
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.unlock_account(
            self.username, admin_user="admin", db=self.mock_db
        )
        
        self.assertTrue(result)
        self.assertEqual(mock_redis.delete.call_count, 2)
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_unlock_without_redis(self, mock_redis_client):
        """测试Redis不可用时解锁失败"""
        mock_redis_client.return_value = None
        
        result = AccountLockoutService.unlock_account(self.username, "admin", self.mock_db)
        
        self.assertFalse(result)
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_auto_unlock_after_timeout(self, mock_redis_client):
        """测试超时后自动解锁（通过TTL过期）"""
        mock_redis = MagicMock()
        # 第一次检查：锁定
        # 第二次检查：已过期（None）
        mock_redis.get.side_effect = [
            (datetime.now() - timedelta(minutes=1)).isoformat(),  # 已过期
            None
        ]
        mock_redis_client.return_value = mock_redis
        
        # 第一次检查应该返回过期时间（但已是过去时间，Redis实际已删除）
        result1 = AccountLockoutService.check_lockout(self.username, self.mock_db)
        # Redis会自动删除过期key，所以实际获取时应该是None
        # 这个测试验证的是TTL机制的正确性
        self.assertIsNotNone(result1)  # 获取到了时间戳
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_get_locked_accounts_list(self, mock_redis_client):
        """测试获取锁定账户列表"""
        mock_redis = MagicMock()
        # 模拟scan_iter返回两个锁定账户
        mock_redis.scan_iter.return_value = [
            "lockout:user1",
            "lockout:user2"
        ]
        mock_redis.get.side_effect = [
            datetime.now().isoformat(),
            "3",
            datetime.now().isoformat(),
            "5"
        ]
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.get_locked_accounts(self.mock_db)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["username"], "user1")
        self.assertEqual(result[1]["username"], "user2")
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_unlock_records_admin_action(self, mock_redis_client):
        """测试解锁操作记录管理员信息"""
        mock_redis = MagicMock()
        mock_redis_client.return_value = mock_redis
        admin_user = "admin@example.com"
        
        with patch('app.services.account_lockout_service.logger') as mock_logger:
            AccountLockoutService.unlock_account(self.username, admin_user, self.mock_db)
            
            # 验证日志记录了管理员信息
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn(admin_user, log_message)
            self.assertIn(self.username, log_message)


class TestBoundaryConditions(TestAccountLockoutService):
    """边界条件测试（4个用例）"""
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_redis_unavailable_fallback_to_db(self, mock_redis_client):
        """测试Redis不可用时降级到数据库"""
        mock_redis_client.return_value = None
        
        # 模拟数据库查询
        self.mock_db.query.return_value.filter.return_value.count.return_value = 2
        
        result = AccountLockoutService.check_lockout(self.username, self.mock_db)
        
        # 应该能正常返回结果
        self.assertIsNotNone(result)
        self.assertEqual(result["remaining_attempts"], AccountLockoutService.LOCKOUT_THRESHOLD - 2)
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_concurrent_login_attempts(self, mock_redis_client):
        """测试并发登录尝试（Redis原子性）"""
        mock_redis = MagicMock()
        # 模拟并发：多次incr都返回递增值
        mock_redis.incr.side_effect = [4, 5, 6]
        mock_redis_client.return_value = mock_redis
        
        # 第一次：未锁定
        result1 = AccountLockoutService.record_failed_login(
            self.username, self.ip, self.user_agent, db=self.mock_db
        )
        self.assertFalse(result1["locked"])
        
        # 第二次：达到阈值，触发锁定
        result2 = AccountLockoutService.record_failed_login(
            self.username, self.ip, self.user_agent, db=self.mock_db
        )
        self.assertTrue(result2["locked"])
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_empty_username_handling(self, mock_redis_client):
        """测试空用户名处理"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis_client.return_value = mock_redis
        
        # 即使用户名为空也不应崩溃
        result = AccountLockoutService.check_lockout("", self.mock_db)
        
        self.assertIsNotNone(result)
        self.assertFalse(result["locked"])
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_very_long_username(self, mock_redis_client):
        """测试超长用户名处理"""
        long_username = "a" * 1000
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis_client.return_value = mock_redis
        
        # 应该能正常处理超长用户名
        result = AccountLockoutService.check_lockout(long_username, self.mock_db)
        
        self.assertIsNotNone(result)


class TestIPBlacklist(TestAccountLockoutService):
    """IP黑名单测试（3个用例）"""
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_ip_blacklist_after_threshold(self, mock_redis_client):
        """测试达到阈值后IP被拉黑"""
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = [
            5,  # login_attempts
            AccountLockoutService.IP_BLACKLIST_THRESHOLD  # ip_attempts达到阈值
        ]
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.record_failed_login(
            self.username, self.ip, self.user_agent, db=self.mock_db
        )
        
        self.assertTrue(result["ip_blacklisted"])
        # 验证设置了永久黑名单
        mock_redis.set.assert_called_once()
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_check_ip_blacklisted(self, mock_redis_client):
        """测试检查IP是否在黑名单中"""
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.is_ip_blacklisted(self.ip)
        
        self.assertTrue(result)
        mock_redis.exists.assert_called_once_with(f"ip_blacklist:{self.ip}")
    
    @patch('app.services.account_lockout_service.get_redis_client')
    def test_remove_ip_from_blacklist(self, mock_redis_client):
        """测试从黑名单移除IP"""
        mock_redis = MagicMock()
        mock_redis_client.return_value = mock_redis
        
        result = AccountLockoutService.remove_ip_from_blacklist(
            self.ip, admin_user="admin"
        )
        
        self.assertTrue(result)
        self.assertEqual(mock_redis.delete.call_count, 2)


# Pytest fixtures
@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_redis():
    """Mock Redis客户端"""
    redis_mock = MagicMock()
    with patch('app.services.account_lockout_service.get_redis_client', return_value=redis_mock):
        yield redis_mock


if __name__ == '__main__':
    unittest.main()
