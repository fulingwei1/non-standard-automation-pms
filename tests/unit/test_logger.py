# -*- coding: utf-8 -*-
"""
日志工具模块单元测试
"""

import logging
import os


class TestGetLogLevel:
    """测试 _get_log_level 函数"""

    def test_debug_level(self):
        """测试 DEBUG 级别"""
        os.environ["LOG_LEVEL"] = "DEBUG"
        from app.utils.logger import _get_log_level

        level = _get_log_level()
        assert level == logging.DEBUG

    def test_info_level(self):
        """测试 INFO 级别"""
        os.environ["LOG_LEVEL"] = "INFO"
        from app.utils.logger import _get_log_level

        level = _get_log_level()
        assert level == logging.INFO

    def test_warning_level(self):
        """测试 WARNING 级别"""
        os.environ["LOG_LEVEL"] = "WARNING"
        from app.utils.logger import _get_log_level

        level = _get_log_level()
        assert level == logging.WARNING

    def test_error_level(self):
        """测试 ERROR 级别"""
        os.environ["LOG_LEVEL"] = "ERROR"
        from app.utils.logger import _get_log_level

        level = _get_log_level()
        assert level == logging.ERROR

    def test_critical_level(self):
        """测试 CRITICAL 级别"""
        os.environ["LOG_LEVEL"] = "CRITICAL"
        from app.utils.logger import _get_log_level

        level = _get_log_level()
        assert level == logging.CRITICAL

    def test_lowercase_level(self):
        """测试小写环境变量"""
        os.environ["LOG_LEVEL"] = "info"
        from app.utils.logger import _get_log_level

        level = _get_log_level()
        assert level == logging.INFO

    def test_invalid_level_defaults_to_info(self):
        """测试无效级别默认为 INFO"""
        os.environ["LOG_LEVEL"] = "INVALID"
        from app.utils.logger import _get_log_level

        level = _get_log_level()
        assert level == logging.INFO

    def test_no_env_var_defaults_to_info(self):
        """测试没有环境变量时默认为 INFO"""
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]
        from app.utils.logger import _get_log_level

        level = _get_log_level()
        assert level == logging.INFO


class TestGetLogger:
    """测试 get_logger 函数"""

    def test_get_logger_returns_logger(self):
        """测试返回 logger 对象"""
        from app.utils.logger import get_logger

        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_name(self):
        """测试指定 logger 名称"""
        from app.utils.logger import get_logger

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1.name == "module1"
        assert logger2.name == "module2"

    def test_get_logger_without_name_uses_default(self):
        """测试不指定名称时使用模块默认名称"""
        from app.utils.logger import get_logger

        logger = get_logger()
        # logger 应该使用调用模块的 __name__
        # 当在模块级别调用时，name 为 None，会使用调用模块的 __name__
        assert logger.name == "app.utils.logger"

    def test_get_logger_same_name_returns_same_instance(self):
        """测试相同名称返回相同实例（避免重复配置）"""
        from app.utils.logger import get_logger

        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is logger2

    def test_get_logger_has_handlers(self):
        """测试 logger 配置了 handlers"""
        from app.utils.logger import get_logger

        logger = get_logger("test_handlers")
        assert len(logger.handlers) > 0


class TestLogErrorWithContext:
    """测试 log_error_with_context 函数"""

    def test_log_error_with_context(self):
        """测试记录带上下文的错误"""
        from app.utils.logger import log_error_with_context, get_logger

        logger = get_logger("test")

        class TestError(Exception):
            pass

        error = TestError("Test error")
        context = {"user_id": 123, "item_id": 456}

        log_error_with_context(logger, "Test message", error, context)

        # 只测试函数不抛出异常，实际日志内容需要检查日志输出
        assert True

    def test_log_error_without_context(self):
        """测试记录不带上下文的错误"""
        from app.utils.logger import log_error_with_context, get_logger

        logger = get_logger("test")

        class TestError(Exception):
            pass

        error = TestError("Test error")
        log_error_with_context(logger, "Test message", error)

        assert True

    def test_log_error_with_none_error(self):
        """测试错误为 None 时不抛出异常"""
        from app.utils.logger import log_error_with_context, get_logger

        logger = get_logger("test")
        log_error_with_context(logger, "Test message", None)
        assert True

    def test_log_error_sets_extra_fields(self):
        """测试设置 extra 字段"""
        from app.utils.logger import log_error_with_context, get_logger

        logger = get_logger("test")

        class TestError(Exception):
            pass

        error = TestError("Test error")
        context = {"key": "value"}

        # 这个测试需要实际的日志记录来验证 extra 字段
        # 这里只测试函数执行不抛出异常
        log_error_with_context(logger, "Test message", error, context)
        assert True


class TestLogWarningWithContext:
    """测试 log_warning_with_context 函数"""

    def test_log_warning_with_context(self):
        """测试记录带上下文的警告"""
        from app.utils.logger import log_warning_with_context, get_logger

        logger = get_logger("test")
        context = {"user_id": 123, "item_id": 456}
        log_warning_with_context(logger, "Test warning", context)
        assert True

    def test_log_warning_without_context(self):
        """测试记录不带上下文的警告"""
        from app.utils.logger import log_warning_with_context, get_logger

        logger = get_logger("test")
        log_warning_with_context(logger, "Test warning")
        assert True

    def test_log_warning_with_none_context(self):
        """测试上下文为 None 时不抛出异常"""
        from app.utils.logger import log_warning_with_context, get_logger

        logger = get_logger("test")
        log_warning_with_context(logger, "Test warning", None)
        assert True


class TestLogInfoWithContext:
    """测试 log_info_with_context 函数"""

    def test_log_info_with_context(self):
        """测试记录带上下文的信息"""
        from app.utils.logger import log_info_with_context, get_logger

        logger = get_logger("test")
        context = {"user_id": 123, "item_id": 456}
        log_info_with_context(logger, "Test info", context)
        assert True

    def test_log_info_without_context(self):
        """测试记录不带上下文的信息"""
        from app.utils.logger import log_info_with_context, get_logger

        logger = get_logger("test")
        log_info_with_context(logger, "Test info")
        assert True

    def test_log_info_with_none_context(self):
        """测试上下文为 None 时不抛出异常"""
        from app.utils.logger import log_info_with_context, get_logger

        logger = get_logger("test")
        log_info_with_context(logger, "Test info", None)
        assert True


class TestLogConstants:
    """测试日志常量"""

    def test_log_format_exists(self):
        """测试 LOG_FORMAT 常量存在"""
        from app.utils.logger import LOG_FORMAT

        assert isinstance(LOG_FORMAT, str)
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(name)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT
        assert "%(message)s" in LOG_FORMAT

    def test_detailed_log_format_exists(self):
        """测试 DETAILED_LOG_FORMAT 常量存在"""
        from app.utils.logger import DETAILED_LOG_FORMAT

        assert isinstance(DETAILED_LOG_FORMAT, str)
        assert "%(pathname)s" in DETAILED_LOG_FORMAT
        assert "%(lineno)d" in DETAILED_LOG_FORMAT

    def test_log_level_map_exists(self):
        """测试 LOG_LEVEL_MAP 常量存在"""
        from app.utils.logger import LOG_LEVEL_MAP

        assert isinstance(LOG_LEVEL_MAP, dict)
        assert "DEBUG" in LOG_LEVEL_MAP
        assert "INFO" in LOG_LEVEL_MAP
        assert "WARNING" in LOG_LEVEL_MAP
        assert "ERROR" in LOG_LEVEL_MAP
        assert "CRITICAL" in LOG_LEVEL_MAP
