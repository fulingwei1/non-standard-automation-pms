# -*- coding: utf-8 -*-
"""
请求签名验证器测试
"""

import hashlib
import hmac
import base64
import time
import pytest
from unittest.mock import MagicMock, patch


class TestRequestSignatureVerifier:
    """请求签名验证器测试"""

    def test_compute_signature(self):
        """测试签名计算"""
        from app.core.request_signature import RequestSignatureVerifier
        
        method = "POST"
        path = "/api/v1/test"
        timestamp = "1234567890000"
        body = b'{"test": "data"}'
        secret = "test_secret"
        
        # 计算body hash
        body_hash = hashlib.sha256(body).hexdigest()
        signature_string = f"{method}\n{path}\n{timestamp}\n{body_hash}"
        expected_sig = base64.b64encode(
            hmac.new(secret.encode(), signature_string.encode(), hashlib.sha256).digest()
        ).decode()
        
        result = RequestSignatureVerifier.compute_signature(method, path, timestamp, body, secret)
        assert result == expected_sig

    def test_verify_signature_valid(self):
        """测试有效签名验证"""
        from app.core.request_signature import RequestSignatureVerifier
        
        method = "POST"
        path = "/api/v1/test"
        timestamp = str(int(time.time() * 1000))
        body = b'{"test": "data"}'
        secret = "test_secret"
        
        signature = RequestSignatureVerifier.compute_signature(method, path, timestamp, body, secret)
        
        # 验证签名
        result = RequestSignatureVerifier.verify_signature(method, path, timestamp, body, secret, signature)
        assert result is True

    def test_verify_signature_invalid(self):
        """测试无效签名验证"""
        from app.core.request_signature import RequestSignatureVerifier
        
        method = "POST"
        path = "/api/v1/test"
        timestamp = str(int(time.time() * 1000))
        body = b'{"test": "data"}'
        secret = "test_secret"
        
        # 使用错误的签名
        result = RequestSignatureVerifier.verify_signature(method, path, timestamp, body, secret, "invalid_signature")
        assert result is False

    def test_verify_signature_expired(self):
        """测试过期签名验证"""
        from app.core.request_signature import RequestSignatureVerifier
        
        method = "POST"
        path = "/api/v1/test"
        # 使用5分钟之前的时间戳
        timestamp = str(int((time.time() - 400) * 1000))
        body = b'{"test": "data"}'
        secret = "test_secret"
        
        signature = RequestSignatureVerifier.compute_signature(method, path, timestamp, body, secret)
        
        result = RequestSignatureVerifier.verify_signature(method, path, timestamp, body, secret, signature)
        assert result is False

    def test_compute_body_hash(self):
        """测试body哈希计算"""
        from app.core.request_signature import RequestSignatureVerifier
        
        body = b'{"key": "value"}'
        result = RequestSignatureVerifier.compute_body_hash(body)
        
        expected = hashlib.sha256(body).hexdigest()
        assert result == expected

    def test_compute_body_hash_empty(self):
        """测试空body哈希计算"""
        from app.core.request_signature import RequestSignatureVerifier
        
        body = b''
        result = RequestSignatureVerifier.compute_body_hash(body)
        
        expected = hashlib.sha256(b'').hexdigest()
        assert result == expected