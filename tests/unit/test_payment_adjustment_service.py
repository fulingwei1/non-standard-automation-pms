# -*- coding: utf-8 -*-
"""
付款调整服务测试（简化版）
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestPaymentAdjustmentService:
    """付款调整服务测试"""

    def test_service_creation(self):
        """测试服务创建"""
        from app.services.payment_adjustment_service import PaymentAdjustmentService
        
        mock_db = MagicMock()
        service = PaymentAdjustmentService(mock_db)
        
        assert service is not None
        assert service.db == mock_db


class TestPaymentAdjustmentHistory:
    """测试调整历史"""

    def test_get_adjustment_history(self):
        """测试获取调整历史"""
        from app.services.payment_adjustment_service import PaymentAdjustmentService
        
        mock_db = MagicMock()
        service = PaymentAdjustmentService(mock_db)
        
        # Mock empty history
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = service.get_adjustment_history(plan_id=1)
        
        assert isinstance(result, list)


class TestPaymentAdjustmentBatch:
    """测试批量调整"""

    def test_check_and_adjust_all(self):
        """测试批量检查和调整"""
        from app.services.payment_adjustment_service import PaymentAdjustmentService
        
        mock_db = MagicMock()
        service = PaymentAdjustmentService(mock_db)
        
        # Mock no projects need adjustment
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = service.check_and_adjust_all()
        
        assert isinstance(result, dict)