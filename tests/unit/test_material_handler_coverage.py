# -*- coding: utf-8 -*-
"""material_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.status_handlers.material_handler import MaterialStatusHandler

class TestMaterialStatusHandlerInit:
    def test_init(self):
        service = MaterialStatusHandler(Mock())
        assert service is not None
