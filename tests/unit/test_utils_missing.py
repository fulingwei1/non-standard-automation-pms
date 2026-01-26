# -*- coding: utf-8 -*-
"""
Utils 模块缺失测试补充
覆盖：logger, project_utils, cache_decorator, wechat_client, alert_escalation_task
"""

import logging
import os
import time
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertStatusEnum
from app.models.project import Project, ProjectStage, ProjectStatus


# ============================================================================
# Tests for logger.py
# ============================================================================

class TestLogger:
    """Test logger utilities"""

    def test_get_logger_with_name(self):
        """Test get_logger with custom name"""
        from app.utils.logger import get_logger
        
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_without_name(self):
        """Test get_logger without name (uses __name__)"""
        from app.utils.logger import get_logger
        
        logger = get_logger()
        assert isinstance(logger, logging.Logger)

    def test_get_log_level_from_env(self):
        """Test _get_log_level reads from environment"""
        from app.utils.logger import _get_log_level
        
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            level = _get_log_level()
            assert level == logging.DEBUG

        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            level = _get_log_level()
            assert level == logging.ERROR

        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            level = _get_log_level()
            assert level == logging.INFO  # Default

    def test_log_error_with_context(self):
        """Test log_error_with_context"""
        from app.utils.logger import log_error_with_context
        
        logger = logging.getLogger("test")
        error = ValueError("Test error")
        
        with patch.object(logger, 'error') as mock_error:
            log_error_with_context(
                logger,
                "Test error message",
                error,
                context={"user_id": 123, "project_id": 456}
            )
            
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "Test error message" in str(call_args)
            assert call_args[1]['extra']['user_id'] == 123
            assert call_args[1]['extra']['error_type'] == 'ValueError'

    def test_log_warning_with_context(self):
        """Test log_warning_with_context"""
        from app.utils.logger import log_warning_with_context
        
        logger = logging.getLogger("test")
        
        with patch.object(logger, 'warning') as mock_warning:
            log_warning_with_context(
                logger,
                "Test warning",
                context={"item_id": 789}
            )
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert "Test warning" in str(call_args)
            assert call_args[1]['extra']['item_id'] == 789

    def test_log_info_with_context(self):
        """Test log_info_with_context"""
        from app.utils.logger import log_info_with_context
        
        logger = logging.getLogger("test")
        
        with patch.object(logger, 'info') as mock_info:
            log_info_with_context(
                logger,
                "Test info",
                context={"action": "create"}
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "Test info" in str(call_args)
            assert call_args[1]['extra']['action'] == "create"


# ============================================================================
# Tests for project_utils.py
# ============================================================================

class TestProjectUtils:
    """Test project utilities"""

    def test_generate_project_code(self, db_session: Session):
        """Test generate_project_code generates correct format"""
        from app.utils.project_utils import generate_project_code
        
        # Create a test project to ensure sequence exists
        project = Project(
            project_code="PJ250101001",
            project_name="Test Project",
            customer_id=1,
            contract_amount=100000.00
        )
        db_session.add(project)
        db_session.commit()
        
        # Generate new code
        code = generate_project_code(db_session)
        
        # Verify format: PJ + yymmdd + xxx
        assert code.startswith("PJ")
        assert len(code) == 11  # PJ + 6 digits + 3 digits
        assert code[2:8].isdigit()  # Date part
        assert code[8:].isdigit()  # Sequence part

    def test_init_project_stages(self, db_session: Session):
        """Test init_project_stages creates all stages and statuses"""
        from app.utils.project_utils import init_project_stages
        
        # Create a test project
        project = Project(
            project_code="PJ250101002",
            project_name="Test Project 2",
            customer_id=1,
            contract_amount=100000.00
        )
        db_session.add(project)
        db_session.flush()
        
        # Initialize stages
        init_project_stages(db_session, project.id)
        
        # Verify stages created
        stages = db_session.query(ProjectStage).filter(
            ProjectStage.project_id == project.id
        ).order_by(ProjectStage.stage_order).all()
        
        assert len(stages) == 9  # S1-S9
        
        # Verify first stage
        assert stages[0].stage_code == "S1"
        assert stages[0].stage_name == "需求进入"
        assert stages[0].status == "PENDING"
        
        # Verify statuses created for S1
        s1_statuses = db_session.query(ProjectStatus).filter(
            ProjectStatus.stage_id == stages[0].id
        ).order_by(ProjectStatus.status_order).all()
        
        assert len(s1_statuses) == 2  # ST01, ST02
        assert s1_statuses[0].status_code == "ST01"
        assert s1_statuses[1].status_code == "ST02"


# ============================================================================
# Tests for cache_decorator.py
# ============================================================================

class TestCacheDecorator:
    """Test cache decorator utilities"""

    def test_get_cache_service_singleton(self):
        """Test get_cache_service returns singleton"""
        from app.utils.cache_decorator import get_cache_service
        
        service1 = get_cache_service()
        service2 = get_cache_service()
        
        assert service1 is service2

    @patch('app.utils.cache_decorator.get_cache_service')
    def test_cache_response_hit(self, mock_get_cache):
        """Test cache_response decorator with cache hit"""
        from app.utils.cache_decorator import cache_response
        
        mock_service = MagicMock()
        mock_service.get.return_value = {"data": "cached"}
        mock_get_cache.return_value = mock_service
        
        @cache_response(prefix="test", ttl=300)
        def test_func(param1: str):
            return {"data": "fresh"}
        
        result = test_func(param1="value")
        
        assert result["data"] == "cached"
        assert result["_from_cache"] is True
        mock_service.get.assert_called_once()

    @patch('app.utils.cache_decorator.get_cache_service')
    def test_cache_response_miss(self, mock_get_cache):
        """Test cache_response decorator with cache miss"""
        from app.utils.cache_decorator import cache_response
        
        mock_service = MagicMock()
        mock_service.get.return_value = None
        mock_get_cache.return_value = mock_service
        
        @cache_response(prefix="test", ttl=300)
        def test_func(param1: str):
            return {"data": "fresh"}
        
        result = test_func(param1="value")
        
        assert result["data"] == "fresh"
        assert result["_from_cache"] is False
        mock_service.set.assert_called_once()

    @patch('app.utils.cache_decorator.get_cache_service')
    def test_cache_project_detail(self, mock_get_cache):
        """Test cache_project_detail decorator"""
        from app.utils.cache_decorator import cache_project_detail
        
        mock_service = MagicMock()
        mock_service.get_project_detail.return_value = {"id": 1, "name": "cached"}
        mock_get_cache.return_value = mock_service
        
        @cache_project_detail
        def get_project(project_id: int):
            return {"id": project_id, "name": "fresh"}
        
        result = get_project(project_id=1)
        
        assert result["name"] == "cached"
        assert result["_from_cache"] is True

    @patch('app.utils.cache_decorator.get_cache_service')
    def test_cache_project_list(self, mock_get_cache):
        """Test cache_project_list decorator"""
        from app.utils.cache_decorator import cache_project_list
        
        mock_service = MagicMock()
        mock_service.get_project_list.return_value = {"items": [{"id": 1}]}
        mock_get_cache.return_value = mock_service
        
        @cache_project_list
        def list_projects(filters: dict):
            return {"items": [{"id": 1, "name": "fresh"}]}
        
        result = list_projects(filters={"status": "active"})
        
        assert result["_from_cache"] is True
        mock_service.get_project_list.assert_called_once()

    def test_log_query_time_fast_query(self):
        """Test log_query_time decorator with fast query"""
        from app.utils.cache_decorator import log_query_time
        
        @log_query_time(threshold=0.5)
        def fast_func():
            return "result"
        
        with patch('app.utils.cache_decorator.logger') as mock_logger:
            result = fast_func()
            assert result == "result"
            mock_logger.warning.assert_not_called()

    def test_log_query_time_slow_query(self):
        """Test log_query_time decorator with slow query"""
        from app.utils.cache_decorator import log_query_time
        
        @log_query_time(threshold=0.1)
        def slow_func():
            time.sleep(0.2)
            return "result"
        
        with patch('app.utils.cache_decorator.logger') as mock_logger:
            result = slow_func()
            assert result == "result"
            mock_logger.warning.assert_called_once()

    def test_query_stats(self):
        """Test QueryStats class"""
        from app.utils.cache_decorator import QueryStats
        
        stats = QueryStats()
        assert stats.queries == []
        assert stats.total_time == 0
        
        stats.record_query("test_func", 0.3, {"param": "value"})
        assert len(stats.queries) == 1
        assert stats.total_time == 0.3
        
        stats.record_query("slow_func", 0.6, {})
        assert len(stats.queries) == 2
        assert len(stats.slow_queries) == 1
        
        stats_data = stats.get_stats()
        assert stats_data["total_queries"] == 2
        assert stats_data["slow_queries"] == 1
        assert stats_data["total_time"] == 0.9

    def test_track_query_decorator(self):
        """Test track_query decorator"""
        from app.utils.cache_decorator import track_query, query_stats
        
        query_stats.reset()
        
        @track_query
        def test_func(param: str):
            return f"result_{param}"
        
        result = test_func("test")
        
        assert result == "result_test"
        assert len(query_stats.queries) == 1
        assert query_stats.queries[0]["function"] == "test_func"


# ============================================================================
# Tests for wechat_client.py
# ============================================================================

class TestWeChatTokenCache:
    """Test WeChatTokenCache"""

    def test_get_missing_key(self):
        """Test get with missing key"""
        from app.utils.wechat_client import WeChatTokenCache
        
        WeChatTokenCache.clear()
        result = WeChatTokenCache.get("missing_key")
        assert result is None

    def test_set_and_get(self):
        """Test set and get token"""
        from app.utils.wechat_client import WeChatTokenCache
        
        WeChatTokenCache.clear()
        WeChatTokenCache.set("test_key", "test_token", expires_in=7200)
        
        result = WeChatTokenCache.get("test_key")
        assert result == "test_token"

    def test_get_expired_token(self):
        """Test get expired token returns None"""
        from app.utils.wechat_client import WeChatTokenCache
        
        WeChatTokenCache.clear()
        # Set token with very short expiry
        WeChatTokenCache.set("test_key", "test_token", expires_in=1)
        
        # Wait for expiry
        time.sleep(2)
        
        result = WeChatTokenCache.get("test_key")
        assert result is None

    def test_clear_specific_key(self):
        """Test clear specific key"""
        from app.utils.wechat_client import WeChatTokenCache
        
        WeChatTokenCache.clear()
        WeChatTokenCache.set("key1", "token1", 7200)
        WeChatTokenCache.set("key2", "token2", 7200)
        
        WeChatTokenCache.clear("key1")
        
        assert WeChatTokenCache.get("key1") is None
        assert WeChatTokenCache.get("key2") == "token2"

    def test_clear_all(self):
        """Test clear all keys"""
        from app.utils.wechat_client import WeChatTokenCache
        
        WeChatTokenCache.set("key1", "token1", 7200)
        WeChatTokenCache.set("key2", "token2", 7200)
        
        WeChatTokenCache.clear()
        
        assert WeChatTokenCache.get("key1") is None
        assert WeChatTokenCache.get("key2") is None


class TestWeChatClient:
    """Test WeChatClient"""

    def test_init_with_params(self):
        """Test initialization with parameters"""
        from app.utils.wechat_client import WeChatClient
        
        client = WeChatClient(
            corp_id="test_corp",
            agent_id="test_agent",
            secret="test_secret"
        )
        
        assert client.corp_id == "test_corp"
        assert client.agent_id == "test_agent"
        assert client.secret == "test_secret"

    def test_init_without_params_raises_error(self):
        """Test initialization without params raises error"""
        from app.utils.wechat_client import WeChatClient
        
        with patch('app.utils.wechat_client.settings') as mock_settings:
            mock_settings.WECHAT_CORP_ID = None
            mock_settings.WECHAT_AGENT_ID = None
            mock_settings.WECHAT_SECRET = None
            
            with pytest.raises(ValueError, match="企业微信配置不完整"):
                WeChatClient()

    @patch('app.utils.wechat_client.requests.get')
    @patch('app.utils.wechat_client.WeChatTokenCache.get')
    @patch('app.utils.wechat_client.WeChatTokenCache.set')
    def test_get_access_token_from_api(self, mock_cache_set, mock_cache_get, mock_get):
        """Test get_access_token from API"""
        from app.utils.wechat_client import WeChatClient
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errcode": 0,
            "access_token": "test_token",
            "expires_in": 7200
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        mock_cache_get.return_value = None
        
        client = WeChatClient(
            corp_id="test_corp",
            agent_id="test_agent",
            secret="test_secret"
        )
        
        token = client.get_access_token()
        
        assert token == "test_token"
        mock_cache_set.assert_called_once()

    @patch('app.utils.wechat_client.requests.get')
    @patch('app.utils.wechat_client.WeChatTokenCache.get')
    def test_get_access_token_from_cache(self, mock_cache_get, mock_get):
        """Test get_access_token from cache"""
        from app.utils.wechat_client import WeChatClient
        
        mock_cache_get.return_value = "cached_token"
        
        client = WeChatClient(
            corp_id="test_corp",
            agent_id="test_agent",
            secret="test_secret"
        )
        
        token = client.get_access_token()
        
        assert token == "cached_token"
        mock_get.assert_not_called()

    @patch('app.utils.wechat_client.requests.post')
    @patch('app.utils.wechat_client.WeChatClient.get_access_token')
    def test_send_message_success(self, mock_get_token, mock_post):
        """Test send_message success"""
        from app.utils.wechat_client import WeChatClient
        
        mock_get_token.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = WeChatClient(
            corp_id="test_corp",
            agent_id="test_agent",
            secret="test_secret"
        )
        
        result = client.send_message(
            user_ids=["user1", "user2"],
            message={"msgtype": "text", "text": {"content": "test"}}
        )
        
        assert result is True
        mock_post.assert_called_once()

    @patch('app.utils.wechat_client.WeChatClient.get_access_token')
    def test_send_message_empty_user_ids(self, mock_get_token):
        """Test send_message with empty user_ids"""
        from app.utils.wechat_client import WeChatClient
        
        client = WeChatClient(
            corp_id="test_corp",
            agent_id="test_agent",
            secret="test_secret"
        )
        
        result = client.send_message(user_ids=[], message={"msgtype": "text"})
        
        assert result is False
        mock_get_token.assert_not_called()

    @patch('app.utils.wechat_client.WeChatClient.send_message')
    def test_send_text_message(self, mock_send):
        """Test send_text_message convenience method"""
        from app.utils.wechat_client import WeChatClient
        
        mock_send.return_value = True
        
        client = WeChatClient(
            corp_id="test_corp",
            agent_id="test_agent",
            secret="test_secret"
        )
        
        result = client.send_text_message(["user1"], "test content")
        
        assert result is True
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == ["user1"]
        assert call_args[0][1]["msgtype"] == "text"
        assert call_args[0][1]["text"]["content"] == "test content"


# ============================================================================
# Tests for alert_escalation_task.py
# ============================================================================

class TestAlertEscalationTask:
    """Test alert escalation task"""

    def test_determine_escalated_level_info_to_warning(self):
        """Test _determine_escalated_level from INFO to WARNING"""
        from app.utils.alert_escalation_task import _determine_escalated_level
        
        result = _determine_escalated_level(AlertLevelEnum.INFO.value)
        assert result == AlertLevelEnum.WARNING.value

    def test_determine_escalated_level_warning_to_critical(self):
        """Test _determine_escalated_level from WARNING to CRITICAL"""
        from app.utils.alert_escalation_task import _determine_escalated_level
        
        result = _determine_escalated_level(AlertLevelEnum.WARNING.value)
        assert result == AlertLevelEnum.CRITICAL.value

    def test_determine_escalated_level_critical_to_urgent(self):
        """Test _determine_escalated_level from CRITICAL to URGENT"""
        from app.utils.alert_escalation_task import _determine_escalated_level
        
        result = _determine_escalated_level(AlertLevelEnum.CRITICAL.value)
        assert result == AlertLevelEnum.URGENT.value

    def test_determine_escalated_level_urgent_no_escalation(self):
        """Test _determine_escalated_level URGENT cannot escalate"""
        from app.utils.alert_escalation_task import _determine_escalated_level
        
        result = _determine_escalated_level(AlertLevelEnum.URGENT.value)
        assert result is None

    @patch('app.utils.alert_escalation_task.get_db_session')
    @patch('app.utils.alert_escalation_task.AlertRuleEngine')
    @patch('app.utils.alert_escalation_task.AlertNotificationService')
    def test_check_alert_timeout_escalation(self, mock_notification_service, mock_engine, mock_db_session):
        """Test check_alert_timeout_escalation escalates timeout alerts"""
        from app.utils.alert_escalation_task import check_alert_timeout_escalation
        
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_db_session.return_value.__enter__.return_value = mock_db
        
        mock_engine_instance = MagicMock()
        mock_engine_instance.RESPONSE_TIMEOUT = {
            AlertLevelEnum.INFO.value: 8,
            AlertLevelEnum.WARNING.value: 4,
        }
        mock_engine_instance.level_priority.return_value = 2
        mock_engine.return_value = mock_engine_instance
        
        # Create test alert
        alert = AlertRecord(
            id=1,
            alert_no="ALERT001",
            alert_level=AlertLevelEnum.INFO.value,
            status=AlertStatusEnum.PENDING.value,
            is_escalated=False,
            triggered_at=datetime.now() - timedelta(hours=10),
            alert_title="Test Alert",
            alert_content="Test content"
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [alert]
        
        # Execute
        result = check_alert_timeout_escalation()
        
        # Verify escalation
        assert result['checked_count'] == 1
        assert alert.alert_level == AlertLevelEnum.WARNING.value
        assert alert.is_escalated is True
        assert alert.escalated_at is not None
