# -*- coding: utf-8 -*-
"""node_operations单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_instance.node_operations import NodeOperationsMixin

class TestNodeOperationsMixinInit:
    def test_init(self):
        service = NodeOperationsMixin(Mock())
        assert service is not None
