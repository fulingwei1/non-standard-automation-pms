# -*- coding: utf-8 -*-
"""
核心异常类测试
"""

import pytest
from fastapi import HTTPException
from app.core.exceptions import BusinessException


class TestBusinessException:
    """测试业务异常类"""
    
    def test_init_with_message(self):
        """测试使用消息初始化"""
        exc = BusinessException("Test error")
        assert exc.message == "Test error"
        assert exc.detail == "Test error"
        assert exc.status_code == 400
    
    def test_init_with_custom_code(self):
        """测试使用自定义状态码初始化"""
        exc = BusinessException("Test error", code=404)
        assert exc.message == "Test error"
        assert exc.code == 404
        assert exc.status_code == 404
    
    def test_is_http_exception(self):
        """测试继承自 HTTPException"""
        exc = BusinessException("Test error")
        assert isinstance(exc, HTTPException)
    
    def test_default_status_code(self):
        """测试默认状态码为 400"""
        exc = BusinessException("Bad request")
        assert exc.status_code == 400
        assert exc.code == 400
    
    def test_various_status_codes(self):
        """测试各种状态码"""
        test_cases = [
            ("Not found", 404),
            ("Unauthorized", 401),
            ("Forbidden", 403),
            ("Internal error", 500),
        ]
        
        for message, code in test_cases:
            exc = BusinessException(message, code=code)
            assert exc.message == message
            assert exc.code == code
            assert exc.status_code == code
    
    def test_message_attribute(self):
        """测试 message 属性"""
        message = "业务逻辑错误"
        exc = BusinessException(message)
        assert exc.message == message
        assert exc.detail == message
    
    def test_can_be_raised(self):
        """测试可以正常抛出和捕获"""
        with pytest.raises(BusinessException) as exc_info:
            raise BusinessException("Test error", code=422)
        
        assert exc_info.value.message == "Test error"
        assert exc_info.value.code == 422
