# -*- coding: utf-8 -*-
"""Tests for data_integrity/auto_fix.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestAutoFixMixin:
    def _make_instance(self):
        from app.services.data_integrity.auto_fix import AutoFixMixin
        obj = AutoFixMixin()
        obj.db = MagicMock()
        obj.check_data_completeness = MagicMock()
        return obj

    def test_suggest_no_issues(self):
        obj = self._make_instance()
        obj.check_data_completeness.return_value = {
            'collab_ratings_count': 5,
            'work_logs_count': 10,
            'warnings': []
        }
        result = obj.suggest_auto_fixes(1, 1)
        assert result == []

    def test_suggest_low_collab(self):
        obj = self._make_instance()
        obj.check_data_completeness.return_value = {
            'collab_ratings_count': 1,
            'work_logs_count': 10,
            'warnings': []
        }
        result = obj.suggest_auto_fixes(1, 1)
        assert any(s['type'] == 'auto_select_collaborators' for s in result)

    def test_suggest_no_work_logs(self):
        obj = self._make_instance()
        obj.check_data_completeness.return_value = {
            'collab_ratings_count': 5,
            'work_logs_count': 0,
            'warnings': []
        }
        result = obj.suggest_auto_fixes(1, 1)
        assert any(s['type'] == 'remind_work_log' for s in result)

    def test_auto_fix_no_fixable(self):
        obj = self._make_instance()
        obj.check_data_completeness.return_value = {
            'collab_ratings_count': 5,
            'work_logs_count': 0,
            'warnings': []
        }
        result = obj.auto_fix_data_issues(1, 1)
        assert result['total_applied'] == 0

    def test_auto_fix_with_collaborators(self):
        obj = self._make_instance()
        obj.check_data_completeness.return_value = {
            'collab_ratings_count': 1,
            'work_logs_count': 10,
            'warnings': []
        }
        with patch('app.services.collaboration_rating.CollaborationRatingService') as mock_svc:
            mock_instance = MagicMock()
            mock_instance.auto_select_collaborators.return_value = [1, 2, 3]
            mock_svc.return_value = mock_instance
            result = obj.auto_fix_data_issues(1, 1)
            assert result['total_applied'] == 1

    def test_auto_fix_exception(self):
        obj = self._make_instance()
        obj.check_data_completeness.return_value = {
            'collab_ratings_count': 1,
            'work_logs_count': 10,
            'warnings': []
        }
        with patch('app.services.collaboration_rating.CollaborationRatingService', side_effect=Exception("err")):
            result = obj.auto_fix_data_issues(1, 1)
            assert result['total_failed'] == 1
