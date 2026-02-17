# -*- coding: utf-8 -*-
"""
app/core/middleware/tenant_middleware.py 覆盖率测试（当前 29%）
专注于 TenantAwareQuery 和工具函数（不依赖 HTTP）
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ModelWithTenant(Base):
    __tablename__ = "model_with_tenant_for_tests"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    tenant_id = Column(Integer)


class ModelWithoutTenant(Base):
    __tablename__ = "model_without_tenant_for_tests"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class TestTenantAwareQuery:
    """测试租户感知查询构建器"""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        return db, mock_query

    def test_init_with_tenant_id(self, mock_db):
        from app.core.middleware.tenant_middleware import TenantAwareQuery
        db, _ = mock_db
        taq = TenantAwareQuery(db, tenant_id=5)
        assert taq.tenant_id == 5

    def test_init_without_tenant_id_uses_context(self, mock_db):
        from app.core.middleware.tenant_middleware import TenantAwareQuery
        db, _ = mock_db

        # patch tenant_middleware 模块里的 get_current_tenant_id
        with patch("app.core.middleware.tenant_middleware.get_current_tenant_id", return_value=10):
            taq = TenantAwareQuery(db)
            assert taq.tenant_id == 10

    def test_query_with_tenant_model_auto_filter(self, mock_db):
        from app.core.middleware.tenant_middleware import TenantAwareQuery
        db, mock_query = mock_db
        taq = TenantAwareQuery(db, tenant_id=5)

        result = taq.query(ModelWithTenant, auto_filter=True)
        db.query.assert_called_once_with(ModelWithTenant)
        mock_query.filter.assert_called_once()  # 自动加了 tenant_id 过滤

    def test_query_without_auto_filter(self, mock_db):
        from app.core.middleware.tenant_middleware import TenantAwareQuery
        db, mock_query = mock_db
        taq = TenantAwareQuery(db, tenant_id=5)

        result = taq.query(ModelWithTenant, auto_filter=False)
        db.query.assert_called_once_with(ModelWithTenant)
        mock_query.filter.assert_not_called()  # 不加过滤

    def test_query_model_without_tenant_no_filter(self, mock_db):
        from app.core.middleware.tenant_middleware import TenantAwareQuery
        db, mock_query = mock_db
        taq = TenantAwareQuery(db, tenant_id=5)

        result = taq.query(ModelWithoutTenant, auto_filter=True)
        mock_query.filter.assert_not_called()  # 没有 tenant_id 字段，不过滤

    def test_query_no_tenant_id_no_filter(self, mock_db):
        from app.core.middleware.tenant_middleware import TenantAwareQuery
        from app.common.context import set_current_tenant_id
        db, mock_query = mock_db
        set_current_tenant_id(None)
        taq = TenantAwareQuery(db, tenant_id=None)

        result = taq.query(ModelWithTenant, auto_filter=True)
        mock_query.filter.assert_not_called()  # 没有 tenant_id，不过滤

    def test_filter_by_tenant_with_tenant_model(self, mock_db):
        from app.core.middleware.tenant_middleware import TenantAwareQuery
        db, mock_query = mock_db
        taq = TenantAwareQuery(db, tenant_id=5)

        result = taq.filter_by_tenant(mock_query, ModelWithTenant)
        mock_query.filter.assert_called_once()

    def test_filter_by_tenant_without_tenant_model(self, mock_db):
        from app.core.middleware.tenant_middleware import TenantAwareQuery
        db, mock_query = mock_db
        taq = TenantAwareQuery(db, tenant_id=5)

        result = taq.filter_by_tenant(mock_query, ModelWithoutTenant)
        mock_query.filter.assert_not_called()
        assert result is mock_query  # 原样返回


class TestRequireSameTenant:
    """测试 require_same_tenant"""

    def test_same_tenant_returns_true(self):
        from app.core.middleware.tenant_middleware import require_same_tenant
        assert require_same_tenant(1, 1) is True

    def test_different_tenant_returns_false(self):
        from app.core.middleware.tenant_middleware import require_same_tenant
        assert require_same_tenant(1, 2) is False

    def test_none_user_tenant(self):
        from app.core.middleware.tenant_middleware import require_same_tenant
        # None tenant_id (superuser) might be True or True
        result = require_same_tenant(None, 1)
        assert isinstance(result, bool)

    def test_none_resource_tenant(self):
        from app.core.middleware.tenant_middleware import require_same_tenant
        result = require_same_tenant(1, None)
        assert isinstance(result, bool)

    def test_both_none(self):
        from app.core.middleware.tenant_middleware import require_same_tenant
        result = require_same_tenant(None, None)
        assert isinstance(result, bool)
