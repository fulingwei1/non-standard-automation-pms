# -*- coding: utf-8 -*-
"""milestone_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.status_handlers.milestone_handler import MilestoneStatusHandler

class TestMilestoneStatusHandlerInit:
    def test_init(self):
        service = MilestoneStatusHandler(Mock())
        assert service is not None
