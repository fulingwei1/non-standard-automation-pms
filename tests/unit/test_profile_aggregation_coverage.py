# -*- coding: utf-8 -*-
"""profile_aggregation单元测试"""
import pytest
from unittest.mock import Mock
from app.services.staff_matching.profile_aggregation import ProfileAggregator

class TestProfileAggregatorInit:
    def test_init(self):
        service = ProfileAggregator(Mock())
        assert service is not None
