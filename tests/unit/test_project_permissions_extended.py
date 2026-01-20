# -*- coding: utf-8 -*-
"""
项目权限检查扩展测试
测试 app/core/permissions/project.py 的完整功能
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

# 延迟导入以避免SQLAlchemy关系配置问题


class TestCheckProjectAccess:
    """测试 check_project_access 函数"""

    @patch("app.services.data_scope_service.DataScopeService.check_project_access")
    def test_delegates_to_service(self, mock_check):
        """测试委托给 DataScopeService"""
        from app.core.permissions.project import check_project_access
        
        user = MagicMock()
        db = MagicMock()

        mock_check.return_value = True

        result = check_project_access(1, user, db)

        assert result is True
        mock_check.assert_called_once_with(db, user, 1)

    @patch("app.services.data_scope_service.DataScopeService.check_project_access")
    def test_returns_false_when_no_access(self, mock_check):
        """测试无权限时返回False"""
        from app.core.permissions.project import check_project_access
        
        user = MagicMock()
        db = MagicMock()

        mock_check.return_value = False

        result = check_project_access(1, user, db)

        assert result is False


class TestRequireProjectAccess:
    """测试 require_project_access 函数"""

    def test_returns_callable(self):
        """测试返回可调用对象"""
        from app.core.permissions.project import require_project_access
        
        checker = require_project_access()
        assert callable(checker)

    @patch("app.core.permissions.project.check_project_access")
    def test_raises_exception_when_no_access(self, mock_check):
        """测试无权限时抛出异常"""
        from app.core.permissions.project import require_project_access
        
        mock_check.return_value = False

        checker = require_project_access()
        user = MagicMock()
        db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            checker(project_id=1, current_user=user, db=db)

        assert exc_info.value.status_code == 403
        assert "没有权限访问该项目" in str(exc_info.value.detail)

    @patch("app.core.permissions.project.check_project_access")
    def test_returns_user_when_has_access(self, mock_check):
        """测试有权限时返回用户"""
        from app.core.permissions.project import require_project_access
        
        mock_check.return_value = True

        checker = require_project_access()
        user = MagicMock()
        db = MagicMock()

        result = checker(project_id=1, current_user=user, db=db)

        assert result == user
