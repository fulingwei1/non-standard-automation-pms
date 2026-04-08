# -*- coding: utf-8 -*-
"""pdca_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.exception.pdca_service import PDCAService

class TestPDCAServiceInit:
    def test_init(self):
        service = PDCAService(Mock())
        assert service is not None
