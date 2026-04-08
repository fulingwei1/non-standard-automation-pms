# -*- coding: utf-8 -*-
"""pitfall_service单元测试"""
import pytest
from unittest.mock import Mock
from services/pitfall/pitfall_service import PitfallService

class TestPitfallServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PitfallService(mock_db)
        assert hasattr(service, 'db')
