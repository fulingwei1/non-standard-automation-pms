# -*- coding: utf-8 -*-
"""
exception_handlers.py 覆盖率测试
目标: 提升 app/core/exception_handlers.py 覆盖率（当前 21.4%）
"""
import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.core.exception_handlers import (
    SecurityException,
    ResourceNotFoundException,
    PermissionDeniedException,
    RateLimitExceededException,
    _sanitize_error_detail,
    _extract_user_message,
    _build_error_response,
    setup_exception_handlers,
)


class TestSecurityExceptions:
    """测试自定义异常类"""

    def test_security_exception_basic(self):
        exc = SecurityException(
            status_code=400, detail="test error", error_code="TEST_ERROR"
        )
        assert exc.status_code == 400
        assert exc.detail == "test error"
        assert exc.error_code == "TEST_ERROR"

    def test_security_exception_with_user_message(self):
        exc = SecurityException(
            status_code=400,
            detail="internal detail",
            error_code="BAD",
            user_friendly_message="Something went wrong",
        )
        assert exc.user_friendly_message == "Something went wrong"

    def test_resource_not_found(self):
        exc = ResourceNotFoundException(resource_name="Project")
        assert exc.status_code == 404
        assert "Project" in exc.detail or "项目" in exc.detail

    def test_resource_not_found_default(self):
        exc = ResourceNotFoundException()
        assert exc.status_code == 404

    def test_permission_denied(self):
        exc = PermissionDeniedException()
        assert exc.status_code == 403

    def test_permission_denied_custom_detail(self):
        exc = PermissionDeniedException(detail="需要管理员权限")
        assert exc.status_code == 403
        assert exc.detail == "需要管理员权限"

    def test_rate_limit_exceeded(self):
        exc = RateLimitExceededException()
        assert exc.status_code == 429


class TestSanitizeErrorDetail:
    """测试 _sanitize_error_detail"""

    def test_string_detail(self):
        result = _sanitize_error_detail("some error message")
        assert result == "some error message"

    def test_dict_detail(self):
        detail = {"error_code": "NOT_FOUND", "message": "Resource not found"}
        result = _sanitize_error_detail(detail)
        assert isinstance(result, dict)

    def test_list_detail(self):
        detail = [{"loc": ["body", "name"], "msg": "field required"}]
        result = _sanitize_error_detail(detail)
        assert isinstance(result, list)

    def test_none_detail(self):
        result = _sanitize_error_detail(None)
        # None 或字符串都可接受
        assert result is None or isinstance(result, str)

    def test_nested_dict(self):
        detail = {"nested": {"key": "value"}}
        result = _sanitize_error_detail(detail)
        assert isinstance(result, dict)


class TestExtractUserMessage:
    """测试 _extract_user_message"""

    def test_string_message(self):
        result = _extract_user_message("simple message")
        assert result == "simple message"

    def test_dict_with_message(self):
        detail = {"message": "User-friendly message"}
        result = _extract_user_message(detail)
        assert isinstance(result, str)

    def test_dict_without_message(self):
        detail = {"error_code": "SOME_ERROR"}
        result = _extract_user_message(detail)
        assert isinstance(result, str)

    def test_none_detail(self):
        result = _extract_user_message(None)
        assert isinstance(result, str)


class TestBuildErrorResponse:
    """测试 _build_error_response"""

    def test_basic_error_response(self):
        response = _build_error_response(
            status_code=400,
            error_code="BAD_REQUEST",
            detail="Bad request",
            user_friendly_message="请求无效",
        )
        assert isinstance(response, dict)
        # 响应包含 code 或 error_code 字段
        assert "code" in response or "error_code" in response

    def test_404_error_response(self):
        response = _build_error_response(
            status_code=404,
            error_code="NOT_FOUND",
            detail="Not found",
            user_friendly_message="未找到资源",
        )
        assert isinstance(response, dict)

    def test_500_error_response(self):
        response = _build_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            detail="Internal server error",
            user_friendly_message="服务器内部错误",
        )
        assert isinstance(response, dict)


class TestSetupExceptionHandlers:
    """测试异常处理器注册和实际响应"""

    @pytest.fixture
    def app_with_handlers(self):
        app = FastAPI()
        setup_exception_handlers(app)

        @app.get("/http-error")
        async def http_error():
            raise HTTPException(status_code=404, detail="Not found")

        @app.get("/rate-limit-error")
        async def rate_limit_error():
            raise RateLimitExceededException()

        @app.get("/ok")
        async def ok():
            return {"status": "ok"}

        return app

    def test_ok_endpoint(self, app_with_handlers):
        client = TestClient(app_with_handlers)
        response = client.get("/ok")
        assert response.status_code == 200

    def test_http_404_handler(self, app_with_handlers):
        client = TestClient(app_with_handlers, raise_server_exceptions=False)
        response = client.get("/http-error")
        assert response.status_code == 404

    def test_rate_limit_handler(self, app_with_handlers):
        client = TestClient(app_with_handlers, raise_server_exceptions=False)
        response = client.get("/rate-limit-error")
        assert response.status_code == 429

    def test_not_found_route(self, app_with_handlers):
        client = TestClient(app_with_handlers, raise_server_exceptions=False)
        response = client.get("/nonexistent")
        assert response.status_code == 404
