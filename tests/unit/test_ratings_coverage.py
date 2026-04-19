# -*- coding: utf-8 -*-
"""ratings单元测试"""
from app.services.collaboration_rating.ratings import RatingManager


class TestRatingManagerInit:
    def test_init(self):
        assert RatingManager.__init__ is not None
