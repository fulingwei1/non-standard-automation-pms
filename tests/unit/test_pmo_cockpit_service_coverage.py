# -*- coding: utf-8 -*-
"""pmo_cockpit_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.pmo_cockpit.pmo_cockpit_service import PmoCockpitService

class TestPmoCockpitServiceInit:
    def test_init(self):
        service = PmoCockpitService(Mock())
        assert service is not None
