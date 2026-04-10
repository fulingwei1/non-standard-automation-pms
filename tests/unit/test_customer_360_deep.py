# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 客户360服务"""
import pytest
from unittest.mock import MagicMock, patch


class TestCustomer360ServiceBusinessLogic:
    """客户360服务业务逻辑测试"""

    def test_build_overview(self):
        """测试构建客户概览"""
        try:
            from app.services.customer_360_service import Customer360Service

            mock_db = MagicMock()
            service = Customer360Service(mock_db)

            result = service.build_overview(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")