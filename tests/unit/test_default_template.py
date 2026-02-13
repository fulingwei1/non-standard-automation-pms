# -*- coding: utf-8 -*-
"""默认模板管理单元测试"""
import pytest
from unittest.mock import MagicMock
from app.services.stage_template.default_template import DefaultTemplateMixin


class TestDefaultTemplateMixin:
    def setup_method(self):
        self.mixin = DefaultTemplateMixin()
        self.mixin.db = MagicMock()

    def test_get_default_template(self):
        template = MagicMock()
        self.mixin.db.query.return_value.filter.return_value.first.return_value = template
        result = self.mixin.get_default_template()
        assert result == template

    def test_get_default_template_none(self):
        self.mixin.db.query.return_value.filter.return_value.first.return_value = None
        result = self.mixin.get_default_template()
        assert result is None

    def test_set_default_template_not_found(self):
        self.mixin.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            self.mixin.set_default_template(999)

    def test_set_default_template_success(self):
        template = MagicMock()
        template.project_type = "CUSTOM"
        self.mixin.db.query.return_value.filter.return_value.first.return_value = template
        self.mixin._clear_default_template = MagicMock()
        result = self.mixin.set_default_template(1)
        assert result.is_default is True
        self.mixin._clear_default_template.assert_called_once_with("CUSTOM")
