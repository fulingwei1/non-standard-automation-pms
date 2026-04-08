# -*- coding: utf-8 -*-
"""exception_enhancement_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.exception.exception_enhancement_service import ExceptionEnhancementService

class TestExceptionEnhancementServiceInit:
    def test_init(self):
        service = ExceptionEnhancementService(Mock())
        assert service is not None
