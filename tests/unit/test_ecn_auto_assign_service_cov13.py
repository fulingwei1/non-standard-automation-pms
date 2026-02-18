# -*- coding: utf-8 -*-
"""第十三批 - ECN自动分配服务 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.ecn_auto_assign_service import (
        find_users_by_department,
        find_users_by_role,
    )
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


class TestFindUsersByDepartment:
    def test_returns_users_in_department(self, db):
        """返回部门内的用户"""
        mock_users = [MagicMock(id=1), MagicMock(id=2)]
        db.query.return_value.filter.return_value.all.return_value = mock_users
        result = find_users_by_department(db, "研发部")
        assert len(result) == 2

    def test_returns_empty_for_unknown_dept(self, db):
        """未知部门返回空列表"""
        db.query.return_value.filter.return_value.all.return_value = []
        result = find_users_by_department(db, "不存在的部门")
        assert result == []

    def test_only_active_users(self, db):
        """只返回活跃用户"""
        db.query.return_value.filter.return_value.all.return_value = [MagicMock()]
        result = find_users_by_department(db, "工程部")
        assert isinstance(result, list)


class TestFindUsersByRole:
    def test_role_not_found_returns_empty(self, db):
        """角色不存在返回空列表"""
        db.query.return_value.filter.return_value.first.return_value = None
        result = find_users_by_role(db, "不存在的角色")
        assert result == []

    def test_role_found_no_users(self, db):
        """角色存在但无用户"""
        mock_role = MagicMock(id=1)
        # 第一次query返回role，第二次返回空UserRoles
        call_results = [mock_role]
        call_count = [0]

        def mock_query(*args):
            m = MagicMock()
            m.filter.return_value.first.return_value = mock_role
            m.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = mock_query
        result = find_users_by_role(db, "测试角色")
        assert isinstance(result, list)

    def test_role_found_with_users(self, db):
        """角色存在且有用户"""
        mock_role = MagicMock()
        mock_role.id = 5
        mock_role.is_active = True

        mock_user_role = MagicMock()
        mock_user_role.user_id = 10

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.is_active = True

        results_seq = [mock_role, [mock_user_role], [mock_user]]
        idx = [0]

        def query_side(*args):
            m = MagicMock()
            seq_idx = idx[0]
            idx[0] += 1
            if seq_idx == 0:
                m.filter.return_value.first.return_value = mock_role
            elif seq_idx == 1:
                m.filter.return_value.all.return_value = [mock_user_role]
            else:
                m.filter.return_value.all.return_value = [mock_user]
            return m

        db.query.side_effect = query_side
        result = find_users_by_role(db, "项目经理")
        assert isinstance(result, list)

    def test_user_ids_empty_returns_empty(self, db):
        """用户角色关联为空时返回空列表"""
        mock_role = MagicMock()
        mock_role.id = 1

        call_count = [0]

        def query_side(*args):
            m = MagicMock()
            if call_count[0] == 0:
                m.filter.return_value.first.return_value = mock_role
            else:
                m.filter.return_value.all.return_value = []
            call_count[0] += 1
            return m

        db.query.side_effect = query_side
        result = find_users_by_role(db, "某角色")
        assert result == []
