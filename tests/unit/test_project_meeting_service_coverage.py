# -*- coding: utf-8 -*-
"""project_meeting_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_meeting_service import ProjectMeetingService

class TestProjectMeetingServiceInit:
    def test_init(self):
        service = ProjectMeetingService(Mock())
        assert service is not None
