# -*- coding: utf-8 -*-
"""
权限辅助函数单元测试
测试 app/utils/permission_helpers.py
"""

import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch, Mock

# 延迟导入以避免SQLAlchemy关系配置问题


class TestCheckProjectAccessOrRaise:
    """测试 check_project_access_or_raise 函数"""

    def test_project_not_found(self):
        """测试项目不存在时抛出404异常"""
        from app.utils.permission_helpers import check_project_access_or_raise
        
        user = MagicMock()
        user.id = 1
        db = MagicMock()
        
        # 模拟查询返回None（项目不存在）
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            check_project_access_or_raise(db, user, 99999)

        assert exc_info.value.status_code == 404
        assert "项目不存在" in str(exc_info.value.detail)

    @patch("app.utils.permission_helpers.DataScopeService.check_project_access")
    def test_no_access_permission(self, mock_check_access):
        """测试无权限时抛出403异常"""
        from app.utils.permission_helpers import check_project_access_or_raise
        
        user = MagicMock()
        user.id = 1
        db = MagicMock()

        # 创建模拟项目
        project = MagicMock()
        project.id = 1
        db.query.return_value.filter.return_value.first.return_value = project

        # 模拟无权限
        mock_check_access.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            check_project_access_or_raise(db, user, 1)

        assert exc_info.value.status_code == 403
        assert "没有权限访问该项目" in str(exc_info.value.detail)

    @patch("app.utils.permission_helpers.DataScopeService.check_project_access")
    def test_has_access_permission(self, mock_check_access):
        """测试有权限时返回项目对象"""
        from app.utils.permission_helpers import check_project_access_or_raise
        
        user = MagicMock()
        user.id = 1
        db = MagicMock()

        # 创建模拟项目
        project = MagicMock()
        project.id = 1
        db.query.return_value.filter.return_value.first.return_value = project

        # 模拟有权限
        mock_check_access.return_value = True

        result = check_project_access_or_raise(db, user, 1)

        assert result == project
        mock_check_access.assert_called_once_with(db, user, 1)

    @patch("app.utils.permission_helpers.DataScopeService.check_project_access")
    def test_custom_error_message(self, mock_check_access):
        """测试自定义错误消息"""
        from app.utils.permission_helpers import check_project_access_or_raise
        
        user = MagicMock()
        user.id = 1
        db = MagicMock()

        project = MagicMock()
        project.id = 1
        db.query.return_value.filter.return_value.first.return_value = project

        mock_check_access.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            check_project_access_or_raise(
                db, user, 1, error_message="自定义错误消息"
            )

        assert exc_info.value.status_code == 403
        assert "自定义错误消息" in str(exc_info.value.detail)


class TestFilterProjectsByScope:
    """测试 filter_projects_by_scope 函数"""

    @patch("app.utils.permission_helpers.DataScopeService.filter_projects_by_scope")
    def test_delegates_to_service(self, mock_filter):
        """测试委托给 DataScopeService"""
        from app.utils.permission_helpers import filter_projects_by_scope
        
        user = MagicMock()
        query = MagicMock()
        db = MagicMock()
        project_ids = [1, 2, 3]

        mock_filter.return_value = query

        result = filter_projects_by_scope(db, query, user, project_ids)

        assert result == query
        mock_filter.assert_called_once_with(db, query, user, project_ids)

    @patch("app.utils.permission_helpers.DataScopeService.filter_projects_by_scope")
    def test_without_project_ids(self, mock_filter):
        """测试不提供项目ID列表"""
        from app.utils.permission_helpers import filter_projects_by_scope
        
        user = MagicMock()
        query = MagicMock()
        db = MagicMock()

        mock_filter.return_value = query

        result = filter_projects_by_scope(db, query, user, None)

        assert result == query
        mock_filter.assert_called_once_with(db, query, user, None)
