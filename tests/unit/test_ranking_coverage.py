# -*- coding: utf-8 -*-
"""ranking单元测试"""
from app.services.lead_priority_scoring.ranking import RankingMixin


class TestRankingMixinInit:
    def test_init(self):
        assert hasattr(RankingMixin, "get_priority_ranking")
