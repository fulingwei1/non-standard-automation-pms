# -*- coding: utf-8 -*-
"""bom_attributes_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.bom_attributes.bom_attributes_service import BomAttributesService

class TestBomAttributesServiceInit:
    def test_init(self):
        service = BomAttributesService(Mock())
        assert service is not None
