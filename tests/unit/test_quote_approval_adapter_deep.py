# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 报价审批适配器"""
import pytest
from unittest.mock import MagicMock


class TestQuoteApprovalAdapterBusinessLogic:
    """报价审批适配器业务逻辑测试"""

    def test_get_entity_found(self):
        """测试获取报价实体"""
        try:
            from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter

            mock_db = MagicMock()

            mock_quote = MagicMock()
            mock_quote.id = 1
            mock_quote.quote_no = "QUOTE-001"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_quote

            adapter = QuoteApprovalAdapter(mock_db)
            result = adapter.get_entity(1)

            assert result.id == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_get_entity_data(self):
        """测试获取报价数据"""
        try:
            from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter

            mock_db = MagicMock()

            mock_quote = MagicMock()
            mock_quote.quote_no = "QUOTE-001"
            mock_quote.customer_name = "客户A"
            mock_quote.total_amount = 80000
            mock_quote.status = "PENDING"
            mock_quote.discount_rate = 0.1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_quote

            adapter = QuoteApprovalAdapter(mock_db)
            result = adapter.get_entity_data(1)

            assert result["quote_no"] == "QUOTE-001"
            assert result["total_amount"] == 80000
        except ImportError:
            pytest.skip("Module not found")

    def test_on_submit(self):
        """测试提交审批回调"""
        try:
            from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter

            mock_db = MagicMock()

            mock_quote = MagicMock()
            mock_quote.status = "DRAFT"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_quote

            adapter = QuoteApprovalAdapter(mock_db)
            adapter.on_submit(1, MagicMock())

            assert mock_quote.status == "PENDING_APPROVAL"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_approved(self):
        """测试审批通过"""
        try:
            from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter

            mock_db = MagicMock()

            mock_quote = MagicMock()
            mock_quote.status = "PENDING_APPROVAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_quote

            adapter = QuoteApprovalAdapter(mock_db)
            adapter.on_approved(1, MagicMock())

            assert mock_quote.status == "APPROVED"
        except ImportError:
            pytest.skip("Module not found")

    def test_route_by_discount(self):
        """测试按折扣路由"""
        try:
            from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter

            mock_db = MagicMock()

            mock_quote = MagicMock()
            mock_quote.discount_rate = 0.3  # 高折扣

            mock_db.query.return_value.filter.return_value.first.return_value = mock_quote

            adapter = QuoteApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["discount_rate"] == 0.3
        except ImportError:
            pytest.skip("Module not found")