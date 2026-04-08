# -*- coding: utf-8 -*-
"""table_builder单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ppt_generator.table_builder import TableSlideBuilder

class TestTableSlideBuilderInit:
    def test_init(self):
        service = TableSlideBuilder(Mock())
        assert service is not None
