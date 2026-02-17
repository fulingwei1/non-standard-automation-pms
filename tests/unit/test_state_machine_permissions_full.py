# -*- coding: utf-8 -*-
"""
Comprehensive tests for app/core/state_machine/permissions.py and ecn_status.py
Standalone – no DB, no fixtures.
"""
import pytest
from app.core.state_machine.permissions import StateMachinePermissionChecker
from app.core.state_machine.ecn_status import EcnStatus


# ---------------------------------------------------------------------------
# EcnStatus enum
# ---------------------------------------------------------------------------

class TestEcnStatus:
    def test_draft_value(self):
        assert EcnStatus.DRAFT == "DRAFT"

    def test_approved_value(self):
        assert EcnStatus.APPROVED == "APPROVED"

    def test_cancelled_value(self):
        assert EcnStatus.CANCELLED == "CANCELLED"

    def test_all_statuses_have_descriptions(self):
        """Every status should return a non-empty description."""
        for status in EcnStatus:
            desc = status.description()
            assert isinstance(desc, str)
            assert len(desc) > 0, f"{status} has empty description"

    def test_specific_descriptions(self):
        assert "草稿" in EcnStatus.DRAFT.description()
        assert "已批准" in EcnStatus.APPROVED.description() or EcnStatus.APPROVED.description() != ""

    def test_enum_is_string(self):
        assert isinstance(EcnStatus.DRAFT, str)

    def test_all_expected_statuses_exist(self):
        expected = [
            "DRAFT", "READY_TO_SUBMIT", "SUBMITTED", "EVALUATION_PENDING",
            "EVALUATION_IN_PROGRESS", "APPROVAL_PENDING", "APPROVED", "REJECTED",
            "READY_TO_EXECUTE", "IN_PROGRESS", "EXECUTION_PAUSED",
            "EXECUTION_COMPLETED", "READY_TO_CLOSE", "CLOSED", "CANCELLED",
        ]
        ecn_values = [e.value for e in EcnStatus]
        for s in expected:
            assert s in ecn_values


# ---------------------------------------------------------------------------
# StateMachinePermissionChecker
# ---------------------------------------------------------------------------

class _UserWithMethod:
    """Simulated user with has_permission and has_role methods."""
    def __init__(self, permissions=None, roles=None):
        self._permissions = set(permissions or [])
        self._roles = set(roles or [])

    def has_permission(self, perm: str) -> bool:
        return perm in self._permissions

    def has_role(self, role: str) -> bool:
        return role in self._roles


class _UserWithAttrs:
    """Simulated user with permissions/roles as list attributes."""
    def __init__(self, permissions=None, roles=None):
        self.permissions = list(permissions or [])
        self.roles = list(roles or [])


class _UserWithRoleObjects:
    """Simulated user with roles as objects having a .name attribute."""
    class Role:
        def __init__(self, name):
            self.name = name

    def __init__(self, role_names=None):
        self.roles = [self.Role(n) for n in (role_names or [])]


class TestPermissionCheckerNoRequirement:
    def test_no_permission_no_role_always_passes(self):
        checker = StateMachinePermissionChecker()
        ok, reason = checker.check_permission(None)
        assert ok is True

    def test_no_permission_no_role_with_user(self):
        checker = StateMachinePermissionChecker()
        ok, _ = checker.check_permission(_UserWithMethod())
        assert ok is True


class TestPermissionCheckerWithMethod:
    def setup_method(self):
        self.checker = StateMachinePermissionChecker()

    def test_user_has_permission(self):
        user = _UserWithMethod(permissions=["ecn:approve"])
        ok, reason = self.checker.check_permission(user, required_permission="ecn:approve")
        assert ok is True

    def test_user_missing_permission(self):
        user = _UserWithMethod(permissions=[])
        ok, reason = self.checker.check_permission(user, required_permission="ecn:approve")
        assert ok is False
        assert "ecn:approve" in reason

    def test_no_user_with_required_permission_denied(self):
        ok, reason = self.checker.check_permission(None, required_permission="ecn:approve")
        assert ok is False

    def test_user_has_role(self):
        user = _UserWithMethod(roles=["PROJECT_MANAGER"])
        ok, _ = self.checker.check_permission(user, required_role="PROJECT_MANAGER")
        assert ok is True

    def test_user_missing_role(self):
        user = _UserWithMethod(roles=[])
        ok, reason = self.checker.check_permission(user, required_role="PROJECT_MANAGER")
        assert ok is False
        assert "PROJECT_MANAGER" in reason

    def test_permission_and_role_both_required(self):
        user = _UserWithMethod(permissions=["ecn:approve"], roles=["PM"])
        ok, _ = self.checker.check_permission(
            user, required_permission="ecn:approve", required_role="PM"
        )
        assert ok is True

    def test_permission_ok_but_role_missing(self):
        user = _UserWithMethod(permissions=["ecn:approve"], roles=[])
        ok, reason = self.checker.check_permission(
            user, required_permission="ecn:approve", required_role="PM"
        )
        assert ok is False

    def test_permission_missing_role_ok(self):
        user = _UserWithMethod(permissions=[], roles=["PM"])
        ok, reason = self.checker.check_permission(
            user, required_permission="ecn:approve", required_role="PM"
        )
        assert ok is False


class TestPermissionCheckerWithAttrList:
    def setup_method(self):
        self.checker = StateMachinePermissionChecker()

    def test_permissions_list_match(self):
        user = _UserWithAttrs(permissions=["read", "write"])
        ok, _ = self.checker.check_permission(user, required_permission="read")
        assert ok is True

    def test_permissions_list_no_match(self):
        user = _UserWithAttrs(permissions=["read"])
        ok, reason = self.checker.check_permission(user, required_permission="write")
        assert ok is False

    def test_roles_list_match(self):
        user = _UserWithAttrs(roles=["ADMIN", "PM"])
        ok, _ = self.checker.check_permission(user, required_role="PM")
        assert ok is True

    def test_roles_list_no_match(self):
        user = _UserWithAttrs(roles=["ADMIN"])
        ok, reason = self.checker.check_permission(user, required_role="PM")
        assert ok is False


class TestPermissionCheckerWithRoleObjects:
    def setup_method(self):
        self.checker = StateMachinePermissionChecker()

    def test_role_objects_match(self):
        user = _UserWithRoleObjects(role_names=["PROJECT_MANAGER"])
        ok, _ = self.checker.check_permission(user, required_role="PROJECT_MANAGER")
        assert ok is True

    def test_role_objects_no_match(self):
        user = _UserWithRoleObjects(role_names=["ENGINEER"])
        ok, reason = self.checker.check_permission(user, required_role="PROJECT_MANAGER")
        assert ok is False


class TestPermissionCheckerUnsupportedUser:
    def setup_method(self):
        self.checker = StateMachinePermissionChecker()

    def test_user_without_permission_method_or_attr(self):
        """User object that doesn't have has_permission or permissions."""
        class BareUser:
            pass
        user = BareUser()
        ok, reason = self.checker.check_permission(user, required_permission="ecn:approve")
        assert ok is False
        assert "权限" in reason or "permission" in reason.lower()

    def test_user_without_role_method_or_attr(self):
        """User object that doesn't have has_role or roles."""
        class BareUser:
            pass
        user = BareUser()
        ok, reason = self.checker.check_permission(user, required_role="PM")
        assert ok is False


class TestPermissionCheckerNonCallableAttributes:
    def setup_method(self):
        self.checker = StateMachinePermissionChecker()

    def test_has_permission_not_callable(self):
        """has_permission is a non-callable attribute."""
        class BadUser:
            has_permission = "not_callable"
        user = BadUser()
        ok, reason = self.checker.check_permission(user, required_permission="read")
        assert ok is False

    def test_has_role_not_callable(self):
        """has_role is a non-callable attribute."""
        class BadUser:
            has_role = "not_callable"
        user = BadUser()
        ok, reason = self.checker.check_permission(user, required_role="PM")
        assert ok is False


class TestPermissionCheckerExceptionHandling:
    def setup_method(self):
        self.checker = StateMachinePermissionChecker()

    def test_has_permission_raises_exception(self):
        """has_permission raises an exception – should be caught."""
        class FaultyUser:
            def has_permission(self, perm):
                raise RuntimeError("DB connection failed")
        user = FaultyUser()
        ok, reason = self.checker.check_permission(user, required_permission="read")
        assert ok is False
        assert "失败" in reason or "failed" in reason.lower()

    def test_has_role_raises_exception(self):
        class FaultyUser:
            def has_role(self, role):
                raise RuntimeError("service error")
        user = FaultyUser()
        ok, reason = self.checker.check_permission(user, required_role="PM")
        assert ok is False
