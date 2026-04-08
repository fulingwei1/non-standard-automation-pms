# -*- coding: utf-8 -*-
"""issue_filter单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_scope.issue_filter import IssueFilterService

class TestIssueFilterServiceInit:
    def test_init(self):
        service = IssueFilterService(Mock())
        assert service is not None
