# -*- coding: utf-8 -*-
"""Tests for app/services/project/core_service.py"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.project.core_service import ProjectCoreService


class TestProjectCoreService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = ProjectCoreService(self.db)

    def test_init(self):
        assert self.service.db == self.db

    @pytest.mark.skip(reason="Complex query with DataScopeService dependency")
    def test_list_user_projects(self):
        user = MagicMock()
        result = self.service.list_user_projects(user)
        assert result is not None

    def test_get_department_found(self):
        mock_dept = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_dept
        result = self.service.get_department(1)
        assert result == mock_dept

    def test_get_department_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.get_department(999)
        assert result is None
