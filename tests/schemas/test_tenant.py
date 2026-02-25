# -*- coding: utf-8 -*-
"""Tests for app/schemas/tenant.py"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.tenant import (
    TenantBase,
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantInitRequest,
    TenantStatsResponse,
    RoleTemplateBase,
    RoleTemplateResponse,
)


class TestTenantBase:
    def test_valid(self):
        t = TenantBase(tenant_name="Test Corp")
        assert t.plan_type == "FREE"

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            TenantBase(tenant_name="")

    def test_long_name(self):
        with pytest.raises(ValidationError):
            TenantBase(tenant_name="x" * 201)


class TestTenantCreate:
    def test_valid(self):
        t = TenantCreate(tenant_name="New")
        assert t.tenant_code is None

    def test_max_users_ge_1(self):
        with pytest.raises(ValidationError):
            TenantCreate(tenant_name="T", max_users=0)


class TestTenantUpdate:
    def test_all_none(self):
        t = TenantUpdate()
        assert t.tenant_name is None

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            TenantUpdate(tenant_name="")


class TestTenantResponse:
    def test_valid(self):
        t = TenantResponse(
            id=1, tenant_code="T001", tenant_name="Corp",
            status="ACTIVE", max_users=100, max_roles=20,
            max_storage_gb=10, created_at=datetime.now(),
        )
        assert t.user_count is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            TenantResponse(id=1)


class TestTenantInitRequest:
    def test_valid(self):
        r = TenantInitRequest(admin_username="admin", admin_password="123456", admin_email="a@b.com")
        assert r.copy_role_templates is True

    def test_short_username(self):
        with pytest.raises(ValidationError):
            TenantInitRequest(admin_username="ab", admin_password="123456", admin_email="a@b.com")

    def test_missing(self):
        with pytest.raises(ValidationError):
            TenantInitRequest()


class TestTenantStatsResponse:
    def test_valid(self):
        s = TenantStatsResponse(
            tenant_id=1, tenant_code="T001",
            user_count=10, role_count=5, project_count=3,
            storage_used_mb=100.5, plan_limits={},
        )
        assert s.storage_used_mb == 100.5


class TestRoleTemplateBase:
    def test_valid(self):
        r = RoleTemplateBase(role_code="R001", role_name="Admin")
        assert r.data_scope == "OWN"

    def test_missing(self):
        with pytest.raises(ValidationError):
            RoleTemplateBase()

    def test_empty_code(self):
        with pytest.raises(ValidationError):
            RoleTemplateBase(role_code="", role_name="Admin")


class TestRoleTemplateResponse:
    def test_valid(self):
        r = RoleTemplateResponse(
            id=1, role_code="R001", role_name="Admin",
            is_active=True, created_at=datetime.now(),
        )
        assert r.is_active is True
