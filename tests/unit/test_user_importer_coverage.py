# -*- coding: utf-8 -*-
"""user_importer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.unified_import.user_importer import UserImporter

class TestUserImporterInit:
    def test_init(self):
        service = UserImporter(Mock())
        assert service is not None
