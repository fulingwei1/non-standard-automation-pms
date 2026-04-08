# -*- coding: utf-8 -*-
"""best_practices_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.best_practices.best_practices_service import BestPracticesService

class TestBestPracticesServiceInit:
    def test_init(self):
        service = BestPracticesService(Mock())
        assert service is not None
