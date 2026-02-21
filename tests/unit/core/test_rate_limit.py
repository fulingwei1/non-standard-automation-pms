# -*- coding: utf-8 -*-
"""
速率限制模块测试
"""

import pytest


class TestRateLimitImports:
    """测试速率限制模块导入"""
    
    def test_import_limiter(self):
        """测试导入 limiter"""
        from app.core.rate_limit import limiter
        assert limiter is not None
    
    def test_import_user_limiter(self):
        """测试导入 user_limiter"""
        from app.core.rate_limit import user_limiter
        assert user_limiter is not None
    
    def test_import_strict_limiter(self):
        """测试导入 strict_limiter"""
        from app.core.rate_limit import strict_limiter
        assert strict_limiter is not None
    
    def test_import_get_remote_address(self):
        """测试导入 get_remote_address"""
        from app.core.rate_limit import get_remote_address
        assert callable(get_remote_address)
    
    def test_import_get_user_or_ip(self):
        """测试导入 get_user_or_ip"""
        from app.core.rate_limit import get_user_or_ip
        assert callable(get_user_or_ip)
    
    def test_import_get_ip_and_user(self):
        """测试导入 get_ip_and_user"""
        from app.core.rate_limit import get_ip_and_user
        assert callable(get_ip_and_user)
    
    def test_all_exports(self):
        """测试所有导出"""
        import app.core.rate_limit as rate_limit
        
        expected_exports = [
            "limiter",
            "user_limiter",
            "strict_limiter",
            "get_remote_address",
            "get_user_or_ip",
            "get_ip_and_user",
        ]
        
        for export in expected_exports:
            assert export in rate_limit.__all__
