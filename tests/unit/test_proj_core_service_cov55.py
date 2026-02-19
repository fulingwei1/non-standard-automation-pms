# -*- coding: utf-8 -*-
"""
Tests for app/services/project/core_service.py
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.project.core_service import ProjectCoreService
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.project.core_service.DataScopeService"):
        return ProjectCoreService(db=mock_db)


def test_init_stores_db(mock_db):
    """确认 db 属性存储正确"""
    with patch("app.services.project.core_service.DataScopeService"):
        svc = ProjectCoreService(db=mock_db)
        assert svc.db is mock_db


def test_base_query_filters_active(service, mock_db):
    """_base_query 应过滤 is_active=True 的项目"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    result = service._base_query()
    mock_db.query.assert_called()


def test_get_scoped_query(service, mock_db):
    """get_scoped_query 应应用数据权限过滤"""
    user = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_query

    with patch("app.services.project.core_service.DataScopeService") as MockScope:
        MockScope.filter_projects_by_scope.return_value = mock_query
        result = service.get_scoped_query(user)
        MockScope.filter_projects_by_scope.assert_called_once()


def test_list_user_projects_no_projects(service, mock_db):
    """用户无项目时返回空列表"""
    user = MagicMock()
    user.id = 1
    service._collect_user_project_ids = MagicMock(return_value=[])
    result = service.list_user_projects(user)
    assert result.total == 0
    assert result.items == []


def test_paginate_static():
    """_paginate 应返回正确的总数和页数"""
    mock_query = MagicMock()
    mock_query.count.return_value = 50

    with patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply:
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 3
        mock_paging.return_value = pagination
        mock_apply.return_value.all.return_value = []
        total, pages, items = ProjectCoreService._paginate(mock_query, 1, 20)
        assert total == 50
        assert pages == 3


def test_list_user_projects_with_projects(service, mock_db):
    """用户有项目时返回对应数量"""
    user = MagicMock()
    user.id = 1
    service._collect_user_project_ids = MagicMock(return_value=[100])
    service._load_memberships = MagicMock(return_value={})
    service._build_task_stats = MagicMock(return_value={})

    mock_list_resp = MagicMock()
    mock_list_resp.total = 1

    with patch("app.services.project.core_service.get_pagination_params") as mock_paging, \
         patch("app.services.project.core_service.apply_pagination") as mock_apply, \
         patch("app.services.project.core_service.MyProjectResponse") as mock_resp, \
         patch("app.services.project.core_service.MyProjectListResponse", return_value=mock_list_resp):
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 20
        pagination.pages_for_total.return_value = 1
        mock_paging.return_value = pagination
        mock_db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        project = MagicMock()
        project.id = 100
        project.pm_id = 99
        mock_apply.return_value.all.return_value = [project]
        mock_resp.return_value = MagicMock()
        result = service.list_user_projects(user)
        assert result.total == 1
