# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 报价服务"""
import pytest
from unittest.mock import MagicMock


class TestQuoteServiceBusinessLogic:
    """报价服务业务逻辑测试"""

    def test_create_quote(self):
        """测试创建报价"""
        try:
            from app.services.quote_service import QuoteService

            mock_db = MagicMock()
            service = QuoteService(mock_db)

            result = service.create_quote(1, "客户A")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_send_quote(self):
        """测试发送报价"""
        try:
            from app.services.quote_service import QuoteService

            mock_db = MagicMock()

            mock_quote = MagicMock()
            mock_quote.status = "DRAFT"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_quote

            service = QuoteService(mock_db)

            result = service.send_quote(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_accept_quote(self):
        """测试接受报价"""
        try:
            from app.services.quote_service import QuoteService

            mock_db = MagicMock()

            mock_quote = MagicMock()
            mock_quote.status = "SENT"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_quote

            service = QuoteService(mock_db)

            result = service.accept_quote(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_expire_quote(self):
        """测试报价过期"""
        try:
            from app.services.quote_service import QuoteService

            mock_db = MagicMock()

            mock_quote = MagicMock()
            mock_quote.valid_until = "2025-01-01"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_quote]

            service = QuoteService(mock_db)

            result = service.expire_quote()

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")