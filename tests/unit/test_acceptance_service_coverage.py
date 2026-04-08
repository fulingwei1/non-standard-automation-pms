# -*- coding: utf-8 -*-
"""acceptance_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.acceptance.acceptance_service import AcceptanceService

class TestAcceptanceServiceInit:
    def test_init(self):
        service = AcceptanceService(Mock())
        assert service is not None
