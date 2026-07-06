# -*- coding: utf-8 -*-
"""
数据权限过滤服务单元测试
覆盖: app/services/data_scope/generic_filter.py, user_scope.py
"""
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


def make_user(user_id=1, is_superuser=False, department=None):
    u = MagicMock()
    u.id = user_id
    u.is_superuser = is_superuser
    u.department = department
    u.roles = []
    return u


# ─── UserScopeService ─────────────────────────────────────────────────────────


class TestUserScopeService:
    def test_superuser_returns_all(self, mock_db):
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.user_scope import UserScopeService

        user = make_user(is_superuser=True)
        result = UserScopeService.get_user_data_scope(mock_db, user)
        assert result == DataScopeEnum.ALL.value

    def test_no_roles_returns_own(self, mock_db):
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.user_scope import UserScopeService

        user = make_user(is_superuser=False)
        user.roles = []
        result = UserScopeService.get_user_data_scope(mock_db, user)
        assert result == DataScopeEnum.OWN.value

    def test_returns_most_permissive_scope(self, mock_db):
        """取最宽松的权限"""
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.user_scope import UserScopeService

        user = make_user(is_superuser=False)

        role1 = MagicMock()
        role1.is_active = True
        role1.data_scope = DataScopeEnum.OWN.value

        role2 = MagicMock()
        role2.is_active = True
        role2.data_scope = DataScopeEnum.DEPT.value

        ur1 = MagicMock()
        ur1.role = role1
        ur2 = MagicMock()
        ur2.role = role2
        user.roles = [ur1, ur2]

        result = UserScopeService.get_user_data_scope(mock_db, user)
        assert result == DataScopeEnum.DEPT.value

    def test_all_scope_wins(self, mock_db):
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.user_scope import UserScopeService

        user = make_user(is_superuser=False)

        role_all = MagicMock()
        role_all.is_active = True
        role_all.data_scope = DataScopeEnum.ALL.value

        role_dept = MagicMock()
        role_dept.is_active = True
        role_dept.data_scope = DataScopeEnum.DEPT.value

        ur1 = MagicMock()
        ur1.role = role_all
        ur2 = MagicMock()
        ur2.role = role_dept
        user.roles = [ur1, ur2]

        result = UserScopeService.get_user_data_scope(mock_db, user)
        assert result == DataScopeEnum.ALL.value

    def test_inactive_roles_not_counted(self, mock_db):
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.user_scope import UserScopeService

        user = make_user(is_superuser=False)

        role_inactive = MagicMock()
        role_inactive.is_active = False
        role_inactive.data_scope = DataScopeEnum.ALL.value

        ur = MagicMock()
        ur.role = role_inactive
        user.roles = [ur]

        result = UserScopeService.get_user_data_scope(mock_db, user)
        # inactive role should not count → OWN
        assert result == DataScopeEnum.OWN.value

    def test_get_user_project_ids(self, mock_db):
        from app.services.data_scope.user_scope import UserScopeService

        mock_db.query.return_value.filter.return_value.all.return_value = [(1,), (2,), (3,)]
        result = UserScopeService.get_user_project_ids(mock_db, user_id=1)
        assert result == {1, 2, 3}

    def test_get_user_project_ids_empty(self, mock_db):
        from app.services.data_scope.user_scope import UserScopeService

        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = UserScopeService.get_user_project_ids(mock_db, user_id=1)
        assert result == set()


# ─── GenericFilterService.filter_by_scope ────────────────────────────────────


class TestGenericFilterService:
    def test_superuser_returns_unfiltered(self, mock_db):
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(is_superuser=True)
        query = MagicMock()

        result = GenericFilterService.filter_by_scope(mock_db, query, MagicMock(), user)
        assert result == query  # no filter applied
        query.filter.assert_not_called()

    def test_all_scope_returns_unfiltered(self, mock_db):
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(is_superuser=False)
        query = MagicMock()

        with patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
            return_value=DataScopeEnum.ALL.value,
        ):
            result = GenericFilterService.filter_by_scope(mock_db, query, MagicMock(), user)
        assert result == query
        query.filter.assert_not_called()

    def test_own_scope_with_owner_field(self, mock_db):
        from app.models.enums import DataScopeEnum
        from app.models.project import Project
        from app.services.data_scope.config import DataScopeConfig
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(user_id=5, is_superuser=False)
        query = MagicMock()
        query.filter.return_value = query

        config = DataScopeConfig(owner_field="created_by")

        with patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
            return_value=DataScopeEnum.OWN.value,
        ):
            result = GenericFilterService.filter_by_scope(mock_db, query, Project, user, config)
        query.filter.assert_called_once()

    def test_own_scope_without_owner_field_filters_false(self, mock_db):
        """OWN 范围但模型无所有者字段，返回空结果"""
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.config import DataScopeConfig
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(user_id=5, is_superuser=False)
        query = MagicMock()
        query.filter.return_value = query

        model = MagicMock()
        # Make hasattr return False for the owner field
        type(model).__name__ = "FakeModel"
        model.created_by = None

        config = DataScopeConfig(owner_field="nonexistent_field_xyz")

        with patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
            return_value=DataScopeEnum.OWN.value,
        ):
            result = GenericFilterService.filter_by_scope(mock_db, query, model, user, config)
        query.filter.assert_called()

    def test_project_scope(self, mock_db):
        from app.models.enums import DataScopeEnum
        from app.models.project import Project
        from app.services.data_scope.config import DataScopeConfig
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(user_id=5, is_superuser=False)
        query = MagicMock()
        query.filter.return_value = query

        config = DataScopeConfig(owner_field="created_by", project_field="project_id")

        with (
            patch(
                "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
                return_value=DataScopeEnum.PROJECT.value,
            ),
            patch(
                "app.services.data_scope.generic_filter.UserScopeService.get_user_project_ids",
                return_value={1, 2, 3},
            ),
        ):
            result = GenericFilterService.filter_by_scope(mock_db, query, Project, user, config)
        query.filter.assert_called()

    def test_dept_scope_prefers_department_id_over_legacy_name(self, mock_db):
        """HR-03: 调岗后 DEPT 范围必须随 department_id，不被旧部门名字符串带偏。"""
        from app.models.enums import DataScopeEnum
        from app.models.organization import Department
        from app.models.user import User
        from app.services.data_scope.config import DataScopeConfig
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(user_id=5, is_superuser=False, department="旧部门")
        user.department_id = 20
        query = MagicMock()
        query.filter.return_value = query

        stale_dept = Department(id=99, dept_code="OLD", dept_name="旧部门")
        mock_db.query.return_value.filter.return_value.first.return_value = stale_dept
        config = DataScopeConfig(owner_field=None, dept_field="department_id")

        with patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
            return_value=DataScopeEnum.DEPT.value,
        ):
            GenericFilterService.filter_by_scope(mock_db, query, User, user, config)

        compiled_filter = str(
            query.filter.call_args.args[0].compile(compile_kwargs={"literal_binds": True})
        )
        assert "users.department_id = 20" in compiled_filter
        assert "users.department_id = 99" not in compiled_filter
        mock_db.query.assert_not_called()


# ─── GenericFilterService.check_customer_access ──────────────────────────────


class TestCheckCustomerAccess:
    def test_superuser_always_has_access(self, mock_db):
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(is_superuser=True)
        result = GenericFilterService.check_customer_access(mock_db, user, customer_id=99)
        assert result is True

    def test_all_scope_has_access(self, mock_db):
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(is_superuser=False)

        with patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
            return_value=DataScopeEnum.ALL.value,
        ):
            result = GenericFilterService.check_customer_access(mock_db, user, customer_id=5)
        assert result is True

    def test_customer_scope_no_projects_returns_false(self, mock_db):
        """CUSTOMER 数据域尚无客户门户归属模型，必须降级为按项目校验而非放行。"""
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(is_superuser=False)

        with patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
            return_value=DataScopeEnum.CUSTOMER.value,
        ), patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_project_ids",
            return_value=set(),
        ):
            result = GenericFilterService.check_customer_access(mock_db, user, customer_id=5)
        assert result is False

    def test_customer_scope_with_matching_project_has_access(self, mock_db):
        """CUSTOMER 用户对参与项目所属客户仍应放行（降级为项目口径，与 sales_permissions 一致）。"""
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(is_superuser=False)
        mock_db.query.return_value.filter.return_value.first.return_value = (5,)

        with patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
            return_value=DataScopeEnum.CUSTOMER.value,
        ), patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_project_ids",
            return_value={101},
        ):
            result = GenericFilterService.check_customer_access(mock_db, user, customer_id=5)
        assert result is True

    def test_customer_scope_with_unrelated_project_denied(self, mock_db):
        """CUSTOMER 用户参与的项目都不属于目标客户时必须拒绝，不能因为有 CUSTOMER 标记就放行。"""
        from app.models.enums import DataScopeEnum
        from app.services.data_scope.generic_filter import GenericFilterService

        user = make_user(is_superuser=False)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
            return_value=DataScopeEnum.CUSTOMER.value,
        ), patch(
            "app.services.data_scope.generic_filter.UserScopeService.get_user_project_ids",
            return_value={101},
        ):
            result = GenericFilterService.check_customer_access(mock_db, user, customer_id=999)
        assert result is False
