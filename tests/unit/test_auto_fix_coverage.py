# -*- coding: utf-8 -*-
"""auto_fix单元测试"""
import pytest
from app.services.data_integrity.auto_fix import AutoFixMixin


class TestAutoFixMixinInit:
    def test_init(self):
        service = AutoFixMixin()
        assert service is not None
        assert hasattr(service, 'suggest_auto_fixes')
