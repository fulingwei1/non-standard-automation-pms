# -*- coding: utf-8 -*-
"""presale_ai_export_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.presale_ai_export_service import PresaleAIExportService

class TestPresaleAIExportServiceInit:
    def test_init(self):
        service = PresaleAIExportService(Mock())
        assert service is not None
