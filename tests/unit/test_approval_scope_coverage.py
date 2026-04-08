# -*- coding: utf-8 -*-
"""approval_scope单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.approval_scope import ParticipantRole

class TestParticipantRoleInit:
    def test_init(self):
        service = ParticipantRole(Mock())
        assert service is not None
