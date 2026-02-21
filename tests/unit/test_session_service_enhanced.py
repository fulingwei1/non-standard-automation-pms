# -*- coding: utf-8 -*-
"""
会话管理服务增强测试套件
覆盖所有核心方法和边界条件
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock, call
from typing import Dict, List

from app.services.session_service import SessionService
from app.models.session import UserSession
from app.models.user import User


class TestSessionServiceCreateSession(unittest.TestCase):
    """测试 create_session 方法"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.mock_db = MagicMock()
        self.user_id = 1
        self.access_jti = "access_123"
        self.refresh_jti = "refresh_123"
        self.ip = "192.168.1.1"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_parse_user_agent')
    @patch.object(SessionService, '_get_location')
    @patch.object(SessionService, '_assess_risk')
    @patch.object(SessionService, '_cleanup_old_sessions')
    @patch.object(SessionService, '_cache_session')
    def test_create_session_success(
        self, mock_cache, mock_cleanup, mock_assess, 
        mock_location, mock_parse_ua, mock_datetime
    ):
        """测试成功创建会话"""
        # 设置mock
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_parse_ua.return_value = {"browser": "Chrome", "os": "Windows"}
        mock_location.return_value = "北京"
        mock_assess.return_value = (False, 10)
        
        # 执行
        session = SessionService.create_session(
            self.mock_db,
            self.user_id,
            self.access_jti,
            self.refresh_jti,
            self.ip,
            self.user_agent,
            {"device_id": "dev123", "device_name": "My PC"}
        )
        
        # 验证
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        mock_cleanup.assert_called_once_with(self.mock_db, self.user_id)
        mock_cache.assert_called_once()
        
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_parse_user_agent')
    @patch.object(SessionService, '_get_location')
    @patch.object(SessionService, '_assess_risk')
    @patch.object(SessionService, '_cleanup_old_sessions')
    @patch.object(SessionService, '_cache_session')
    def test_create_session_without_optional_params(
        self, mock_cache, mock_cleanup, mock_assess,
        mock_location, mock_parse_ua, mock_datetime
    ):
        """测试不带可选参数创建会话"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_assess.return_value = (False, 0)
        
        session = SessionService.create_session(
            self.mock_db,
            self.user_id,
            self.access_jti,
            self.refresh_jti
        )
        
        self.mock_db.add.assert_called_once()
        mock_parse_ua.assert_not_called()
        mock_location.assert_not_called()
        
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_parse_user_agent')
    @patch.object(SessionService, '_get_location')
    @patch.object(SessionService, '_assess_risk')
    @patch.object(SessionService, '_cleanup_old_sessions')
    @patch.object(SessionService, '_cache_session')
    def test_create_session_suspicious_login(
        self, mock_cache, mock_cleanup, mock_assess,
        mock_location, mock_parse_ua, mock_datetime
    ):
        """测试可疑登录创建会话"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_parse_ua.return_value = {}
        mock_location.return_value = "未知"
        mock_assess.return_value = (True, 75)  # 高风险
        
        session = SessionService.create_session(
            self.mock_db,
            self.user_id,
            self.access_jti,
            self.refresh_jti,
            self.ip,
            self.user_agent
        )
        
        self.mock_db.add.assert_called_once()
        mock_assess.assert_called_once()


class TestSessionServiceGetSessions(unittest.TestCase):
    """测试获取会话相关方法"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.user_id = 1
        
    def test_get_user_sessions_active_only(self):
        """测试只获取活跃会话"""
        mock_query = self.mock_db.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value  # active_only会添加第二个filter
        mock_order = mock_filter2.order_by.return_value
        mock_sessions = [MagicMock(access_token_jti="jti1")]
        mock_order.all.return_value = mock_sessions
        
        sessions = SessionService.get_user_sessions(
            self.mock_db, self.user_id, active_only=True
        )
        
        self.assertEqual(sessions, mock_sessions)
        self.mock_db.query.assert_called_once()
        
    def test_get_user_sessions_all(self):
        """测试获取所有会话（包括非活跃）"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_sessions = [MagicMock(), MagicMock()]
        mock_order.all.return_value = mock_sessions
        
        sessions = SessionService.get_user_sessions(
            self.mock_db, self.user_id, active_only=False
        )
        
        self.assertEqual(len(sessions), 2)
        
    def test_get_user_sessions_mark_current(self):
        """测试标记当前会话"""
        session1 = MagicMock(access_token_jti="current_jti")
        session2 = MagicMock(access_token_jti="other_jti")
        
        mock_query = self.mock_db.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value  # active_only默认True
        mock_order = mock_filter2.order_by.return_value
        mock_order.all.return_value = [session1, session2]
        
        sessions = SessionService.get_user_sessions(
            self.mock_db, self.user_id, current_jti="current_jti"
        )
        
        # 验证是_current属性被正确设置
        self.assertEqual(session1.is_current, True)
        self.assertEqual(session2.is_current, False)
        
    def test_get_session_by_jti_access(self):
        """测试通过access JTI获取会话"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_session = MagicMock()
        mock_filter.first.return_value = mock_session
        
        session = SessionService.get_session_by_jti(
            self.mock_db, "jti123", token_type="access"
        )
        
        self.assertIsNotNone(session)
        self.mock_db.query.assert_called_once()
        
    def test_get_session_by_jti_refresh(self):
        """测试通过refresh JTI获取会话"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_session = MagicMock()
        mock_filter.first.return_value = mock_session
        
        session = SessionService.get_session_by_jti(
            self.mock_db, "refresh_jti", token_type="refresh"
        )
        
        self.assertIsNotNone(session)
        
    def test_get_session_by_jti_not_found(self):
        """测试JTI不存在返回None"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        session = SessionService.get_session_by_jti(
            self.mock_db, "nonexistent", token_type="access"
        )
        
        self.assertIsNone(session)


class TestSessionServiceUpdateActivity(unittest.TestCase):
    """测试更新会话活动"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, 'get_session_by_jti')
    @patch.object(SessionService, '_cache_session')
    def test_update_activity_with_refresh_jti(
        self, mock_cache, mock_get_session, mock_datetime
    ):
        """测试使用refresh JTI更新活动"""
        now = datetime(2024, 1, 1, 13, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        result = SessionService.update_session_activity(
            self.mock_db, "refresh_jti"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(mock_session.last_activity_at, now)
        self.mock_db.commit.assert_called_once()
        mock_cache.assert_called_once()
        
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, 'get_session_by_jti')
    @patch.object(SessionService, '_cache_session')
    def test_update_activity_with_new_access_jti(
        self, mock_cache, mock_get_session, mock_datetime
    ):
        """测试刷新token时更新access JTI"""
        now = datetime(2024, 1, 1, 13, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        result = SessionService.update_session_activity(
            self.mock_db, "refresh_jti", new_access_jti="new_access_123"
        )
        
        self.assertEqual(mock_session.access_token_jti, "new_access_123")
        
    @patch.object(SessionService, 'get_session_by_jti')
    def test_update_activity_fallback_to_access(self, mock_get_session):
        """测试当refresh JTI找不到时回退到access JTI"""
        mock_get_session.side_effect = [None, MagicMock()]
        
        result = SessionService.update_session_activity(
            self.mock_db, "jti"
        )
        
        self.assertEqual(mock_get_session.call_count, 2)
        
    @patch.object(SessionService, 'get_session_by_jti')
    def test_update_activity_session_not_found(self, mock_get_session):
        """测试会话不存在时返回None"""
        mock_get_session.return_value = None
        
        result = SessionService.update_session_activity(
            self.mock_db, "nonexistent_jti"
        )
        
        self.assertIsNone(result)
        self.mock_db.commit.assert_not_called()


class TestSessionServiceRevokeSession(unittest.TestCase):
    """测试撤销会话"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_add_to_blacklist')
    @patch.object(SessionService, '_remove_session_cache')
    def test_revoke_session_success(
        self, mock_remove_cache, mock_blacklist, mock_datetime
    ):
        """测试成功撤销会话"""
        now = datetime(2024, 1, 1, 14, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        mock_session = MagicMock()
        mock_session.id = 123
        mock_session.access_token_jti = "access_jti"
        mock_session.refresh_token_jti = "refresh_jti"
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_session
        
        result = SessionService.revoke_session(self.mock_db, 123, 1)
        
        self.assertTrue(result)
        self.assertFalse(mock_session.is_active)
        self.assertEqual(mock_session.logout_at, now)
        self.assertEqual(mock_blacklist.call_count, 2)
        mock_remove_cache.assert_called_once_with(123)
        
    def test_revoke_session_not_found(self):
        """测试撤销不存在的会话"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        result = SessionService.revoke_session(self.mock_db, 999, 1)
        
        self.assertFalse(result)
        self.mock_db.commit.assert_not_called()
        
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_add_to_blacklist')
    @patch.object(SessionService, '_remove_session_cache')
    def test_revoke_all_sessions_except_current(
        self, mock_remove_cache, mock_blacklist, mock_datetime
    ):
        """测试撤销所有会话但保留当前会话"""
        now = datetime(2024, 1, 1, 14, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        session1 = MagicMock(
            id=1, 
            access_token_jti="current_jti",
            refresh_token_jti="current_refresh"
        )
        session2 = MagicMock(
            id=2,
            access_token_jti="other_jti",
            refresh_token_jti="other_refresh"
        )
        
        mock_query = self.mock_db.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_filter2.all.return_value = [session2]
        
        count = SessionService.revoke_all_sessions(
            self.mock_db, 1, except_jti="current_jti"
        )
        
        self.assertEqual(count, 1)
        self.assertFalse(session2.is_active)
        
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_add_to_blacklist')
    @patch.object(SessionService, '_remove_session_cache')
    def test_revoke_all_sessions_no_exception(
        self, mock_remove_cache, mock_blacklist, mock_datetime
    ):
        """测试撤销所有会话不保留任何会话"""
        now = datetime(2024, 1, 1, 14, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        sessions = [MagicMock(id=i, access_token_jti=f"jti{i}", 
                              refresh_token_jti=f"refresh{i}") 
                   for i in range(3)]
        
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = sessions
        
        count = SessionService.revoke_all_sessions(self.mock_db, 1)
        
        self.assertEqual(count, 3)
        for session in sessions:
            self.assertFalse(session.is_active)


class TestSessionServiceCleanup(unittest.TestCase):
    """测试清理功能"""
    
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_remove_session_cache')
    def test_cleanup_expired_sessions(self, mock_remove_cache, mock_datetime):
        """测试清理过期会话"""
        now = datetime(2024, 1, 10, 0, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        expired_session1 = MagicMock(id=1, expires_at=datetime(2024, 1, 1))
        expired_session2 = MagicMock(id=2, expires_at=datetime(2024, 1, 5))
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [expired_session1, expired_session2]
        
        count = SessionService.cleanup_expired_sessions(mock_db)
        
        self.assertEqual(count, 2)
        self.assertFalse(expired_session1.is_active)
        self.assertFalse(expired_session2.is_active)
        self.assertEqual(mock_remove_cache.call_count, 2)
        
    @patch('app.services.session_service.datetime')
    def test_cleanup_no_expired_sessions(self, mock_datetime):
        """测试没有过期会话时的清理"""
        now = datetime(2024, 1, 10, 0, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = []
        
        count = SessionService.cleanup_expired_sessions(mock_db)
        
        self.assertEqual(count, 0)


class TestSessionServicePrivateMethods(unittest.TestCase):
    """测试私有辅助方法"""
    
    def test_parse_user_agent_success(self):
        """测试成功解析User-Agent"""
        ua_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        result = SessionService._parse_user_agent(ua_string)
        
        self.assertIn("browser", result)
        self.assertIn("os", result)
        
    @patch('app.services.session_service.parse_user_agent')
    def test_parse_user_agent_exception(self, mock_parse):
        """测试解析User-Agent异常时返回空字典"""
        mock_parse.side_effect = Exception("Parse error")
        
        result = SessionService._parse_user_agent("invalid ua")
        
        self.assertEqual(result, {})
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_get_location_from_cache(self, mock_redis_client):
        """测试从Redis缓存获取位置"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "上海"
        mock_redis_client.return_value = mock_redis
        
        location = SessionService._get_location("1.2.3.4")
        
        self.assertEqual(location, "上海")
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_get_location_cache_miss(self, mock_redis_client):
        """测试缓存未命中时返回默认位置"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis_client.return_value = mock_redis
        
        location = SessionService._get_location("1.2.3.4")
        
        self.assertEqual(location, "未知位置")
        
    def test_get_location_no_ip(self):
        """测试无IP时返回None"""
        location = SessionService._get_location(None)
        self.assertIsNone(location)
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_get_location_redis_exception(self, mock_redis_client):
        """测试Redis异常时返回默认位置"""
        mock_redis_client.side_effect = Exception("Redis error")
        
        location = SessionService._get_location("1.2.3.4")
        
        self.assertEqual(location, "未知位置")


class TestSessionServiceRiskAssessment(unittest.TestCase):
    """测试风险评估功能"""
    
    @patch('app.services.session_service.datetime')
    def test_assess_risk_new_user(self, mock_datetime):
        """测试新用户无历史记录时的风险评估"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_limit = mock_order.limit.return_value
        mock_limit.all.return_value = []
        
        is_suspicious, risk_score = SessionService._assess_risk(
            mock_db, 1, "1.2.3.4", {"device_id": "dev1"}, "北京"
        )
        
        self.assertFalse(is_suspicious)
        self.assertEqual(risk_score, 0)
        
    @patch('app.services.session_service.datetime')
    def test_assess_risk_new_ip(self, mock_datetime):
        """测试新IP地址登录的风险评估"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        old_session = MagicMock(
            ip_address="192.168.1.1",
            device_id="dev1",
            location="北京",
            login_at=now - timedelta(days=5)
        )
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_limit = mock_order.limit.return_value
        mock_limit.all.return_value = [old_session]
        
        is_suspicious, risk_score = SessionService._assess_risk(
            mock_db, 1, "10.0.0.1", {"device_id": "dev1"}, "北京"
        )
        
        self.assertGreaterEqual(risk_score, 30)  # 新IP +30
        
    @patch('app.services.session_service.datetime')
    def test_assess_risk_new_device(self, mock_datetime):
        """测试新设备登录的风险评估"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        old_session = MagicMock(
            ip_address="192.168.1.1",
            device_id="old_device",
            location="北京",
            login_at=now - timedelta(days=5)
        )
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_limit = mock_order.limit.return_value
        mock_limit.all.return_value = [old_session]
        
        is_suspicious, risk_score = SessionService._assess_risk(
            mock_db, 1, "192.168.1.1", {"device_id": "new_device"}, "北京"
        )
        
        self.assertGreaterEqual(risk_score, 20)  # 新设备 +20
        
    @patch('app.services.session_service.datetime')
    def test_assess_risk_new_location(self, mock_datetime):
        """测试异地登录的风险评估"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        old_session = MagicMock(
            ip_address="192.168.1.1",
            device_id="dev1",
            location="北京",
            login_at=now - timedelta(days=5)
        )
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_limit = mock_order.limit.return_value
        mock_limit.all.return_value = [old_session]
        
        is_suspicious, risk_score = SessionService._assess_risk(
            mock_db, 1, "192.168.1.1", {"device_id": "dev1"}, "上海"
        )
        
        self.assertGreaterEqual(risk_score, 25)  # 异地 +25
        
    @patch('app.services.session_service.datetime')
    def test_assess_risk_frequent_login(self, mock_datetime):
        """测试频繁登录的风险评估"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        # 创建6个最近1小时内的登录
        recent_sessions = [
            MagicMock(
                ip_address="192.168.1.1",
                device_id="dev1",
                location="北京",
                login_at=now - timedelta(minutes=i*10)
            )
            for i in range(6)
        ]
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_limit = mock_order.limit.return_value
        mock_limit.all.return_value = recent_sessions
        
        is_suspicious, risk_score = SessionService._assess_risk(
            mock_db, 1, "192.168.1.1", {"device_id": "dev1"}, "北京"
        )
        
        self.assertGreaterEqual(risk_score, 25)  # 频繁登录 +25
        
    @patch('app.services.session_service.datetime')
    def test_assess_risk_high_score_marks_suspicious(self, mock_datetime):
        """测试高风险分数标记为可疑"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        old_session = MagicMock(
            ip_address="192.168.1.1",
            device_id="dev1",
            location="北京",
            login_at=now - timedelta(days=5)
        )
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_limit = mock_order.limit.return_value
        mock_limit.all.return_value = [old_session]
        
        # 新IP + 新设备 + 新位置 = 30 + 20 + 25 = 75 > 50
        is_suspicious, risk_score = SessionService._assess_risk(
            mock_db, 1, "10.0.0.1", {"device_id": "new_dev"}, "上海"
        )
        
        self.assertTrue(is_suspicious)
        self.assertGreaterEqual(risk_score, 50)
        self.assertLessEqual(risk_score, 100)  # 最大值限制


class TestSessionServiceCleanupOldSessions(unittest.TestCase):
    """测试清理旧会话功能"""
    
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_add_to_blacklist')
    def test_cleanup_old_sessions_under_limit(
        self, mock_blacklist, mock_datetime
    ):
        """测试会话数未超限时不清理"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        sessions = [MagicMock(id=i) for i in range(3)]
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = sessions
        
        SessionService._cleanup_old_sessions(mock_db, 1)
        
        # 会话数未超限，不应调用blacklist
        mock_blacklist.assert_not_called()
            
    @patch('app.services.session_service.datetime')
    @patch.object(SessionService, '_add_to_blacklist')
    def test_cleanup_old_sessions_over_limit(
        self, mock_blacklist, mock_datetime
    ):
        """测试会话数超限时清理最旧的会话"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        # 创建6个会话（超过限制5个）
        sessions = [
            MagicMock(
                id=i,
                access_token_jti=f"access_{i}",
                refresh_token_jti=f"refresh_{i}"
            )
            for i in range(6)
        ]
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = sessions
        
        SessionService._cleanup_old_sessions(mock_db, 1)
        
        # 最后2个会话应被清理（从第5个开始，索引4和5）
        self.assertFalse(sessions[4].is_active)
        self.assertFalse(sessions[5].is_active)


class TestSessionServiceCacheMethods(unittest.TestCase):
    """测试Redis缓存相关方法"""
    
    @patch('app.utils.redis_client.get_redis_client')
    def test_cache_session_success(self, mock_redis_client):
        """测试成功缓存会话"""
        mock_redis = MagicMock()
        mock_redis_client.return_value = mock_redis
        
        session = MagicMock(
            id=123,
            user_id=1,
            is_active=True,
            access_token_jti="access_jti",
            refresh_token_jti="refresh_jti"
        )
        
        SessionService._cache_session(session)
        
        mock_redis.hmset.assert_called_once()
        mock_redis.expire.assert_called_once()
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_cache_session_redis_unavailable(self, mock_redis_client):
        """测试Redis不可用时不抛异常"""
        mock_redis_client.return_value = None
        
        session = MagicMock(id=123)
        
        # 不应抛异常
        SessionService._cache_session(session)
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_cache_session_redis_exception(self, mock_redis_client):
        """测试Redis异常时不影响主流程"""
        mock_redis = MagicMock()
        mock_redis.hmset.side_effect = Exception("Redis error")
        mock_redis_client.return_value = mock_redis
        
        session = MagicMock(
            id=123,
            user_id=1,
            is_active=True,
            access_token_jti="jti",
            refresh_token_jti="refresh"
        )
        
        # 不应抛异常
        SessionService._cache_session(session)
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_remove_session_cache_success(self, mock_redis_client):
        """测试成功删除会话缓存"""
        mock_redis = MagicMock()
        mock_redis_client.return_value = mock_redis
        
        SessionService._remove_session_cache(123)
        
        mock_redis.delete.assert_called_once_with("session:123")
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_remove_session_cache_redis_unavailable(self, mock_redis_client):
        """测试Redis不可用时不抛异常"""
        mock_redis_client.return_value = None
        
        # 不应抛异常
        SessionService._remove_session_cache(123)
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_add_to_blacklist_success(self, mock_redis_client):
        """测试成功添加到黑名单"""
        mock_redis = MagicMock()
        mock_redis_client.return_value = mock_redis
        
        SessionService._add_to_blacklist("jti123", 3600)
        
        mock_redis.setex.assert_called_once_with(
            "jwt:blacklist:jti123", 3600, "1"
        )
        
    @patch('app.utils.redis_client.get_redis_client')
    def test_add_to_blacklist_redis_unavailable(self, mock_redis_client):
        """测试Redis不可用时记录警告"""
        mock_redis_client.return_value = None
        
        # 不应抛异常
        SessionService._add_to_blacklist("jti123", 3600)


class TestSessionServiceEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_constants_values(self):
        """测试常量配置值"""
        self.assertEqual(SessionService.ACCESS_TOKEN_EXPIRE_MINUTES, 60 * 24)
        self.assertEqual(SessionService.REFRESH_TOKEN_EXPIRE_DAYS, 7)
        self.assertEqual(SessionService.SESSION_EXPIRE_DAYS, 7)
        self.assertEqual(SessionService.MAX_SESSIONS_PER_USER, 5)
        self.assertEqual(SessionService.RISK_SCORE_THRESHOLD, 50)
        
    def test_redis_key_prefixes(self):
        """测试Redis键前缀"""
        self.assertEqual(SessionService.SESSION_KEY_PREFIX, "session:")
        self.assertEqual(SessionService.BLACKLIST_KEY_PREFIX, "jwt:blacklist:")
        self.assertEqual(SessionService.LOCATION_CACHE_PREFIX, "ip:location:")
        
    @patch('app.services.session_service.datetime')
    def test_assess_risk_max_score_limit(self, mock_datetime):
        """测试风险分数最大值限制为100"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        # 创建一个老会话
        old_session = MagicMock(
            ip_address="192.168.1.1",
            device_id="dev1",
            location="北京",
            login_at=now - timedelta(days=5)
        )
        
        # 创建6个频繁登录会话
        recent_sessions = [old_session] + [
            MagicMock(
                ip_address="192.168.1.1",
                device_id="dev1",
                location="北京",
                login_at=now - timedelta(minutes=i*10)
            )
            for i in range(6)
        ]
        
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_limit = mock_order.limit.return_value
        mock_limit.all.return_value = recent_sessions
        
        # 新IP(30) + 新设备(20) + 新位置(25) + 频繁登录(25) = 100
        is_suspicious, risk_score = SessionService._assess_risk(
            mock_db, 1, "10.0.0.1", {"device_id": "new_dev"}, "上海"
        )
        
        self.assertEqual(risk_score, 100)  # 应被限制在100


if __name__ == '__main__':
    unittest.main()
