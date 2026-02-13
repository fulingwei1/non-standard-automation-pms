# -*- coding: utf-8 -*-
"""InitializationMixin 单元测试"""
from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from app.services.stage_instance.initialization import InitializationMixin


class ConcreteInit(InitializationMixin):
    def __init__(self, db):
        self.db = db


class TestInitializationMixin:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = ConcreteInit(self.db)

    def test_project_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            self.svc.initialize_project_stages(999, 1)

    def test_template_not_found(self):
        self.db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        project = MagicMock()
        # first call returns project, second returns None for template
        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            self.svc.initialize_project_stages(1, 999)

    def test_clear_project_stages(self):
        self.db.query.return_value.filter.return_value.update.return_value = 1
        self.db.query.return_value.filter.return_value.delete.return_value = 3
        count = self.svc.clear_project_stages(1)
        assert isinstance(count, int)
