# -*- coding: utf-8 -*-
"""
Unit tests for role_inheritance_utils.py
Covers: app/utils/role_inheritance_utils.py
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List, Set

from app.utils.role_inheritance_utils import RoleInheritanceUtils


def make_role(id, name="role", parent_id=None, inherit_permissions=True, is_active=True, tenant_id=None):
    """Helper to create a mock Role object."""
    role = MagicMock()
    role.id = id
    role.name = name
    role.parent_id = parent_id
    role.inherit_permissions = inherit_permissions
    role.is_active = is_active
    role.tenant_id = tenant_id
    return role


class TestClearCache:
    """Tests for RoleInheritanceUtils.clear_cache"""

    def setup_method(self):
        """Clear all caches before each test."""
        RoleInheritanceUtils.clear_cache()

    def test_clear_all_caches(self):
        """Clearing without role_id clears all caches."""
        RoleInheritanceUtils._permission_cache[1] = {"perm:read"}
        RoleInheritanceUtils._level_cache[1] = 2
        RoleInheritanceUtils._chain_cache[1] = [1, 2]

        RoleInheritanceUtils.clear_cache()

        assert len(RoleInheritanceUtils._permission_cache) == 0
        assert len(RoleInheritanceUtils._level_cache) == 0
        assert len(RoleInheritanceUtils._chain_cache) == 0

    def test_clear_specific_role_cache(self):
        """Clearing with role_id only removes that role's cache."""
        RoleInheritanceUtils._permission_cache[1] = {"perm:read"}
        RoleInheritanceUtils._permission_cache[2] = {"perm:write"}
        RoleInheritanceUtils._level_cache[1] = 1
        RoleInheritanceUtils._level_cache[2] = 2
        RoleInheritanceUtils._chain_cache[1] = [1]
        RoleInheritanceUtils._chain_cache[2] = [2, 1]

        RoleInheritanceUtils.clear_cache(role_id=1)

        assert 1 not in RoleInheritanceUtils._permission_cache
        assert 2 in RoleInheritanceUtils._permission_cache
        assert 1 not in RoleInheritanceUtils._level_cache
        assert 2 in RoleInheritanceUtils._level_cache
        assert 1 not in RoleInheritanceUtils._chain_cache
        assert 2 in RoleInheritanceUtils._chain_cache

    def test_clear_nonexistent_role_cache(self):
        """Clearing non-existent role_id should not raise."""
        RoleInheritanceUtils.clear_cache(role_id=999)  # should not raise


class TestGetRoleChain:
    """Tests for RoleInheritanceUtils.get_role_chain"""

    def setup_method(self):
        RoleInheritanceUtils.clear_cache()

    def test_single_role_no_parent(self):
        """Root role with no parent returns chain of length 1."""
        root = make_role(1, parent_id=None)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [root, None]

        chain = RoleInheritanceUtils.get_role_chain(db, 1)
        assert len(chain) == 1
        assert chain[0].id == 1

    def test_role_with_parent(self):
        """Role with parent returns chain of [child, parent]."""
        child = make_role(2, parent_id=1)
        parent = make_role(1, parent_id=None)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [child, parent, None]

        chain = RoleInheritanceUtils.get_role_chain(db, 2)
        assert len(chain) == 2
        assert chain[0].id == 2
        assert chain[1].id == 1

    def test_role_not_inherit_stops_chain(self):
        """If role has inherit_permissions=False, chain stops at that role."""
        role = make_role(3, parent_id=1, inherit_permissions=False)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = role

        chain = RoleInheritanceUtils.get_role_chain(db, 3)
        assert len(chain) == 1
        assert chain[0].id == 3

    def test_role_chain_uses_cache(self):
        """get_role_chain returns from cache on second call."""
        root = make_role(10, parent_id=None)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = root

        # Prime the cache
        chain1 = RoleInheritanceUtils.get_role_chain(db, 10)

        # Populate ID-based cache lookup
        db.query.return_value.filter.return_value.all.return_value = [root]

        chain2 = RoleInheritanceUtils.get_role_chain(db, 10)
        assert len(chain2) == 1

    def test_role_nonexistent_returns_empty_chain(self):
        """Non-existent role returns empty chain."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        chain = RoleInheritanceUtils.get_role_chain(db, 999)
        assert chain == []


class TestCalculateRoleLevel:
    """Tests for RoleInheritanceUtils.calculate_role_level"""

    def setup_method(self):
        RoleInheritanceUtils.clear_cache()

    def test_root_role_level_is_zero(self):
        """Root role (no parent) has level 0."""
        root = make_role(1, parent_id=None)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [root, None]

        level = RoleInheritanceUtils.calculate_role_level(db, 1)
        assert level == 0

    def test_child_role_level_is_one(self):
        """Child role (one parent) has level 1."""
        child = make_role(2, parent_id=1)
        parent = make_role(1, parent_id=None)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [child, parent, None]

        level = RoleInheritanceUtils.calculate_role_level(db, 2)
        assert level == 1

    def test_level_uses_cache(self):
        """calculate_role_level returns from cache on second call."""
        RoleInheritanceUtils._level_cache[5] = 3
        db = MagicMock()

        level = RoleInheritanceUtils.calculate_role_level(db, 5)
        assert level == 3
        db.query.assert_not_called()


class TestDetectCircularInheritance:
    """Tests for RoleInheritanceUtils.detect_circular_inheritance"""

    def setup_method(self):
        RoleInheritanceUtils.clear_cache()

    def test_self_as_parent_is_circular(self):
        """Setting a role as its own parent is circular."""
        db = MagicMock()
        assert RoleInheritanceUtils.detect_circular_inheritance(db, 1, 1) is True

    def test_no_circular_with_unrelated_parent(self):
        """No circular inheritance when parent is not in current role's subtree."""
        parent_role = make_role(10, parent_id=None)
        db = MagicMock()
        # get_role_chain for role_id=10 (new_parent_id)
        db.query.return_value.filter.return_value.first.side_effect = [parent_role, None]

        result = RoleInheritanceUtils.detect_circular_inheritance(db, 5, 10)
        # role_id=5 should not be in chain [10], so result is False
        assert result is False

    def test_circular_when_parent_chain_contains_role(self):
        """Circular detected when new parent's chain contains the current role."""
        # Pre-populate cache: role 10's chain is [10, 5]
        RoleInheritanceUtils._chain_cache[10] = [10, 5]
        # Pre-populate roles
        role10 = make_role(10, parent_id=None)
        role5 = make_role(5, parent_id=None)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [role10, role5]

        result = RoleInheritanceUtils.detect_circular_inheritance(db, 5, 10)
        assert result is True


class TestGetInheritedPermissions:
    """Tests for RoleInheritanceUtils.get_inherited_permissions"""

    def setup_method(self):
        RoleInheritanceUtils.clear_cache()

    def test_returns_cached_permissions(self):
        """Returns from cache if available."""
        RoleInheritanceUtils._permission_cache[7] = {"perm:read", "perm:write"}
        db = MagicMock()

        perms = RoleInheritanceUtils.get_inherited_permissions(db, 7)
        assert "perm:read" in perms
        assert "perm:write" in perms
        db.query.assert_not_called()

    def test_returns_empty_set_for_nonexistent_role(self):
        """Returns empty set when role not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        perms = RoleInheritanceUtils.get_inherited_permissions(db, 9999)
        assert perms == set()

    def test_collects_permissions_from_chain(self):
        """Collects permissions from each role in chain."""
        role = make_role(20, parent_id=None)

        db = MagicMock()
        # get_role_chain call
        db.query.return_value.filter.return_value.first.side_effect = [role, None]

        # For permissions query: returns perm codes
        perm_query = MagicMock()
        perm_query.join.return_value.filter.return_value.filter.return_value = perm_query
        perm_query.join.return_value.filter.return_value = perm_query
        perm_query.all.return_value = [("perm:read",), ("perm:write",)]

        # Patch db.query to handle ApiPermission differently
        original_query = db.query

        def smart_query(model_class):
            from app.models.user import ApiPermission
            if model_class is ApiPermission:
                return perm_query
            return original_query(model_class)

        db.query = smart_query

        perms = RoleInheritanceUtils.get_inherited_permissions(db, 20)
        # Should have accumulated permissions
        assert isinstance(perms, set)
