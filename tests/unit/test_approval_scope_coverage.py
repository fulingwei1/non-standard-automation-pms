# -*- coding: utf-8 -*-
"""approval_scope单元测试"""

import pytest
from app.services.approval_engine.approval_scope import ParticipantRole


class TestParticipantRoleInit:
    def test_init(self):
        assert ParticipantRole.INITIATOR.value == "INITIATOR"
