# -*- coding: utf-8 -*-
"""
API Key认证测试
"""

import pytest
import hashlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAPIKeyAuth:
    """API Key认证测试"""

    def test_generate_api_key(self):
        """测试API Key生成"""
        from app.core.api_key_auth import APIKeyAuth
        
        api_key, key_hash = APIKeyAuth.generate_api_key("test")
        
        assert api_key.startswith("test_")
        assert len(api_key) > 10
        assert key_hash == hashlib.sha256(api_key.encode()).hexdigest()

    def test_generate_api_key_default_prefix(self):
        """测试默认前缀"""
        from app.core.api_key_auth import APIKeyAuth
        
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        assert api_key.startswith("pms_")

    def test_hash_api_key(self):
        """测试API Key哈希"""
        from app.core.api_key_auth import APIKeyAuth
        
        api_key = "test_key_12345"
        result = APIKeyAuth.hash_api_key(api_key)
        
        expected = hashlib.sha256(api_key.encode()).hexdigest()
        assert result == expected

    def test_create_api_key_from_secret(self):
        """测试从密钥创建API Key"""
        from app.core.api_key_auth import APIKeyAuth
        
        secret = "my_secret_key"
        result = APIKeyAuth.create_api_key_from_secret(secret)
        
        assert result.startswith("sk_")
        assert len(result) > 20

    def test_validate_api_key_format_valid(self):
        """测试有效格式验证"""
        from app.core.api_key_auth import APIKeyAuth
        
        valid_keys = ["pms_abc123", "test_key", "sk_xyz789"]
        for key in valid_keys:
            assert APIKeyAuth.validate_api_key_format(key) is True

    def test_validate_api_key_format_invalid(self):
        """测试无效格式验证"""
        from app.core.api_key_auth import APIKeyAuth
        
        invalid_keys = ["", "abc", "short"]
        for key in invalid_keys:
            assert APIKeyAuth.validate_api_key_format(key) is False

    def test_is_api_key_expired_not_expired(self):
        """测试未过期检查"""
        from app.core.api_key_auth import APIKeyAuth
        
        # 设置1天后过期
        expires_at = datetime.utcnow() + timedelta(days=1)
        result = APIKeyAuth.is_api_key_expired(expires_at)
        
        assert result is False

    def test_is_api_key_expired_expired(self):
        """测试已过期检查"""
        from app.core.api_key_auth import APIKeyAuth
        
        # 设置1天前过期
        expires_at = datetime.utcnow() - timedelta(days=1)
        result = APIKeyAuth.is_api_key_expired(expires_at)
        
        assert result is True

    def test_is_api_key_expired_none(self):
        """测试永不过期"""
        from app.core.api_key_auth import APIKeyAuth
        
        result = APIKeyAuth.is_api_key_expired(None)
        assert result is False