# -*- coding: utf-8 -*-
"""node_management单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_template.node_management import NodeManagementMixin

class TestNodeManagementMixinInit:
    def test_init(self):
        service = NodeManagementMixin(Mock())
        assert service is not None
