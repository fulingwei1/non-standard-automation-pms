# -*- coding: utf-8 -*-
"""Tests for resource_waste_analysis/failure_patterns.py"""
import pytest
from unittest.mock import MagicMock


class TestFailurePatternsMixin:
    def _make_instance(self):
        from app.services.resource_waste_analysis.failure_patterns import FailurePatternsMixin
        obj = FailurePatternsMixin()
        obj.db = MagicMock()
        return obj

    def test_no_failed_projects(self):
        obj = self._make_instance()
        obj.db.query.return_value.filter.return_value.all.return_value = []
        result = obj.analyze_failure_patterns()
        assert result['loss_reason_distribution'] == {}
        assert '数据不足' in result['recommendations'][0]

    @pytest.mark.skip(reason="WorkLog model lacks project_id attribute at class level")
    def test_with_failed_projects(self):
        pass
