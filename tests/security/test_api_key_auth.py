# -*- coding: utf-8 -*-
"""
API Key认证测试
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.api_key_auth import APIKeyAuth
from app.models.api_key import APIKey


class TestAPIKeyAuth:
    """API Key认证测试"""

    # ============================================
    # 1. API Key生成测试
    # ============================================

    def test_generate_api_key_format(self):
        """测试：生成的API Key格式正确"""
        api_key, key_hash = APIKeyAuth.generate_api_key(prefix="test")
        
        # 检查格式
        assert api_key.startswith("test_")
        assert len(api_key) > 10
        
        # 检查哈希
        assert len(key_hash) == 64  # SHA256哈希长度

    def test_generate_api_key_unique(self):
        """测试：每次生成的API Key都不同"""
        key1, _ = APIKeyAuth.generate_api_key()
        key2, _ = APIKeyAuth.generate_api_key()
        
        assert key1 != key2

    def test_api_key_hash_consistency(self):
        """测试：相同的API Key哈希结果一致"""
        api_key = "test_api_key_123"
        
        hash1 = APIKeyAuth.hash_api_key(api_key)
        hash2 = APIKeyAuth.hash_api_key(api_key)
        
        assert hash1 == hash2

    def test_different_api_key_different_hash(self):
        """测试：不同的API Key哈希结果不同"""
        key1 = "test_api_key_1"
        key2 = "test_api_key_2"
        
        hash1 = APIKeyAuth.hash_api_key(key1)
        hash2 = APIKeyAuth.hash_api_key(key2)
        
        assert hash1 != hash2

    # ============================================
    # 2. API Key验证测试
    # ============================================

    def test_verify_valid_api_key(self, db: Session, test_user):
        """测试：验证有效的API Key"""
        # 生成API Key
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        # 存储到数据库
        api_key_obj = APIKey(
            name="Test API Key",
            key_hash=key_hash,
            key_prefix="pms",
            user_id=test_user.id,
            tenant_id=test_user.tenant_id,
            is_active=True,
            scopes=["projects:read", "projects:write"]
        )
        db.add(api_key_obj)
        db.commit()
        
        # 验证
        result = APIKeyAuth.verify_api_key(db, api_key)
        
        assert result is not None
        assert result["name"] == "Test API Key"
        assert result["user_id"] == test_user.id
        assert "projects:read" in result["scopes"]

    def test_verify_invalid_api_key(self, db: Session):
        """测试：验证无效的API Key"""
        result = APIKeyAuth.verify_api_key(db, "invalid_api_key")
        assert result is None

    def test_verify_disabled_api_key(self, db: Session, test_user):
        """测试：已禁用的API Key不能通过验证"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        api_key_obj = APIKey(
            name="Disabled Key",
            key_hash=key_hash,
            user_id=test_user.id,
            is_active=False  # 已禁用
        )
        db.add(api_key_obj)
        db.commit()
        
        result = APIKeyAuth.verify_api_key(db, api_key)
        assert result is None

    def test_verify_expired_api_key(self, db: Session, test_user):
        """测试：过期的API Key不能通过验证"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        api_key_obj = APIKey(
            name="Expired Key",
            key_hash=key_hash,
            user_id=test_user.id,
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1)  # 昨天过期
        )
        db.add(api_key_obj)
        db.commit()
        
        result = APIKeyAuth.verify_api_key(db, api_key)
        assert result is None

    def test_verify_api_key_ip_whitelist_allowed(self, db: Session, test_user):
        """测试：IP白名单 - 允许的IP"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        api_key_obj = APIKey(
            name="IP Restricted Key",
            key_hash=key_hash,
            user_id=test_user.id,
            is_active=True,
            allowed_ips=["192.168.1.100", "10.0.0.1"]
        )
        db.add(api_key_obj)
        db.commit()
        
        result = APIKeyAuth.verify_api_key(db, api_key, client_ip="192.168.1.100")
        assert result is not None

    def test_verify_api_key_ip_whitelist_denied(self, db: Session, test_user):
        """测试：IP白名单 - 拒绝的IP"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        api_key_obj = APIKey(
            name="IP Restricted Key",
            key_hash=key_hash,
            user_id=test_user.id,
            is_active=True,
            allowed_ips=["192.168.1.100"]
        )
        db.add(api_key_obj)
        db.commit()
        
        result = APIKeyAuth.verify_api_key(db, api_key, client_ip="10.0.0.1")
        assert result is None

    def test_verify_api_key_updates_usage(self, db: Session, test_user):
        """测试：验证API Key时更新使用统计"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        api_key_obj = APIKey(
            name="Usage Test Key",
            key_hash=key_hash,
            user_id=test_user.id,
            is_active=True,
            usage_count=0
        )
        db.add(api_key_obj)
        db.commit()
        initial_id = api_key_obj.id
        
        # 第一次验证
        APIKeyAuth.verify_api_key(db, api_key)
        
        # 刷新对象
        db.refresh(api_key_obj)
        
        # 检查使用次数和最后使用时间
        assert api_key_obj.usage_count == 1
        assert api_key_obj.last_used_at is not None

    # ============================================
    # 3. 权限范围测试
    # ============================================

    def test_api_key_scopes(self, db: Session, test_user):
        """测试：API Key权限范围"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        scopes = ["projects:read", "users:read"]
        api_key_obj = APIKey(
            name="Scoped Key",
            key_hash=key_hash,
            user_id=test_user.id,
            is_active=True,
            scopes=scopes
        )
        db.add(api_key_obj)
        db.commit()
        
        result = APIKeyAuth.verify_api_key(db, api_key)
        
        assert result["scopes"] == scopes

    def test_api_key_no_scopes(self, db: Session, test_user):
        """测试：没有权限范围的API Key"""
        api_key, key_hash = APIKeyAuth.generate_api_key()
        
        api_key_obj = APIKey(
            name="No Scopes Key",
            key_hash=key_hash,
            user_id=test_user.id,
            is_active=True,
            scopes=None
        )
        db.add(api_key_obj)
        db.commit()
        
        result = APIKeyAuth.verify_api_key(db, api_key)
        
        assert result["scopes"] == []

    # ============================================
    # Fixtures
    # ============================================

    @pytest.fixture
    def db(self):
        """数据库会话（模拟）"""
        from app.core.database import SessionLocal
        session = SessionLocal()
        try:
            yield session
        finally:
            session.rollback()
            session.close()

    @pytest.fixture
    def test_user(self, db: Session):
        """测试用户"""
        from app.models.user import User
        
        user = User(
            username="test_api_user",
            email="test@example.com",
            tenant_id=1,
            is_active=True,
        password_hash="test_hash_123"
    )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        yield user
        
        # 清理
        db.delete(user)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
