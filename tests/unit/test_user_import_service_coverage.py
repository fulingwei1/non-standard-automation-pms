# -*- coding: utf-8 -*-
"""user_import_service单元测试"""
from app.services.user_import_service import UserImportService


class TestUserImportServiceInit:
    def test_init(self):
        assert hasattr(UserImportService, "read_file")
        assert hasattr(UserImportService, "normalize_columns")
