# -*- coding: utf-8 -*-
"""Tests for app/services/data_scope/project_filter.py"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.data_scope.project_filter import ProjectFilterService


class TestProjectFilterService:
    def setup_method(self):
        self.db = MagicMock()

    @pytest.mark.skip(reason="Complex scope/permission queries")
    def test_get_accessible_project_ids(self):
        user = MagicMock()
        result = ProjectFilterService.get_accessible_project_ids(self.db, user)
        assert isinstance(result, (list, set))

    @pytest.mark.skip(reason="Complex scope/permission queries")
    def test_check_project_access(self):
        user = MagicMock()
        result = ProjectFilterService.check_project_access(self.db, user, 1)
        assert isinstance(result, bool)
