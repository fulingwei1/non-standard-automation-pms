# -*- coding: utf-8 -*-
"""escalation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.exception.escalation_service import EscalationService

class TestEscalationServiceInit:
    def test_init(self):
        service = EscalationService(Mock())
        assert service is not None
