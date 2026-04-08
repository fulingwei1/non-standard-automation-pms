# -*- coding: utf-8 -*-
"""data_scope_service_enhanced单元测试"""
import pytest
from app.services.data_scope.data_scope_service_enhanced import DataScopeServiceEnhanced

class TestDataScopeServiceEnhancedInit:
    def test_init_without_db(self):
        """测试无参数初始化"""
        service = DataScopeServiceEnhanced()
        assert service is not None