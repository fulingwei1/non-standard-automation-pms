# -*- coding: utf-8 -*-
"""
Tests for permission_service
"""

from sqlalchemy.orm import Session

from app.models.user import User, Role, UserRole
from app.services.permission_service import PermissionService


def test_superuser_always_has_permission(db_session: Session):
    """Superuser always returns True regardless of permissions."""
    user = User(username="admin", is_superuser=True)
    db_session.add(user)
    db_session.flush()

    has_perm = PermissionService.check_permission(
        db_session, user.id, "any:permission", user
    )

    assert has_perm is True


def test_user_has_direct_roles(db_session: Session):
    """User with direct assigned roles only."""
    user = User(username="testuser", is_superuser=False)
    db_session.add(user)
    db_session.flush()

    role1 = Role(role_code="ROLE1", role_name="Role One", is_active=True)
    role2 = Role(role_code="ROLE2", role_name="Role Two", is_active=True)
    db_session.add_all([role1, role2])
    db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=role1.id))
    db_session.add(UserRole(user_id=user.id, role_id=role2.id))
    db_session.flush()

    roles = PermissionService.get_user_effective_roles(db_session, user.id)

    assert len(roles) == 2
    role_codes = [r.role_code for r in roles]
    assert "ROLE1" in role_codes
    assert "ROLE2" in role_codes
