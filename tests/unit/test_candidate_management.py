# -*- coding: utf-8 -*-
"""候选人管理单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.staff_matching.candidate_management import CandidateManager


class TestCandidateManager:
    def setup_method(self):
        self.db = MagicMock()

    def test_accept_candidate_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert CandidateManager.accept_candidate(self.db, 999, 1) is False

    def test_accept_candidate_success(self):
        log = MagicMock()
        log.staffing_need_id = 1
        need = MagicMock()
        need.filled_count = 0
        need.headcount = 2
        self.db.query.return_value.filter.return_value.first.side_effect = [log, need]
        result = CandidateManager.accept_candidate(self.db, 1, 10)
        assert result is True
        assert log.is_accepted is True
        self.db.commit.assert_called_once()

    def test_accept_candidate_fills_need(self):
        log = MagicMock()
        log.staffing_need_id = 1
        need = MagicMock()
        need.filled_count = 1
        need.headcount = 2
        self.db.query.return_value.filter.return_value.first.side_effect = [log, need]
        CandidateManager.accept_candidate(self.db, 1, 10)
        assert need.status == 'FILLED'

    def test_reject_candidate_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert CandidateManager.reject_candidate(self.db, 999, "不合适") is False

    def test_reject_candidate_success(self):
        log = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = log
        result = CandidateManager.reject_candidate(self.db, 1, "不合适")
        assert result is True
        assert log.is_accepted is False
        assert log.reject_reason == "不合适"

    def test_get_matching_history(self):
        self.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = CandidateManager.get_matching_history(self.db, project_id=1)
        assert result == []

    def test_get_matching_history_no_filters(self):
        self.db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = CandidateManager.get_matching_history(self.db)
        assert isinstance(result, list)
