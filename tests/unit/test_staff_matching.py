# -*- coding: utf-8 -*-
"""Tests for staff_matching/matching.py"""

from unittest.mock import MagicMock, patch

import pytest


class TestMatchingEngine:
    def test_import(self):
        from app.services.staff_matching.matching import MatchingEngine
        assert MatchingEngine is not None

    def test_match_candidates_no_need_raises(self):
        from app.services.staff_matching.matching import MatchingEngine
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="人员需求不存在"):
            MatchingEngine.match_candidates(db, staffing_need_id=999)
