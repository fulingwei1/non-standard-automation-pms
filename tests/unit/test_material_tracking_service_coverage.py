# -*- coding: utf-8 -*-
"""material_tracking_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.material_tracking.material_tracking_service import MaterialTrackingService

class TestMaterialTrackingServiceInit:
    def test_init(self):
        service = MaterialTrackingService(Mock())
        assert service is not None
