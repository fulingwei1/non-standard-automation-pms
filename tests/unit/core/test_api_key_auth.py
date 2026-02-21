# -*- coding: utf-8 -*-
"""
API Key认证测试
"""

import hashlib
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.api_key_auth import APIKeyAuth, get_api_key_user, require_api_key_scope


class TestAPIKeyAuthGenerate:
    """测试API Key生成"""
    
    def test_generate_api_key_default_prefix(self):
        """测试默认前缀生成"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        assert api_key.startswith("pms_")
        assert len(api_key) > 10
        assert len(key_hash) == 64  # SHA256 = 64 hex chars
    
    def test_generate_api_key_custom_prefix(self):
        """测试自定义前缀"""
        api_key, key_hash = APIKeyAuth.generate_api_key(prefix="custom")
        
        assert api_key.startswith("custom_")
    
    def test_generate_unique_keys(self):
        """测试生成的key是唯一的"""
        key1, hash1 = APIKeyAuth.generate_api_key()
        key2, hash2 = APIKeyAuth.generate_api_key()
        
        assert key1 != key2
        assert hash1 != hash2
    
    def test_generated_hash_matches_raw_key(self):
        """测试生成的哈希与原始key匹配"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        computed_hash = APIKeyAuth.hash_api_key(api_key)
        
        assert computed_hash == key_hash


class TestAPIKeyAuthHash:
    """测试API Key哈希"""
    
    def test_hash_api_key(self):
        """测试哈希API Key"""
        api_key = "test_key_12345"
        
        key_hash = APIKeyAuth.hash_api_key(api_key)
        
        assert len(key_hash) == 64
        assert isinstance(key_hash, str)
    
    def test_hash_same_key_produces_same_hash(self):
        """测试相同key产生相同哈希"""
        api_key = "test_key_12345"
        
        hash1 = APIKeyAuth.hash_api_key(api_key)
        hash2 = APIKeyAuth.hash_api_key(api_key)
        
        assert hash1 == hash2
    
    def test_hash_different_keys_produce_different_hashes(self):
        """测试不同key产生不同哈希"""
        hash1 = APIKeyAuth.hash_api_key("key1")
        hash2 = APIKeyAuth.hash_api_key("key2")
        
        assert hash1 != hash2
    
    def test_hash_uses_sha256(self):
        """测试使用SHA256算法"""
        api_key = "test_key"
        
        expected_hash = hashlib.sha256(api_key.encode()).hexdigest()
        actual_hash = APIKeyAuth.hash_api_key(api_key)
        
        assert actual_hash == expected_hash


class TestAPIKeyAuthVerify:
    """测试API Key验证"""
    
    def test_verify_api_key_none(self):
        """测试验证None key"""
        db = Mock(spec=Session)
        
        result = APIKeyAuth.verify_api_key(db, None)
        
        assert result is None
    
    def test_verify_api_key_empty_string(self):
        """测试验证空字符串"""
        db = Mock(spec=Session)
        
        result = APIKeyAuth.verify_api_key(db, "")
        
        assert result is None
    
    @patch('app.models.api_key.APIKey')
    def test_verify_api_key_valid(self, mock_api_key_class):
        """测试验证有效的API Key"""
        db = Mock(spec=Session)
        api_key = "test_key_123"
        key_hash = APIKeyAuth.hash_api_key(api_key)
        
        # 模拟数据库查询
        mock_api_key_obj = Mock()
        mock_api_key_obj.id = 1
        mock_api_key_obj.name = "Test API Key"
        mock_api_key_obj.user_id = 100
        mock_api_key_obj.tenant_id = 1
        mock_api_key_obj.scopes = ["read", "write"]
        mock_api_key_obj.metadata = {"app": "test"}
        mock_api_key_obj.expires_at = None
        mock_api_key_obj.allowed_ips = None
        mock_api_key_obj.last_used_at = None
        mock_api_key_obj.usage_count = 0
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_api_key_obj
        db.query.return_value = mock_query
        
        result = APIKeyAuth.verify_api_key(db, api_key)
        
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Test API Key"
        assert result["user_id"] == 100
        assert result["scopes"] == ["read", "write"]
    
    @patch('app.models.api_key.APIKey')
    def test_verify_api_key_not_found(self, mock_api_key_class):
        """测试验证不存在的API Key"""
        db = Mock(spec=Session)
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query
        
        result = APIKeyAuth.verify_api_key(db, "invalid_key")
        
        assert result is None
    
    @patch('app.models.api_key.APIKey')
    def test_verify_api_key_expired(self, mock_api_key_class):
        """测试验证过期的API Key"""
        db = Mock(spec=Session)
        
        mock_api_key_obj = Mock()
        mock_api_key_obj.expires_at = datetime.utcnow() - timedelta(days=1)
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_api_key_obj
        db.query.return_value = mock_query
        
        result = APIKeyAuth.verify_api_key(db, "test_key")
        
        assert result is None
    
    @patch('app.models.api_key.APIKey')
    def test_verify_api_key_ip_whitelist_allowed(self, mock_api_key_class):
        """测试IP白名单验证通过"""
        db = Mock(spec=Session)
        client_ip = "192.168.1.100"
        
        mock_api_key_obj = Mock()
        mock_api_key_obj.id = 1
        mock_api_key_obj.name = "Test"
        mock_api_key_obj.user_id = 1
        mock_api_key_obj.tenant_id = 1
        mock_api_key_obj.scopes = []
        mock_api_key_obj.metadata = {}
        mock_api_key_obj.expires_at = None
        mock_api_key_obj.allowed_ips = ["192.168.1.100", "192.168.1.101"]
        mock_api_key_obj.last_used_at = None
        mock_api_key_obj.usage_count = 5  # 设置初始值
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_api_key_obj
        db.query.return_value = mock_query
        
        result = APIKeyAuth.verify_api_key(db, "test_key", client_ip=client_ip)
        
        assert result is not None
    
    @patch('app.models.api_key.APIKey')
    def test_verify_api_key_ip_whitelist_denied(self, mock_api_key_class):
        """测试IP白名单验证失败"""
        db = Mock(spec=Session)
        client_ip = "192.168.1.200"  # 不在白名单中
        
        mock_api_key_obj = Mock()
        mock_api_key_obj.allowed_ips = ["192.168.1.100", "192.168.1.101"]
        mock_api_key_obj.expires_at = None
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_api_key_obj
        db.query.return_value = mock_query
        
        result = APIKeyAuth.verify_api_key(db, "test_key", client_ip=client_ip)
        
        assert result is None
    
    def test_verify_api_key_model_not_implemented(self):
        """测试API Key模型未实现的情况"""
        db = Mock(spec=Session)
        
        # 模拟 ImportError
        with patch.dict('sys.modules', {'app.models.api_key': None}):
            result = APIKeyAuth.verify_api_key(db, "test_key")
            
            # 由于模型未实现，会返回 None
            assert result is None


class TestGetAPIKeyUser:
    """测试get_api_key_user函数"""
    
    @pytest.mark.asyncio
    async def test_get_api_key_user_none(self):
        """测试无API Key"""
        result = await get_api_key_user(api_key=None, db=Mock())
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('app.core.api_key_auth.APIKeyAuth.verify_api_key')
    async def test_get_api_key_user_valid(self, mock_verify):
        """测试有效的API Key"""
        mock_verify.return_value = {"id": 1, "name": "Test"}
        
        result = await get_api_key_user(api_key="test_key", db=Mock())
        
        assert result == {"id": 1, "name": "Test"}
    
    @pytest.mark.asyncio
    @patch('app.core.api_key_auth.APIKeyAuth.verify_api_key')
    async def test_get_api_key_user_invalid(self, mock_verify):
        """测试无效的API Key"""
        mock_verify.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key_user(api_key="invalid_key", db=Mock())
        
        assert exc_info.value.status_code == 401


class TestRequireAPIKeyScope:
    """测试require_api_key_scope装饰器"""
    
    @pytest.mark.asyncio
    async def test_require_scope_valid(self):
        """测试有效的权限范围"""
        checker = require_api_key_scope("projects:read")
        
        api_key_info = {
            "id": 1,
            "scopes": ["projects:read", "projects:write"]
        }
        
        result = await checker(api_key_info=api_key_info)
        
        assert result == api_key_info
    
    @pytest.mark.asyncio
    async def test_require_scope_admin(self):
        """测试管理员权限"""
        checker = require_api_key_scope("projects:read")
        
        api_key_info = {
            "id": 1,
            "scopes": ["admin"]
        }
        
        result = await checker(api_key_info=api_key_info)
        
        assert result == api_key_info
    
    @pytest.mark.asyncio
    async def test_require_scope_insufficient(self):
        """测试权限不足"""
        checker = require_api_key_scope("projects:delete")
        
        api_key_info = {
            "id": 1,
            "scopes": ["projects:read"]
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await checker(api_key_info=api_key_info)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_require_scope_no_api_key(self):
        """测试无API Key"""
        checker = require_api_key_scope("projects:read")
        
        with pytest.raises(HTTPException) as exc_info:
            await checker(api_key_info=None)
        
        assert exc_info.value.status_code == 401
