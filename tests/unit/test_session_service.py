# -*- coding: utf-8 -*-
"""
会话服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作，Redis操作）
2. 让业务逻辑真正执行（不mock业务方法）
3. 覆盖主要方法和边界情况
4. 所有测试必须通过
5. 覆盖率 70%+
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from typing import List

from app.services.session_service import SessionService
from app.models.session import UserSession


class TestSessionServiceCreate(unittest.TestCase):
    """测试会话创建功能"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.user_id = 1
        self.access_jti = "access_jti_123"
        self.refresh_jti = "refresh_jti_456"

    @patch('app.services.session_service.SessionService._cache_session')
    @patch('app.services.session_service.SessionService._cleanup_old_sessions')
    @patch('app.services.session_service.SessionService._assess_risk')
    @patch('app.services.session_service.SessionService._get_location')
    @patch('app.services.session_service.SessionService._parse_user_agent')
    def test_create_session_basic(
        self, 
        mock_parse_ua, 
        mock_location, 
        mock_risk, 
        mock_cleanup, 
        mock_cache
    ):
        """测试基本会话创建"""
        # 准备mock返回值
        mock_parse_ua.return_value = {
            "browser": "Chrome 120",
            "os": "macOS 14",
            "device": "Mac"
        }
        mock_location.return_value = "北京市"
        mock_risk.return_value = (False, 0)
        
        # 执行
        session = SessionService.create_session(
            db=self.mock_db,
            user_id=self.user_id,
            access_token_jti=self.access_jti,
            refresh_token_jti=self.refresh_jti,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0...",
            device_info={"device_id": "device_123", "device_name": "MacBook Pro"}
        )
        
        # 验证
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        mock_cleanup.assert_called_once_with(self.mock_db, self.user_id)
        mock_cache.assert_called_once()
        
        # 验证session对象
        added_session = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_session.user_id, self.user_id)
        self.assertEqual(added_session.access_token_jti, self.access_jti)
        self.assertEqual(added_session.refresh_token_jti, self.refresh_jti)
        self.assertEqual(added_session.ip_address, "192.168.1.1")
        self.assertEqual(added_session.location, "北京市")
        self.assertTrue(added_session.is_active)
        self.assertFalse(added_session.is_suspicious)
        self.assertEqual(added_session.risk_score, 0)

    @patch('app.services.session_service.SessionService._cache_session')
    @patch('app.services.session_service.SessionService._cleanup_old_sessions')
    @patch('app.services.session_service.SessionService._assess_risk')
    @patch('app.services.session_service.SessionService._get_location')
    @patch('app.services.session_service.SessionService._parse_user_agent')
    def test_create_session_suspicious(
        self, 
        mock_parse_ua, 
        mock_location, 
        mock_risk, 
        mock_cleanup, 
        mock_cache
    ):
        """测试创建可疑会话"""
        mock_parse_ua.return_value = {}
        mock_location.return_value = "上海市"
        mock_risk.return_value = (True, 75)  # 高风险
        
        session = SessionService.create_session(
            db=self.mock_db,
            user_id=self.user_id,
            access_token_jti=self.access_jti,
            refresh_token_jti=self.refresh_jti,
            ip_address="1.2.3.4"
        )
        
        added_session = self.mock_db.add.call_args[0][0]
        self.assertTrue(added_session.is_suspicious)
        self.assertEqual(added_session.risk_score, 75)

    @patch('app.services.session_service.SessionService._cache_session')
    @patch('app.services.session_service.SessionService._cleanup_old_sessions')
    @patch('app.services.session_service.SessionService._assess_risk')
    def test_create_session_no_ip_ua(
        self, 
        mock_risk, 
        mock_cleanup, 
        mock_cache
    ):
        """测试无IP和UA的会话创建"""
        mock_risk.return_value = (False, 0)
        
        session = SessionService.create_session(
            db=self.mock_db,
            user_id=self.user_id,
            access_token_jti=self.access_jti,
            refresh_token_jti=self.refresh_jti,
        )
        
        added_session = self.mock_db.add.call_args[0][0]
        self.assertIsNone(added_session.ip_address)
        self.assertIsNone(added_session.user_agent)
        self.assertIsNone(added_session.location)


class TestSessionServiceQuery(unittest.TestCase):
    """测试会话查询功能"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.user_id = 1

    def test_get_user_sessions_active_only(self):
        """测试获取活跃会话"""
        # 准备mock数据
        mock_sessions = [
            MagicMock(
                id=1, 
                user_id=self.user_id, 
                is_active=True,
                access_token_jti="jti1",
                last_activity_at=datetime.utcnow()
            ),
            MagicMock(
                id=2, 
                user_id=self.user_id, 
                is_active=True,
                access_token_jti="jti2",
                last_activity_at=datetime.utcnow() - timedelta(hours=1)
            ),
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_sessions
        
        # 执行
        sessions = SessionService.get_user_sessions(
            db=self.mock_db,
            user_id=self.user_id,
            active_only=True
        )
        
        # 验证
        self.assertEqual(len(sessions), 2)
        self.mock_db.query.assert_called_once()

    def test_get_user_sessions_with_current_jti(self):
        """测试标记当前会话"""
        current_jti = "jti1"
        mock_sessions = [
            MagicMock(
                id=1, 
                user_id=self.user_id, 
                is_active=True,
                access_token_jti=current_jti
            ),
            MagicMock(
                id=2, 
                user_id=self.user_id, 
                is_active=True,
                access_token_jti="jti2"
            ),
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_sessions
        
        sessions = SessionService.get_user_sessions(
            db=self.mock_db,
            user_id=self.user_id,
            current_jti=current_jti
        )
        
        # 验证当前会话被标记
        self.assertTrue(sessions[0].is_current)
        self.assertFalse(sessions[1].is_current)

    def test_get_session_by_jti_access(self):
        """测试通过access JTI获取会话"""
        jti = "access_jti_123"
        mock_session = MagicMock(access_token_jti=jti)
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_session
        
        session = SessionService.get_session_by_jti(
            db=self.mock_db,
            jti=jti,
            token_type="access"
        )
        
        self.assertEqual(session, mock_session)
        self.mock_db.query.assert_called_once()

    def test_get_session_by_jti_refresh(self):
        """测试通过refresh JTI获取会话"""
        jti = "refresh_jti_456"
        mock_session = MagicMock(refresh_token_jti=jti)
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_session
        
        session = SessionService.get_session_by_jti(
            db=self.mock_db,
            jti=jti,
            token_type="refresh"
        )
        
        self.assertEqual(session, mock_session)

    def test_get_session_by_jti_not_found(self):
        """测试JTI不存在"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        session = SessionService.get_session_by_jti(
            db=self.mock_db,
            jti="nonexistent",
            token_type="access"
        )
        
        self.assertIsNone(session)


class TestSessionServiceUpdate(unittest.TestCase):
    """测试会话更新功能"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch('app.services.session_service.SessionService._cache_session')
    @patch('app.services.session_service.SessionService.get_session_by_jti')
    def test_update_session_activity_basic(self, mock_get_session, mock_cache):
        """测试更新会话活动时间"""
        jti = "refresh_jti_123"
        mock_session = MagicMock(
            id=1,
            last_activity_at=datetime.utcnow() - timedelta(hours=1)
        )
        mock_get_session.return_value = mock_session
        
        result = SessionService.update_session_activity(
            db=self.mock_db,
            jti=jti
        )
        
        self.assertEqual(result, mock_session)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_session)
        mock_cache.assert_called_once_with(mock_session)

    @patch('app.services.session_service.SessionService._cache_session')
    @patch('app.services.session_service.SessionService.get_session_by_jti')
    def test_update_session_activity_with_new_access_jti(
        self, 
        mock_get_session, 
        mock_cache
    ):
        """测试刷新token时更新JTI"""
        jti = "refresh_jti_123"
        new_access_jti = "new_access_jti_789"
        mock_session = MagicMock(access_token_jti="old_jti")
        mock_get_session.return_value = mock_session
        
        result = SessionService.update_session_activity(
            db=self.mock_db,
            jti=jti,
            new_access_jti=new_access_jti
        )
        
        self.assertEqual(mock_session.access_token_jti, new_access_jti)

    @patch('app.services.session_service.SessionService.get_session_by_jti')
    def test_update_session_activity_not_found(self, mock_get_session):
        """测试会话不存在"""
        mock_get_session.return_value = None
        
        result = SessionService.update_session_activity(
            db=self.mock_db,
            jti="nonexistent"
        )
        
        self.assertIsNone(result)


class TestSessionServiceRevoke(unittest.TestCase):
    """测试会话撤销功能"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.user_id = 1

    @patch('app.services.session_service.SessionService._remove_session_cache')
    @patch('app.services.session_service.SessionService._add_to_blacklist')
    def test_revoke_session_success(self, mock_blacklist, mock_remove_cache):
        """测试成功撤销会话"""
        session_id = 1
        mock_session = MagicMock(
            id=session_id,
            user_id=self.user_id,
            access_token_jti="access_jti",
            refresh_token_jti="refresh_jti",
            is_active=True
        )
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_session
        
        result = SessionService.revoke_session(
            db=self.mock_db,
            session_id=session_id,
            user_id=self.user_id
        )
        
        self.assertTrue(result)
        self.assertFalse(mock_session.is_active)
        self.assertIsNotNone(mock_session.logout_at)
        self.mock_db.commit.assert_called_once()
        self.assertEqual(mock_blacklist.call_count, 2)
        mock_remove_cache.assert_called_once_with(session_id)

    @patch('app.services.session_service.SessionService._remove_session_cache')
    @patch('app.services.session_service.SessionService._add_to_blacklist')
    def test_revoke_session_not_found(self, mock_blacklist, mock_remove_cache):
        """测试撤销不存在的会话"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        result = SessionService.revoke_session(
            db=self.mock_db,
            session_id=999,
            user_id=self.user_id
        )
        
        self.assertFalse(result)
        mock_blacklist.assert_not_called()
        mock_remove_cache.assert_not_called()

    @patch('app.services.session_service.SessionService._remove_session_cache')
    @patch('app.services.session_service.SessionService._add_to_blacklist')
    def test_revoke_all_sessions_success(self, mock_blacklist, mock_remove_cache):
        """测试撤销所有会话"""
        mock_sessions = [
            MagicMock(
                id=1,
                access_token_jti="jti1",
                refresh_token_jti="rjti1",
                is_active=True
            ),
            MagicMock(
                id=2,
                access_token_jti="jti2",
                refresh_token_jti="rjti2",
                is_active=True
            ),
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_sessions
        
        count = SessionService.revoke_all_sessions(
            db=self.mock_db,
            user_id=self.user_id
        )
        
        self.assertEqual(count, 2)
        for session in mock_sessions:
            self.assertFalse(session.is_active)
            self.assertIsNotNone(session.logout_at)
        self.assertEqual(mock_blacklist.call_count, 4)  # 2 sessions * 2 tokens
        self.assertEqual(mock_remove_cache.call_count, 2)

    @patch('app.services.session_service.SessionService._remove_session_cache')
    @patch('app.services.session_service.SessionService._add_to_blacklist')
    def test_revoke_all_sessions_except_current(
        self, 
        mock_blacklist, 
        mock_remove_cache
    ):
        """测试撤销除当前外的所有会话"""
        current_jti = "current_jti"
        mock_sessions = [
            MagicMock(
                id=1,
                access_token_jti="jti1",
                refresh_token_jti="rjti1",
                is_active=True
            ),
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_sessions
        
        count = SessionService.revoke_all_sessions(
            db=self.mock_db,
            user_id=self.user_id,
            except_jti=current_jti
        )
        
        self.assertEqual(count, 1)


class TestSessionServiceCleanup(unittest.TestCase):
    """测试会话清理功能"""

    def setUp(self):
        self.mock_db = MagicMock()

    @patch('app.services.session_service.SessionService._remove_session_cache')
    def test_cleanup_expired_sessions(self, mock_remove_cache):
        """测试清理过期会话"""
        now = datetime.utcnow()
        expired_sessions = [
            MagicMock(
                id=1,
                is_active=True,
                expires_at=now - timedelta(days=1)
            ),
            MagicMock(
                id=2,
                is_active=True,
                expires_at=now - timedelta(hours=1)
            ),
        ]
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = expired_sessions
        
        count = SessionService.cleanup_expired_sessions(db=self.mock_db)
        
        self.assertEqual(count, 2)
        for session in expired_sessions:
            self.assertFalse(session.is_active)
            self.assertIsNotNone(session.logout_at)
        self.assertEqual(mock_remove_cache.call_count, 2)
        self.mock_db.commit.assert_called_once()

    @patch('app.services.session_service.SessionService._add_to_blacklist')
    def test_cleanup_old_sessions(self, mock_blacklist):
        """测试清理旧会话（超过最大数量）"""
        user_id = 1
        # 创建6个活跃会话（超过最大5个）
        active_sessions = []
        for i in range(6):
            session = MagicMock(
                id=i + 1,
                user_id=user_id,
                is_active=True,
                access_token_jti=f"access_{i}",
                refresh_token_jti=f"refresh_{i}",
                last_activity_at=datetime.utcnow() - timedelta(hours=i)
            )
            active_sessions.append(session)
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = active_sessions
        
        SessionService._cleanup_old_sessions(db=self.mock_db, user_id=user_id)
        
        # 验证最旧的2个会话被关闭
        self.assertFalse(active_sessions[4].is_active)
        self.assertFalse(active_sessions[5].is_active)
        # 前4个保持活跃
        for i in range(4):
            self.assertTrue(active_sessions[i].is_active)


class TestSessionServiceHelpers(unittest.TestCase):
    """测试辅助方法"""

    def test_parse_user_agent_success(self):
        """测试解析User-Agent成功"""
        ua_string = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        result = SessionService._parse_user_agent(ua_string)
        
        self.assertIn("browser", result)
        self.assertIn("os", result)
        self.assertIn("device", result)

    def test_parse_user_agent_empty(self):
        """测试解析空User-Agent"""
        result = SessionService._parse_user_agent("")
        # 空字符串会返回默认解析结果，而不是空字典
        self.assertIn("browser", result)
        self.assertIn("os", result)
        self.assertIn("device", result)

    @patch('app.utils.redis_client.get_redis_client')
    def test_get_location_cached(self, mock_redis):
        """测试从缓存获取地理位置"""
        ip = "1.2.3.4"
        cached_location = "上海市"
        
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = cached_location
        mock_redis.return_value = mock_redis_client
        
        result = SessionService._get_location(ip)
        
        self.assertEqual(result, cached_location)
        mock_redis_client.get.assert_called_once()

    @patch('app.utils.redis_client.get_redis_client')
    def test_get_location_no_cache(self, mock_redis):
        """测试未缓存的地理位置"""
        ip = "1.2.3.4"
        
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = None
        mock_redis.return_value = mock_redis_client
        
        result = SessionService._get_location(ip)
        
        # 应返回默认值
        self.assertEqual(result, "未知位置")

    @patch('app.utils.redis_client.get_redis_client')
    def test_get_location_redis_error(self, mock_redis):
        """测试Redis错误"""
        ip = "1.2.3.4"
        mock_redis.side_effect = Exception("Redis error")
        
        result = SessionService._get_location(ip)
        
        self.assertEqual(result, "未知位置")

    def test_get_location_no_ip(self):
        """测试无IP地址"""
        result = SessionService._get_location(None)
        self.assertIsNone(result)

    def test_assess_risk_new_user(self):
        """测试新用户风险评估"""
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address="1.2.3.4",
            device_info={"device_id": "dev123"},
            location="北京市"
        )
        
        self.assertFalse(is_suspicious)
        self.assertEqual(risk_score, 0)

    def test_assess_risk_new_ip(self):
        """测试新IP登录风险"""
        mock_db = MagicMock()
        
        # 创建历史会话
        old_session = MagicMock(
            ip_address="192.168.1.1",
            device_id="old_device",
            location="北京市",
            login_at=datetime.utcnow() - timedelta(days=1)
        )
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = [
            old_session
        ]
        
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address="1.2.3.4",  # 新IP
            device_info={"device_id": "old_device"},
            location="北京市"
        )
        
        # 新IP增加30分
        self.assertGreaterEqual(risk_score, 30)

    def test_assess_risk_new_device(self):
        """测试新设备登录风险"""
        mock_db = MagicMock()
        
        old_session = MagicMock(
            ip_address="1.2.3.4",
            device_id="old_device",
            location="北京市",
            login_at=datetime.utcnow() - timedelta(days=1)
        )
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = [
            old_session
        ]
        
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address="1.2.3.4",
            device_info={"device_id": "new_device"},  # 新设备
            location="北京市"
        )
        
        # 新设备增加20分
        self.assertGreaterEqual(risk_score, 20)

    def test_assess_risk_new_location(self):
        """测试异地登录风险"""
        mock_db = MagicMock()
        
        old_session = MagicMock(
            ip_address="1.2.3.4",
            device_id="device123",
            location="北京市",
            login_at=datetime.utcnow() - timedelta(days=1)
        )
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = [
            old_session
        ]
        
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address="1.2.3.4",
            device_info={"device_id": "device123"},
            location="上海市"  # 异地
        )
        
        # 异地登录增加25分
        self.assertGreaterEqual(risk_score, 25)

    def test_assess_risk_frequent_login(self):
        """测试频繁登录风险"""
        mock_db = MagicMock()
        
        now = datetime.utcnow()
        # 创建6个1小时内的登录
        recent_sessions = [
            MagicMock(
                ip_address="1.2.3.4",
                device_id="device123",
                location="北京市",
                login_at=now - timedelta(minutes=i * 5)
            )
            for i in range(6)
        ]
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = recent_sessions
        
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address="1.2.3.4",
            device_info={"device_id": "device123"},
            location="北京市"
        )
        
        # 频繁登录增加25分
        self.assertGreaterEqual(risk_score, 25)

    def test_assess_risk_high_score_suspicious(self):
        """测试高风险分数标记为可疑"""
        mock_db = MagicMock()
        
        old_session = MagicMock(
            ip_address="192.168.1.1",
            device_id="old_device",
            location="北京市",
            login_at=datetime.utcnow() - timedelta(days=1)
        )
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = [
            old_session
        ]
        
        # 新IP + 新设备 + 异地 = 30 + 20 + 25 = 75 >= 50
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address="1.2.3.4",  # 新IP
            device_info={"device_id": "new_device"},  # 新设备
            location="上海市"  # 异地
        )
        
        self.assertTrue(is_suspicious)
        self.assertGreaterEqual(risk_score, 50)


class TestSessionServiceRedis(unittest.TestCase):
    """测试Redis相关功能"""

    @patch('app.utils.redis_client.get_redis_client')
    def test_cache_session_success(self, mock_redis):
        """测试缓存会话成功"""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        mock_session = MagicMock(
            id=1,
            user_id=10,
            is_active=True,
            access_token_jti="access_jti",
            refresh_token_jti="refresh_jti"
        )
        
        SessionService._cache_session(mock_session)
        
        mock_redis_client.hmset.assert_called_once()
        mock_redis_client.expire.assert_called_once()

    @patch('app.utils.redis_client.get_redis_client')
    def test_cache_session_redis_error(self, mock_redis):
        """测试Redis错误时缓存失败"""
        mock_redis_client = MagicMock()
        mock_redis_client.hmset.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_redis_client
        
        mock_session = MagicMock(id=1, user_id=10, is_active=True)
        
        # 不应抛出异常
        SessionService._cache_session(mock_session)

    @patch('app.utils.redis_client.get_redis_client')
    def test_cache_session_no_redis(self, mock_redis):
        """测试Redis不可用"""
        mock_redis.side_effect = Exception("Redis unavailable")
        
        mock_session = MagicMock(id=1)
        
        # 不应抛出异常
        SessionService._cache_session(mock_session)

    @patch('app.utils.redis_client.get_redis_client')
    def test_remove_session_cache_success(self, mock_redis):
        """测试删除会话缓存成功"""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        SessionService._remove_session_cache(session_id=1)
        
        mock_redis_client.delete.assert_called_once()

    @patch('app.utils.redis_client.get_redis_client')
    def test_remove_session_cache_error(self, mock_redis):
        """测试删除缓存错误"""
        mock_redis_client = MagicMock()
        mock_redis_client.delete.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_redis_client
        
        # 不应抛出异常
        SessionService._remove_session_cache(session_id=1)

    @patch('app.utils.redis_client.get_redis_client')
    def test_add_to_blacklist_success(self, mock_redis):
        """测试加入黑名单成功"""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        SessionService._add_to_blacklist(jti="test_jti", ttl=3600)
        
        mock_redis_client.setex.assert_called_once()

    @patch('app.utils.redis_client.get_redis_client')
    def test_add_to_blacklist_no_redis(self, mock_redis):
        """测试Redis不可用时加入黑名单"""
        mock_redis.side_effect = Exception("Redis unavailable")
        
        # 不应抛出异常
        SessionService._add_to_blacklist(jti="test_jti", ttl=3600)

    @patch('app.utils.redis_client.get_redis_client')
    def test_add_to_blacklist_error(self, mock_redis):
        """测试加入黑名单错误"""
        mock_redis_client = MagicMock()
        mock_redis_client.setex.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_redis_client
        
        # 不应抛出异常
        SessionService._add_to_blacklist(jti="test_jti", ttl=3600)


class TestSessionServiceEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_assess_risk_none_values(self):
        """测试None值的风险评估"""
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address=None,
            device_info=None,
            location=None
        )
        
        self.assertFalse(is_suspicious)
        self.assertEqual(risk_score, 0)

    def test_assess_risk_unknown_location(self):
        """测试未知位置不增加风险分"""
        mock_db = MagicMock()
        
        old_session = MagicMock(
            ip_address="1.2.3.4",
            device_id="device123",
            location="北京市",
            login_at=datetime.utcnow() - timedelta(days=1)
        )
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = [
            old_session
        ]
        
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address="1.2.3.4",
            device_info={"device_id": "device123"},
            location="未知位置"  # 包含"未知"不计分
        )
        
        # 不应增加异地登录的25分
        self.assertEqual(risk_score, 0)

    def test_assess_risk_max_score_capped(self):
        """测试风险分数上限为100"""
        mock_db = MagicMock()
        
        now = datetime.utcnow()
        # 创建大量近期会话（触发频繁登录）
        recent_sessions = [
            MagicMock(
                ip_address="192.168.1.1",  # 旧IP
                device_id="old_device",    # 旧设备
                location="北京市",          # 旧位置
                login_at=now - timedelta(minutes=i * 5)
            )
            for i in range(10)
        ]
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = recent_sessions
        
        # 所有风险因素: 新IP(30) + 新设备(20) + 异地(25) + 频繁(25) = 100
        is_suspicious, risk_score = SessionService._assess_risk(
            db=mock_db,
            user_id=1,
            ip_address="1.2.3.4",
            device_info={"device_id": "new_device"},
            location="上海市"
        )
        
        # 分数应该被限制在100
        self.assertEqual(risk_score, 100)

    @patch('app.services.session_service.SessionService._add_to_blacklist')
    def test_cleanup_old_sessions_exact_limit(self, mock_blacklist):
        """测试正好达到会话限制（会关闭最旧的一个）"""
        mock_db = MagicMock()
        user_id = 1
        
        # 正好5个会话（达到限制）
        active_sessions = [
            MagicMock(
                id=i + 1,
                user_id=user_id,
                is_active=True,
                access_token_jti=f"access_{i}",
                refresh_token_jti=f"refresh_{i}",
                last_activity_at=datetime.utcnow() - timedelta(hours=i)
            )
            for i in range(5)
        ]
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = active_sessions
        
        SessionService._cleanup_old_sessions(db=mock_db, user_id=user_id)
        
        # 前4个应该保持活跃（最近的）
        for i in range(4):
            self.assertTrue(active_sessions[i].is_active)
        
        # 最后1个（最旧的）应该被关闭
        self.assertFalse(active_sessions[4].is_active)

    def test_parse_user_agent_exception(self):
        """测试User-Agent解析异常"""
        # 传入会导致异常的数据
        invalid_ua = None
        result = SessionService._parse_user_agent(invalid_ua)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
