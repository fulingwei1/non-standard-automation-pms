# -*- coding: utf-8 -*-
"""generator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ppt_generator.generator import PresentationGenerator

class TestPresentationGeneratorInit:
    def test_init(self):
        service = PresentationGenerator(Mock())
        assert service is not None
