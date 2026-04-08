# -*- coding: utf-8 -*-
"""change_log单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_template.change_log import ChangeLogMixin

class TestChangeLogMixinInit:
    def test_init(self):
        service = ChangeLogMixin(Mock())
        assert service is not None
