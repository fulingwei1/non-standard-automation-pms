# -*- coding: utf-8 -*-
"""config_loader单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.config_loader import ConfigError

class TestConfigErrorInit:
    def test_init(self):
        service = ConfigError(Mock())
        assert service is not None
