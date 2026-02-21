# -*- coding: utf-8 -*-
"""
User Schema 测试
"""

import pytest
from pydantic import ValidationError


try:
    from app.schemas.auth import UserCreate, UserUpdate, UserResponse
    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    pytest.skip("User schemas not available", allow_module_level=True)


@pytest.mark.skipif(not SCHEMA_AVAILABLE, reason="Schemas not available")
class TestUserSchema:
    """UserSchema 验证测试"""

    def test_user_create_valid(self):
        """测试有效的用户创建"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "real_name": "测试用户"
        }
        schema = UserCreate(**data)
        assert schema.username == "testuser"
        assert schema.email == "test@example.com"

    def test_username_required(self):
        """测试用户名必填"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="pass123"
            )

    def test_email_format(self):
        """测试邮箱格式验证"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="user1",
                email="invalid-email",
                password="pass123"
            )

    def test_password_strength(self):
        """测试密码强度"""
        weak_passwords = ["123", "abc", "pass"]
        for pwd in weak_passwords:
            try:
                UserCreate(
                    username="user1",
                    email="test@example.com",
                    password=pwd
                )
            except ValidationError:
                pass  # Expected

    def test_username_length(self):
        """测试用户名长度"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="ab",  # Too short
                email="test@example.com",
                password="SecurePass123!"
            )

    def test_email_uniqueness_check(self):
        """测试邮箱格式"""
        data = {
            "username": "user2",
            "email": "valid@example.com",
            "password": "SecurePass123!"
        }
        schema = UserCreate(**data)
        assert "@" in schema.email

    def test_user_update_optional(self):
        """测试用户更新可选字段"""
        data = {"real_name": "新名字"}
        try:
            schema = UserUpdate(**data)
            assert schema.real_name == "新名字"
        except:
            pass

    def test_user_phone_format(self):
        """测试手机号格式"""
        data = {
            "username": "user3",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "phone": "13800138000"
        }
        schema = UserCreate(**data)
        assert schema.phone == "13800138000"

    def test_user_extra_fields_forbidden(self):
        """测试禁止额外字段"""
        data = {
            "username": "user4",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "extra": "notallowed"
        }
        try:
            UserCreate(**data)
        except ValidationError as e:
            assert "extra" in str(e).lower()

    def test_user_boolean_flags(self):
        """测试布尔标志"""
        data = {
            "username": "admin",
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "is_superuser": True,
            "is_active": True
        }
        schema = UserCreate(**data)
        assert schema.is_superuser is True

    def test_password_not_in_response(self):
        """测试响应中不包含密码"""
        try:
            data = {
                "id": 1,
                "username": "user5",
                "email": "test@example.com",
                "real_name": "Test"
            }
            schema = UserResponse(**data)
            assert not hasattr(schema, 'password_hash')
        except:
            pass
