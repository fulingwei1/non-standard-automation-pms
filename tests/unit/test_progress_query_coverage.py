# -*- coding: utf-8 -*-
"""progress_query单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_instance.progress_query import ProgressQueryMixin

class TestProgressQueryMixinInit:
    def test_init(self):
        service = ProgressQueryMixin(Mock())
        assert service is not None
