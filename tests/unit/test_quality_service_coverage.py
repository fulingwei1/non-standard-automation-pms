# -*- coding: utf-8 -*-
"""quality_service单元测试"""
import pytest
from app.services.quality_service import QualityService

class TestQualityServiceInit:
    def test_init_without_db(self):
        """测试无参数初始化"""
        service = QualityService()
        assert service is not None