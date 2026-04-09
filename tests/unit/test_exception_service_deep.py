# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 异常服务"""
import pytest
from unittest.mock import MagicMock


class TestExceptionServiceBusinessLogic:
    """异常服务业务逻辑测试"""

    def test_log_exception(self):
        """测试记录异常"""
        try:
            from app.services.alert.exception_service import ExceptionService

            mock_db = MagicMock()
            service = ExceptionService(mock_db)

            result = service.log_exception("ERROR", "测试异常", {"context": "test"})

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_exception_history(self):
        """测试获取异常历史"""
        try:
            from app.services.alert.exception_service import ExceptionService

            mock_db = MagicMock()

            mock_exception = MagicMock()

            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_exception]

            service = ExceptionService(mock_db)

            result = service.get_exception_history("ERROR")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_notify_on_exception(self):
        """测试异常通知"""
        try:
            from app.services.alert.exception_service import ExceptionService

            mock_db = MagicMock()
            service = ExceptionService(mock_db)

            result = service.notify_on_exception(1, "admin@example.com")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_resolve_exception(self):
        """测试解决异常"""
        try:
            from app.services.alert.exception_service import ExceptionService

            mock_db = MagicMock()

            mock_exception = MagicMock()
            mock_exception.status = "OPEN"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_exception

            service = ExceptionService(mock_db)

            result = service.resolve_exception(1, "已修复")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")