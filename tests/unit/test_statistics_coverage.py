# -*- coding: utf-8 -*-
"""statistics单元测试"""
import pytest
from unittest.mock import Mock
from app.services.collaboration_rating.statistics import RatingStatistics

class TestRatingStatisticsInit:
    def test_init(self):
        service = RatingStatistics(Mock())
        assert service is not None
