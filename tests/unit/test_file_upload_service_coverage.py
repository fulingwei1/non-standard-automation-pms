# -*- coding: utf-8 -*-
"""file_upload_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.file_upload_service import FileUploadService

class TestFileUploadServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = FileUploadService(mock_db)
        assert hasattr(service, 'db')
