# -*- coding: utf-8 -*-
"""第四十六批 - 租户服务单元测试"""
import pytest

pytest.importorskip("app.services.tenant_service",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.tenant_service import TenantService


def _make_db():
    return MagicMock()


def _make_tenant(tid=1, code="T12345678"):
    t = MagicMock()
    t.id = tid
    t.tenant_code = code
    t.tenant_name = "测试公司"
    t.get_plan_limits.return_value = {"users": 5}
    return t


class TestGenerateTenantCode:
    def test_returns_t_prefixed_code(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None  # no duplicate
        svc = TenantService(db)
        code = svc.generate_tenant_code()
        assert code.startswith("T")
        assert len(code) == 9  # T + 8 hex chars

    def test_retries_on_duplicate(self):
        db = _make_db()
        existing = MagicMock()
        # first call returns existing, second returns None
        db.query.return_value.filter.return_value.first.side_effect = [existing, None]
        svc = TenantService(db)
        code = svc.generate_tenant_code()
        assert code.startswith("T")


class TestGetTenant:
    def test_returns_tenant_when_found(self):
        db = _make_db()
        tenant = _make_tenant()
        db.query.return_value.filter.return_value.first.return_value = tenant
        svc = TenantService(db)
        result = svc.get_tenant(1)
        assert result is tenant

    def test_returns_none_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = TenantService(db)
        result = svc.get_tenant(99)
        assert result is None


class TestGetTenantByCode:
    def test_returns_tenant_by_code(self):
        db = _make_db()
        tenant = _make_tenant()
        db.query.return_value.filter.return_value.first.return_value = tenant
        svc = TenantService(db)
        result = svc.get_tenant_by_code("T12345678")
        assert result is tenant


class TestCreateTenant:
    def test_raises_on_duplicate_code(self):
        db = _make_db()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        svc = TenantService(db)
        tenant_in = MagicMock()
        tenant_in.tenant_code = "TDUP"
        tenant_in.tenant_name = "重复公司"
        tenant_in.plan_type = "FREE"
        tenant_in.max_users = None
        tenant_in.max_roles = None

        with pytest.raises(ValueError, match="已存在"):
            svc.create_tenant(tenant_in)

    def test_creates_when_code_unique(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        svc = TenantService(db)
        tenant_in = MagicMock()
        tenant_in.tenant_code = "TNEW"
        tenant_in.tenant_name = "新公司"
        tenant_in.plan_type = "FREE"
        tenant_in.max_users = None
        tenant_in.max_roles = None
        tenant_in.contact_name = "张三"
        tenant_in.contact_email = "admin@test.com"
        tenant_in.contact_phone = None
        tenant_in.settings = {}
        tenant_in.expired_at = None

        with patch("app.services.tenant_service.save_obj"):
            result = svc.create_tenant(tenant_in)


class TestDeleteTenant:
    def test_returns_false_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = TenantService(db)
        assert svc.delete_tenant(99) is False

    def test_soft_deletes_tenant(self):
        db = _make_db()
        tenant = _make_tenant()
        db.query.return_value.filter.return_value.first.return_value = tenant
        svc = TenantService(db)
        result = svc.delete_tenant(1)
        assert result is True
        db.commit.assert_called_once()


class TestGetTenantStats:
    def test_returns_none_when_tenant_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = TenantService(db)
        result = svc.get_tenant_stats(99)
        assert result is None

    def test_returns_stats_dict_when_found(self):
        db = _make_db()
        tenant = _make_tenant()
        db.query.return_value.filter.return_value.first.return_value = tenant
        db.query.return_value.filter.return_value.scalar.return_value = 3
        svc = TenantService(db)

        with patch("app.services.tenant_service.func"):
            result = svc.get_tenant_stats(1)

        assert result is not None
        assert "tenant_id" in result
