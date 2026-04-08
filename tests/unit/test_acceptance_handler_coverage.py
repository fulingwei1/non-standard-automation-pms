# -*- coding: utf-8 -*-
"""acceptance_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler

class TestAcceptanceStatusHandlerInit:
    def test_init(self):
        service = AcceptanceStatusHandler(Mock())
        assert service is not None
