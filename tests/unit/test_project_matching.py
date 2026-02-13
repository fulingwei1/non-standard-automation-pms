# -*- coding: utf-8 -*-
"""项目匹配模块单元测试"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.services.work_log_ai.project_matching import ProjectMatchingMixin


class TestProjectMatchingMixin:
    def setup_method(self):
        self.mixin = ProjectMatchingMixin()
        self.mixin.db = MagicMock()

    def test_extract_project_keywords_with_name_and_code(self):
        project = MagicMock()
        project.project_name = "自动化 产线"
        project.project_code = "PRJ001"
        project.customer_name = "客户A"
        result = self.mixin._extract_project_keywords(project)
        assert "PRJ001" in result
        assert "客户A" in result

    def test_extract_project_keywords_empty(self):
        project = MagicMock()
        project.project_name = None
        project.project_code = None
        project.customer_name = None
        result = self.mixin._extract_project_keywords(project)
        assert isinstance(result, list)

    def test_get_user_projects_no_members(self):
        self.mixin.db.query.return_value.filter.return_value.all.return_value = []
        result = self.mixin._get_user_projects(1)
        assert result == []

    def test_get_user_projects_for_suggestion(self):
        self.mixin.db.query.return_value.filter.return_value.all.return_value = []
        result = self.mixin.get_user_projects_for_suggestion(1)
        assert isinstance(result, list)
