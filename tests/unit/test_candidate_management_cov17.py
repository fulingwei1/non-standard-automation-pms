# -*- coding: utf-8 -*-
"""第十七批 - 候选人管理服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.staff_matching.candidate_management")


def _make_db():
    return MagicMock()


class TestCandidateManager:

    def test_accept_candidate_log_not_found(self):
        """匹配日志不存在时返回 False"""
        from app.services.staff_matching.candidate_management import CandidateManager
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = CandidateManager.accept_candidate(db, matching_log_id=999, acceptor_id=1)
        assert result is False

    def test_accept_candidate_success(self):
        """成功采纳候选人，更新日志和需求计数"""
        from app.services.staff_matching.candidate_management import CandidateManager
        db = _make_db()
        log = MagicMock()
        log.staffing_need_id = 10

        staffing_need = MagicMock()
        staffing_need.filled_count = 1
        staffing_need.headcount = 3

        db.query.return_value.filter.return_value.first.side_effect = [log, staffing_need]
        result = CandidateManager.accept_candidate(db, matching_log_id=1, acceptor_id=5)

        assert result is True
        assert log.is_accepted is True
        assert log.acceptor_id == 5
        assert staffing_need.filled_count == 2
        db.commit.assert_called_once()

    def test_accept_candidate_fills_need_when_count_reaches_headcount(self):
        """filled_count 达到 headcount 时状态变为 FILLED"""
        from app.services.staff_matching.candidate_management import CandidateManager
        db = _make_db()
        log = MagicMock()
        log.staffing_need_id = 10

        staffing_need = MagicMock()
        staffing_need.filled_count = 2
        staffing_need.headcount = 3

        db.query.return_value.filter.return_value.first.side_effect = [log, staffing_need]
        CandidateManager.accept_candidate(db, matching_log_id=1, acceptor_id=5)

        assert staffing_need.status == "FILLED"

    def test_reject_candidate_log_not_found(self):
        """匹配日志不存在时返回 False"""
        from app.services.staff_matching.candidate_management import CandidateManager
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = CandidateManager.reject_candidate(db, matching_log_id=999, reject_reason="技能不匹配")
        assert result is False

    def test_reject_candidate_success(self):
        """成功拒绝候选人"""
        from app.services.staff_matching.candidate_management import CandidateManager
        db = _make_db()
        log = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = log

        result = CandidateManager.reject_candidate(db, matching_log_id=1, reject_reason="不符合要求")

        assert result is True
        assert log.is_accepted is False
        assert log.reject_reason == "不符合要求"
        db.commit.assert_called_once()

    def test_get_matching_history_no_filters(self):
        """无过滤条件时返回所有匹配历史"""
        from app.services.staff_matching.candidate_management import CandidateManager
        db = _make_db()
        fake_logs = [MagicMock(), MagicMock()]
        db.query.return_value.order_by.return_value.limit.return_value.all.return_value = fake_logs

        result = CandidateManager.get_matching_history(db)
        assert result == fake_logs

    def test_get_matching_history_with_project_filter(self):
        """按 project_id 过滤匹配历史"""
        from app.services.staff_matching.candidate_management import CandidateManager
        db = _make_db()
        fake_logs = [MagicMock()]
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = fake_logs

        result = CandidateManager.get_matching_history(db, project_id=7)
        assert result == fake_logs
