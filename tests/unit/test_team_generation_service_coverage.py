# -*- coding: utf-8 -*-
"""team_generation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.team_generation_service import TeamGenerationService

class TestTeamGenerationServiceInit:
    def test_init(self):
        service = TeamGenerationService(Mock())
        assert service is not None
