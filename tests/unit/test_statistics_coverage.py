# -*- coding: utf-8 -*-
"""statistics单元测试"""
from app.services.collaboration_rating.statistics import RatingStatistics


class TestRatingStatisticsInit:
    def test_init(self):
        assert RatingStatistics.__init__ is not None
