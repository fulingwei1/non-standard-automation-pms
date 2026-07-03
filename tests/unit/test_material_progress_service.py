# -*- coding: utf-8 -*-
"""
物料进度服务测试
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestMaterialProgressSchemas:
    def test_key_material_item_allows_unlinked_material_id(self):
        """BOM 行可能还没有关联物料主数据，但仍应能返回关键物料进度。"""
        from app.schemas.material_progress import KeyMaterialItem

        item = KeyMaterialItem(
            material_id=None,
            material_code="TMP-001",
            material_name="临时关键物料",
            required_qty=Decimal("10"),
            received_qty=Decimal("2"),
            shortage_qty=Decimal("8"),
            kitting_status="SHORTAGE",
        )

        assert item.material_id is None


class TestMaterialProgressService:
    """物料进度服务测试"""

    def test_get_material_progress_overview(self):
        """测试获取物料进度总览"""
        from app.services.material_progress_service import get_material_progress_overview

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False

        # Mock project
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.pm_id = 999  # Different from mock_user.id

        # Mock project member check - not a member
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,  # Project query
            None,  # Not a member
        ]

        # This should raise HTTPException due to no access
        with pytest.raises(Exception):
            get_material_progress_overview(mock_db, project_id=1, user=mock_user)

    def test_check_project_access_superuser(self):
        """测试超级管理员权限"""
        from app.services.material_progress_service import _check_project_access

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = True

        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = _check_project_access(mock_db, project_id=1, user=mock_user)
        assert result == mock_project

    def test_check_project_access_pm(self):
        """测试项目经理权限"""
        from app.services.material_progress_service import _check_project_access

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 100
        mock_user.is_superuser = False

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.pm_id = 100  # Same as user.id

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = _check_project_access(mock_db, project_id=1, user=mock_user)
        assert result == mock_project

    def test_check_project_access_member(self):
        """测试项目成员权限"""
        from app.services.material_progress_service import _check_project_access

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 100
        mock_user.is_superuser = False

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.pm_id = 999  # Different from user.id

        mock_member = MagicMock()
        mock_member.is_active = True

        # First call returns project, second returns member
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,
            mock_member,
        ]

        result = _check_project_access(mock_db, project_id=1, user=mock_user)
        assert result == mock_project

    def test_check_project_access_denied(self):
        """测试访问被拒绝"""
        from app.services.material_progress_service import _check_project_access
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 100
        mock_user.is_superuser = False

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.pm_id = 999

        # Not a member
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,
            None,
        ]

        with pytest.raises(HTTPException) as exc_info:
            _check_project_access(mock_db, project_id=1, user=mock_user)

        assert exc_info.value.status_code == 403

    def test_check_project_not_found(self):
        """测试项目不存在"""
        from app.services.material_progress_service import _check_project_access
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            _check_project_access(mock_db, project_id=999, user=mock_user)

        assert exc_info.value.status_code == 404
