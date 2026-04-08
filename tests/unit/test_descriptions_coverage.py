# -*- coding: utf-8 -*-
"""descriptions单元测试"""
import pytest
from unittest.mock import Mock
from app.services.lead_priority_scoring.descriptions import DescriptionsMixin

class TestDescriptionsMixinInit:
    def test_init(self):
        service = DescriptionsMixin(Mock())
        assert service is not None
