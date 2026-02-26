# -*- coding: utf-8 -*-
"""Tests for app.services.statistics.base"""
from datetime import date
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from app.services.statistics.base import (
    AggregationServiceProtocol,
    SyncStatisticsService,
)


class FakeModel:
    id = "id_col"
    status = "status_col"
    severity = "severity_col"

    class _notin:
        pass


class TestSyncStatisticsService:
    def test_import(self):
        from app.services.statistics import SyncStatisticsService, AggregationServiceProtocol
        assert SyncStatisticsService is not None
        assert AggregationServiceProtocol is not None

    def test_aggregation_protocol_isinstance(self):
        class MyAgg:
            def aggregate(self, start_date, end_date, **kwargs):
                return {}

        assert isinstance(MyAgg(), AggregationServiceProtocol)

    def test_aggregation_protocol_not_isinstance(self):
        class NotAgg:
            pass

        assert not isinstance(NotAgg(), AggregationServiceProtocol)
