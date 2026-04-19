# -*- coding: utf-8 -*-
"""user_importer单元测试"""
from app.services.unified_import.user_importer import UserImporter


class TestUserImporterInit:
    def test_init(self):
        assert hasattr(UserImporter, "import_user_data")
