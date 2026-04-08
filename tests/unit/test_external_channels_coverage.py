# -*- coding: utf-8 -*-
"""external_channels单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.notify.external_channels import ExternalChannelsMixin

class TestExternalChannelsMixinInit:
    def test_init(self):
        service = ExternalChannelsMixin(Mock())
        assert service is not None
