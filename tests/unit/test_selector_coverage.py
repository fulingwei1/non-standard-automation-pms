# -*- coding: utf-8 -*-
"""selector单元测试"""
import pytest
from unittest.mock import Mock
from app.services.collaboration_rating.selector import CollaboratorSelector

class TestCollaboratorSelectorInit:
    def test_init(self):
        service = CollaboratorSelector(Mock())
        assert service is not None
