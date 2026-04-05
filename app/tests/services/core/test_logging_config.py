# -*- coding: utf-8 -*-
"""
日志配置模块测试
"""
import logging
import pytest
from unittest.mock import patch, MagicMock


class TestSensitiveDataFilter:
    """测试敏感数据过滤器"""

    def test_password_filtering(self):
        """测试密码过滤"""
        from app.core.logging_config import SensitiveDataFilter

        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="User password is 123456",
            args=(),
            exc_info=None,
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        # 密码应该被替换为 *****
        assert "****" in record.msg

    def test_token_filtering(self):
        """测试Token过滤"""
        from app.core.logging_config import SensitiveDataFilter

        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API token is abc123xyz",
            args=(),
            exc_info=None,
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        # token应该被替换为 ******
        assert "******" in record.msg

    def test_api_key_filtering(self):
        """测试API Key过滤"""
        from app.core.logging_config import SensitiveDataFilter

        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API api_key: sk-1234567890",
            args=(),
            exc_info=None,
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        # api_key 应该被替换为 ******
        assert "******" in record.msg


class TestProductionSensitiveFilter:
    """测试生产环境敏感数据过滤器"""

    def test_debug_log_filtered_in_production(self):
        """测试生产环境过滤DEBUG日志"""
        from app.core.logging_config import ProductionSensitiveFilter

        # 模拟生产环境设置
        with patch("app.core.logging_config.settings") as mock_settings:
            mock_settings.DEBUG = False
            
            filter_obj = ProductionSensitiveFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.DEBUG,
                pathname="test.py",
                lineno=1,
                msg="Debug message",
                args=(),
                exc_info=None,
            )
            
            result = filter_obj.filter(record)
            
            assert result is False

    def test_debug_log_allowed_in_development(self):
        """测试开发环境允许DEBUG日志"""
        from app.core.logging_config import ProductionSensitiveFilter

        # 模拟开发环境设置
        with patch("app.core.logging_config.settings") as mock_settings:
            mock_settings.DEBUG = True
            
            filter_obj = ProductionSensitiveFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.DEBUG,
                pathname="test.py",
                lineno=1,
                msg="Debug message",
                args=(),
                exc_info=None,
            )
            
            result = filter_obj.filter(record)
            
            assert result is True

    def test_sql_query_filtered_in_production(self):
        """测试生产环境过滤SQL查询"""
        from app.core.logging_config import ProductionSensitiveFilter

        # 模拟生产环境设置
        with patch("app.core.logging_config.settings") as mock_settings:
            mock_settings.DEBUG = False
            
            filter_obj = ProductionSensitiveFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.DEBUG,
                pathname="test.py",
                lineno=1,
                msg="SELECT * FROM users WHERE password_hash='xxx'",
                args=(),
                exc_info=None,
            )
            
            result = filter_obj.filter(record)
            
            # DEBUG级别的SQL查询在生产环境应被过滤
            assert result is False


class TestLoggingConfig:
    """测试日志配置函数"""

    def test_setup_logging_dev_mode(self):
        """测试开发环境日志配置"""
        with patch("app.core.logging_config.settings") as mock_settings:
            mock_settings.DEBUG = True
            
            from app.core.logging_config import setup_logging, SensitiveDataFilter, ProductionSensitiveFilter
            
            # 调用 setup_logging 不应抛出异常
            setup_logging()
            
            root_logger = logging.getLogger()
            # 开发环境应该设置DEBUG级别
            assert root_logger.level == logging.DEBUG

    def test_get_logger_returns_configured_logger(self):
        """测试获取已配置的logger"""
        from app.core.logging_config import get_logger
        
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_default_name(self):
        """测试获取logger使用默认名称"""
        from app.core.logging_config import get_logger
        
        logger = get_logger()
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "app"

    def test_log_format_constants(self):
        """测试日志格式常量"""
        from app.core.logging_config import LOG_FORMAT, DETAILED_LOG_FORMAT, LOG_LEVEL_MAP
        
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(name)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT
        assert "%(message)s" in LOG_FORMAT
        assert "DEBUG" in LOG_LEVEL_MAP
        assert "INFO" in LOG_LEVEL_MAP
        assert "WARNING" in LOG_LEVEL_MAP
        assert "ERROR" in LOG_LEVEL_MAP


class TestLogContextHelpers:
    """测试带上下文的日志辅助函数"""

    def test_log_error_with_context(self):
        """测试错误日志上下文"""
        from app.core.logging_config import log_error_with_context
        
        mock_logger = MagicMock()
        test_error = ValueError("Test error")
        
        log_error_with_context(
            mock_logger,
            "操作失败",
            test_error,
            context={"user_id": 123, "project_id": 456}
        )
        
        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args.kwargs
        assert "exc_info" in call_kwargs
        assert call_kwargs["extra"]["error_type"] == "ValueError"
        assert call_kwargs["extra"]["error_message"] == "Test error"

    def test_log_warning_with_context(self):
        """测试警告日志上下文"""
        from app.core.logging_config import log_warning_with_context
        
        mock_logger = MagicMock()
        
        log_warning_with_context(
            mock_logger,
            "资源不存在",
            context={"item_id": 789}
        )
        
        mock_logger.warning.assert_called_once()
        call_kwargs = mock_logger.warning.call_args.kwargs
        assert call_kwargs["extra"]["item_id"] == 789

    def test_log_info_with_context(self):
        """测试信息日志上下文"""
        from app.core.logging_config import log_info_with_context
        
        mock_logger = MagicMock()
        
        log_info_with_context(
            mock_logger,
            "操作成功",
            context={"action": "create", "id": 100}
        )
        
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args.kwargs
        assert call_kwargs["extra"]["action"] == "create"
        assert call_kwargs["extra"]["id"] == 100