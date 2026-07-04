# -*- coding: utf-8 -*-
"""TEN-01: tenant management API must expose real routes."""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints import tenants
from app.models.tenant import TenantStatus
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantUpdate


def _super_admin(db: Session) -> User:
    suffix = uuid4().hex[:8]
    user = User(
        username=f"ten01-admin-{suffix}",
        password_hash="test",
        real_name="TEN01 Admin",
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.flush()
    return user


def _normal_user(db: Session) -> User:
    suffix = uuid4().hex[:8]
    user = User(
        username=f"ten01-user-{suffix}",
        password_hash="test",
        real_name="TEN01 User",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    return user


def test_tenant_router_exposes_real_management_routes():
    routes = {
        (route.path, tuple(sorted(route.methods or [])))
        for route in tenants.router.routes
        if hasattr(route, "methods")
    }

    assert ("/tenants/", ("GET",)) in routes
    assert ("/tenants/", ("POST",)) in routes
    assert ("/tenants/{tenant_id}", ("GET",)) in routes
    assert ("/tenants/{tenant_id}", ("PUT",)) in routes
    assert ("/tenants/{tenant_id}/stats", ("GET",)) in routes


def test_tenant_management_endpoints_call_tenant_service(db_session: Session):
    admin = _super_admin(db_session)
    suffix = uuid4().hex[:8]

    created = tenants.create_tenant(
        tenant_in=TenantCreate(
            tenant_code=f"TEN01-{suffix}",
            tenant_name=f"TEN01 租户 {suffix}",
            plan_type="STANDARD",
            contact_name="符哥",
            contact_email=f"ten01-{suffix}@example.com",
        ),
        db=db_session,
        current_user=admin,
    )

    assert created.id is not None
    assert created.tenant_code == f"TEN01-{suffix}"
    assert created.tenant_name == f"TEN01 租户 {suffix}"

    listing = tenants.list_tenants(
        db=db_session,
        page=1,
        page_size=20,
        status=None,
        keyword=suffix,
        current_user=admin,
    )
    assert listing.total == 1
    assert listing.items[0].id == created.id

    detail = tenants.get_tenant(
        tenant_id=created.id,
        db=db_session,
        current_user=admin,
    )
    assert detail.id == created.id

    updated = tenants.update_tenant(
        tenant_id=created.id,
        tenant_in=TenantUpdate(contact_name="更新联系人"),
        db=db_session,
        current_user=admin,
    )
    assert updated.contact_name == "更新联系人"

    stats = tenants.get_tenant_stats(
        tenant_id=created.id,
        db=db_session,
        current_user=admin,
    )
    assert stats.tenant_id == created.id
    assert stats.user_count == 0
    assert stats.role_count == 0


def test_tenant_management_requires_super_admin(db_session: Session):
    user = _normal_user(db_session)

    with pytest.raises(HTTPException) as exc_info:
        tenants.list_tenants(
            db=db_session,
            page=1,
            page_size=20,
            status=None,
            keyword=None,
            current_user=user,
        )
    assert exc_info.value.status_code == 403
