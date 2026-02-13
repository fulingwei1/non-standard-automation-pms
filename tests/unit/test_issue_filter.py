# -*- coding: utf-8 -*-
"""Tests for data_scope/issue_filter.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestIssueFilterService:
    def test_superuser_no_filter(self):
        from app.services.data_scope.issue_filter import IssueFilterService
        db = MagicMock()
        query = MagicMock()
        user = MagicMock(is_superuser=True)
        result = IssueFilterService.filter_issues_by_scope(db, query, user)
        assert result is query

    @patch('app.services.data_scope.issue_filter.UserScopeService')
    def test_own_scope(self, mock_scope_svc):
        from app.services.data_scope.issue_filter import IssueFilterService
        mock_scope_svc.get_user_data_scope.return_value = "OWN"
        db = MagicMock()
        query = MagicMock()
        user = MagicMock(is_superuser=False, id=1)
        result = IssueFilterService.filter_issues_by_scope(db, query, user)
        query.filter.assert_called_once()

    @patch('app.services.data_scope.issue_filter.UserScopeService')
    def test_all_scope(self, mock_scope_svc):
        from app.services.data_scope.issue_filter import IssueFilterService
        mock_scope_svc.get_user_data_scope.return_value = "ALL"
        db = MagicMock()
        query = MagicMock()
        user = MagicMock(is_superuser=False)
        result = IssueFilterService.filter_issues_by_scope(db, query, user)
        assert result is query
