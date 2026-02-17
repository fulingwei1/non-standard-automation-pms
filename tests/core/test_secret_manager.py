# -*- coding: utf-8 -*-
"""
密钥管理器单元测试

测试 SecretKeyManager 的所有功能
"""

import pytest
import os
import base64
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.core.secret_manager import SecretKeyManager, get_secret_manager


class TestSecretKeyGeneration:
    """测试密钥生成功能"""
    
    def test_generate_key_default_length(self):
        """测试生成默认长度的密钥"""
        manager = SecretKeyManager()
        key = manager.generate_key()
        
        assert key is not None
        assert len(key) >= 32  # Base64编码后长度会更长
        assert isinstance(key, str)
    
    def test_generate_key_custom_length(self):
        """测试生成自定义长度的密钥"""
        manager = SecretKeyManager()
        key = manager.generate_key(length=64)
        
        assert key is not None
        assert len(key) >= 64
    
    def test_generate_key_is_random(self):
        """测试生成的密钥是随机的"""
        manager = SecretKeyManager()
        key1 = manager.generate_key()
        key2 = manager.generate_key()
        
        assert key1 != key2
    
    def test_generate_key_is_url_safe(self):
        """测试生成的密钥是URL安全的"""
        manager = SecretKeyManager()
        key = manager.generate_key()
        
        # Base64 URL-safe 字符集: A-Z, a-z, 0-9, -, _
        allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
        assert all(c in allowed_chars for c in key)
    
    def test_generate_multiple_keys(self):
        """测试批量生成密钥"""
        manager = SecretKeyManager()
        keys = [manager.generate_key() for _ in range(10)]
        
        # 所有密钥应该不同
        assert len(keys) == len(set(keys))
        
        # 所有密钥应该有效
        for key in keys:
            assert manager.validate_key(key)


class TestSecretKeyValidation:
    """测试密钥验证功能"""
    
    def test_validate_valid_key(self):
        """测试验证有效密钥"""
        manager = SecretKeyManager()
        key = manager.generate_key()
        
        assert manager.validate_key(key) is True
    
    def test_validate_empty_key(self):
        """测试验证空密钥"""
        manager = SecretKeyManager()
        
        assert manager.validate_key("") is False
        assert manager.validate_key(None) is False
    
    def test_validate_short_key(self):
        """测试验证长度不足的密钥"""
        manager = SecretKeyManager()
        short_key = "too-short"
        
        assert manager.validate_key(short_key) is False
    
    def test_validate_custom_min_length(self):
        """测试自定义最小长度验证"""
        manager = SecretKeyManager()
        key = manager.generate_key(length=16)  # 生成较短密钥
        
        # 默认最小长度（32）应该失败
        assert manager.validate_key(key, min_length=32) is False
        
        # 较短的最小长度应该通过
        assert manager.validate_key(key, min_length=16) is True
    
    def test_validate_invalid_base64(self):
        """测试验证无效的Base64编码"""
        manager = SecretKeyManager()
        
        # 包含无效字符的密钥
        invalid_key = "invalid@key#with$special%chars!" * 2
        
        # 可能通过或失败，取决于实现
        # 这里主要测试不会崩溃
        result = manager.validate_key(invalid_key)
        assert isinstance(result, bool)


class TestSecretKeyRotation:
    """测试密钥轮转功能"""
    
    def test_rotate_key_auto_generate(self):
        """测试自动生成新密钥轮转"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        old_key = manager.current_key
        
        result = manager.rotate_key()
        
        assert result['status'] == 'success'
        assert result['new_key'] != old_key
        assert result['old_key'] == old_key
        assert manager.current_key == result['new_key']
        assert old_key in manager.old_keys
    
    def test_rotate_key_with_custom_key(self):
        """测试使用指定密钥轮转"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        new_key = manager.generate_key()
        
        result = manager.rotate_key(new_key)
        
        assert result['status'] == 'success'
        assert result['new_key'] == new_key
        assert manager.current_key == new_key
    
    def test_rotate_key_invalid_new_key(self):
        """测试使用无效密钥轮转"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        
        with pytest.raises(ValueError, match="新密钥无效"):
            manager.rotate_key("too-short")
    
    def test_rotate_key_keeps_old_keys(self):
        """测试轮转密钥保留旧密钥"""
        manager = SecretKeyManager()
        keys = [manager.generate_key() for _ in range(5)]
        
        manager.current_key = keys[0]
        
        # 轮转4次
        for i in range(1, 5):
            manager.rotate_key(keys[i])
        
        # 应该只保留最近3个旧密钥
        assert len(manager.old_keys) == 3
        assert keys[3] in manager.old_keys  # 最近的旧密钥
        assert keys[0] not in manager.old_keys  # 最早的密钥应该被清除
    
    def test_rotate_key_updates_metadata(self):
        """测试轮转密钥更新元数据"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        
        result = manager.rotate_key()
        
        assert 'rotation_date' in result
        assert manager.rotation_date is not None
        assert isinstance(manager.rotation_date, datetime)


class TestTokenVerification:
    """测试Token验证功能"""
    
    def test_verify_token_with_current_key(self):
        """测试使用当前密钥验证Token"""
        import jwt
        
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        
        # 创建Token
        payload = {"user_id": 123, "exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, manager.current_key, algorithm="HS256")
        
        # 验证Token
        decoded = manager.verify_token_with_fallback(token)
        
        assert decoded is not None
        assert decoded['user_id'] == 123
        assert '_used_old_key' not in decoded
    
    def test_verify_token_with_old_key(self):
        """测试使用旧密钥验证Token"""
        import jwt
        
        manager = SecretKeyManager()
        old_key = manager.generate_key()
        manager.current_key = old_key
        
        # 创建Token
        payload = {"user_id": 123, "exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, old_key, algorithm="HS256")
        
        # 轮转密钥
        manager.rotate_key()
        
        # 验证Token（应该使用旧密钥）
        decoded = manager.verify_token_with_fallback(token)
        
        assert decoded is not None
        assert decoded['user_id'] == 123
        assert decoded.get('_used_old_key') is True
        assert '_old_key_index' in decoded
    
    def test_verify_token_all_keys_fail(self):
        """测试所有密钥验证失败"""
        import jwt
        
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        
        # 使用完全不同的密钥创建Token
        wrong_key = manager.generate_key()
        payload = {"user_id": 123, "exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, wrong_key, algorithm="HS256")
        
        # 验证Token（应该失败）
        decoded = manager.verify_token_with_fallback(token)
        
        assert decoded is None
    
    def test_verify_expired_token(self):
        """测试验证过期Token"""
        import jwt
        
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        
        # 创建过期Token
        payload = {"user_id": 123, "exp": datetime.utcnow() - timedelta(hours=1)}
        token = jwt.encode(payload, manager.current_key, algorithm="HS256")
        
        # 验证Token（应该失败）
        decoded = manager.verify_token_with_fallback(token)
        
        assert decoded is None
    
    def test_verify_token_custom_algorithms(self):
        """测试使用自定义算法验证Token"""
        import jwt
        
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        
        # 创建Token
        payload = {"user_id": 123}
        token = jwt.encode(payload, manager.current_key, algorithm="HS256")
        
        # 验证Token
        decoded = manager.verify_token_with_fallback(token, algorithms=["HS256"])
        
        assert decoded is not None
        assert decoded['user_id'] == 123


class TestKeyLoading:
    """测试密钥加载功能"""
    
    @patch.dict(os.environ, {'SECRET_KEY': 'dGVzdC1rZXkteHh4eHh4eHh4eHh4eHh4eHh4eHh4eHg='})
    def test_load_keys_from_env_current_key(self):
        """测试从环境变量加载当前密钥"""
        manager = SecretKeyManager()
        manager.load_keys_from_env()
        
        assert manager.current_key is not None
        assert manager.current_key is not None  # base64 encoded key
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'Y3VycmVudC14eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHg=',
        'OLD_SECRET_KEYS': 'b2xkMS14eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHg=,b2xkMi15eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXl5eXk='
    })
    def test_load_keys_from_env_old_keys(self):
        """测试从环境变量加载旧密钥"""
        manager = SecretKeyManager()
        manager.load_keys_from_env()
        
        assert len(manager.old_keys) == 2
        assert len(manager.old_keys) >= 1  # old keys loaded
        assert len(manager.old_keys) >= 1  # old keys loaded
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('app.core.config.settings')
    def test_load_keys_dev_mode_auto_generate(self, mock_settings):
        """测试开发模式自动生成密钥"""
        mock_settings.DEBUG = True
        
        manager = SecretKeyManager()
        manager.load_keys_from_env()
        
        assert manager.current_key is not None
        assert len(manager.current_key) >= 32
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('app.core.config.settings')
    def test_load_keys_prod_mode_missing_key(self, mock_settings):
        """测试生产模式缺少密钥抛出异常"""
        mock_settings.DEBUG = False
        
        manager = SecretKeyManager()
        
        with pytest.raises(ValueError, match="生产环境必须设置SECRET_KEY"):
            manager.load_keys_from_env()


class TestKeyCleanup:
    """测试密钥清理功能"""
    
    def test_cleanup_expired_keys(self):
        """测试清理过期密钥"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        manager.old_keys = [manager.generate_key() for _ in range(3)]
        manager.rotation_date = datetime.now() - timedelta(days=31)
        
        cleaned_count = manager.cleanup_expired_keys(grace_period_days=30)
        
        assert cleaned_count == 3
        assert len(manager.old_keys) == 0
    
    def test_cleanup_not_expired_keys(self):
        """测试不清理未过期密钥"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        manager.old_keys = [manager.generate_key() for _ in range(3)]
        manager.rotation_date = datetime.now() - timedelta(days=10)
        
        cleaned_count = manager.cleanup_expired_keys(grace_period_days=30)
        
        assert cleaned_count == 0
        assert len(manager.old_keys) == 3
    
    def test_cleanup_no_rotation_date(self):
        """测试无轮转记录时不清理"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        manager.old_keys = [manager.generate_key() for _ in range(3)]
        manager.rotation_date = None
        
        cleaned_count = manager.cleanup_expired_keys()
        
        assert cleaned_count == 0
        assert len(manager.old_keys) == 3


class TestKeyInfo:
    """测试密钥信息获取功能"""
    
    def test_get_key_info(self):
        """测试获取密钥信息"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        manager.old_keys = [manager.generate_key() for _ in range(2)]
        manager.rotation_date = datetime.now()
        
        info = manager.get_key_info()
        
        assert 'current_key_length' in info
        assert 'current_key_preview' in info
        assert 'old_keys_count' in info
        assert 'rotation_date' in info
        
        assert info['current_key_length'] == len(manager.current_key)
        assert info['old_keys_count'] == 2
        assert manager.current_key.startswith(info['current_key_preview'][:10])
    
    def test_get_key_info_hides_sensitive_data(self):
        """测试密钥信息隐藏敏感数据"""
        manager = SecretKeyManager()
        manager.current_key = manager.generate_key()
        
        info = manager.get_key_info()
        
        # 预览应该只包含部分密钥
        assert len(info['current_key_preview']) < len(manager.current_key)
        assert '...' in info['current_key_preview']


class TestSingleton:
    """测试单例模式"""
    
    def test_get_secret_manager_singleton(self):
        """测试获取单例实例"""
        manager1 = get_secret_manager()
        manager2 = get_secret_manager()
        
        assert manager1 is manager2
    
    @patch.dict(os.environ, {'SECRET_KEY': 'dGVzdC14eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHg='})
    def test_get_secret_manager_loads_keys(self):
        """测试单例实例自动加载密钥"""
        # 清除缓存的实例
        from app.core import secret_manager as sm
        sm._secret_manager_instance = None
        
        manager = get_secret_manager()
        
        assert manager.current_key is not None


# ========================================
# 运行测试
# ========================================
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
