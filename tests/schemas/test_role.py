# -*- coding: utf-8 -*-
"""Tests for app/schemas/role.py"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
)


class TestRoleBase:
    def test_valid(self):
        r = RoleBase(role_code="ADMIN", role_name="管理员")
        assert r.data_scope == "OWN"

    def test_missing_code(self):
        with pytest.raises(ValidationError):
            RoleBase(role_name="Admin")

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            RoleBase(role_code="ADMIN")

    def test_empty_code(self):
        with pytest.raises(ValidationError):
            RoleBase(role_code="", role_name="Admin")

    def test_long_code(self):
        with pytest.raises(ValidationError):
            RoleBase(role_code="x" * 51, role_name="Admin")

    def test_long_name(self):
        with pytest.raises(ValidationError):
            RoleBase(role_code="A", role_name="x" * 101)

    def test_custom_data_scope(self):
        r = RoleBase(role_code="A", role_name="B", data_scope="ALL")
        assert r.data_scope == "ALL"


class TestRoleCreate:
    def test_valid(self):
        r = RoleCreate(role_code="PM", role_name="项目经理")
        assert r.parent_id is None
        assert r.permission_ids == []
        assert r.sort_order == 0

    def test_with_parent(self):
        r = RoleCreate(role_code="PM", role_name="PM", parent_id=1, permission_ids=[1, 2])
        assert r.parent_id == 1

    def test_with_nav_groups(self):
        r = RoleCreate(role_code="A", role_name="B", nav_groups=[{"name": "g1"}])
        assert len(r.nav_groups) == 1


class TestRoleUpdate:
    def test_all_none(self):
        r = RoleUpdate()
        assert r.role_code is None

    def test_partial(self):
        r = RoleUpdate(role_name="新名称", is_active=False)
        assert r.role_name == "新名称"

    def test_empty_code(self):
        with pytest.raises(ValidationError):
            RoleUpdate(role_code="")


class TestRoleResponse:
    def test_valid(self):
        r = RoleResponse(
            id=1, role_code="ADMIN", role_name="Admin",
            data_scope="ALL", created_at=datetime.now(),
        )
        assert r.is_system is False
        assert r.is_active is True
        assert r.permissions == []
        assert r.permission_count == 0

    def test_full(self):
        r = RoleResponse(
            id=1, role_code="A", role_name="B", data_scope="OWN",
            created_at=datetime.now(), tenant_id=1,
            parent_id=2, parent_name="Parent",
            permissions=["p1"], permission_count=1,
            inherited_permission_count=3,
        )
        assert r.inherited_permission_count == 3
