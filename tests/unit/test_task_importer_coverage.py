# -*- coding: utf-8 -*-
"""task_importer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.unified_import.task_importer import TaskImporter

class TestTaskImporterInit:
    def test_init(self):
        service = TaskImporter(Mock())
        assert service is not None
