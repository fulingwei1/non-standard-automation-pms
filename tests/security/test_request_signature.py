# -*- coding: utf-8 -*-
"""
请求签名验证测试
"""

import pytest
import time
from fastapi import Request
from unittest.mock import Mock, MagicMock

from app.core.request_signature import (
    RequestSignatureVerifier,
    generate_client_signature
)


class TestRequestSignature:
    """请求签名验证测试"""

    # ============================================
    # 1. 签名计算测试
    # ============================================

    def test_compute_signature_consistency(self):
        """测试：相同输入产生相同签名"""
        method = "POST"
        path = "/api/v1/projects"
        timestamp = "1234567890000"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        sig1 = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, body, secret
        )
        sig2 = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, body, secret
        )
        
        assert sig1 == sig2

    def test_compute_signature_different_method(self):
        """测试：不同HTTP方法产生不同签名"""
        timestamp = "1234567890000"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        sig_post = RequestSignatureVerifier.compute_signature(
            "POST", "/api/v1/projects", timestamp, body, secret
        )
        sig_put = RequestSignatureVerifier.compute_signature(
            "PUT", "/api/v1/projects", timestamp, body, secret
        )
        
        assert sig_post != sig_put

    def test_compute_signature_different_path(self):
        """测试：不同路径产生不同签名"""
        method = "POST"
        timestamp = "1234567890000"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        sig1 = RequestSignatureVerifier.compute_signature(
            method, "/api/v1/projects", timestamp, body, secret
        )
        sig2 = RequestSignatureVerifier.compute_signature(
            method, "/api/v1/users", timestamp, body, secret
        )
        
        assert sig1 != sig2

    def test_compute_signature_different_body(self):
        """测试：不同body产生不同签名"""
        method = "POST"
        path = "/api/v1/projects"
        timestamp = "1234567890000"
        secret = "test-secret"
        
        sig1 = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, b'{"name":"test1"}', secret
        )
        sig2 = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, b'{"name":"test2"}', secret
        )
        
        assert sig1 != sig2

    def test_compute_signature_different_timestamp(self):
        """测试：不同时间戳产生不同签名"""
        method = "POST"
        path = "/api/v1/projects"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        sig1 = RequestSignatureVerifier.compute_signature(
            method, path, "1234567890000", body, secret
        )
        sig2 = RequestSignatureVerifier.compute_signature(
            method, path, "1234567890001", body, secret
        )
        
        assert sig1 != sig2

    def test_compute_signature_different_secret(self):
        """测试：不同密钥产生不同签名"""
        method = "POST"
        path = "/api/v1/projects"
        timestamp = "1234567890000"
        body = b'{"name":"test"}'
        
        sig1 = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, body, "secret1"
        )
        sig2 = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, body, "secret2"
        )
        
        assert sig1 != sig2

    # ============================================
    # 2. 签名验证测试
    # ============================================

    def test_verify_valid_signature(self):
        """测试：验证有效签名"""
        method = "POST"
        path = "/api/v1/projects"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        # 生成当前时间戳
        timestamp = str(int(time.time() * 1000))
        
        # 计算签名
        signature = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, body, secret
        )
        
        # 模拟Request对象
        request = self._create_mock_request(method, path)
        
        # 验证签名
        result = RequestSignatureVerifier.verify_signature(
            request, signature, timestamp, body, secret
        )
        
        assert result is True

    def test_verify_invalid_signature(self):
        """测试：验证无效签名"""
        method = "POST"
        path = "/api/v1/projects"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        timestamp = str(int(time.time() * 1000))
        request = self._create_mock_request(method, path)
        
        # 使用错误的签名
        with pytest.raises(Exception) as exc_info:
            RequestSignatureVerifier.verify_signature(
                request, "invalid_signature", timestamp, body, secret
            )
        
        assert "Invalid request signature" in str(exc_info.value.detail)

    def test_verify_expired_signature(self):
        """测试：过期的签名被拒绝"""
        method = "POST"
        path = "/api/v1/projects"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        # 10分钟前的时间戳（超过5分钟有效期）
        timestamp = str(int((time.time() - 600) * 1000))
        
        signature = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, body, secret
        )
        
        request = self._create_mock_request(method, path)
        
        # 验证签名（应该因过期失败）
        with pytest.raises(Exception) as exc_info:
            RequestSignatureVerifier.verify_signature(
                request, signature, timestamp, body, secret
            )
        
        assert "expired" in str(exc_info.value.detail).lower()

    def test_verify_future_timestamp(self):
        """测试：未来时间戳被拒绝"""
        method = "POST"
        path = "/api/v1/projects"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        # 10分钟后的时间戳
        timestamp = str(int((time.time() + 600) * 1000))
        
        signature = RequestSignatureVerifier.compute_signature(
            method, path, timestamp, body, secret
        )
        
        request = self._create_mock_request(method, path)
        
        with pytest.raises(Exception) as exc_info:
            RequestSignatureVerifier.verify_signature(
                request, signature, timestamp, body, secret
            )
        
        assert "expired" in str(exc_info.value.detail).lower()

    def test_verify_invalid_timestamp_format(self):
        """测试：无效的时间戳格式"""
        request = self._create_mock_request("POST", "/api/v1/projects")
        
        with pytest.raises(Exception) as exc_info:
            RequestSignatureVerifier.verify_signature(
                request, "signature", "invalid_timestamp", b"body", "secret"
            )
        
        assert "Invalid timestamp" in str(exc_info.value.detail)

    def test_verify_signature_with_query_params(self):
        """测试：包含查询参数的签名验证"""
        method = "GET"
        path = "/api/v1/projects"
        query = "page=1&size=10"
        full_path = f"{path}?{query}"
        body = b""
        secret = "test-secret"
        
        timestamp = str(int(time.time() * 1000))
        
        signature = RequestSignatureVerifier.compute_signature(
            method, full_path, timestamp, body, secret
        )
        
        request = self._create_mock_request(method, path, query)
        
        result = RequestSignatureVerifier.verify_signature(
            request, signature, timestamp, body, secret
        )
        
        assert result is True

    # ============================================
    # 3. 客户端签名生成测试
    # ============================================

    def test_generate_client_signature(self):
        """测试：客户端签名生成"""
        method = "POST"
        url = "https://api.example.com/api/v1/projects"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        signature, timestamp = generate_client_signature(
            method, url, body, secret
        )
        
        # 签名应该是base64字符串
        assert len(signature) > 0
        # 时间戳应该是数字字符串
        assert timestamp.isdigit()

    def test_generate_client_signature_with_query(self):
        """测试：包含查询参数的客户端签名"""
        method = "GET"
        url = "https://api.example.com/api/v1/projects?page=1&size=10"
        body = b""
        secret = "test-secret"
        
        signature, timestamp = generate_client_signature(
            method, url, body, secret
        )
        
        assert len(signature) > 0
        assert timestamp.isdigit()

    def test_client_signature_server_verification(self):
        """测试：客户端生成的签名可以被服务端验证"""
        method = "POST"
        url = "https://api.example.com/api/v1/projects"
        body = b'{"name":"test"}'
        secret = "test-secret"
        
        # 客户端生成签名
        signature, timestamp = generate_client_signature(
            method, url, body, secret
        )
        
        # 服务端验证
        request = self._create_mock_request(method, "/api/v1/projects")
        
        result = RequestSignatureVerifier.verify_signature(
            request, signature, timestamp, body, secret
        )
        
        assert result is True

    # ============================================
    # 辅助方法
    # ============================================

    def _create_mock_request(
        self, 
        method: str, 
        path: str, 
        query: str = ""
    ) -> Request:
        """创建模拟的Request对象"""
        mock_request = Mock(spec=Request)
        mock_request.method = method
        
        # 模拟URL对象
        mock_url = Mock()
        mock_url.path = path
        mock_url.query = query
        mock_request.url = mock_url
        
        return mock_request


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
