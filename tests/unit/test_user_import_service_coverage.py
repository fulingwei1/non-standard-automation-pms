# -*- coding: utf-8 -*-
"""user_import_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.user_import_service import UserImportService

class TestUserImportServiceInit:
    def test_init(self):
        service = UserImportService(Mock())
        assert service is not None
