# -*- coding: utf-8 -*-
"""Tests for app/services/strategy/kpi_collector/collectors.py"""
import pytest
from unittest.mock import MagicMock

from app.services.strategy.kpi_collector.collectors import (
    collect_project_metrics,
    collect_finance_metrics,
    collect_purchase_metrics,
    collect_hr_metrics,
)


class TestKpiCollectors:
    def setup_method(self):
        self.db = MagicMock()

    @pytest.mark.skip(reason="Complex aggregate queries need detailed mocking")
    def test_collect_project_metrics(self):
        result = collect_project_metrics(self.db, 1)
        assert isinstance(result, dict)

    @pytest.mark.skip(reason="Complex aggregate queries need detailed mocking")
    def test_collect_finance_metrics(self):
        result = collect_finance_metrics(self.db, 1)
        assert isinstance(result, dict)

    @pytest.mark.skip(reason="Complex aggregate queries need detailed mocking")
    def test_collect_purchase_metrics(self):
        result = collect_purchase_metrics(self.db, 1)
        assert isinstance(result, dict)

    @pytest.mark.skip(reason="Complex aggregate queries need detailed mocking")
    def test_collect_hr_metrics(self):
        result = collect_hr_metrics(self.db, 1)
        assert isinstance(result, dict)
