# -*- coding: utf-8 -*-
"""Tests for app/schemas/auth.py"""
import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    validate_password_strength,
    Token,
    TokenData,
    LoginRequest,
    UserCreate,
    UserUpdate,
    PasswordChange,
    UserResponse,
    PermissionResponse,
    UserRoleAssign,
    RoleTemplateCreate,
    RoleComparisonRequest,
    DataScopeRuleCreate,
    RoleWithFullPermissions,
)


class TestValidatePasswordStrength:
    def test_valid(self):
        assert validate_password_strength("Abcdef1x") == "Abcdef1x"

    def test_too_short(self):
        with pytest.raises(ValueError, match="至少8位"):
            validate_password_strength("Abc1x")

    def test_no_upper(self):
        with pytest.raises(ValueError, match="大写"):
            validate_password_strength("abcdefg1")

    def test_no_lower(self):
        with pytest.raises(ValueError, match="小写"):
            validate_password_strength("ABCDEFG1")

    def test_no_digit(self):
        with pytest.raises(ValueError, match="数字"):
            validate_password_strength("Abcdefgh")


class TestToken:
    def test_valid(self):
        t = Token(access_token="abc", expires_in=3600)
        assert t.token_type == "bearer"

    def test_missing(self):
        with pytest.raises(ValidationError):
            Token(expires_in=3600)


class TestTokenData:
    def test_defaults(self):
        t = TokenData()
        assert t.user_id is None


class TestLoginRequest:
    def test_valid(self):
        r = LoginRequest(username="admin", password="123456")
        assert r.username == "admin"

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="ab", password="123456")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="admin", password="12345")

    def test_missing(self):
        with pytest.raises(ValidationError):
            LoginRequest()


class TestUserCreate:
    def test_valid(self):
        u = UserCreate(username="testuser", password="123456")
        assert u.role_ids == []

    def test_username_min(self):
        with pytest.raises(ValidationError):
            UserCreate(username="ab", password="123456")


class TestUserUpdate:
    def test_all_none(self):
        u = UserUpdate()
        assert u.email is None

    def test_partial(self):
        u = UserUpdate(email="a@b.com", is_active=False)
        assert u.is_active is False


class TestPasswordChange:
    def test_valid(self):
        p = PasswordChange(old_password="123456", new_password="Abcdef1x")
        assert p.new_password == "Abcdef1x"

    def test_weak(self):
        with pytest.raises(ValidationError):
            PasswordChange(old_password="123456", new_password="weakpass")


class TestUserResponse:
    def test_valid(self):
        u = UserResponse(id=1, username="admin")
        assert u.is_active is True
        assert u.permissions == []


class TestRoleComparisonRequest:
    def test_valid(self):
        r = RoleComparisonRequest(role_ids=[1, 2])
        assert len(r.role_ids) == 2

    def test_too_few(self):
        with pytest.raises(ValidationError):
            RoleComparisonRequest(role_ids=[1])

    def test_too_many(self):
        with pytest.raises(ValidationError):
            RoleComparisonRequest(role_ids=[1, 2, 3, 4, 5, 6])


class TestRoleTemplateCreate:
    def test_valid(self):
        r = RoleTemplateCreate(template_code="T001", template_name="Admin")
        assert r.data_scope == "OWN"

    def test_missing(self):
        with pytest.raises(ValidationError):
            RoleTemplateCreate()


class TestDataScopeRuleCreate:
    def test_valid(self):
        d = DataScopeRuleCreate(role_id=1, rule_type="INCLUDE", target_type="DEPARTMENT", target_id=10)
        assert d.role_id == 1

    def test_missing(self):
        with pytest.raises(ValidationError):
            DataScopeRuleCreate()


class TestRoleWithFullPermissions:
    def test_valid(self):
        r = RoleWithFullPermissions(id=1, role_code="R001", role_name="Admin", data_scope="ALL")
        assert r.direct_permissions == []
        assert r.data_scope_rules == []
