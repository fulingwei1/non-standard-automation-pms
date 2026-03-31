# -*- coding: utf-8 -*-
"""
核心异常类测试
"""

import pytest
from fastapi import HTTPException

from app.core.exceptions import (
    AlreadyExistsException,
    BusinessException,
    InsufficientDataException,
    NotFoundException,
    OperationNotAllowedException,
    ValidationException,
)


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


class TestNotFoundException:
    """测试资源不存在异常"""

    def test_with_resource_name_only(self):
        exc = NotFoundException("项目")
        assert exc.status_code == 404
        assert exc.message == "项目不存在"
        assert exc.resource_name == "项目"
        assert exc.resource_id is None

    def test_with_resource_id(self):
        exc = NotFoundException("任务", 42)
        assert exc.status_code == 404
        assert exc.message == "任务 (ID=42) 不存在"
        assert exc.resource_id == 42

    def test_is_business_exception(self):
        exc = NotFoundException("项目")
        assert isinstance(exc, BusinessException)

    def test_catchable_as_business_exception(self):
        with pytest.raises(BusinessException):
            raise NotFoundException("项目", 1)


class TestAlreadyExistsException:
    """测试资源已存在异常"""

    def test_with_resource_name_only(self):
        exc = AlreadyExistsException("供应商")
        assert exc.status_code == 409
        assert exc.message == "供应商已存在"

    def test_with_field_and_value(self):
        exc = AlreadyExistsException("供应商", field="编码", value="SUP001")
        assert exc.status_code == 409
        assert "编码=SUP001" in exc.message

    def test_is_business_exception(self):
        assert isinstance(AlreadyExistsException("x"), BusinessException)


class TestValidationException:
    """测试业务验证异常"""

    def test_basic(self):
        exc = ValidationException("不支持的预测算法: XYZ")
        assert exc.status_code == 400
        assert exc.message == "不支持的预测算法: XYZ"

    def test_is_business_exception(self):
        assert isinstance(ValidationException("x"), BusinessException)


class TestOperationNotAllowedException:
    """测试操作不允许异常"""

    def test_basic(self):
        exc = OperationNotAllowedException("系统预置角色不允许删除")
        assert exc.status_code == 400
        assert exc.message == "系统预置角色不允许删除"

    def test_is_business_exception(self):
        assert isinstance(OperationNotAllowedException("x"), BusinessException)


class TestInsufficientDataException:
    """测试数据不足异常"""

    def test_basic(self):
        exc = InsufficientDataException("历史数据不足，无法进行预测")
        assert exc.status_code == 400
        assert exc.message == "历史数据不足，无法进行预测"

    def test_is_business_exception(self):
        assert isinstance(InsufficientDataException("x"), BusinessException)
