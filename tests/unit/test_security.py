# -*- coding: utf-8 -*-
import pytest
from sqlalchemy.orm import Session
from app.core.security import (
    check_permission,
    check_sales_create_permission,
    check_sales_edit_permission,
    check_sales_delete_permission,
    get_sales_data_scope,
    has_sales_approval_access,
)
from app.models.user import User, Role, UserRole, ApiPermission, RoleApiPermission


def _clear_permission_cache():
    """Clear permission cache between tests"""
    try:
        from app.services.permission_cache_service import get_permission_cache_service
        cache_service = get_permission_cache_service()
        # Clear the underlying CacheService memory_cache
        cache_service._cache.memory_cache.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clear_cache_before_test():
    """Automatically clear permission cache before each test"""
    _clear_permission_cache()
    yield
    _clear_permission_cache()


@pytest.mark.unit
@pytest.mark.security
class TestBasePermissionChecks:
    @pytest.fixture
    def setup_permissions(self, db_session: Session):
        perms = [
            ("project:read", "Read Project", "project"),
            ("project:write", "Write Project", "project"),
            ("finance:read", "Read Finance", "finance"),
            ("procurement:read", "Read Procurement", "procurement"),
        ]
        for code, name, mod in perms:
            p = (
                db_session.query(ApiPermission)
                .filter(ApiPermission.perm_code == code)
                .first()
            )
            if not p:
                db_session.add(
                    ApiPermission(perm_code=code, perm_name=name, module=mod)
                )

        role_pm = db_session.query(Role).filter(Role.role_code == "PM").first()
        if not role_pm:
            role_pm = Role(
                role_code="PM", role_name="Project Manager", data_scope="OWN"
            )
            db_session.add(role_pm)
        db_session.flush()

        for code in ["project:read", "project:write"]:
            p = (
                db_session.query(ApiPermission)
                .filter(ApiPermission.perm_code == code)
                .first()
            )
            exists = (
                db_session.query(RoleApiPermission)
                .filter_by(role_id=role_pm.id, permission_id=p.id)
                .first()
            )
            if not exists:
                db_session.add(
                    RoleApiPermission(role_id=role_pm.id, permission_id=p.id)
                )

        db_session.commit()
        return {"pm": role_pm}

    @pytest.fixture
    def test_user(self, db_session, setup_permissions):
        user = db_session.query(User).filter_by(username="test_user").first()
        if not user:
            user = User(
                employee_id=9001,
                username="test_user",
                real_name="Test User",
                is_superuser=False,
                password_hash="hashed",
            )
            db_session.add(user)
            db_session.flush()
            db_session.add(
                UserRole(user_id=user.id, role_id=setup_permissions["pm"].id)
            )
            db_session.commit()
        return user

    @pytest.fixture
    def superuser(self, db_session):
        user = db_session.query(User).filter_by(username="admin_test").first()
        if not user:
            user = User(
                employee_id=9005,
                username="admin_test",
                real_name="Admin",
                is_superuser=True,
                password_hash="hashed",
            )
            db_session.add(user)
            db_session.commit()
        return user

    @pytest.fixture
    def no_role_user(self, db_session):
        uname = "no_role_base_user"
        user = db_session.query(User).filter_by(username=uname).first()
        if not user:
            user = User(
                employee_id=9002,
                username=uname,
                real_name="No Role",
                is_superuser=False,
                password_hash="hashed",
            )
            db_session.add(user)
            db_session.commit()
        return user

    def test_check_permission_success(self, test_user, db_session):
        assert check_permission(test_user, "project:read", db_session) is True

    def test_superuser_all_perms(self, superuser, db_session):
        assert check_permission(superuser, "any:perm", db_session) is True

    def test_user_with_no_roles_fail(self, no_role_user, db_session):
        assert check_permission(no_role_user, "project:read", db_session) is False


@pytest.mark.unit
@pytest.mark.security
class TestModulePermissions:
    """Testing module-specific permissions using the generic check_permission"""

    @pytest.fixture
    def procurement_user(self, db_session):
        role = db_session.query(Role).filter_by(role_code="PROC_ENG").first()
        if not role:
            role = Role(role_code="PROC_ENG", role_name="Procurement Engineer")
            db_session.add(role)
            db_session.flush()

        p = (
            db_session.query(ApiPermission)
            .filter_by(perm_code="procurement:read")
            .first()
        )
        if not p:
            p = ApiPermission(
                perm_code="procurement:read",
                perm_name="Read Proc",
                module="procurement",
            )
            db_session.add(p)
            db_session.flush()

        exists = (
            db_session.query(RoleApiPermission)
            .filter_by(role_id=role.id, permission_id=p.id)
            .first()
        )
        if not exists:
            db_session.add(RoleApiPermission(role_id=role.id, permission_id=p.id))

        user = db_session.query(User).filter_by(username="proc_user").first()
        if not user:
            user = User(
                employee_id=8001,
                username="proc_user",
                real_name="Proc User",
                password_hash="hashed",
            )
            db_session.add(user)
            db_session.flush()
            db_session.add(UserRole(user_id=user.id, role_id=role.id))
        db_session.commit()
        return user

    def test_procurement_access(self, procurement_user, db_session):
        assert (
            check_permission(procurement_user, "procurement:read", db_session) is True
        )
        assert check_permission(procurement_user, "finance:read", db_session) is False


@pytest.mark.unit
@pytest.mark.security
class TestSalesPermissions:
    @pytest.fixture
    def sales_director(self, db_session):
        role = db_session.query(Role).filter_by(role_code="SALES_DIRECTOR").first()
        if not role:
            role = Role(
                role_code="SALES_DIRECTOR", role_name="Sales Director", data_scope="ALL"
            )
            db_session.add(role)
        else:
            role.data_scope = "ALL"

        for p_code in ["sales:create", "sales:edit", "sales:delete", "sales:approve"]:
            p = db_session.query(ApiPermission).filter_by(perm_code=p_code).first()
            if not p:
                p = ApiPermission(perm_code=p_code, perm_name=p_code, module="sales")
                db_session.add(p)
                db_session.flush()
            exists = (
                db_session.query(RoleApiPermission)
                .filter_by(role_id=role.id, permission_id=p.id)
                .first()
            )
            if not exists:
                db_session.add(RoleApiPermission(role_id=role.id, permission_id=p.id))

        user = db_session.query(User).filter_by(username="sales_dir_test").first()
        if not user:
            user = User(
                employee_id=9003,
                username="sales_dir_test",
                real_name="Director",
                password_hash="hashed",
            )
            db_session.add(user)
            db_session.flush()
            db_session.add(UserRole(user_id=user.id, role_id=role.id))
        db_session.commit()
        return user

    @pytest.fixture
    def sales_rep(self, db_session):
        role = db_session.query(Role).filter_by(role_code="SALES_REP_TEST").first()
        if not role:
            role = Role(
                role_code="SALES_REP_TEST", role_name="Sales Rep", data_scope="OWN"
            )
            db_session.add(role)
        else:
            role.data_scope = "OWN"

        p = db_session.query(ApiPermission).filter_by(perm_code="sales:create").first()
        if not p:
            p = ApiPermission(
                perm_code="sales:create", perm_name="sales:create", module="sales"
            )
            db_session.add(p)
            db_session.flush()
        exists = (
            db_session.query(RoleApiPermission)
            .filter_by(role_id=role.id, permission_id=p.id)
            .first()
        )
        if not exists:
            db_session.add(RoleApiPermission(role_id=role.id, permission_id=p.id))

        user = db_session.query(User).filter_by(username="sales_rep_test").first()
        if not user:
            user = User(
                employee_id=9004,
                username="sales_rep_test",
                real_name="Rep",
                password_hash="hashed",
            )
            db_session.add(user)
            db_session.flush()
            db_session.add(UserRole(user_id=user.id, role_id=role.id))
        db_session.commit()
        return user

    def test_sales_director_scope(self, sales_director, db_session):
        assert get_sales_data_scope(sales_director, db_session) == "ALL"

    def test_sales_rep_scope(self, sales_rep, db_session):
        assert get_sales_data_scope(sales_rep, db_session) == "OWN"

    def test_sales_director_delete(self, sales_director, db_session):
        assert check_sales_delete_permission(sales_director, db_session) is True

    def test_sales_rep_delete_fail(self, sales_rep, db_session):
        assert check_sales_delete_permission(sales_rep, db_session) is False

    def test_sales_approval(self, sales_director, db_session):
        assert has_sales_approval_access(sales_director, db_session) is True
