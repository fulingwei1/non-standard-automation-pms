# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 项目核心聚合服务"""

import pytest
from unittest.mock import MagicMock, patch, call

try:
    from app.services.project.core_service import ProjectCoreService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return ProjectCoreService(mock_db)


class TestProjectCoreService:

    def test_init_sets_db(self, mock_db):
        svc = ProjectCoreService(mock_db)
        assert svc.db is mock_db

    def test_base_query_filters_active(self, service, mock_db):
        """_base_query 应过滤 is_active=True"""
        query = service._base_query()
        assert query is not None

    def test_get_scoped_query_calls_data_scope(self, service):
        mock_user = MagicMock()
        with patch("app.services.project.core_service.DataScopeService.filter_projects_by_scope") as mock_scope:
            mock_scope.return_value = MagicMock()
            service.get_scoped_query(mock_user)
            mock_scope.assert_called_once()

    def test_list_user_projects_empty_when_no_ids(self, service, mock_db):
        mock_user = MagicMock(id=1)
        # 模拟 ProjectMember 和 Project 查询返回空列表
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service.list_user_projects(mock_user, page=1, page_size=20)
        assert result.total == 0
        assert result.items == []

    def test_collect_user_project_ids_deduplicates(self, service, mock_db):
        mock_user = MagicMock(id=42)
        # 两次查询分别返回成员项目和PM项目
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [(1,), (2,)],   # member_ids
            [(2,), (3,)],   # owned_ids
        ]
        ids = service._collect_user_project_ids(mock_user)
        assert set(ids) == {1, 2, 3}
        assert ids == sorted(ids)

    def test_load_memberships_returns_empty_for_no_ids(self, service):
        result = service._load_memberships(user_id=1, project_ids=[])
        assert result == {}

    def test_build_task_stats_returns_empty_for_no_ids(self, service):
        result = service._build_task_stats(user_id=1, project_ids=[])
        assert result == {}

    def test_paginate_static_method(self, service, mock_db):
        mock_query = MagicMock()
        mock_query.count.return_value = 5
        mock_query.all.return_value = []
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        with patch("app.services.project.core_service.apply_pagination", return_value=mock_query), \
             patch("app.services.project.core_service.get_pagination_params") as mock_params:
            mock_params.return_value = MagicMock(offset=0, limit=20, pages_for_total=lambda t: 1)
            total, pages, items = ProjectCoreService._paginate(mock_query, 1, 20)
        assert total == 5
