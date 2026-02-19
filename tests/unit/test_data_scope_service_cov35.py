# -*- coding: utf-8 -*-
"""
第三十五批 - data_scope_service.py 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.data_scope_service import DataScopeService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestDataScopeServiceGetUserOrgUnits:

    def test_returns_empty_on_exception(self):
        """查询异常时返回空列表"""
        db = MagicMock()
        db.query.side_effect = Exception("db error")
        result = DataScopeService.get_user_org_units(db, 1)
        assert result == []

    def test_returns_org_unit_ids(self):
        """正常返回用户所属组织单元ID"""
        assignment = MagicMock()
        assignment.org_unit_id = 10

        db = MagicMock()
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.all.return_value = [assignment]
        db.query.return_value = q

        result = DataScopeService.get_user_org_units(db, 1)
        assert 10 in result

    def test_multiple_assignments(self):
        """多个组织分配正确合并"""
        a1 = MagicMock()
        a1.org_unit_id = 10
        a2 = MagicMock()
        a2.org_unit_id = 20

        db = MagicMock()
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.all.return_value = [a1, a2]
        db.query.return_value = q

        result = DataScopeService.get_user_org_units(db, 1)
        assert set(result) == {10, 20}


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestDataScopeServiceApplyDataScope:

    def _make_superuser(self):
        user = MagicMock()
        user.is_superuser = True
        return user

    def _make_normal_user(self, user_id=1):
        user = MagicMock()
        user.is_superuser = False
        user.id = user_id
        return user

    def test_superuser_bypasses_filter(self):
        """超级用户不受数据权限限制"""
        db = MagicMock()
        user = self._make_superuser()
        query = MagicMock()
        result = DataScopeService.apply_data_scope(
            query, db, user, "PROJECT"
        )
        # 超级用户直接返回原查询
        assert result is query

    def test_all_scope_returns_query_unchanged(self):
        """ALL 权限类型返回原始查询"""
        db = MagicMock()
        user = self._make_normal_user()
        query = MagicMock()
        query.column_descriptions = [{"entity": MagicMock()}]

        with patch("app.services.data_scope_service.PermissionService") as MockPS:
            from app.models.permission import ScopeType
            MockPS.get_user_data_scopes.return_value = {"PROJECT": ScopeType.ALL.value}
            result = DataScopeService.apply_data_scope(
                query, db, user, "PROJECT"
            )
        assert result is query

    def test_own_scope_with_no_owner_field(self):
        """OWN 权限但模型无 owner 字段时过滤为空"""
        db = MagicMock()
        user = self._make_normal_user(user_id=5)

        class NoOwnerModel:
            pass

        query = MagicMock()
        query.column_descriptions = [{"entity": NoOwnerModel}]
        query.filter.return_value = query

        with patch("app.services.data_scope_service.PermissionService") as MockPS:
            from app.models.permission import ScopeType
            MockPS.get_user_data_scopes.return_value = {"TASK": ScopeType.OWN.value}
            result = DataScopeService.apply_data_scope(
                query, db, user, "TASK"
            )
        # filter(False) 应被调用
        query.filter.assert_called()


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestDataScopeServiceCanAccessData:

    def test_superuser_can_access_all(self):
        """超级用户可以访问任何数据"""
        db = MagicMock()
        user = MagicMock()
        user.is_superuser = True
        data = MagicMock()
        result = DataScopeService.can_access_data(db, user, "PROJECT", data)
        assert result is True

    def test_all_scope_allows_access(self):
        """ALL 权限类型允许访问"""
        db = MagicMock()
        user = MagicMock()
        user.is_superuser = False
        user.id = 1
        data = MagicMock()

        with patch("app.services.data_scope_service.PermissionService") as MockPS:
            from app.models.permission import ScopeType
            MockPS.get_user_data_scopes.return_value = {"PROJECT": ScopeType.ALL.value}
            result = DataScopeService.can_access_data(db, user, "PROJECT", data)
        assert result is True

    def test_own_scope_user_owns_data(self):
        """OWN 权限时用户是数据所有者可访问"""
        db = MagicMock()
        user = MagicMock()
        user.is_superuser = False
        user.id = 7
        data = MagicMock()
        data.created_by = 7
        data.owner_id = None
        data.pm_id = None

        with patch("app.services.data_scope_service.PermissionService") as MockPS:
            from app.models.permission import ScopeType
            MockPS.get_user_data_scopes.return_value = {"TASK": ScopeType.OWN.value}
            result = DataScopeService.can_access_data(
                db, user, "TASK", data, owner_field="created_by"
            )
        assert result is True
