# -*- coding: utf-8 -*-
"""milestone_handler单元测试"""
from app.services.status_handlers.milestone_handler import MilestoneStatusHandler


class TestMilestoneStatusHandlerInit:
    def test_init(self):
        assert callable(MilestoneStatusHandler.handle_milestone_completed)
