# -*- coding: utf-8 -*-
"""config单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ppt_generator.config import PresentationConfig

class TestPresentationConfigInit:
    def test_init(self):
        service = PresentationConfig(Mock())
        assert service is not None
