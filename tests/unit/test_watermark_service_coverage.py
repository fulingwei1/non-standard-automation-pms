# -*- coding: utf-8 -*-
"""watermark_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.export.watermark_service import WatermarkConfig

class TestWatermarkConfigInit:
    def test_init(self):
        service = WatermarkConfig(Mock())
        assert service is not None
